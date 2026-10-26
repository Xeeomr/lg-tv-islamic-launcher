'use strict';
var fs=require('fs'),cp=require('child_process'),policy=require('./runtime-policy');
function monotonic(){var t=process.hrtime();return t[0]*1000+t[1]/1e6;}
var root='/media/developer/apps/usr/palm/applications/com.local.nativehome';
var data=root+'/state';
var launchParams=JSON.parse(process.argv[2]||'{}'),automatic=launchParams.nativeHomeAuto===true;
function block(){fs.writeFileSync(data+'/blocked','stopped',{mode:420});}
require('./state-permissions')(data,function(x){console.error(JSON.stringify(x));});
if(automatic&&fs.existsSync(data+'/blocked'))process.exit(0);
var logPath=data+'/controller.log', pidPath=data+'/controller.pid';
fs.writeFileSync(pidPath,String(process.pid));fs.writeFileSync(logPath,'');
function log(x){
 try{fs.appendFileSync(logPath,JSON.stringify(Object.assign({time:Date.now()},x))+'\n');}
 catch(e){try{console.error('Helper log failed: '+String(e));console.error(x);}catch(ignore){}}
}
process.on('uncaughtException',function(e){
 try{block();}catch(ignore){}
 log({error:String(e),stack:e&&e.stack});
 setTimeout(function(){process.exit(2);},2500);
 try{if(child)child.stdin.end();}catch(ignore){}
});
var Service=require('/usr/lib/node_modules/webos-service');
var service=new Service('com.local.nativehome');
service.activityManager.create('native-home-controller',function(){});
if(!automatic){try{fs.unlinkSync(data+'/blocked');}catch(e){if(e.code!=='ENOENT')throw e;}}
var lastForeground=null,lastForegroundAt=null,monitor='starting',monitorReason=null,shouldResumeLaunch=require('./resume-policy');
var child,ready=false,stopping=false,lastAck=monotonic(),buffer='',lastCommand='',launching=false,resumePendingUntil=0;
var resumeGuardUntil=0,resumeRetries=0,lgHomeSince=null,lastLaunchSettledAt=0;
// Opt-in, bounded observation only; never changes routing or starts another watcher.
var diagnosticUntil=0,diagnosticNext=0,homeSequence=0,lastHomeAt=null,launchSequence=0,diagnosticSession=null;
function diagnostic(trigger,details){
 if(!diagnosticUntil)return;
 var now=monotonic();
 if(now>=diagnosticUntil&&trigger!=='expired'){diagnostic('expired');diagnosticUntil=0;return;}
 log(Object.assign({event:'home-diagnostic',session:diagnosticSession,trigger:trigger,homeSequence:homeSequence,
  sinceHomeMs:lastHomeAt===null?null:Math.round(now-lastHomeAt),
  foreground:lastForeground,foregroundSource:'subscription-cache',
  foregroundAgeMs:lastForegroundAt===null?null:Math.round(now-lastForegroundAt),
  monitor:monitor,monitorReason:monitorReason,ready:ready,enabled:homeControl?homeControl.enabled():null,
  launching:launching,visitingLG:!!visitingLG},details||{}));
}
function diagnosticCommand(cmd,nonce){
 if(cmd==='diagnostics-start'){
  diagnosticSession=typeof nonce==='string'&&/^[a-f0-9]{32}$/.test(nonce)?nonce:null;
  diagnosticUntil=monotonic()+60000;diagnosticNext=monotonic()+1000;
  homeSequence=0;lastHomeAt=null;diagnostic('started',{durationMs:60000});
 }
 if(cmd==='diagnostics-stop'){diagnostic('stopped');diagnosticUntil=0;}
}
function screenLog(x){
 if(x.event.indexOf('screen-watch-')===0){monitor=x.event;monitorReason=x.reason||null;}
 log(x);diagnostic('monitor');
}
function cancelResume(){resumePendingUntil=0;resumeGuardUntil=0;lgHomeSince=null;}
log({event:'start',pid:process.pid,uid:process.getuid(),automatic:automatic,diagnosticsSchema:1});
fs.writeFileSync(data+'/control.json','{}',{mode:432});fs.chmodSync(data+'/control.json',432);
function launch(id,done){var request=++launchSequence;diagnostic('launch-request',{launchSequence:request,id:id});var settled=false;var deadline=setTimeout(function(){if(settled)return;settled=true;lastLaunchSettledAt=monotonic();log({event:'launch-timeout',id:id});diagnostic('launch-timeout',{launchSequence:request,id:id});if(done)done(false);},3000);service.call('luna://com.webos.applicationManager/launch',{id:id},function(m){if(settled)return;settled=true;lastLaunchSettledAt=monotonic();clearTimeout(deadline);log({event:'launch',id:id,result:m.payload});diagnostic('launch-result',{launchSequence:request,id:id,returnValue:!!(m.payload&&m.payload.returnValue===true)});if(done)done(m.payload&&m.payload.returnValue===true);});}
var visitingLG=false,suppressReturnUntil=0;
function visitLG(done){
 if(visitingLG){if(done)done(false);return;}
 visitingLG=true;cancelResume();suppressReturnUntil=monotonic()+7000;
 var deadline=monotonic()+3500;
 function open(){
  if(launching&&monotonic()<deadline){setTimeout(open,50);return;}
  if(launching||stopping){visitingLG=false;if(done)done(false);return;}
  if(screenPolicy)screenPolicy.reset();
  launch('com.webos.app.home',function(ok){visitingLG=false;if(done)done(ok);});
 }
 open();
}
var homeControl=require('./home-control')(fs,data,function(enabled){
 cancelResume();if(screenPolicy)screenPolicy.reset();
 if(child)child.stdin.write(enabled?'E':'D');
},visitLG);
var lastHomeRequest='';
function readHomeRequest(){
 var request;
 try{request=JSON.parse(fs.readFileSync(data+'/home-request.json','utf8'));}catch(e){return;}
 if(!request||typeof request.id!=='string'||!/^[a-f0-9]{32}$/.test(request.id)||request.id===lastHomeRequest)return;
 lastHomeRequest=request.id;
 if(typeof request.expires!=='number'||request.expires<Date.now()||request.expires>Date.now()+6000)return;
 function respond(result){
  result.id=request.id;
  try{fs.writeFileSync(data+'/home-response.tmp',JSON.stringify(result),{mode:432});fs.chmodSync(data+'/home-response.tmp',432);fs.renameSync(data+'/home-response.tmp',data+'/home-response.json');}catch(e){log({event:'home-response-error',error:String(e)});}
 }
 try{
  if(request.method==='homeStatus')respond({returnValue:true,enabled:homeControl.enabled()});
  else if(request.method==='setHomeControl'){homeControl.set(request.enabled);respond({returnValue:true,enabled:homeControl.enabled()});}
  else if(request.method==='openLGHome')visitLG(function(ok){respond({returnValue:ok});});
  else respond({returnValue:false,errorText:'Invalid Home request'});
 }catch(e){respond({returnValue:false,errorText:String(e)});}
}
function finish(code,signal){if(stopping)return;stopping=true;closePointer();clearTimeout(pointerRetry);if(screenWatch)screenWatch.close();clearInterval(timer);log({event:'worker-exit',code:code,signal:signal});if(policy.shouldBlock(code,signal))fs.writeFileSync(data+'/blocked','stopped',{mode:420});
 function end(){try{fs.unlinkSync(pidPath);}catch(e){}process.exit(code===22?0:(code||0));}
 // Let an already-issued custom-Home request settle before the final LG launch.
 var finishDeadline=monotonic()+3200;
 function cleaned(){if(code!==22){end();return;}
  if(launching&&monotonic()<finishDeadline){setTimeout(cleaned,50);return;}
  launch('com.webos.app.home',function(){setTimeout(end,300);});
 }
 if(ready){var c=cp.spawn(root+'/relay',['cleanup'],{stdio:'ignore'});c.on('exit',function(n){log({event:'cleanup',code:n});cleaned();});}else cleaned();
}
// Standby/Quick Start freezes the worker and re-enumerates input devices on resume, and a busy TV can
// stall the controller past the worker's ping timeout (exit 20). Treat those exits as recoverable:
// restart the worker instead of blocking Helper until a manual start; repeated failures still block.
var powerSleep=false,powerChangedAt=0,powerRestarts=[];
function onWorkerExit(code,signal){
 var now=monotonic();
 powerRestarts=powerRestarts.filter(function(t){return now-t<600000;});
 if(!stopping&&(code===20||powerSleep||now-powerChangedAt<45000)&&powerRestarts.length<6){
  powerRestarts.push(now);child=null;ready=false;buffer='';
  // The worker writes the emergency-stop flag on any unexpected exit; this one was the power change.
  try{fs.unlinkSync(data+'/blocked');}catch(e){}
  log({event:'worker-power-restart',code:code,signal:signal,sleeping:powerSleep});
  (function wait(){if(stopping)return;if(powerSleep){setTimeout(wait,1000);return;}setTimeout(function(){if(!stopping&&!child)start();},1500);}());
  return;
 }
 finish(code,signal);
}
// LG shows its own clock screensaver after a few idle minutes, and the API for refusing it is closed to
// Developer Mode apps. When it is requested, press a key Home ignores (RED) through
// the TV's remote-control socket, which cancels the request, and ask Home to show its own screensaver.
var SSAP_PERMISSIONS=['LAUNCH','LAUNCH_WEBAPP','APP_TO_APP','CLOSE','TEST_OPEN','TEST_PROTECTED','CONTROL_AUDIO','CONTROL_DISPLAY','CONTROL_INPUT_JOYSTICK','CONTROL_INPUT_MEDIA_RECORDING','CONTROL_INPUT_MEDIA_PLAYBACK','CONTROL_INPUT_TV','CONTROL_POWER','CONTROL_TV_SCREEN','READ_APP_STATUS','READ_CURRENT_CHANNEL','READ_INPUT_DEVICE_LIST','READ_NETWORK_STATE','READ_RUNNING_APPS','READ_TV_CHANNEL_LIST','WRITE_NOTIFICATION_TOAST','READ_POWER_STATE','READ_COUNTRY_INFO','CONTROL_INPUT_TEXT','CONTROL_MOUSE_AND_KEYBOARD','READ_INSTALLED_APPS','READ_SETTINGS','READ_STORAGE_DEVICE_LIST'];
// A ready pointer socket answers within milliseconds; opening one takes over a second, longer than LG waits.
var pointer=null,pointerSession=null,pointerRetry=null;
function closePointer(){var p=pointer,ss=pointerSession;pointer=null;pointerSession=null;try{if(p)p.terminate();}catch(e){}try{if(ss)ss.terminate();}catch(e){}}
function openPointer(){
 clearTimeout(pointerRetry);pointerRetry=null;
 if(pointerSession||stopping)return;
 try{
  var key=JSON.parse(fs.readFileSync(data+'/ssap-key.json','utf8')).key,WS=require('./websocket'),ifs=require('os').networkInterfaces(),host=null;
  Object.keys(ifs).forEach(function(n){ifs[n].forEach(function(a){if(!host&&!a.internal&&(a.family==='IPv4'||a.family===4)&&a.address.indexOf('169.254.')!==0)host=a.address;});});
  if(!host||!key)return;
  var s=new WS('wss://'+host+':3001',{rejectUnauthorized:false,handshakeTimeout:3000,perMessageDeflate:false}),alive=true,pulse=null;
  pointerSession=s;
  function lost(){if(pointerSession!==s)return;clearInterval(pulse);closePointer();if(!stopping)pointerRetry=setTimeout(openPointer,powerSleep?15000:5000);}
  s.on('open',function(){s.send(JSON.stringify({type:'register',id:'r',payload:{forcePairing:false,pairingType:'PROMPT','client-key':key,manifest:{manifestVersion:1,appVersion:'1.1',permissions:SSAP_PERMISSIONS}}}));});
  s.on('pong',function(){alive=true;});
  s.on('message',function(raw){
   var m;try{m=JSON.parse(String(raw));}catch(e){return;}
   if(m.type==='registered')s.send(JSON.stringify({type:'request',id:'p',uri:'ssap://com.webos.service.networkinput/getPointerInputSocket',payload:{}}));
   else if(m.id==='p'&&m.payload&&m.payload.socketPath){
    var p=new WS(m.payload.socketPath,{rejectUnauthorized:false});
    p.on('open',function(){if(pointerSession===s)pointer=p;});p.on('error',lost);p.on('close',lost);
    pulse=setInterval(function(){if(!alive){lost();return;}alive=false;try{s.ping();}catch(e){lost();}},20000);
   }
   else if(m.type==='error'||(m.payload&&m.payload.pairingType)){log({event:'pointer-unavailable',error:String(m.error||'pairing')});lost();}
  });
  s.on('error',lost);s.on('close',lost);
 }catch(e){log({event:'ssap-button-error',error:String(e)});}
}
function ssapButton(name){
 if(pointer){try{pointer.send('type:button\nname:'+name+'\n\n');return;}catch(e){closePointer();}}
 // Not connected yet: connect and press once ready.
 openPointer();var tries=0;(function wait(){if(pointer){try{pointer.send('type:button\nname:'+name+'\n\n');}catch(e){}return;}if(++tries<40)setTimeout(wait,100);}());
}
var lastSaverSwap=0;
function replaceLgSaver(p){
 if(p.processing!=='Request Screen Saver'&&p.state!=='Screen Saver')return;
 if(!homeControl.enabled()||stopping||monotonic()-lastSaverSwap<20000)return;
 lastSaverSwap=monotonic();
 var home=lastForeground==='com.gathin.tvhome';
 log({event:home?'lg-saver-replaced':'lg-saver-cancelled',app:lastForeground,state:p.state,processing:p.processing});
 ssapButton('RED');
 // Over Home show our own screensaver; over any other app (a paused video) just keep the app on screen.
 if(home)setTimeout(function(){service.call('luna://com.webos.applicationManager/launch',{id:'com.gathin.tvhome',params:{saver:true}},function(){});},1200);
}
function start(){lastAck=monotonic();child=cp.spawn(root+'/relay',[],{stdio:['pipe','pipe','pipe']});log({event:'worker-start',pid:child.pid});child.stderr.on('data',function(b){log({stderr:String(b)});});child.on('error',function(e){log({error:String(e)});finish(1);});child.on('exit',onWorkerExit);
 child.stdout.on('data',function(b){buffer+=b;var i;while((i=buffer.indexOf('\n'))>=0){var line=buffer.slice(0,i);buffer=buffer.slice(i+1);if(line==='P'){lastAck=monotonic();continue;}log({event:'worker',message:line});if(line==='BACK_DOWN'){cancelResume();screenPolicy.back(true,monotonic());}if(line==='BACK_UP')screenPolicy.back(false,monotonic());if(line==='HOME'){screenPolicy.clearBack();homeSequence++;lastHomeAt=monotonic();diagnostic('home');}if(line==='READY'){ready=true;lastAck=monotonic();child.stdin.write(homeControl.enabled()?'E':'D');}if(line==='LGHOME'&&!stopping)visitLG();if(line==='HOME'&&homeControl.enabled()&&!visitingLG&&!stopping&&!launching){suppressReturnUntil=0;launching=true;launch('com.gathin.tvhome',function(ok){launching=false;if(!ok)child.stdin.end();});}}});
 child.stdin.on('error',function(){});
}
var timer=setInterval(function(){if(stopping)return;readHomeRequest();try{var raw=fs.readFileSync(data+'/control.json','utf8');if(raw!==lastCommand){lastCommand=raw;var command=JSON.parse(raw);diagnosticCommand(command.cmd,command.nonce);if(command.cmd==='startup-status')service.call('luna://com.local.nativehome.service/status',{},function(r){log({event:'startup-status',result:r.payload});});if(command.cmd==='stop'&&child)child.stdin.write('Q');if(command.cmd==='stall-worker'&&child)child.stdin.write('S');if(command.cmd==='stall-controller'){cp.spawn(root+'/resume',[String(process.pid)],{stdio:'ignore'});log({event:'simulate-controller-stall'});process.kill(process.pid,'SIGSTOP');}}}catch(e){}
 // Waking from standby: the key reader may still be restarting; launching Home does not need it.
 if(resumePendingUntil&&!launching&&!visitingLG&&homeControl.enabled()){
  var resumeDue=resumePendingUntil;resumePendingUntil=0;
  if(!shouldResumeLaunch(lastForeground)){log({event:'resume-already-foreground'});}
  else if(monotonic()<=resumeDue){launching=true;log({event:'resume-launch'});launch('com.gathin.tvhome',function(ok){launching=false;if(!ok)log({event:'resume-launch-failed'});});}
 }
 // A successful Luna reply only acknowledges the request. LG Home can win
 // later, including while a launch is in flight, so check the current level.
 var now=monotonic();
 if(diagnosticUntil&&now>=diagnosticNext){diagnostic('sample');diagnosticNext=now+1000;}
 if(resumeGuardUntil&&now>=resumeGuardUntil)cancelResume();
 if(resumeGuardUntil&&resumeRetries<4&&!launching&&!visitingLG&&homeControl.enabled()&&
    lastForeground==='com.webos.app.home'&&lgHomeSince!==null&&now-lgHomeSince>=1500&&now-lastLaunchSettledAt>=5000){
  resumeRetries++;launching=true;log({event:'resume-retry',attempt:resumeRetries});
  launch('com.gathin.tvhome',function(ok){launching=false;if(!ok)log({event:'resume-retry-failed'});});
 }
 if(child){if(!powerSleep&&monotonic()-powerChangedAt>8000&&policy.expired(lastAck,monotonic())){log({event:'worker-watchdog'});child.kill('SIGKILL');return;}child.stdin.write('P');}
},400);
setTimeout(function(){if(!homeControl.enabled()){start();return;}launch('com.gathin.tvhome',function(ok){if(ok)start();else {block();process.exit(3);}});},automatic?0:1000);


