'use strict';
exports.expired=function(last,now){return now-last>6000;};
exports.shouldBlock=function(code,signal){return !!signal||code!==25;};
