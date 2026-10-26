'use strict';
module.exports = function (execute) {
  var busy = false;
  function valid(payload, boot) {
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return false;
    if (Object.keys(payload).some(function (key) { return key !== '$activity' && !(boot && key === 'reason'); })) return false;
    return !boot || (payload.reason === 'activity' && payload.$activity &&
      Number.isInteger(payload.$activity.activityId) && payload.$activity.activityId > 0);
  }
  function handler(command) {
    return async function (payload) {
      var confirmation = command === 'confirm';
      var allowed = confirmation ? payload && Object.keys(payload).length === 1 && typeof payload.transaction === 'string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(payload.transaction) : valid(payload, command === 'boot');
      if (!allowed) return {returnValue:false,errorText:'Invalid recovery request'};
      if (busy) return {returnValue:false,errorText:'Recovery busy'};
      busy = true;
      try { return {returnValue:true,result:await execute(command, confirmation ? payload.transaction : undefined)}; }
      catch (error) { return {returnValue:false,errorText:error.message}; }
      finally { busy = false; }
    };
  }
  return {boot:handler('boot'),status:handler('status'),restore:handler('restore'),enable:handler('enable'),confirm:handler('confirm')};
};