process.on('exit',function(code){log({event:'controller-exit',code:code});});

service.call('luna://com.local.nativehome.service/status',{},function(m){
 log({event:'startup-status',result:m.payload});
 if(!m.payload||!m.payload.returnValue||(m.payload.state.enabled&&m.payload.state.schema===3))return;
 service.call('luna://com.local.nativehome.service/enable',{},function(a){
  if(!a.payload||!a.payload.returnValue){log({event:'startup-arm-error',result:a.payload});return;}
  service.call('luna://com.palm.activitymanager/create',{activity:{name:'com.local.nativehome.boot',description:'Bounded Native Home once per boot',type:{foreground:true,persist:true},schedule:{interval:'10s',precise:true},callback:{method:'luna://com.local.nativehome.service/tick',params:{}}},start:true,replace:true,subscribe:false},function(r){log({event:'startup-create',result:r.payload});});
 });
});

var powerPolicy=require('./power-policy')();
setTimeout(openPointer,3000);
var screenPolicy=require('./screen-policy')(),gapTimer=null;
var screenWatch=require('./screen-watch')(data,screenLog,function(id){
 if(id==='com.webos.app.home'){if(lgHomeSince===null)lgHomeSince=monotonic();}
 else {lgHomeSince=null;if(id&&id!=='com.webos.app.cpcover'&&id!=='com.gathin.tvhome')cancelResume();}
 lastForeground=id;lastForegroundAt=monotonic();log({event:'foreground',id:id});diagnostic('foreground');
 var exited=screenPolicy.next(id,monotonic());
 clearTimeout(gapTimer);
 if(id===''&&screenPolicy.gapFromApp(monotonic()))gapTimer=setTimeout(function(){
  var now=monotonic();
  if(lastForeground!==''||!screenPolicy.gapFromApp(now)||!homeControl.enabled()||visitingLG||stopping||launching||!ready||
     powerSleep||now-powerChangedAt<8000||now<=suppressReturnUntil)return;
  resumeGuardUntil=now+30000;resumeRetries=0;launching=true;log({event:'return-on-gap'});
  launch('com.gathin.tvhome',function(ok){launching=false;if(!ok)log({event:'return-on-gap-failed'});});
 },350);
 if(exited&&homeControl.enabled()&&!visitingLG&&monotonic()>suppressReturnUntil&&ready&&!stopping&&!launching){
  resumeGuardUntil=monotonic()+30000;resumeRetries=0;
  launching=true;log({event:'return-after-exit'});
  launch('com.gathin.tvhome',function(ok){launching=false;if(!ok)log({event:'return-after-exit-failed'});});
 }
 // LG often takes the screen back ~1s after our launch. Answer at once instead of waiting for the slow retry.
 if(id==='com.webos.app.home'&&resumeGuardUntil&&resumeRetries<5&&!launching&&!visitingLG&&!stopping&&homeControl.enabled()&&
    monotonic()>suppressReturnUntil&&monotonic()-lastLaunchSettledAt<20000){
  resumeRetries++;launching=true;log({event:'resume-retry-fast',attempt:resumeRetries});
  launch('com.gathin.tvhome',function(ok){launching=false;if(!ok)log({event:'resume-retry-fast-failed'});});
 }
},function(){lastForeground=null;lastForegroundAt=null;monitor='reset';monitorReason=null;lgHomeSince=null;screenPolicy.reset();diagnostic('monitor-reset');},function(p){
 log({event:'power',state:p.state,processing:p.processing,onOff:p.onOff});
 replaceLgSaver(p);
 var sleeping=p.onOff==='off'||p.state==='Suspend'||p.state==='Active Standby'||/Suspend|Power Off|Standby/.test(p.processing||'');
 if(sleeping!==powerSleep){powerSleep=sleeping;powerChangedAt=monotonic();if(!sleeping)lastAck=monotonic();}
 if(p.onOff==='off'||p.state==='Active Standby'||p.state==='Suspend')cancelResume();
 if(powerPolicy.next(p)&&homeControl.enabled()&&!visitingLG&&!stopping){
  var now=monotonic();resumePendingUntil=now+20000;resumeGuardUntil=now+40000;resumeRetries=0;
  lgHomeSince=lastForeground==='com.webos.app.home'?now:null;
 }
});
