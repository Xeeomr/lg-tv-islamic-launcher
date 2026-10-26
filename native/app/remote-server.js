'use strict';
// Xee Remote: a small web app served on the local network so a phone can drive the TV and Home.
// A phone pairs once with a code shown on the TV; every other request needs the token it receives.
// Home commands travel through Home's own service directory; private assets (fonts, adhans) are
// served to the TV itself only.
var http = require('http'), crypto = require('crypto'), fs = require('fs'), path = require('path');
var PORT = 8090, HOME = 'com.gathin.tvhome';
var HOME_DIR = '/media/developer/apps/usr/palm/applications/com.gathin.tvhome';
var PRAYER_STATE = '/media/developer/apps/usr/palm/services/com.gathin.tvhome.prayer/state';
var KEYS = ['UP', 'DOWN', 'LEFT', 'RIGHT', 'ENTER', 'BACK', 'EXIT', 'MENU', 'INFO', 'PLAY', 'PAUSE', 'STOP', 'FASTFORWARD', 'REWIND',
  'MUTE', 'VOLUMEUP', 'VOLUMEDOWN', 'CHANNELUP', 'CHANNELDOWN', 'RED', 'GREEN', 'YELLOW', 'BLUE', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
var TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.woff2': 'font/woff2',
  '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.webmanifest': 'application/manifest+json'};

