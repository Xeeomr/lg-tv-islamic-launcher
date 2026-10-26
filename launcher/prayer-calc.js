/* Offline prayer times (standard solar-angle method) and Umm al-Qura Hijri dates. */
(function (root, factory) { if (typeof module === 'object' && module.exports) module.exports = factory(); else root.PrayerCalc = factory(); }(this, function () {
  'use strict';
  // fajr/isha: degrees below the horizon, or {min: n} minutes after maghrib. maghrib: degrees when it is not sunset.
  var METHODS = {
    4: {name: 'أم القرى - مكة المكرمة', fajr: 18.5, isha: {min: 90}, ramadanIsha: {min: 120}},
    3: {name: 'رابطة العالم الإسلامي', fajr: 18, isha: 17},
    5: {name: 'الهيئة المصرية العامة للمساحة', fajr: 19.5, isha: 17.5},
    2: {name: 'أمريكا الشمالية (ISNA)', fajr: 15, isha: 15},
    1: {name: 'جامعة العلوم الإسلامية - كراتشي', fajr: 18, isha: 18},
    8: {name: 'منطقة الخليج', fajr: 19.5, isha: {min: 90}},
    9: {name: 'الكويت', fajr: 18, isha: 17.5},
    10: {name: 'قطر', fajr: 18, isha: {min: 90}},
    16: {name: 'دبي', fajr: 18.2, isha: 18.2, adj: {Sunrise: -3, Dhuhr: 3, Asr: 3, Maghrib: 3}},
    13: {name: 'رئاسة الشؤون الدينية - تركيا', fajr: 18, isha: 17, adj: {Sunrise: -7, Dhuhr: 5, Asr: 4, Maghrib: 7}},
    11: {name: 'سنغافورة', fajr: 20, isha: 18},
    12: {name: 'فرنسا (UOIF)', fajr: 12, isha: 12},
    7: {name: 'جامعة طهران', fajr: 17.7, isha: 14, maghrib: 4.5},
    19: {name: 'الجزائر', fajr: 18, isha: 17},
    18: {name: 'تونس', fajr: 18, isha: 18},
    21: {name: 'المغرب', fajr: 19, isha: 17},
    23: {name: 'الأردن', fajr: 18, isha: 18}
  };
  var BY_COUNTRY = {SA: 4, EG: 5, SD: 5, LY: 5, SY: 5, LB: 5, IQ: 3, YE: 4, KW: 9, QA: 10, AE: 16, BH: 8, OM: 8, TR: 13, SG: 11, FR: 12, IR: 7,
    PK: 1, IN: 1, BD: 1, AF: 1, US: 2, CA: 2, DZ: 19, TN: 18, MA: 21, JO: 23, PS: 23};
  var D = Math.PI / 180;
  function sin(d) { return Math.sin(d * D); } function cos(d) { return Math.cos(d * D); } function tan(d) { return Math.tan(d * D); }
  function asin(x) { return Math.asin(x) / D; } function acos(x) { return Math.acos(Math.max(-1, Math.min(1, x))) / D; } function atan2(y, x) { return Math.atan2(y, x) / D; }
  function fix(a, b) { a = a - b * Math.floor(a / b); return a < 0 ? a + b : a; }
  function julian(y, m, d) {
    if (m <= 2) { y -= 1; m += 12; }
    var A = Math.floor(y / 100), B = 2 - A + Math.floor(A / 4);
    return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + d + B - 1524.5;
  }
  function sun(jd) {
    var n = jd - 2451545.0, g = fix(357.529 + 0.98560028 * n, 360), q = fix(280.459 + 0.98564736 * n, 360);
    var L = fix(q + 1.915 * sin(g) + 0.020 * sin(2 * g), 360), e = 23.439 - 0.00000036 * n;
    var RA = atan2(cos(e) * sin(L), cos(L)) / 15;
    return {decl: asin(sin(e) * sin(L)), eqt: q / 15 - fix(RA, 24)};
  }
  // Hours after local midnight (in the city's standard meridian frame) for one day.
  function compute(y, m, d, lat, lon, tzHours, method, asrFactor) {
    var cfg = METHODS[method] || METHODS[3], jd = julian(y, m, d) - lon / (15 * 24);
    function midDay(t) { return fix(12 - sun(jd + t).eqt, 24); }
    function angleTime(angle, t, ccw) {
      var s = sun(jd + t), noon = midDay(t);
      var x = acos((-sin(angle) - sin(s.decl) * sin(lat)) / (cos(s.decl) * cos(lat))) / 15;
      return noon + (ccw ? -x : x);
    }
    function asrTime(factor, t) {
      var dec = sun(jd + t).decl, angle = -Math.atan(1 / (factor + tan(Math.abs(lat - dec)))) / D;
      return angleTime(angle, t);
    }
    var t = {
      Fajr: angleTime(cfg.fajr, 5 / 24, true), Sunrise: angleTime(0.833, 6 / 24, true), Dhuhr: midDay(12 / 24),
      Asr: asrTime(asrFactor || 1, 13 / 24), Sunset: angleTime(0.833, 18 / 24), Maghrib: 0, Isha: 0
    };
    t.Maghrib = cfg.maghrib ? angleTime(cfg.maghrib, 18 / 24) : t.Sunset;
    t.IshaAngle = typeof cfg.isha === 'number' ? angleTime(cfg.isha, 18 / 24) : null;
    var shift = tzHours - lon / 15, out = {}, adj = cfg.adj || {};
    Object.keys(t).forEach(function (k) { if (t[k] !== null) out[k] = t[k] + shift + (adj[k] || 0) / 60; });
    out.ishaMinutes = typeof cfg.isha === 'number' ? null : cfg.isha.min;
    out.ramadanIshaMinutes = cfg.ramadanIsha ? cfg.ramadanIsha.min : null;
    return out;
  }
  // Hijri date from the Umm al-Qura calendar built into the browser; offset shifts by whole days.
  var hijriFmt = null;
  function hijri(date, offsetDays) {
    var d = new Date(date.getTime() + (offsetDays || 0) * 86400000);
    try {
      hijriFmt = hijriFmt || new Intl.DateTimeFormat('en-u-ca-islamic-umalqura', {day: 'numeric', month: 'numeric', year: 'numeric', timeZone: 'UTC'});
      var p = {};
      hijriFmt.formatToParts(new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate(), 12))).forEach(function (x) { p[x.type] = x.value; });
      return {d: parseInt(p.day, 10), m: parseInt(p.month, 10), y: parseInt(p.year || p.relatedYear, 10)};
    } catch (_) { return null; }
  }
  var HIJRI_MONTHS = ['محرم', 'صفر', 'ربيع الأول', 'ربيع الآخر', 'جمادى الأولى', 'جمادى الآخرة', 'رجب', 'شعبان', 'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة'];
  return {METHODS: METHODS, BY_COUNTRY: BY_COUNTRY, compute: compute, hijri: hijri, HIJRI_MONTHS: HIJRI_MONTHS};
}));
