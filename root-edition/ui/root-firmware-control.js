(function (root, factory) {
  'use strict';
  if (typeof module === 'object' && module.exports) module.exports = factory;
  else root.createRootFirmwareControl = factory;
}(this, function (request) {
  'use strict';
  // Homebrew owns the preference and its boot-time hosts overlay. No new
  // privileged service, mount, reboot, firmware deletion or persisted CYTV flag.
  var busy = false;
  function call(method, payload) {
    return Promise.resolve().then(function () {
      return request('luna://org.webosbrew.hbchannel.service/' + method, payload, 10000);
    }).then(function (reply) {
      if (!reply || reply.returnValue !== true || typeof reply.blockUpdates !== 'boolean' ||
          (method === 'getConfiguration' && reply.root !== true)) throw Error('unavailable');
      return {returnValue:true, enabled:reply.blockUpdates};
    });
  }
  function status() { return call('getConfiguration', {}); }
  return {
    get:function () { return status().catch(function () { return {returnValue:false, errorCode:'unavailable'}; }); },
    set:async function (enabled, expectedEnabled) {
      if (typeof enabled !== 'boolean' || typeof expectedEnabled !== 'boolean') return {returnValue:false, errorCode:'invalid'};
      if (busy) return {returnValue:false, errorCode:'busy'};
      busy = true;
      var attempted = false;
      try {
        var before = await status();
        if (before.enabled !== expectedEnabled) return {returnValue:false, errorCode:'changed', status:before};
        if (before.enabled === enabled) return before;
        attempted = true;
        await call('setConfiguration', {blockUpdates:enabled});
        var after = await status();
        if (after.enabled !== enabled) return {returnValue:false, errorCode:'unconfirmed', status:after};
        return after;
      } catch (_) {
        var reply = {returnValue:false, errorCode:attempted ? 'unconfirmed' : 'unavailable'};
        if (attempted) try { reply.status = await status(); } catch (_) {}
        return reply;
      } finally { busy = false; }
    }
  };
}));