module.exports = function (ctx) {
  var data = ctx.data, log = ctx.log, ui = path.join(__dirname, 'remote-ui'), assets = path.join(data, 'assets');
  var tokensPath = data + '/remote-tokens.json', pairing = null, apps = null, appsAt = 0, icons = {};
  function readJSON(p, fallback) { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch (e) { return fallback; } }
  function writeJSON(p, value, mode) {
    fs.writeFileSync(p + '.tmp', JSON.stringify(value), {mode: mode || 420}); fs.renameSync(p + '.tmp', p);
  }
  function tokens() { var t = readJSON(tokensPath, []); return Array.isArray(t) ? t : []; }
  function hash(t) { return crypto.createHash('sha256').update(String(t)).digest('hex'); }
  function authorized(req) {
    // Images cannot send headers, so icons may carry the token in the query string.
    var t = req.headers['x-xee-token'] || (/^\/api\/icon\?/.test(req.url) && (String(req.url).match(/[?&]t=([a-f0-9]+)/) || [])[1]);
    if (typeof t !== 'string' || t.length < 32) return false;
    var h = hash(t);
    return tokens().some(function (x) { return x.h === h; });
  }
  function local(req) {
    var a = String(req.socket.remoteAddress || '').replace(/^::ffff:/, '');
    return a === '127.0.0.1' || a === '::1' || a === ctx.address();
  }
  function send(res, code, body, type, extra) {
    var headers = Object.assign({'Content-Type': type || 'application/json; charset=utf-8', 'Cache-Control': 'no-store'}, extra || {});
    res.writeHead(code, headers);
    res.end(typeof body === 'string' || Buffer.isBuffer(body) ? body : JSON.stringify(body));
  }
  function file(res, p, extra) {
    fs.readFile(p, function (err, buf) {
      if (err) return send(res, 404, {error: 'not-found'});
      send(res, 200, buf, TYPES[path.extname(p).toLowerCase()] || 'application/octet-stream', Object.assign({'Cache-Control': 'max-age=300'}, extra || {}));
    });
  }
  function body(req, cb) {
    var chunks = [], size = 0;
    req.on('data', function (c) { size += c.length; if (size > 65536) { req.destroy(); return; } chunks.push(c); });
    req.on('end', function () { try { cb(chunks.length ? JSON.parse(Buffer.concat(chunks).toString('utf8')) : {}); } catch (e) { cb(null); } });
  }

  // ---- Home commands ---------------------------------------------------------------------------
  function queue(cmd) {
    var list = readJSON(PRAYER_STATE + '/remote-queue.json', []);
    if (!Array.isArray(list)) list = [];
    list.push(cmd); writeJSON(PRAYER_STATE + '/remote-queue.json', list.slice(-30), 438);
  }
  var FRONT = /^(radio\.play|mushaf\.play|mushaf\.continue|live\.open|open\.|adhan\.test)/;
  function homeCommand(cmd, done) {
    cmd.id = crypto.randomBytes(6).toString('hex'); cmd.at = Date.now();
    // Home in front gets the command at once through a relaunch; audio and screens bring Home forward.
    if (ctx.foreground() === HOME || FRONT.test(cmd.type)) ctx.launchWith(HOME, {remote: cmd}, function (ok) { done({returnValue: ok, delivered: true}); });
    else { try { queue(cmd); done({returnValue: true, queued: true}); } catch (e) { done({returnValue: false, errorText: 'queue-unavailable'}); } }
  }

  // ---- TV state ------------------------------------------------------------------------------
  function listApps(cb) {
    if (apps && Date.now() - appsAt < 600000) return cb(apps);
    ctx.ssapCall('ssap://com.webos.applicationManager/listLaunchPoints', {}, function (r) {
      var list = (r && r.launchPoints || []).filter(function (a) { return a.id && a.title && a.id !== 'com.local.nativehome'; })
        .map(function (a) { return {id: a.id, title: a.title, icon: a.largeIcon || a.mediumLargeIcon || a.icon || '', bg: a.bgColor || ''}; });
      if (list.length) { apps = list; appsAt = Date.now(); }
      cb(apps || []);
    }, 8000);
  }
  function status(cb) {
    var home = readJSON(PRAYER_STATE + '/remote-state.json', null), update = readJSON(data + '/update-status.json', null);
    ctx.ssapCall('ssap://audio/getVolume', {}, function (v) {
      var vs = v && (v.volumeStatus || v);
      cb({returnValue: true, tv: {foreground: ctx.foreground(), power: ctx.power(), volume: vs && typeof vs.volume === 'number' ? vs.volume : null, muted: !!(vs && (vs.muteStatus || vs.muted))},
        home: home, update: update, paired: tokens().length});
    }, 2500);
  }

  // ---- routes --------------------------------------------------------------------------------
  function api(req, res, route, payload) {
    var p = payload || {};
    switch (route) {
      case 'status': return status(function (r) { send(res, 200, r); });
      case 'catalog': return send(res, 200, readJSON(PRAYER_STATE + '/remote-catalog.json', {}));
      case 'apps': return listApps(function (list) { send(res, 200, {returnValue: true, apps: list.map(function (a) { return {id: a.id, title: a.title, bg: a.bg}; })}); });
      case 'key':
        if (p.key === 'HOME') return ctx.launchWith(HOME, null, function (ok) { send(res, 200, {returnValue: ok}); });
        if (KEYS.indexOf(p.key) < 0) return send(res, 400, {returnValue: false, errorText: 'unknown-key'});
        ctx.ssapButton(p.key); return send(res, 200, {returnValue: true});
      case 'volume':
        var uri = p.action === 'up' ? 'ssap://audio/volumeUp' : p.action === 'down' ? 'ssap://audio/volumeDown' : p.action === 'mute' ? 'ssap://audio/setMute' : 'ssap://audio/setVolume';
        var args = p.action === 'mute' ? {mute: !!p.value} : p.action === 'set' ? {volume: Math.max(0, Math.min(100, p.value | 0))} : {};
        return ctx.ssapCall(uri, args, function (r) { send(res, 200, r || {}); });
      case 'launch':
        if (typeof p.id !== 'string' || !/^[A-Za-z0-9._-]+$/.test(p.id)) return send(res, 400, {returnValue: false});
        ctx.noteRemoteLaunch();
        return ctx.ssapCall('ssap://system.launcher/launch', {id: p.id}, function (r) { send(res, 200, r || {}); });
      case 'power':
        if (p.action === 'off') return ctx.ssapCall('ssap://system/turnOff', {}, function (r) { send(res, 200, r || {}); });
        if (p.action === 'screenOff' || p.action === 'screenOn')
          return ctx.ssapCall('ssap://com.webos.service.tvpower/power/' + (p.action === 'screenOff' ? 'turnOffScreen' : 'turnOnScreen'), {standbyMode: 'active'}, function (r) { send(res, 200, r || {}); });
        return send(res, 400, {returnValue: false});
      case 'text':
        var text = String(p.text || '').slice(0, 200);
        return ctx.ssapCall('ssap://com.webos.service.ime/insertText', {text: text, replace: 0}, function (r) {
          if (p.enter) ctx.ssapCall('ssap://com.webos.service.ime/sendEnterKey', {}, function () {});
          send(res, 200, r || {});
        });
      case 'home':
        if (!p.cmd || typeof p.cmd.type !== 'string' || p.cmd.type.length > 40) return send(res, 400, {returnValue: false});
        return homeCommand(p.cmd, function (r) { send(res, 200, r); });
      case 'update':
        ctx.updater.request(p.action === 'install' ? 'install' : 'check');
        return send(res, 200, {returnValue: true});
      case 'unpair':
        var h = hash(req.headers['x-xee-token']);
        writeJSON(tokensPath, tokens().filter(function (x) { return x.h !== h; }), 420);
        return send(res, 200, {returnValue: true});
    }
    send(res, 404, {returnValue: false, errorText: 'unknown'});
  }
  function pair(req, res, route, p) {
    var now = Date.now();
    if (route === 'pair') {
      if (pairing && now < pairing.until && now - pairing.at < 15000) return send(res, 429, {returnValue: false, errorText: 'wait'});
      var code = String(crypto.randomBytes(4).readUInt32BE(0) % 9000 + 1000);
      pairing = {code: code, at: now, until: now + 300000, tries: 0};
      ctx.ssapCall('ssap://system.notifications/createToast', {message: 'رمز ربط الموبايل بـ Xee Launcher: ' + code}, function () {});
      log({event: 'remote-pair-request'});
      return send(res, 200, {returnValue: true, expires: 300});
    }
    if (!pairing || now > pairing.until) return send(res, 400, {returnValue: false, errorText: 'expired'});
    if (++pairing.tries > 5) { pairing = null; return send(res, 400, {returnValue: false, errorText: 'too-many'}); }
    if (!p || String(p.code) !== pairing.code) return send(res, 400, {returnValue: false, errorText: 'wrong-code'});
    pairing = null;
    var token = crypto.randomBytes(24).toString('hex'), list = tokens();
    list.push({h: hash(token), name: String(p.name || 'هاتف').slice(0, 40), at: now});
    writeJSON(tokensPath, list.slice(-10), 420);
    ctx.ssapCall('ssap://system.notifications/createToast', {message: 'تم ربط الموبايل بـ Xee Launcher'}, function () {});
    log({event: 'remote-paired'});
    send(res, 200, {returnValue: true, token: token});
  }
  // A paired device can add private fonts and adhan recordings; they stay in Helper's data and survive updates.
  function upload(req, res, query) {
    if (!authorized(req)) { req.resume(); return send(res, 401, {returnValue: false, errorText: 'pair-required'}); }
    var rel = decodeURIComponent((String(query || '').match(/(?:^|&)path=([^&]+)/) || [])[1] || '');
    if (!/^(fonts\/[A-Za-z0-9._-]+\.woff2|audio\/[A-Za-z0-9._-]+\.(mp3|ogg|m4a)|audio\/voices\.json)$/.test(rel)) { req.resume(); return send(res, 400, {returnValue: false, errorText: 'bad-path'}); }
    var target = path.join(assets, rel), chunks = [], size = 0, failed = false;
    req.on('data', function (c) { size += c.length; if (size > 25 * 1024 * 1024) { failed = true; req.destroy(); return; } chunks.push(c); });
    req.on('end', function () {
      if (failed) return;
      try {
        [assets, path.dirname(target)].forEach(function (d) { if (!fs.existsSync(d)) fs.mkdirSync(d, {mode: 493}); });
        fs.writeFileSync(target + '.tmp', Buffer.concat(chunks), {mode: 420}); fs.renameSync(target + '.tmp', target);
        log({event: 'asset-uploaded', path: rel, bytes: size});
        send(res, 200, {returnValue: true, bytes: size});
      } catch (e) { send(res, 500, {returnValue: false, errorText: e.code || String(e)}); }
    });
  }
  var server = http.createServer(function (req, res) {
    var url = String(req.url || '/').split('?'), pathname = decodeURIComponent(url[0]);
    // Private assets for Home on this TV only (fonts and adhans that may not be redistributed).
    if (pathname.indexOf('/assets/') === 0) {
      if (!local(req)) return send(res, 403, {error: 'local-only'});
      var rel = pathname.slice(8);
      if (!/^[A-Za-z0-9._\/-]+$/.test(rel) || rel.indexOf('..') >= 0) return send(res, 400, {});
      return file(res, path.join(assets, rel), {'Access-Control-Allow-Origin': '*'});
    }
    if (pathname === '/cities.json') return file(res, HOME_DIR + '/cities.json');
    if (pathname === '/api/asset' && req.method === 'POST') return upload(req, res, url[1]);
    if (pathname.indexOf('/api/') === 0) {
      var route = pathname.slice(5);
      if (req.method !== 'GET' && req.method !== 'POST') return send(res, 405, {});
      return body(req, function (p) {
        if (route === 'pair' || route === 'pair/confirm') return pair(req, res, route, p);
        if (!authorized(req)) return send(res, 401, {returnValue: false, errorText: 'pair-required'});
        if (route === 'icon') {
          var q = (String(url[1] || '').match(/(?:^|&)id=([^&]+)/) || [])[1] || '';
          return listApps(function (list) {
            var a = list.filter(function (x) { return x.id === decodeURIComponent(q); })[0];
            if (!a || !a.icon) return send(res, 404, {});
            if (icons[a.id]) return send(res, 200, icons[a.id], 'image/png', {'Cache-Control': 'max-age=86400'});
            // Launch point icons are published by the TV's own control service on this address.
            var m = /^https:\/\/([0-9.]+):3001\/resources\/[A-Za-z0-9]+\/[^?#]+\.(png|jpg|jpeg)$/i.exec(a.icon);
            if (!m || m[1] !== ctx.address()) return send(res, 404, {});
            require('https').get(a.icon, {rejectUnauthorized: false, timeout: 8000}, function (r) {
              var chunks = [];
              r.on('data', function (c) { chunks.push(c); });
              r.on('end', function () {
                if (r.statusCode !== 200) return send(res, 404, {});
                icons[a.id] = Buffer.concat(chunks);
                send(res, 200, icons[a.id], r.headers['content-type'] || 'image/png', {'Cache-Control': 'max-age=86400'});
              });
            }).on('error', function () { send(res, 404, {}); });
          });
        }
        try { api(req, res, route, p); } catch (e) { log({event: 'remote-error', error: String(e)}); send(res, 500, {returnValue: false}); }
      });
    }
    var name = pathname === '/' ? 'index.html' : pathname.slice(1);
    if (!/^[A-Za-z0-9._-]+$/.test(name)) return send(res, 404, {});
    file(res, path.join(ui, name));
  });
  server.on('error', function (e) { log({event: 'remote-server-error', error: e.code || String(e)}); });
  server.listen(PORT, function () { log({event: 'remote-server', port: PORT}); });
  if (server.unref) server.unref();
  return {close: function () { try { server.close(); } catch (e) {} }};
};
