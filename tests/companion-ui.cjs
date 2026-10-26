// Run with Playwright available in NODE_PATH. Exercises real packaged Root UI
// and shared Home UI with deterministic device replies; never connects to a TV.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os'),http=require('node:http'),{execFileSync}=require('node:child_process');
const {chromium}=require('playwright');
(async()=>{
 const root=path.resolve(__dirname,'..'),tmp=fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'cytv-companion-')));
 execFileSync(process.env.PYTHON||'python3',['-c',`import sys,json\nfrom pathlib import Path\nsys.path.insert(0,'root-edition')\nimport build_updater\nsys.path.insert(0,'.')\nfrom cytv.package import data_files\np=build_updater.build(Path(sys.argv[1])/'bundle')\nprefix='usr/palm/applications/com.cleanyourtv.root.updater/'\nfor name,data in data_files(p.read_bytes()).items():\n if name.startswith(prefix):\n  out=Path(sys.argv[1])/'root'/name[len(prefix):];out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)`,tmp],{cwd:root});
 const server=http.createServer((req,res)=>{
  let name=decodeURIComponent(req.url.split('?')[0]);let file;
  if(name.startsWith('/root/'))file=path.join(tmp,name);
  else if(name.startsWith('/updater-app/')&&['renewal-panel.css','i18n.css','i18n.js','catalogs.js'].includes(path.basename(name)))file=path.join(root,'launcher',path.basename(name));
  else if(name==='/updater-app/root-locales.js')file=path.join(root,'root-edition/ui/root-locales.js');
  else file=path.join(root,name);
  if(!file.startsWith(root+path.sep)&&!file.startsWith(tmp+path.sep)){res.writeHead(403);return res.end();}
  const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.ttf':'font/ttf','.png':'image/png'};try{res.setHeader('Content-Type',types[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));}catch(_){res.writeHead(404);res.end();}
 });
 await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;
 try{
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});const page=await browser.newPage({viewport:{width:1920,height:1080}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/launcher/apps.js',r=>r.fulfill({body:'window.TV_APPS={apps:[{id:"test.app",title:"Test App",icon:"brand-v2-icon.png"}],inputs:[]};'}));
 await page.route('**/launcher/config.js',r=>r.fulfill({body:'window.CONFIG={columns:5,dockApps:[],hiddenApps:[]};'}));
 await page.addInitScript(()=>{
  localStorage.setItem('tvhome.language','ru');window.calls=[];window.helperRunning=true;window.helperBlocked=false;window.update=null;window.failStatus=false;
  window.PalmSystem={launchParams:JSON.stringify({showHelper:true})};
  window.PalmServiceBridge=class{cancel(){}call(uri,raw){const p=JSON.parse(raw);window.calls.push({uri,p});let reply={returnValue:true};
   if(uri.endsWith('/getSystemSettings'))reply.settings={localeInfo:{locales:{UI:'ru-RU'}}};
   else if(uri.endsWith('/homeStatus'))reply.enabled=true;
   else if(uri==='luna://com.local.nativehome.service/status')Object.assign(reply,{running:window.helperRunning,blocked:window.helperBlocked});
   else if(uri.includes('updater.service/')){reply={returnValue:!window.failStatus,result:window.update};}
   else if(uri.endsWith('/status'))reply.state={enabled:false,last:{}};
   else if(uri.endsWith('/listApps'))reply.apps=[];
   else if(uri.endsWith('/launch')&&p.params&&p.params.nativeHomeStart){window.helperRunning=true;window.helperBlocked=false;}
   this.onservicecallback(JSON.stringify(reply));
  }};
 });
 const base='http://127.0.0.1:'+server.address().port;
 await page.goto(base+'/launcher/index.html');const helper=page.locator('.root-settings').filter({has:page.getByRole('heading',{name:'Home Helper',exact:true})});await helper.waitFor();
 await page.locator('#tiles .item[data-app-id]').waitFor();
 assert.equal(await page.evaluate(()=>document.activeElement.textContent),'Открыть Home','initial Helper panel retains focus after Home renders');
 fs.mkdirSync(path.join(root,'build/companion-ui'),{recursive:true});await page.screenshot({path:path.join(root,'build/companion-ui/helper-ru.png')});
 await page.keyboard.press('Enter');await helper.waitFor({state:'hidden'});
 assert(!await page.evaluate(()=>calls.some(c=>c.p.id==='test.app')),'closing Helper must not launch the underlying app on OK release');
 await page.evaluate(()=>document.dispatchEvent(new CustomEvent('webOSRelaunch',{detail:{}})));await helper.waitFor({timeout:1500});await page.keyboard.press('Escape');
 await page.evaluate(()=>{helperRunning=false;helperBlocked=true;document.dispatchEvent(new CustomEvent('webOSRelaunch',{detail:{showHelper:true}}));});await helper.waitFor();
 assert((await helper.innerText()).includes('остановлен для безопасности'));
 assert(!await page.evaluate(()=>calls.some(c=>c.p.params&&c.p.params.nativeHomeStart)),'viewing stopped Helper must not restart it');
 await helper.getByRole('button',{name:'Запустить Helper',exact:true}).click();await page.locator('#homeConfirmation').waitFor();
 await page.locator('#homeConfirmation').getByRole('button',{name:'Отмена'}).click();assert(!await page.evaluate(()=>calls.some(c=>c.p.params&&c.p.params.nativeHomeStart)));
 await helper.getByRole('button',{name:'Запустить Helper',exact:true}).click();await page.locator('#homeConfirmation').getByRole('button',{name:'Запустить Helper',exact:true}).click();
 assert.equal(await page.evaluate(()=>calls.filter(c=>c.p.params&&c.p.params.nativeHomeStart).length),1);
 await page.waitForFunction(()=>Array.from(document.querySelectorAll('.root-settings button')).some(b=>b.textContent==='Запустить Helper'&&b.hidden),null,{timeout:4000});assert.equal(await page.evaluate(()=>document.activeElement.textContent),'Открыть Home','focus leaves the hidden restart action');
 await helper.getByRole('button',{name:'Обновить состояние',exact:true}).click();await helper.getByRole('button',{name:'Настроить кнопку Home'}).click();await page.locator('#renewalPanel').waitFor();
 for(const url of ['/updater-app/index.html','/root/index.html']){
  await page.goto(base+url);await page.getByText('Восстановление не требуется.',{exact:false}).waitFor();
  assert((await page.locator('body').innerText()).includes('Обычные обновления доступны в настройках Home.'));
  assert.equal(await page.getByRole('button',{name:/Восстановить предыдущую версию|Откатить/}).count(),0);
  if(url.includes('updater-app')){
   assert(await page.locator('#restore').isHidden());assert.equal(await page.evaluate(()=>document.activeElement.id),'open');
   await page.evaluate(()=>{failStatus=true;document.dispatchEvent(new Event('webOSRelaunch'));});await page.getByText('Не удалось проверить состояние.',{exact:true}).waitFor();assert(await page.locator('#restore').isHidden());
   await page.evaluate(()=>{failStatus=false;update={status:'complete',prior:{home:'1.3.5'}};document.dispatchEvent(new Event('webOSRelaunch'));});await page.locator('#restore').waitFor();
   await page.locator('#restore').click();await page.locator('#homeConfirmation').waitFor();assert((await page.locator('#homeConfirmation').innerText()).includes('будут потеряны'));await page.keyboard.press('Escape');
  }
  if(url==='/root/index.html'){
   await page.getByRole('button',{name:'Открыть Home',exact:true}).click();await page.locator('.root-updates').waitFor({state:'hidden'});
   await page.evaluate(()=>document.dispatchEvent(new Event('webOSRelaunch')));await page.locator('.root-updates').waitFor({timeout:1500});
   assert.equal(await page.evaluate(()=>document.activeElement.textContent),'Открыть Home');
  }
  const actions=await page.locator('button:visible').evaluateAll(bs=>bs.map(b=>b.getBoundingClientRect().bottom));assert(actions.every(y=>y<=1080),'actions fit TV viewport');
  fs.mkdirSync(path.join(root,'build/companion-ui'),{recursive:true});await page.screenshot({path:path.join(root,'build/companion-ui',url.includes('updater-app')?'updater-ru.png':'root-updater-ru.png')});
 }
 assert.deepEqual(errors,[]);console.log('PASS companion UI: manual Helper focus/OK release, emergency restart consent, settings, both packaged Updaters, unavailable status and restore confirmation');
 }finally{if(browser)await browser.close();await new Promise(r=>server.close(r));fs.rmSync(tmp,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exitCode=1;});
