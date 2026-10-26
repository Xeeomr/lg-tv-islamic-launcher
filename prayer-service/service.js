'use strict';
var fs = require('fs'), Service = require('webos-service'), ssap = require('./ssap');
var service = new Service('com.gathin.tvhome.prayer');
var dir = __dirname + '/state', file = dir + '/prayer.json', activityName = 'com.gathin.tvhome.prayer.tick';
var HOME = 'com.gathin.tvhome', SKIP = [HOME, 'com.local.nativehome', 'com.webos.app.home'];
var state = {enabled: false, mode: 'adhan', volume: 0, prealert: 10, events: [], fired: {}, pre: {}, pausedBy: '', prevVolume: null, volumeFor: ''};
try { state = Object.assign(state, JSON.parse(fs.readFileSync(file, 'utf8'))); } catch (_) {}
function save() {
  try {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, {mode: 448});
    fs.writeFileSync(file + '.tmp', JSON.stringify(state), {mode: 384}); fs.renameSync(file + '.tmp', file);
  } catch (_) {}
}
function call(uri, payload) {
  return new Promise(function (resolve) {
    var ended = false, req, timer = setTimeout(function () { finish({returnValue: false}); }, 10000);
    function finish(r) { if (ended) return; ended = true; clearTimeout(timer); if (req && req.cancel) req.cancel(); resolve(r); }
    try { req = service.call(uri, payload, function (m) { finish(m.payload); }); } catch (_) { finish({returnValue: false}); }
  });
}
function callerOk(m) {
  try { var id = m.ls2Message.applicationID(); return id === '' || String(id).split(' ')[0] === HOME; } catch (_) { return false; }
}
function schedule() {
  return call('luna://com.palm.activitymanager/create', {
    activity: {name: activityName, description: 'Prayer time check', type: {foreground: true, persist: true},
      schedule: {interval: '1m', precise: true}, callback: {method: 'luna://com.gathin.tvhome.prayer/tick', params: {}}},
    start: true, replace: true, subscribe: false});
}
function toast(text) { return ssap([{uri: 'ssap://system.notifications/createToast', payload: {message: text}}]).catch(function () {}); }
function launchHome(params) {
  return ssap([{uri: 'ssap://system.launcher/launch', payload: {id: HOME, params: params}}]).then(function (r) {
    if (r[0] && r[0].returnValue === false) throw new Error('launch-denied');
  }).catch(function () { return call('luna://com.webos.applicationManager/launch', {id: HOME, params: params}); });
}
function volumeOf(r) { r = r || {}; var v = r.volume !== undefined ? r.volume : r.volumeStatus && r.volumeStatus.volume; return typeof v === 'number' ? v : null; }
// Raise the TV volume once per adhan and remember the level to restore afterwards.
function raiseVolume(id) {
  if (!state.volume || state.volumeFor === id) return Promise.resolve();
  state.volumeFor = id; save();
  return ssap([{uri: 'ssap://audio/getVolume'}]).then(function (r) {
    var cur = volumeOf(r[0]);
    if (cur === null) return;
    state.prevVolume = cur; save();
    var reqs = [{uri: 'ssap://audio/setMute', payload: {mute: false}}];
    if (cur < state.volume) reqs.push({uri: 'ssap://audio/setVolume', payload: {volume: state.volume}});
    return ssap(reqs);
  }).catch(function () {});
}
function restoreVolume() {
  var prev = state.prevVolume; state.prevVolume = null; state.volumeFor = ''; save();
  if (typeof prev !== 'number') return Promise.resolve();
  return ssap([{uri: 'ssap://audio/setVolume', payload: {volume: prev}}]).catch(function () {});
}
var diag = {};
function fire(ev) {
  diag = state.diag = {at: Date.now(), id: ev.id};
  return ssap([{uri: 'ssap://com.webos.applicationManager/getForegroundAppInfo'}]).then(function (r) {
    var id = r[0] && r[0].appId, ret = id && SKIP.indexOf(id) < 0 ? id : '';
    diag.fg = id || JSON.stringify(r[0]).slice(0, 80);
    if (!ret) return ret;
    state.pausedBy = ev.id; save();
    return ssap([{uri: 'ssap://media.controls/pause'}]).then(function () { return ret; }, function () { return ret; });
  }, function (e) { diag.fgError = String(e && e.message); return ''; }).then(function (returnTo) {
    diag.returnTo = returnTo; save();
    return raiseVolume(ev.id).then(function () { return launchHome({adhan: {id: ev.id, name: ev.name, ts: ev.ts, returnTo: returnTo}}); });
  });
}
function check() {
  var now = Date.now(), work = [];
  if (!state.enabled) return Promise.resolve(0);
  state.events.forEach(function (ev) {
    var pre = state.prealert * 60000;
    if (pre && now >= ev.ts - pre && now < ev.ts && !state.pre[ev.id]) {
      state.pre[ev.id] = 1; work.push(toast('اقترب موعد صلاة ' + ev.name + ' — متبقٍ ' + Math.max(1, Math.ceil((ev.ts - now) / 60000)) + ' دقائق'));
    }
    if (now >= ev.ts && now < ev.ts + 120000 && !state.fired[ev.id]) { state.fired[ev.id] = 1; work.push(state.mode === 'notify' ? toast('حان الآن موعد صلاة ' + ev.name) : fire(ev)); }
  });
  Object.keys(state.fired).forEach(function (k) { var e = state.events.filter(function (x) { return x.id === k; })[0]; if (!e || e.ts < now - 86400000) { delete state.fired[k]; delete state.pre[k]; } });
  save();
  return Promise.all(work).then(function () { return work.length; });
}
function respond(m, extra) { m.respond(Object.assign({returnValue: true, enabled: state.enabled, events: state.events.length}, extra || {})); }
service.register('setSchedule', function (m) {
  if (!callerOk(m)) { m.respond({returnValue: false, errorText: 'caller-not-authorized'}); return; }
  var p = m.payload || {};
  state.enabled = p.enabled === true;
  state.mode = ['adhan', 'notify', 'off'].indexOf(p.mode) >= 0 ? p.mode : 'adhan';
  state.volume = Math.max(0, Math.min(60, parseInt(p.volume, 10) || 0));
  state.prealert = Math.max(0, Math.min(60, parseInt(p.prealert, 10) || 0));
  if (Array.isArray(p.events)) state.events = p.events.filter(function (e) { return e && typeof e.id === 'string' && typeof e.ts === 'number'; }).slice(0, 400);
  save();
  (state.enabled ? schedule() : call('luna://com.palm.activitymanager/cancel', {activityName: activityName})).then(function (r) { respond(m, {scheduled: !!(r && r.returnValue)}); });
});
service.register('status', function (m) {
  var base = {fired: Object.keys(state.fired).length, diag: state.diag, lastDone: state.lastDone, uid: process.getuid && process.getuid()};
  if (!(m.payload && m.payload.probe)) return respond(m, base);
  ssap([{uri: 'ssap://com.webos.applicationManager/getForegroundAppInfo'}], 6000).then(function (r) {
    base.probe = r[0] && r[0].appId; respond(m, base);
  }, function (e) { base.probe = 'error: ' + (e && e.message); respond(m, base); });
});
service.register('tick', function (m) {
  check().then(function (n) {
    if (m.activity) service.activityManager.complete(m.activity, {restart: state.enabled}, function () { respond(m, {handled: n}); });
    else respond(m, {handled: n});
  });
});
// Manual test: fires the full adhan flow now or after a delay. The keep-alive activity holds the
// service process for the countdown, so the test still runs when another app is in front.
service.register('fire', function (m) {
  if (!callerOk(m)) { m.respond({returnValue: false, errorText: 'caller-not-authorized'}); return; }
  var p = m.payload || {}, delay = Math.max(0, Math.min(120000, parseInt(p.delay, 10) || 0));
  var name = typeof p.name === 'string' && p.name.length < 20 ? p.name : 'العصر';
  function go() { var ev = {id: 'test-' + Date.now(), name: name, ts: Date.now()}; return fire(ev); }
  if (!delay) { go().then(function () { respond(m); }, function (e) { m.respond({returnValue: false, errorText: String(e && e.message)}); }); return; }
  service.activityManager.create('prayer-test-' + Date.now(), function (activity) {
    setTimeout(function () { go().catch(function () {}).then(function () { service.activityManager.complete(activity, function () {}); }); }, delay);
  });
  respond(m, {scheduled: delay});
});
service.register('toast', function (m) {
  if (!callerOk(m)) { m.respond({returnValue: false, errorText: 'caller-not-authorized'}); return; }
  var text = String((m.payload || {}).message || '').slice(0, 120), delay = Math.max(0, Math.min(60000, parseInt((m.payload || {}).delay, 10) || 0));
  if (!delay) { toast(text).then(function () { respond(m); }); return; }
  service.activityManager.create('prayer-toast-' + Date.now(), function (activity) {
    setTimeout(function () { toast(text).then(function () { service.activityManager.complete(activity, function () {}); }); }, delay);
  });
  respond(m, {scheduled: delay});
});
var backupFile = dir + '/backup.json';
service.register('backup', function (m) {
  if (!callerOk(m)) { m.respond({returnValue: false, errorText: 'caller-not-authorized'}); return; }
  var data = String((m.payload || {}).data || '');
  try { if (data.length > 200000) throw new Error('too-large'); JSON.parse(data); if (!fs.existsSync(dir)) fs.mkdirSync(dir, {mode: 448}); fs.writeFileSync(backupFile, data, {mode: 384}); respond(m); }
  catch (e) { m.respond({returnValue: false, errorText: String(e.message)}); }
});
service.register('restore', function (m) {
  if (!callerOk(m)) { m.respond({returnValue: false, errorText: 'caller-not-authorized'}); return; }
  try { respond(m, {data: fs.readFileSync(backupFile, 'utf8')}); } catch (_) { m.respond({returnValue: false, errorText: 'no-backup'}); }
});
// ---- Xee Remote and Helper bridge: small files shared with Home Helper -------------------------------
var HELPER_STATE = '/media/developer/apps/usr/palm/applications/com.local.nativehome/state';
function writeShared(path, value, mode) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, {mode: 509});
  fs.writeFileSync(path + '.tmp', JSON.stringify(value), {mode: mode || 420}); fs.renameSync(path + '.tmp', path);
}
service.register('remoteState', function (m) {
  if (!callerOk(m)) { m.respond({returnValue: false, errorText: 'caller-not-authorized'}); return; }
  try { var p = m.payload || {}; if (p.state) writeShared(dir + '/remote-state.json', p.state); if (p.catalog) writeShared(dir + '/remote-catalog.json', p.catalog); respond(m); }
  catch (e) { m.respond({returnValue: false, errorText: String(e.code || e)}); }
});
service.register('remoteTake', function (m) {
  if (!callerOk(m)) { m.respond({returnValue: false, errorText: 'caller-not-authorized'}); return; }
  var list = [];
  try { list = JSON.parse(fs.readFileSync(dir + '/remote-queue.json', 'utf8')); fs.unlinkSync(dir + '/remote-queue.json'); } catch (_) {}
  m.respond({returnValue: true, commands: Array.isArray(list) ? list : []});
});
service.register('helperRequest', function (m) {
  if (!callerOk(m)) { m.respond({returnValue: false, errorText: 'caller-not-authorized'}); return; }
  var cmd = (m.payload || {}).cmd;
  if (['update-check', 'update-install', 'remote-revoke'].indexOf(cmd) < 0) { m.respond({returnValue: false, errorText: 'unknown'}); return; }
  try { fs.writeFileSync(HELPER_STATE + '/xee-request.json', JSON.stringify({id: String(Date.now()) + Math.random().toString(16).slice(2), cmd: cmd}), {mode: 432}); respond(m); }
  catch (e) { m.respond({returnValue: false, errorText: String(e.code || e)}); }
});
service.register('helperStatus', function (m) {
  if (!callerOk(m)) { m.respond({returnValue: false, errorText: 'caller-not-authorized'}); return; }
  var update = null, paired = 0;
  try { update = JSON.parse(fs.readFileSync(HELPER_STATE + '/update-status.json', 'utf8')); delete update.manifest; delete update.assets; } catch (_) {}
  try { paired = JSON.parse(fs.readFileSync(HELPER_STATE + '/remote-tokens.json', 'utf8')).length; } catch (_) {}
  m.respond({returnValue: true, update: update, paired: paired});
});
// Quran radio: turn the screen off while audio keeps playing, or turn the TV off when the sleep timer ends.
service.register('power', function (m) {
  if (!callerOk(m)) { m.respond({returnValue: false, errorText: 'caller-not-authorized'}); return; }
  var off = (m.payload || {}).action === 'off';
  var uri = off ? 'system/turnOff' : 'com.webos.service.tvpower/power/turnOffScreen';
  ssap([{uri: 'ssap://' + uri, payload: off ? {} : {standbyMode: 'active'}}]).then(function (r) {
    if (r[0] && r[0].returnValue === false) throw new Error(r[0].errorText || 'denied');
    return r[0];
  }).catch(function () { return call('luna://' + uri.replace('system/turnOff', 'com.webos.service.tvpower/power/turnOff'), off ? {reason: 'unknown'} : {standbyMode: 'active'}); }).then(function (r) {
    respond(m, {result: r});
  });
});
service.register('adhanStart', function (m) {
  if (!callerOk(m)) { m.respond({returnValue: false, errorText: 'caller-not-authorized'}); return; }
  raiseVolume((m.payload || {}).id || 'local').then(function () { respond(m); });
});
service.register('adhanDone', function (m) {
  state.lastDone = {at: Date.now(), payload: m.payload};
  if (!callerOk(m)) { m.respond({returnValue: false, errorText: 'caller-not-authorized'}); return; }
  var p = m.payload || {}, back = typeof p.returnTo === 'string' && /^[A-Za-z0-9._-]+$/.test(p.returnTo) && SKIP.indexOf(p.returnTo) < 0 ? p.returnTo : '';
  var resume = p.resume !== false && state.pausedBy && state.pausedBy === p.id; state.pausedBy = ''; save();
  if (!back) { restoreVolume().then(function () { respond(m); }); return; }
  restoreVolume().then(function () { return ssap([{uri: 'ssap://system.launcher/launch', payload: {id: back}}]).then(function () {
    if (!resume) return;
    return new Promise(function (r) { setTimeout(r, 5000); }).then(function () { return ssap([{uri: 'ssap://media.controls/play'}]); });
  }); }).catch(function () { return call('luna://com.webos.applicationManager/launch', {id: back}); }).then(function () { respond(m); });
});
