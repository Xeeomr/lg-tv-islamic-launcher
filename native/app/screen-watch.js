'use strict';
var fs=require('fs'),os=require('os'),WebSocket=require('./websocket');
// Local self-connection: the TV rejects loopback, but accepts its own LAN address.
// Never accepts a remote endpoint or launches anything itself.
module.exports=function(data,log,onForeground,onReset,onPower){
 var closed=false,socket=null,retry=null,index=0,cleanup=null,backoff=10000;
 function later(){if(!closed){retry=setTimeout(connect,backoff);backoff=Math.min(backoff*2,60000);}}
 function connect(){
  if(closed)return;
  onReset();
  if(!require('./state-permissions')(data,log)){log({event:'screen-watch-unavailable',reason:'state-permissions'});later();return;}
  var key,addresses=[];
  try{key=JSON.parse(fs.readFileSync(data+'/ssap-key.json','utf8')).key;
   if(typeof key!=='string'||!key)throw Error('missing-key');
  }catch(e){log({event:'screen-watch-unavailable',reason:'missing-pairing-key'});return;}
  var interfaces=os.networkInterfaces();
  Object.keys(interfaces).forEach(function(name){interfaces[name].forEach(function(a){
   if(!a.internal&&(a.family==='IPv4'||a.family===4)&&a.address.indexOf('169.254.')!==0)addresses.push(a.address);
  });});
  if(!addresses.length){later();return;}
  var host=addresses[index++%addresses.length],s;
  try{s=new WebSocket('wss://'+host+':3001',{rejectUnauthorized:false,handshakeTimeout:5000,maxPayload:65536,perMessageDeflate:false});}
  catch(e){later();return;}
  socket=s;
  var deadline=setTimeout(function(){s.terminate();},10000),pulse=null,alive=true;
  cleanup=function(){clearTimeout(deadline);clearInterval(pulse);};
  s.on('open',function(){
   s.send(JSON.stringify({type:'register',id:'register',payload:{forcePairing:false,pairingType:'PROMPT','client-key':key,manifest:{manifestVersion:1,appVersion:'1.1',permissions:['READ_APP_STATUS','READ_RUNNING_APPS','READ_POWER_STATE','CONTROL_POWER']}}}));
  });
  s.on('pong',function(){alive=true;});
  s.on('message',function(raw){
   if(closed)return;
   var m;try{m=JSON.parse(String(raw));}catch(e){return;}
   if(m.type==='registered'){
    s.send(JSON.stringify({type:'subscribe',id:'foreground',uri:'ssap://com.webos.applicationManager/getForegroundAppInfo',payload:{}}));
    if(onPower)s.send(JSON.stringify({type:'subscribe',id:'power',uri:'ssap://com.webos.service.tvpower/power/getPowerState',payload:{}}));
   }else if(m.id==='power'){
    if(m.type==='error')log({event:'power-watch-error',error:String(m.error)});
    else if(m.payload&&m.payload.returnValue!==false&&typeof m.payload.state==='string'&&onPower)onPower(m.payload);
   }else if(m.id==='foreground'&&m.type!=='error'&&m.payload&&typeof m.payload.appId==='string'){
    if(!pulse){backoff=10000;clearTimeout(deadline);log({event:'screen-watch-connected'});
     pulse=setInterval(function(){if(!alive){s.terminate();return;}alive=false;s.ping();},5000);
    }
    onForeground(m.payload.appId);
   }else if(m.type==='error'){
    log({event:'screen-watch-error',error:String(m.error)});
    if(/^(400|401|403|404)\b/.test(String(m.error)))closed=true;
    s.terminate();
   }else if(m.payload&&m.payload.pairingType){
    // A revoked key must not leave an unattended pairing flow running.
    log({event:'screen-watch-unavailable',reason:'pairing-required'});closed=true;s.terminate();
   }
  });
  s.on('error',function(e){log({event:'screen-watch-error',error:e.code||e.message});});
  s.on('close',function(code){clearTimeout(deadline);clearInterval(pulse);onReset();log({event:'screen-watch-disconnected',code:code});later();});
 }
 connect();
 return {close:function(){closed=true;clearTimeout(retry);if(cleanup)cleanup();onReset();if(socket)socket.terminate();}};
};
