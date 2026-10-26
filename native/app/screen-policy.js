'use strict';
// Leaving any app or input returns to the custom Home, not only the apps that were on the dock at install;
// LG's own Home, its settings and system overlays keep their normal behaviour.
var SYSTEM=/^(com\.webos\.app\.(home|cpcover|screensaver.*|factorywin|softwareupdate)|com\.palm\.app\.settings|com\.gathin\.tvhome|com\.local\.nativehome)$/;
function returnsHome(id){return typeof id==='string'&&id!==''&&!SYSTEM.test(id);}
module.exports=function(){
 var previous=null,gapSince=null,backSince=null,backUntil=0,backConsumed=false;
 function clearBack(){backSince=null;backUntil=0;backConsumed=false;}
 return {
  reset:function(){previous=null;gapSince=null;clearBack();},
  clearBack:clearBack,
  // An app just closed (nothing in front yet) and LG Home is about to be raised: answer before it appears.
  gapFromApp:function(now){
   return gapSince!==null&&returnsHome(previous)&&!(backSince!==null&&now-backSince>=700)&&!(backUntil>0&&now<=backUntil);
  },
  back:function(down,now){
   if(down){if(backSince===null){backSince=now;backUntil=0;backConsumed=false;}}
   else {if(backSince!==null&&!backConsumed&&now-backSince>=700&&now-backSince<=10000)backUntil=now+2500;backSince=null;}
  },
  next:function(id,now){
   // webOS briefly reports no foreground app between app exit and LG Home.
   // Keep that origin only for a bounded gap; any real intermediate app resets it.
   if(id===''){
    if(gapSince===null)gapSince=now;
    return false;
   }
   if(id==='com.gathin.tvhome')clearBack();
   var intentionalHome=id==='com.webos.app.home'&&!backConsumed&&
    ((backSince!==null&&now-backSince>=700&&now-backSince<=10000)||(backUntil>0&&now<=backUntil));
   if(intentionalHome){backConsumed=true;backUntil=0;}
   var redirect=!intentionalHome&&id==='com.webos.app.home'&&returnsHome(previous)&&
    (gapSince===null||now-gapSince<=2500);
   previous=id;gapSince=null;return redirect;
  }
 };
};
