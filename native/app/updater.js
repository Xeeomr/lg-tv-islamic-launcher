'use strict';
// Updates from GitHub releases without a computer. A release carries update.json, signed with the
// project's Ed25519 key, listing each package with its version and SHA-256. Nothing is installed unless
// the signature and every hash match. Home is updated while it is not in use; Helper updates last and
// restarts itself.
var https = require('https'), crypto = require('crypto'), fs = require('fs'), cp = require('child_process');
var REPO = 'Xeeomr/lg-tv-islamic-launcher';
var PUBLIC_KEY = '-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEAOeoLDY1uLsYF7LqFf19bd5RIAngtQsJ0ACQTnc6Mjro=\n-----END PUBLIC KEY-----\n';
var APPS = '/media/developer/apps/usr/palm/applications/';
var HELPER = 'com.local.nativehome';

module.exports = function (ctx) {
  var data = ctx.data, log = ctx.log, statusPath = data + '/update-status.json', busy = false, timer = null;
  var status = read(statusPath) || {};
  function read(p) { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { return null; } }
  function save(extra) {
    Object.keys(extra || {}).forEach(function (k) { status[k] = extra[k]; });
    status.installed = installed();
    try { fs.writeFileSync(statusPath + '.tmp', JSON.stringify(status), {mode: 420}); fs.renameSync(statusPath + '.tmp', statusPath); } catch (e) {}
  }
  function installed() {
    var out = {};
    ['com.gathin.tvhome', HELPER].forEach(function (id) { var a = read(APPS + id + '/appinfo.json'); out[id] = a ? a.version : null; });
    return out;
  }
  function newer(a, b) {
    var x = String(a || '0').split('.').map(Number), y = String(b || '0').split('.').map(Number);
    for (var i = 0; i < 3; i++) { if ((x[i] || 0) !== (y[i] || 0)) return (x[i] || 0) > (y[i] || 0); }
    return false;
  }
  function get(url, binary, cb, hops) {
    var req = https.get(url, {headers: {'User-Agent': 'XeeLauncher', 'Accept': binary ? 'application/octet-stream' : 'application/vnd.github+json'}, timeout: 30000}, function (res) {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location && (hops || 0) < 5) { res.resume(); return get(res.headers.location, binary, cb, (hops || 0) + 1); }
      if (res.statusCode !== 200) { res.resume(); return cb(new Error('http-' + res.statusCode)); }
      var chunks = [], size = 0;
      res.on('data', function (c) { size += c.length; if (size > 60 * 1024 * 1024) { req.destroy(); return; } chunks.push(c); });
      res.on('end', function () { cb(null, Buffer.concat(chunks)); });
    });
    req.on('timeout', function () { req.destroy(new Error('timeout')); });
    req.on('error', function (e) { cb(e); });
  }
  // The signed text is the manifest without its signature, with keys in a fixed order.
  function signedText(m) { return JSON.stringify({version: m.version, apps: m.apps.map(function (a) { return {id: a.id, version: a.version, file: a.file, sha256: a.sha256}; })}); }
  function verify(m) {
    try {
      if (!m || typeof m.version !== 'string' || !Array.isArray(m.apps) || typeof m.signature !== 'string') return false;
      return crypto.verify(null, Buffer.from(signedText(m)), PUBLIC_KEY, Buffer.from(m.signature, 'base64'));
    } catch (e) { return false; }
  }
  function check(done) {
    if (busy) return done && done();
    busy = true; save({state: 'checking', error: ''});
    get('https://api.github.com/repos/' + REPO + '/releases/latest', false, function (err, buf) {
      var rel; try { rel = !err && JSON.parse(buf.toString('utf8')); } catch (e) { rel = null; }
      var asset = rel && (rel.assets || []).filter(function (a) { return a.name === 'update.json'; })[0];
      if (!asset) { busy = false; save({state: 'idle', checkedAt: Date.now(), error: err && !/http-404/.test(err.message) ? 'connection' : 'no-release'}); return done && done(); }
      get(asset.browser_download_url, true, function (err2, mbuf) {
        var m; try { m = !err2 && JSON.parse(mbuf.toString('utf8')); } catch (e) { m = null; }
        if (!verify(m)) { busy = false; save({state: 'idle', checkedAt: Date.now(), error: 'bad-signature'}); log({event: 'update-bad-signature'}); return done && done(); }
        var have = installed(), pending = m.apps.filter(function (a) { return have[a.id] && newer(a.version, have[a.id]); });
        busy = false;
        save({state: 'idle', checkedAt: Date.now(), latest: m.version, notes: String(rel.body || '').slice(0, 1500), available: pending.length > 0,
          manifest: m, assets: (rel.assets || []).map(function (a) { return {name: a.name, url: a.browser_download_url}; })});
        log({event: 'update-checked', latest: m.version, available: pending.length});
        if (done) done();
      });
    });
  }
  function luna(uri, payload, terminal, cb) {
    // luna-send-pub exits early when its stdin closes, so keep it open and stop it on the final reply.
    var child = cp.spawn('/usr/bin/luna-send-pub', ['-i', uri, JSON.stringify(payload)], {stdio: ['pipe', 'pipe', 'pipe']}), out = '', ended = false;
    var t = setTimeout(function () { finish(new Error('timeout')); }, 180000);
    function finish(err) { if (ended) return; ended = true; clearTimeout(t); try { child.kill(); } catch (e) {} cb(err, out); }
    child.stdout.on('data', function (b) {
      out += b; if (out.length > 20000) out = out.slice(-10000);
      if (out.indexOf('"' + terminal + '"') >= 0) finish(null);
      else if (/"returnValue"\s*:\s*false|"state"\s*:\s*"(failed|install failed)"/i.test(out)) finish(new Error('install-failed'));
    });
    child.on('error', finish); child.on('exit', function () { setTimeout(function () { finish(out.indexOf('"' + terminal + '"') >= 0 ? null : new Error('exited')); }, 200); });
  }
  function download(app, cb) {
    var asset = (status.assets || []).filter(function (a) { return a.name === app.file; })[0];
    if (!asset || !/^[A-Za-z0-9._-]+\.ipk$/.test(app.file)) return cb(new Error('missing-asset'));
    get(asset.url, true, function (err, buf) {
      if (err) return cb(err);
      if (crypto.createHash('sha256').update(buf).digest('hex') !== app.sha256) return cb(new Error('hash-mismatch'));
      try { if (!fs.existsSync(data + '/dl')) fs.mkdirSync(data + '/dl'); } catch (e) {}
      var p = data + '/dl/' + app.file;
      fs.writeFile(p, buf, function (e) { cb(e, p); });
    });
  }
  function install() {
    var m = status.manifest;
    if (busy || !m || !verify(m)) return;
    var have = installed(), list = m.apps.filter(function (a) { return have[a.id] && newer(a.version, have[a.id]); });
    if (!list.length) return save({available: false});
    busy = true; save({state: 'downloading', error: ''});
    list.sort(function (a, b) { return (a.id === HELPER) - (b.id === HELPER); });
    var files = [];
    (function next(i) {
      if (i < list.length) return download(list[i], function (err, p) {
        if (err) { busy = false; log({event: 'update-download-failed', error: String(err.message)}); return save({state: 'idle', error: 'download'}); }
        files.push({app: list[i], path: p}); next(i + 1);
      });
      save({state: 'installing'});
      (function inst(j) {
        if (j >= files.length) { busy = false; return save({state: 'done', available: false, doneAt: Date.now()}); }
        var f = files[j];
        if (f.app.id === HELPER) return selfUpdate(f.path);
        log({event: 'update-install', id: f.app.id, version: f.app.version});
        luna('luna://com.webos.appInstallService/dev/install', {id: f.app.id, ipkUrl: f.path, subscribe: true}, 'installed', function (err) {
          if (err) { busy = false; log({event: 'update-install-failed', id: f.app.id, error: String(err.message)}); return save({state: 'idle', error: 'install'}); }
          try { fs.unlinkSync(f.path); } catch (e) {}
          if (f.app.id === 'com.gathin.tvhome') setTimeout(function () { ctx.homeUpdated(); }, 1500);
          inst(j + 1);
        });
      }(0));
    }(0));
  }
  // Installing Helper replaces this process's files: a detached script installs, stops this controller,
  // and starts the new one.
  function selfUpdate(ipk) {
    save({state: 'restarting'});
    log({event: 'update-self', ipk: ipk});
    var script = data + '/self-update.sh', q = function (s) { return "'" + String(s).replace(/'/g, "'\\''") + "'"; };
    fs.writeFileSync(script, [
      '#!/bin/sh',
      'L=' + q(data + '/self-update.log'),
      '( sleep 300 ) | /usr/bin/luna-send-pub -i luna://com.webos.appInstallService/dev/install ' + q(JSON.stringify({id: HELPER, ipkUrl: ipk, subscribe: true})) + ' > "$L" 2>&1 &',
      'P=$!',
      'n=0; while [ $n -lt 150 ]; do grep -q \'"installed"\' "$L" && break; grep -qi \'failed\' "$L" && break; sleep 1; n=$((n+1)); done',
      'kill $P 2>/dev/null',
      'echo \'{"cmd":"stop","n":"update-\'$(date +%s)\'"}\' > ' + q(data + '/control.json'),
      'sleep 6',
      'rm -f ' + q(ipk),
      '/usr/bin/luna-send-pub -n 1 luna://com.webos.applicationManager/launch \'{"id":"' + HELPER + '","params":{"nativeHomeStart":true}}\' >> "$L" 2>&1',
      ''].join('\n'), {mode: 493});
    cp.spawn('/bin/sh', [script], {detached: true, stdio: 'ignore'}).unref();
  }
  // Auto mode installs when nothing would be interrupted: Home not in front and nothing playing in it.
  function tick() {
    var home = read('/media/developer/apps/usr/palm/services/com.gathin.tvhome.prayer/state/remote-state.json') || {};
    var auto = !home.settings || home.settings.autoUpdate !== false;
    var due = !status.checkedAt || Date.now() - status.checkedAt > 6 * 3600000;
    if (due) return check();
    var idle = ctx.foreground() !== 'com.gathin.tvhome' && !(home.radio && home.radio.kind) && ctx.power() !== 'Screen Off';
    if (auto && status.available && idle && !busy) install();
  }
  // A restart after a self-update finishes it; any other interrupted state starts over.
  if (status.state === 'restarting') save({state: 'done', available: false, doneAt: Date.now()});
  else if (status.state && status.state !== 'idle' && status.state !== 'done') save({state: 'idle'});
  else save({});
  // Background work never keeps a process alive on its own.
  var first = setTimeout(tick, 120000); if (first.unref) first.unref();
  timer = setInterval(tick, 10 * 60000); if (timer.unref) timer.unref();
  return {
    request: function (what) { if (what === 'install') check(install); else check(); },
    close: function () { clearInterval(timer); }
  };
};
