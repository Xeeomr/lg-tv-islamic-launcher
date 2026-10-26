(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory;
  else root.createRootExit = factory;
}(this, function (call, launch) {
  'use strict';
  var busy = false;
  function unwrap(reply) {
    if (!reply || reply.returnValue !== true || !reply.result || reply.result.returnValue !== true)
      throw new Error('Recovery service did not confirm success. Retry or use host restore.');
    return reply.result.result;
  }
  return async function () {
    if (busy) throw new Error('Exit already in progress');
    busy = true;
    try {
      var result = unwrap(await call('restore'));
      if (result !== 'restored' && result !== 'absent') throw new Error('Recovery incomplete. Keep the recovery state and use host restore.');
      var status = unwrap(await call('status'));
      var e = status && status.effective;
      if (!e || e.sam_home !== 'com.webos.app.home' || !e.profiles ||
          !e.profiles.defaultApps || !e.profiles.defaultApps.categories ||
          e.profiles.defaultApps.categories.home !== 'com.webos.app.home' ||
          !e.profiles.idleApp || e.profiles.idleApp.appId !== 'com.webos.app.home')
        throw new Error('Original Home is not confirmed. Use host restore.');
      await launch();
    } finally { busy = false; }
  };
}));
