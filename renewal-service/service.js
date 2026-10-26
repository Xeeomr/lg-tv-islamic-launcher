'use strict';
var fs=require('fs'),Service=require('webos-service');
var service=new Service('com.gathin.tvhome.renewal');
var dir=__dirname+'/state',activityName='com.gathin.tvhome.renewal.hourly';
var manager,worker;
function call(uri,payload){return new Promise(function(resolve){
 var ended=false,request,timer=setTimeout(function(){finish({returnValue:false});},10000);
 function finish(r){if(ended)return;ended=true;clearTimeout(timer);if(request&&request.cancel)request.cancel();resolve(r);}
 try{request=service.call(uri,payload,function(m){finish(m.payload);});}catch(_){finish({returnValue:false});}
});}
function readConfig(){
 try{return JSON.parse(fs.readFileSync(dir+'/settings.json','utf8'));}catch(e){if(e.code==='ENOENT')return {enabled:false};throw e;}
}
function saveConfig(s){
 if(!fs.existsSync(dir))fs.mkdirSync(dir,{mode:448});
 fs.writeFileSync(dir+'/settings.tmp',JSON.stringify(s),{mode:384});fs.renameSync(dir+'/settings.tmp',dir+'/settings.json');
}
var io=require('./local-io').createLocalIO({stateFile:dir+'/renewal.json',request:async function(op,token){
 if(!manager.allowed())throw new Error('disabled');
 return requestLG(op,token);
}});
var requestLG=require('./transport').createRequest();
var readToken=io.readToken;
io.readToken=async function(){if(!manager.allowed())return '';return readToken();};
worker=require('./renewal').createRenewal(io,{enabled:true});
manager=require('./manager')({load:readConfig,save:saveConfig,now:Date.now,run:function(){return worker.run();},
 schedule:function(){return call('luna://com.palm.activitymanager/create',{
  activity:{name:activityName,description:'Opt-in Developer Mode renewal Beta',type:{foreground:true,persist:true},
   schedule:{interval:'1h'},callback:{method:'luna://com.gathin.tvhome.renewal/tick',params:{}}},start:true,replace:true,subscribe:false});},
 cancel:function(){return call('luna://com.palm.activitymanager/cancel',{activityName:activityName});}
});
function respond(m,state){m.respond({returnValue:true,beta:true,version:'1.2.0',state:state});}
service.register('status',function(m){respond(m,manager.status());});
service.register('enable',function(m){manager.enable().then(function(s){respond(m,s);});});
service.register('disable',function(m){manager.disable().then(function(s){respond(m,s);});});
service.register('check',function(m){manager.check().then(function(s){respond(m,s);});});
service.register('tick',function(m){manager.check().then(function(s){
 if(m.activity)service.activityManager.complete(m.activity,{restart:manager.allowed()},function(){respond(m,s);});
 else respond(m,s);
});});

service.register('restoreHistory',function(m){
 var raw=m.ls2Message,id=raw&&raw.applicationID&&raw.applicationID();
 if(typeof id!=='string'||id.split(' ')[0]!=='com.gathin.tvhome'){m.respond({returnValue:false});return;}
 manager.restoreHistory(m.payload.state).then(function(s){respond(m,s);});
});

// Only the independent updater may manage a transactional pause. A web app
// cannot impersonate it with a JSON field or a supplied application identity.
function fromUpdater(m){
 try{var raw=m.ls2Message;return raw.applicationID()===''&&raw.senderServiceName()==='com.cleanyourtv.updater.service';}catch(_){return false;}
}
['pauseForUpdate','resumeAfterUpdate','importUpdatePause'].forEach(function(method){
 service.register(method,function(m){
  if(!fromUpdater(m)){m.respond({returnValue:false,errorText:'caller-not-authorized'});return;}
  manager[method](method==='importUpdatePause'?(m.payload||{}).receipt:(m.payload||{}).id).then(function(s){respond(m,s);});
 });
});

var homeControl=require('./home-control')(fs,'/media/developer/apps/usr/palm/applications/com.local.nativehome/state');
['homeStatus','setHomeControl','openLGHome'].forEach(function(method){
 service.register(method,function(m){
  var raw=m.ls2Message,id=raw&&raw.applicationID&&raw.applicationID();
  if(typeof id!=='string'||id.split(' ')[0]!=='com.gathin.tvhome'){m.respond({returnValue:false,errorText:'caller-not-authorized'});return;}
  homeControl(method,m.payload).then(function(r){m.respond(r);});
 });
});
