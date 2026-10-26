'use strict';
// Same-package UI endpoint; the existing helper data directory is prisoner:jailer 0770.
// Fixed request/response files avoid granting the launcher new cross-package bus access.
module.exports=function(fs,dir,options){
 options=options||{};
 var busy=false,now=options.now||Date.now,later=options.later||setTimeout;
 var nonce=options.nonce||function(){return require('crypto').randomBytes(16).toString('hex');};
 return function(method,payload){
  if(['homeStatus','setHomeControl','openLGHome'].indexOf(method)<0||
     (method==='setHomeControl'&&(!payload||typeof payload.enabled!=='boolean')))
   return Promise.resolve({returnValue:false,errorText:'Invalid Home request'});
  if(busy)return Promise.resolve({returnValue:false,errorText:'Home control busy'});
  busy=true;
  return new Promise(function(resolve){
   var id=nonce(),deadline=now()+5000;
   function finish(r){busy=false;resolve(r);}
   try{
    var request={id:id,method:method,expires:deadline};
    if(method==='setHomeControl')request.enabled=payload.enabled;
    fs.writeFileSync(dir+'/home-request.tmp',JSON.stringify(request),{mode:432});
    fs.chmodSync(dir+'/home-request.tmp',432);
    fs.renameSync(dir+'/home-request.tmp',dir+'/home-request.json');
   }catch(e){finish({returnValue:false,errorText:'Home Helper data unavailable'});return;}
   function poll(){
    try{
     var r=JSON.parse(fs.readFileSync(dir+'/home-response.json','utf8'));
     if(r.id===id){finish(r);return;}
    }catch(e){}
    if(now()>=deadline){finish({returnValue:false,errorText:'Home Helper did not respond'});return;}
    later(poll,100);
   }
   poll();
  });
 };
};
