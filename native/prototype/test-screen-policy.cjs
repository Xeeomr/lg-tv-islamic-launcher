const a=require('node:assert/strict'),make=require('../app/screen-policy');
const home='com.webos.app.home',app='com.example.video';
let p=make([app]);
a.equal(p.next(home),false); // Initial LG screen is not an exit.
a.equal(p.next(app),false);
a.equal(p.next(app),false); // Internal navigation and cancelled exit.
a.equal(p.next(home),true);
a.equal(p.next(home),false); // One attempt, no launch loop.
p.next(app);p.next('com.webos.app.hdmi1');a.equal(p.next(home),true); // inputs return to the custom Home too
p.next('com.palm.app.settings');a.equal(p.next(home),false); // LG settings stay with LG Home
p.next('com.other.unlisted');a.equal(p.next(home),true); // apps added after install
p.next(app);p.reset();a.equal(p.next(home),false); // Reconnect loses stale state.
p.next(app);p.next('com.gathin.tvhome');a.equal(p.next(home),false);
console.log('PASS: exit transitions, internal Back, HDMI, reconnect and duplicate events');
p.reset();p.next(app,100);p.next('',200);a.equal(p.next(home,1300),true);
p.reset();p.next(app,100);p.next('',200);p.next('',2200);a.equal(p.next(home,2800),false);
p.reset();p.next(app,100);p.next('',200);p.next('com.palm.app.settings',300);a.equal(p.next(home,400),false);
console.log('PASS: bounded empty foreground gap and unrelated transitions');
// A long Back explicitly asks to stay in LG Home, without stopping the helper.
p=make([app,'com.webos.app.hdmi1']);
a.equal(typeof p.back,'function','screen policy must distinguish long Back from ordinary app exit');
p.next(app,0);p.back(true,100);p.next('',800);a.equal(p.next(home,1100),false);
p.back(false,1200);p.next(app,1300);a.equal(p.next(home,1400),true); // consumed once
p.next('com.webos.app.hdmi1',2000);p.back(true,2100);p.back(false,3200);a.equal(p.next(home,3500),false); // long Back from an input
p.next(app,4000);p.back(true,4100);p.back(false,4200);a.equal(p.next(home,4300),true); // short Back
p.next(app,5000);p.back(true,5100);p.back(false,6200);a.equal(p.next(home,9000),true); // expired
p.next(app,10000);p.back(true,10100);p.back(false,11200);p.reset();p.next(app,11300);a.equal(p.next(home,11400),true);
p.next(app,12000);p.back(true,12100);p.back(true,12500);a.equal(p.next(home,12900),false); // repeat doesn't reset hold
console.log('PASS: long Back, HDMI, empty gap, release ordering, short Back, expiry and reconnect');
p=make();p.next(app,0);p.next('',100);a.equal(p.gapFromApp(150),true);
p.next('com.other.app',200);a.equal(p.gapFromApp(250),false); // another app took the screen
p.reset();p.next('com.gathin.tvhome',0);p.next('',100);a.equal(p.gapFromApp(150),false); // leaving our Home
p.reset();p.next(app,0);p.back(true,100);p.next('',900);a.equal(p.gapFromApp(950),false); // long Back wants LG Home
console.log('PASS: early return while the closing app leaves an empty foreground');
