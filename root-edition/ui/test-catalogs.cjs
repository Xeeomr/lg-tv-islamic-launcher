const assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
const catalogs={};vm.runInNewContext(fs.readFileSync(__dirname+'/root-locales.js','utf8'),{window:{HomeI18n:{add:values=>Object.assign(catalogs,values)}}});
const sources=Object.keys(catalogs.en);
for(const locale of ['en','de','es','pt-BR','fr','it','ko','hi','pl','ru']){
 assert.deepEqual(Object.keys(catalogs[locale]).sort(),sources.slice().sort());
 for(const source of sources){assert(catalogs[locale][source].trim());assert.deepEqual((catalogs[locale][source].match(/\{\w+\}/g)||[]).sort(),(source.match(/\{\w+\}/g)||[]).sort());}
}
for(const file of ['root-settings.js','root-firmware.js','root-updates.js','root-profile.js','root-profile-data.js','root-exit.js']){
 const content=fs.readFileSync(__dirname+'/'+file,'utf8');
 for(const match of content.matchAll(/'([^'\n]*)'/g)){
  const source=match[1];if((/^[A-Z]/.test(source)&&source.includes(' '))||['Back','Update','Language','unknown'].includes(source))assert(source in catalogs.en,file+' missing '+source);
 }
}
console.log('PASS '+sources.length+' Root and recovery sources translated in ten languages with intact placeholders');
