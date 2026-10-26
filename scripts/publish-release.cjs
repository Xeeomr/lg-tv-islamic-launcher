#!/usr/bin/env node
'use strict';
// Normal publication delegates signing to the protected GitHub environment.
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const {execFileSync}=require('node:child_process');
const policy=require('../root-edition/updater/fetch'),homePolicy=require('../updater-service/policy'),systemPolicy=require('../system-updater/policy');
function verifyRootRelease(feed,build,bytes,key=fs.readFileSync(path.join(__dirname,'../updater-service/release-public.pem'))){
 if(!build.versions||typeof build.versions.root!=='string')throw Error('release-root-version-missing');
 const candidate=policy.verify(feed,key);
 if(candidate.version!==build.versions.root)throw Error('stale-root-feed: signed '+candidate.version+', release '+build.versions.root);
 if(bytes.length!==candidate.size||crypto.createHash('sha256').update(bytes).digest('hex')!==candidate.sha256)throw Error('root-package-mismatch');
 return candidate;
}
function verifyHomeRelease(feed,build,bytes,key=fs.readFileSync(path.join(__dirname,'../updater-service/release-public.pem'))){
 if(!build.versions||typeof build.versions.home!=='string'||typeof build.versions.helper!=='string')throw Error('release-home-version-missing');
 const candidate=homePolicy.verify(feed,key);
 if(candidate.home!==build.versions.home)throw Error('stale-home-feed: signed '+candidate.home+', release '+build.versions.home);
 if(candidate.helper!==build.versions.helper)throw Error('helper-feed-mismatch');
 if(crypto.createHash('sha256').update(bytes).digest('hex')!==candidate.sha256)throw Error('home-package-mismatch');
 const prior=homePolicy.verify(feed.previous,key);
 if(prior.helper!==candidate.helper||homePolicy.compare(prior.home,candidate.home)>=0)throw Error('incompatible-home-rollback');
 return candidate;
}
function verifySystemRelease(feed,build,assets,key=fs.readFileSync(path.join(__dirname,'../updater-service/release-public.pem'))){
 const manifest=systemPolicy.verify(feed,key);
 if(manifest.release!==build.tag)throw Error('system-release-tag-mismatch');
 for(const item of manifest.components){
  const version=build.versions[({'root-infrastructure':'root','root-updater':'updater'})[item.name]||item.name];
  if(typeof version!=='string'||item.version!==version)throw Error('system-release-version-mismatch');
  const filename=path.basename(new URL(item.url).pathname),raw=assets[filename];
  if(!raw||raw.length!==item.size||crypto.createHash('sha256').update(raw).digest('hex')!==item.sha256)throw Error('system-release-package-mismatch');
 }
 return manifest;
}
function main(args){
 const [tag,option]=args;
 if(!/^v\d{1,4}\.\d{1,4}\.\d{1,4}$/.test(tag||'')||args.length>2||(option&&!['--check-only','--publish-verified'].includes(option)))throw Error('Usage: node scripts/publish-release.cjs vX.Y.Z [--check-only|--publish-verified]');
 if(!option){
  execFileSync('gh',['workflow','run','publish-release.yml','--ref','main','-f','tag='+tag,'-f','publish=true'],{stdio:'inherit'});
  process.stdout.write('Queued signing and checked publication of '+tag+'. Follow the Sign and publish release workflow in GitHub Actions.\n');
  return;
 }
 if(option==='--publish-verified'&&process.env.GITHUB_ACTIONS!=='true')throw Error('Publication requires the protected signing workflow');
 const folder=fs.mkdtempSync(path.join(os.tmpdir(),'cytv-release-'));
 const gh=argv=>execFileSync('gh',argv,{encoding:'utf8',maxBuffer:1024*1024,stdio:['ignore','pipe','pipe']});
 try{
  gh(['release','download',tag,'--pattern','root-update.json','--pattern','BUILD-INFO.json','--pattern','update.json','--pattern','previous-update.json','--pattern','system-update-root.json','--pattern','system-update-no-root.json','--dir',folder]);
  const feed=JSON.parse(fs.readFileSync(path.join(folder,'root-update.json')));
  const build=JSON.parse(fs.readFileSync(path.join(folder,'BUILD-INFO.json')));
  if(build.tag!==tag)throw Error('release-tag-mismatch');
  const candidate=policy.verify(feed,fs.readFileSync(path.join(__dirname,'../updater-service/release-public.pem')));
  const filename=path.basename(new URL(candidate.url).pathname);
  gh(['release','download',candidate.release,'--pattern',filename,'--dir',folder]);
  verifyRootRelease(feed,build,fs.readFileSync(path.join(folder,filename)));
  const homeFeed=JSON.parse(fs.readFileSync(path.join(folder,'update.json')));
  const previous=JSON.parse(fs.readFileSync(path.join(folder,'previous-update.json')));
  const key=fs.readFileSync(path.join(__dirname,'../updater-service/release-public.pem'));
  const home=homePolicy.verify(homeFeed,key),prior=homePolicy.verify(homeFeed.previous,key);
  if(previous.payload!==homeFeed.previous.payload||previous.signature!==homeFeed.previous.signature)throw Error('home-rollback-feed-mismatch');
  for(const item of [home,prior]){
   const file=path.basename(new URL(item.url).pathname);
   gh(['release','download',item.release,'--pattern',file,'--dir',folder]);
   const raw=fs.readFileSync(path.join(folder,file));
   if(crypto.createHash('sha256').update(raw).digest('hex')!==item.sha256)throw Error('home-package-mismatch');
   if(item===home)verifyHomeRelease(homeFeed,build,raw,key);
  }
  for(const edition of ['root','no-root']){
   const envelope=JSON.parse(fs.readFileSync(path.join(folder,'system-update-'+edition+'.json')));
   const system=systemPolicy.verify(envelope,key),assets={};
   if(system.edition!==edition)throw Error('system-edition-mismatch');
   for(const item of system.components){
    const filename=path.basename(new URL(item.url).pathname);
    if(!fs.existsSync(path.join(folder,filename)))gh(['release','download',tag,'--pattern',filename,'--dir',folder]);
    assets[filename]=fs.readFileSync(path.join(folder,filename));
   }
   verifySystemRelease(envelope,build,assets,key);
  }
  process.stdout.write('Verified '+tag+': Root '+candidate.version+', Home '+home.home+', Helper '+home.helper+' and signed rollback '+prior.home+' match release metadata and packages.\n');
  if(option!=='--check-only')process.stdout.write(gh(['release','edit',tag,'--draft=false','--latest']));
 }finally{fs.rmSync(folder,{recursive:true,force:true});}
}
module.exports={verifyRootRelease,verifyHomeRelease,verifySystemRelease};
if(require.main===module){try{main(process.argv.slice(2));}catch(error){process.stderr.write(String(error.message)+'\n');process.exitCode=1;}}
