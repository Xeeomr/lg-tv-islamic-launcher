'use strict';
// Fixed read-only query. No caller-supplied commands, paths or launch parameters.
module.exports=function(execFile,getuid){
 return new Promise(function(resolve,reject){
  if((getuid||process.getuid)()!==0){reject(Error('Root service required'));return;}
  (execFile||require('child_process').execFile)('/usr/bin/luna-send',['-n','1','luna://com.webos.applicationManager/dev/listApps','{}'],{timeout:8000,maxBuffer:1024*1024},function(error,stdout){
   if(error){reject(Error('inventory-unavailable'));return;}
   try{
    var result=JSON.parse(stdout);
    if(result.returnValue!==true||!Array.isArray(result.apps))throw Error('invalid-inventory');
    var fs=require('fs'),path=require('path'),iconBudget=512*1024;
    var apps=result.apps.slice(0,200).map(function(a){
     var icon='';
     if(typeof a.icon==='string'&&typeof a.folderPath==='string'){
      var file=path.resolve(a.folderPath,a.icon);
      var allowed=/^\/(usr\/palm|media\/(developer|cryptofs)\/apps\/usr\/palm|mnt\/otncabi\/usr\/palm)\/applications\//;
      if(allowed.test(file)&&/\.(png|jpe?g|webp)$/i.test(file))try{
       var real=fs.realpathSync(file),stat=fs.statSync(real);
       if(allowed.test(real)&&stat.isFile()&&stat.size<=32768&&stat.size<=iconBudget){var ext=/\.webp$/i.test(real)?'webp':/\.jpe?g$/i.test(real)?'jpeg':'png';iconBudget-=stat.size;icon='data:image/'+ext+';base64,'+fs.readFileSync(real).toString('base64');}
      }catch(_){}
     }
     return {id:a.id,title:a.title,icon:icon,iconColor:a.iconColor||a.bgColor||'',hidden:a.visible===false||a.hidden===true};
    });resolve(apps);
   }catch(_){reject(Error('invalid-inventory'));}
  });
 });
};
