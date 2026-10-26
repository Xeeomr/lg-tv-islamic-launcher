const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const base=process.env.PREVIEW_URL||'http://127.0.0.1:8876';
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'chrome'});
 try{
  const samples={en:'Settings',de:'Einstellungen',es:'Ajustes','pt-BR':'Configurações',fr:'Paramètres',it:'Impostazioni',ko:'설정',hi:'सेटिंग्स',pl:'Ustawienia',ru:'Настройки'};
  for(const edition of ['launcher','root-launcher'])for(const [locale,label] of Object.entries(samples)){
   const context=await browser.newContext({viewport:{width:1920,height:1080},locale});
   const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&r.url().includes('/fonts/'))errors.push('Font resource failed: '+r.url());});
   await page.goto(base+'/'+edition+'/index.html');await page.locator('#tiles .add-app').waitFor();
   await page.evaluate(()=>document.fonts.ready);
   assert.equal(await page.locator('html').getAttribute('lang'),locale);
   assert(await page.locator('#topButtons').evaluate(el=>el.getBoundingClientRect().right<=1809),'localized date must keep shortcuts inside header');
   assert.equal(await page.locator('#btnSettings span').textContent(),label);
   assert((await page.locator('#tiles .item .name').allTextContents()).includes('YouTube'),'third-party app names must not be translated');
   const languageButton=()=>edition==='launcher'?page.locator('#homeLanguage'):page.locator('.root-settings button').filter({hasText:new RegExp('^'+({en:'Language',de:'Sprache',es:'Idioma','pt-BR':'Idioma',fr:'Langue',it:'Lingua',ko:'언어',hi:'भाषा',pl:'Język',ru:'Язык'}[locale])+'$')});
   await page.locator('#btnSettings').click();await languageButton().waitFor({state:'visible'});
   assert(await page.locator(edition==='launcher'?'#renewalPanel':'.root-settings').evaluate(el=>getComputedStyle(el).fontFamily.includes('CYTV')),'settings must retain packaged language font fallbacks');
   await (edition==='launcher'?page.locator('#homeLanguage'):page.locator('.root-settings button').filter({hasText:await page.evaluate(()=>HomeI18n.t('Language'))})).click();assert.equal(await page.locator('#languageChoices button').count(),12);
   await page.evaluate(()=>{const parent=document.querySelector('#homeVisit')||document.querySelector('.root-settings button');parent.focus();});
   assert.equal(await page.evaluate(()=>document.activeElement.dataset.language),'auto','delayed settings replies cannot steal modal focus');
   // Remote navigation follows the displayed row-major order; Back restores focus.
   await page.keyboard.press('ArrowDown');assert.equal(await page.evaluate(()=>document.activeElement.dataset.language),'de');
   await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>document.activeElement.textContent),await page.evaluate(()=>HomeI18n.t('Language')));
   await (edition==='launcher'?page.locator('#homeLanguage'):page.locator('.root-settings button').filter({hasText:await page.evaluate(()=>HomeI18n.t('Language'))})).click();
   const target=locale==='ru'?'de':'ru';await page.locator('[data-language="'+target+'"]').click();
   await page.waitForFunction(code=>document.documentElement.lang===code,target);
   await page.locator('#tiles .add-app').waitFor();
   assert.equal(await page.evaluate(()=>localStorage.getItem('tvhome.language')),target);
   await page.reload();await page.locator('#tiles .add-app').waitFor();assert.equal(await page.locator('html').getAttribute('lang'),target);
   await page.locator('#btnSettings').click();await (edition==='launcher'?page.locator('#homeLanguage'):page.locator('.root-settings button').filter({hasText:await page.evaluate(()=>HomeI18n.t('Language'))})).click();await page.locator('[data-language="auto"]').click();
   await page.waitForFunction(code=>document.documentElement.lang===code,locale);await page.locator('#tiles .add-app').waitFor();
   await page.locator('#btnSettings').click();await languageButton().waitFor({state:'visible'});
   await page.screenshot({path:'/tmp/cytv-settings-'+edition+'-'+locale+'.png'});
   assert.deepEqual(errors,[],locale+' browser errors');await context.close();
  }
  console.log('PASS ten UI languages, app name preservation, remote modal, persisted override and automatic reset');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
