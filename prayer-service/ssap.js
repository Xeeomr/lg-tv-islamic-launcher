'use strict';
// Talks to the TV's own remote-control API with the pairing key Home Helper already holds.
var fs = require('fs'), os = require('os');
// The service runs in its own sandbox and cannot see Home Helper's files, so it carries its own copy of
// the pairing key (written at build time from .lgtv-key.json) and of the ws library.
// Same list as lgtv.py: registering with fewer permissions would narrow the shared key for every client.
var PERMISSIONS = ['LAUNCH', 'LAUNCH_WEBAPP', 'APP_TO_APP', 'CLOSE', 'TEST_OPEN', 'TEST_PROTECTED', 'CONTROL_AUDIO',
  'CONTROL_DISPLAY', 'CONTROL_INPUT_JOYSTICK', 'CONTROL_INPUT_MEDIA_RECORDING', 'CONTROL_INPUT_MEDIA_PLAYBACK', 'CONTROL_INPUT_TV',
  'CONTROL_POWER', 'CONTROL_TV_SCREEN', 'READ_APP_STATUS', 'READ_CURRENT_CHANNEL', 'READ_INPUT_DEVICE_LIST', 'READ_NETWORK_STATE',
  'READ_RUNNING_APPS', 'READ_TV_CHANNEL_LIST', 'WRITE_NOTIFICATION_TOAST', 'READ_POWER_STATE', 'READ_COUNTRY_INFO', 'CONTROL_INPUT_TEXT',
  'CONTROL_MOUSE_AND_KEYBOARD', 'READ_INSTALLED_APPS', 'READ_SETTINGS', 'READ_STORAGE_DEVICE_LIST'];
function readKey() {
  var k = JSON.parse(fs.readFileSync(__dirname + '/ssap-key.json', 'utf8'));
  if (!k || typeof k.key !== 'string' || !k.key) throw new Error('missing-pairing');
  return k.key;
}
function hosts() {
  var out = [], ifs = os.networkInterfaces();
  Object.keys(ifs).forEach(function (n) { ifs[n].forEach(function (a) { if (!a.internal && (a.family === 'IPv4' || a.family === 4) && a.address.indexOf('169.254.') !== 0) out.push(a.address); }); });
  return out;
}
// requests: [{uri, payload}] sent in order on one connection; resolves with their payloads.
module.exports = function ssap(requests, timeoutMs) {
  return new Promise(function (resolve, reject) {
    var socket, done = false, results = [], step = 0, timer, key, list;
    function finish(error) { if (done) return; done = true; clearTimeout(timer); try { if (socket) socket.terminate(); } catch (_) {} if (error) reject(new Error(error)); else resolve(results); }
    try { key = readKey(); list = hosts(); var WebSocket = require('./ws'); } catch (e) { reject(e); return; }
    if (!list.length) { reject(new Error('network-unavailable')); return; }
    timer = setTimeout(function () { finish('timeout'); }, timeoutMs || 10000);
    var idx = 0;
    function connect() {
      if (done) return;
      if (idx >= list.length) { finish('connect-failed'); return; }
      var s;
      try { s = new WebSocket('wss://' + list[idx++] + ':3001', {rejectUnauthorized: false, handshakeTimeout: 3000, perMessageDeflate: false}); } catch (_) { connect(); return; }
      socket = s;
      var registered = false;
      function sendNext() {
        if (step >= requests.length) { finish(null); return; }
        s.send(JSON.stringify({type: 'request', id: 'r' + step, uri: requests[step].uri, payload: requests[step].payload || {}}));
      }
      s.on('open', function () { s.send(JSON.stringify({type: 'register', id: 'register', payload: {forcePairing: false, pairingType: 'PROMPT', 'client-key': key, manifest: {manifestVersion: 1, appVersion: '1.1', permissions: PERMISSIONS}}})); });
      s.on('message', function (raw) {
        var m; try { m = JSON.parse(String(raw)); } catch (_) { return finish('invalid-response'); }
        if (m.type === 'registered') { registered = true; sendNext(); }
        else if (m.payload && m.payload.pairingType) finish('pairing-required');
        else if (m.id && m.id.indexOf('r') === 0) { results[step] = m.type === 'error' ? {returnValue: false, error: m.error} : m.payload; step++; sendNext(); }
        else if (m.type === 'error') finish('denied');
      });
      s.on('error', function () { if (!registered && !done) connect(); });
      s.on('close', function () { if (!registered && !done) connect(); });
    }
    connect();
  });
};
