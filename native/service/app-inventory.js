'use strict';
// Uses the existing pairing key and only the TV's own LAN address. Never pairs.
module.exports=function(options){
 options=options||{};
 return new Promise(function(resolve,reject){
  var socket,done=false,timer,attemptTimer;
  function finish(error,apps){if(done)return;done=true;clearTimeout(timer);clearTimeout(attemptTimer);if(socket)socket.terminate();if(error)reject(Error(error));else resolve(apps);}
  try{
   var base='/media/developer/apps/usr/palm/applications/com.local.nativehome';
   if(!options.readKey&&!require(base+'/state-permissions')(base+'/state')){finish('state-permissions');return;}
   var key=(options.readKey||function(){return JSON.parse(require('fs').readFileSync(base+'/state/ssap-key.json','utf8'));})();
   if(!key||typeof key.key!=='string'||!key.key){finish('missing-pairing');return;}
   var interfaces=(options.interfaces||require('os').networkInterfaces)(),hosts=[];
   Object.keys(interfaces).forEach(function(name){interfaces[name].forEach(function(a){if(!a.internal&&(a.family==='IPv4'||a.family===4)&&a.address.indexOf('169.254.')!==0)hosts.push(a.address);});});
   if(!hosts.length){finish('network-unavailable');return;}
   var WebSocket=options.WebSocket||require(base+'/websocket');
   var index=0;
   timer=setTimeout(function(){finish('inventory-timeout');},options.timeout||8000);
   function connect(){
    if(done)return;
    if(index>=hosts.length){finish('network-unavailable');return;}
    var current;
    try{current=new WebSocket('wss://'+hosts[index++]+':3001',{rejectUnauthorized:false,handshakeTimeout:2000,maxPayload:1024*1024,perMessageDeflate:false});}
    catch(_){connect();return;}
    socket=current;
    function retry(){
     if(done||socket!==current)return;
     clearTimeout(attemptTimer);socket=null;current.terminate();connect();
    }
    attemptTimer=setTimeout(retry,Math.max(500,Math.floor((options.timeout||8000)/hosts.length)));

   current.on('open',function(){if(done||socket!==current)return;current.send(JSON.stringify({type:'register',id:'register',payload:{forcePairing:false,pairingType:'PROMPT','client-key':key.key,manifest:{manifestVersion:1,appVersion:'1.1',permissions:['READ_INSTALLED_APPS']}}}));});
   current.on('message',function(raw){
    if(done||socket!==current)return;
    var message;try{message=JSON.parse(String(raw));}catch(_){finish('invalid-response');return;}
    if(message.type==='registered')socket.send(JSON.stringify({type:'request',id:'apps',uri:'ssap://com.webos.applicationManager/listLaunchPoints',payload:{}}));
    else if(message.payload&&message.payload.pairingType)finish('pairing-required');
    else if(message.type==='error')finish('inventory-denied');
    else if(message.id==='apps'){
     var result=message.payload;
     if(!result||result.returnValue===false||!Array.isArray(result.launchPoints))finish('invalid-inventory');
     else finish(null,result.launchPoints.slice(0,200));
    }
   });
   current.on('error',retry);
   current.on('close',retry);
   }
   connect();
  }catch(_){finish('inventory-unavailable');}
 });
};
