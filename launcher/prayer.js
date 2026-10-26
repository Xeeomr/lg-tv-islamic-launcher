/* Arabic Islamic home: clock, dates, weather, offline prayer times, Ramadan countdown, Quran/hadith,
   adhan, pre-prayer alerts, screensaver, time-of-day wallpapers and a full Arabic settings panel. */
(function () {
  'use strict';
  var STORE = 'tvhome.prayer.v1', BACKUP = 'tvhome.prayer.backup.v1', WEATHER = 'tvhome.weather.v1', FIRED = 'tvhome.prayer.fired.v1', RECENT = 'tvhome.content.recent.v1', VERSION = 6;
  var SERVICE = 'luna://com.gathin.tvhome.prayer/', APP_VERSION = '2.0.0';
  var Calc = window.PrayerCalc;
  var ORDER = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'];
  var NAMES = {Fajr: 'الفجر', Sunrise: 'الشروق', Dhuhr: 'الظهر', Asr: 'العصر', Maghrib: 'المغرب', Isha: 'العشاء'};
  var DAYS = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'];
  var MONTHS = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'];
  var PERIODS = {fajr: 'الفجر', day: 'النهار', maghrib: 'المغرب', night: 'الليل'};
  var VOICES = window.PRAYER_VOICES || [];
  var WALLS = window.PRAYER_WALLPAPERS || [];
  var PASS_KEYS = [447, 448, 449, 33, 34]; // volume, mute, channel: keep their usual job during the adhan
  var DEFAULTS = {
    v: VERSION,
    city: {name: 'مكة المكرمة', country: 'السعودية', cc: 'SA', lat: 21.4266, lon: 39.8256, tz: 'Asia/Riyadh'},
    autoMethod: true, method: 4, asr: 1, offsets: {Fajr: 0, Sunrise: 0, Dhuhr: 0, Asr: 0, Maghrib: 0, Isha: 0},
    alert: 'adhan', perPrayer: {Fajr: true, Dhuhr: true, Asr: true, Maghrib: true, Isha: true}, fullScreen: true,
    voice: 'adhan-makkah.mp3', fajrVoice: 'same', appVolume: 100, volume: 0, returnPrev: true, resume: true,
    preEnabled: true, prealert: 10,
    contentType: 'mix',
    wallMode: 'time', wallFixed: 'nabawi', wallEvery: 20, showCredit: true, dim: 0.75, textScale: 100,
    saver: 3, saverWallMode: 'time', saverWall: 'nabawi',
    weather: true, unit: 'c',
    hijriOffset: 0, showHijri: true
  };
  var settings, days = [], weather = null, ramadan = null, cities = null, content = {index: null, hadith: null};
  var head, card, credit, overlay, saver, banner, panel, wallA, wallB, wallDim, wallFront = 0, wallShown = '';
  var adhanAudio = null, adhanEvent = null, idleAt = Date.now(), saverOn = false, saverTimer = 0, saverStep = 0, saverLayer = 0, cardKey = '', homeItem = null, testTimer = 0;

  // ---- helpers ------------------------------------------------------------------------------
  function ar(n) { return String(n).replace(/\d/g, function (d) { return '٠١٢٣٤٥٦٧٨٩'.charAt(d); }); }
  function pad(n) { return n < 10 ? '0' + n : String(n); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function byId(id) { return document.getElementById(id); }
  function read(key, fallback) { try { var raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback; } catch (_) { return fallback; } }
  function write(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch (_) { return false; } }
  function merge(base, extra) {
    var out = {};
    Object.keys(base).forEach(function (k) {
      var b = base[k], e = extra ? extra[k] : undefined;
      out[k] = b && typeof b === 'object' && !Array.isArray(b) && k !== 'city' ? merge(b, e) : e !== undefined && (typeof e === typeof b || b === null) ? e : b;
    });
    return out;
  }
  function wallById(id) { return WALLS.filter(function (x) { return x.id === id; })[0] || null; }
  function voiceName(file) { var v = VOICES.filter(function (x) { return x.file === file; })[0]; return v ? v.name : 'غير متوفر'; }
  function loadSettings() {
    var s = read(STORE, {});
    var out = merge(DEFAULTS, s);
    if (!s.v || s.v < VERSION) {
      out.v = VERSION;
      if (s.alert) out.alert = s.alert;
      if (s.wallpaper && s.wallpaper !== 'auto') { out.wallMode = s.wallpaper === 'none' ? 'none' : 'fixed'; if (wallById(s.wallpaper)) out.wallFixed = s.wallpaper; }
    }
    if (!out.city || typeof out.city.lat !== 'number') out.city = DEFAULTS.city;
    if (!VOICES.some(function (v) { return v.file === out.voice; })) out.voice = VOICES.length ? VOICES[0].file : '';
    if (out.fajrVoice !== 'same' && !VOICES.some(function (v) { return v.file === out.fajrVoice; })) out.fajrVoice = 'same';
    if (!wallById(out.wallFixed)) out.wallFixed = WALLS.length ? WALLS[0].id : '';
    if (!wallById(out.saverWall)) out.saverWall = out.wallFixed;
    return out;
  }
  function save() { write(STORE, settings); document.documentElement.style.fontSize = settings.textScale + '%'; }
  function fmtTime(ms) { var d = new Date(ms), h = d.getHours(); return {t: ar((h % 12 || 12) + ':' + pad(d.getMinutes())), s: h < 12 ? 'ص' : 'م', long: h < 12 ? 'صباحًا' : 'مساءً'}; }
  function fmtClock(ms) { var f = fmtTime(ms); return f.t + ' ' + f.s; }
  function fmtLeft(ms) {
    var m = Math.max(1, Math.ceil(ms / 60000)), h = Math.floor(m / 60), r = m % 60;
    var hours = h === 1 ? 'ساعة' : h === 2 ? 'ساعتان' : ar(h) + (h <= 10 ? ' ساعات' : ' ساعة');
    var mins = r === 1 ? 'دقيقة' : r === 2 ? 'دقيقتان' : ar(r) + (r <= 10 ? ' دقائق' : ' دقيقة');
    if (!h) return mins;
    return hours + (r ? ' و' + mins : '');
  }

  // ---- offline prayer times ---------------------------------------------------------------------
  var zoneFormats = {};
  function offsetAt(utc, tz) {
    var parts = {};
    try {
      // Building an Intl formatter is slow on the TV; keep one per time zone.
      (zoneFormats[tz] = zoneFormats[tz] || new Intl.DateTimeFormat('en-US', {timeZone: tz, hourCycle: 'h23', year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric', second: 'numeric'}))
        .formatToParts(new Date(utc)).forEach(function (p) { parts[p.type] = p.value; });
      return Date.UTC(+parts.year, +parts.month - 1, +parts.day, +parts.hour % 24, +parts.minute, +parts.second) - utc;
    } catch (_) { return -new Date(utc).getTimezoneOffset() * 60000; }
  }
  function methodFor() { return settings.autoMethod && Calc.BY_COUNTRY[settings.city.cc] ? Calc.BY_COUNTRY[settings.city.cc] : settings.method; }
  function hijriOf(date) { return Calc.hijri(date, settings.hijriOffset); }
  function hijriText(h) { return h ? ar(h.d) + ' ' + Calc.HIJRI_MONTHS[h.m - 1] + ' ' + ar(h.y) + ' هـ' : ''; }
  function computeDay(date) {
    var c = settings.city, y = date.getFullYear(), m = date.getMonth() + 1, d = date.getDate();
    var midnight = Date.UTC(y, m - 1, d), tzMs = offsetAt(midnight + 12 * 3600000, c.tz), tzH = tzMs / 3600000;
    var h = hijriOf(date), method = methodFor();
    var raw = Calc.compute(y, m, d, c.lat, c.lon, tzH, method, settings.asr), t = {};
    if (raw.ishaMinutes !== null) raw.Isha = raw.Maghrib + ((h && h.m === 9 && raw.ramadanIshaMinutes) || raw.ishaMinutes) / 60;
    else raw.Isha = raw.IshaAngle;
    ORDER.concat(['Sunrise']).forEach(function (k) {
      t[k] = midnight - tzMs + Math.round(raw[k] * 60 + (settings.offsets[k] || 0)) * 60000;
    });
    return {d: y + '-' + pad(m) + '-' + pad(d), h: h, t: t};
  }
  function ensureData() {
    var start = new Date(); start.setHours(12, 0, 0, 0); start.setDate(start.getDate() - 1);
    var key = start.toDateString() + '|' + JSON.stringify([settings.city, settings.method, settings.autoMethod, settings.asr, settings.offsets, settings.hijriOffset]);
    if (ensureData.key === key) return;
    ensureData.key = key; days = [];
    for (var i = 0; i < 62; i++) { var d = new Date(start); d.setDate(start.getDate() + i); days.push(computeDay(d)); }
    eventCache = null; cardKey = '';
    // Not needed for the first paint.
    setTimeout(function () { computeRamadan(); renderRamadan(); syncService(); }, 1500);
  }
  var eventCache = null;
  function events() {
    if (eventCache) return eventCache;
    var out = [];
    days.forEach(function (day) { ORDER.forEach(function (name) { out.push({id: day.d + '-' + name, key: name, name: NAMES[name], ts: day.t[name], day: day.d}); }); });
    return (eventCache = out);
  }
  function todayRow() {
    var n = new Date(), id = n.getFullYear() + '-' + pad(n.getMonth() + 1) + '-' + pad(n.getDate());
    for (var i = 0; i < days.length; i++) if (days[i].d === id) return days[i];
    return null;
  }
  function neighbours(now) {
    var list = events(), prev = null, next = null;
    for (var i = 0; i < list.length; i++) { if (list[i].ts <= now) prev = list[i]; else { next = list[i]; break; } }
    return {prev: prev, next: next};
  }
  function computeRamadan() {
    var today = new Date(); today.setHours(12, 0, 0, 0);
    var h = hijriOf(today);
    if (!h) { ramadan = null; return; }
    if (h.m === 9) { ramadan = {inside: true, day: h.d}; return; }
    for (var i = 1; i < 400; i++) {
      var d = new Date(today); d.setDate(today.getDate() + i);
      var x = hijriOf(d);
      if (x && x.m === 9 && x.d === 1) { ramadan = {inside: false, days: i, date: d}; return; }
    }
    ramadan = null;
  }

  // ---- weather (cached; shows the last update when offline) -------------------------------------
  var WEATHER_TEXT = [[0, 'صافٍ'], [1, 'صافٍ غالبًا'], [2, 'غائم جزئيًا'], [3, 'غائم'], [48, 'ضباب'], [57, 'رذاذ'], [67, 'مطر'], [77, 'ثلج'], [82, 'زخّات مطر'], [86, 'زخّات ثلج'], [99, 'عواصف رعدية']];
  function weatherText(code) { for (var i = 0; i < WEATHER_TEXT.length; i++) if (code <= WEATHER_TEXT[i][0]) return WEATHER_TEXT[i][1]; return ''; }
  function weatherIcon(code, day) {
    if (code >= 95) return '<svg viewBox="0 0 24 24"><path d="M6.5 16a4.5 4.5 0 0 1-.4-9A6 6 0 0 1 17.6 6a4.5 4.5 0 0 1 .4 9z"/><path d="M12 14l-2 4h3l-2 4" stroke="currentColor" stroke-width="1.6" fill="none"/></svg>';
    if (code >= 51) return '<svg viewBox="0 0 24 24"><path d="M6.5 16a4.5 4.5 0 0 1-.4-9A6 6 0 0 1 17.6 6a4.5 4.5 0 0 1 .4 9z"/><path d="M8 19l-1 2M12 19l-1 2M16 19l-1 2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>';
    if (code >= 45) return '<svg viewBox="0 0 24 24"><path d="M3 9h18M5 13h14M3 17h18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
    if (code >= 2) return '<svg viewBox="0 0 24 24"><path d="M6.5 19a4.5 4.5 0 0 1-.4-9A6 6 0 0 1 17.6 9a4.5 4.5 0 0 1 .4 9z"/></svg>';
    if (day) return '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4.6"/><path d="M12 1.5v3M12 19.5v3M1.5 12h3M19.5 12h3M4.6 4.6l2.1 2.1M17.3 17.3l2.1 2.1M4.6 19.4l2.1-2.1M17.3 6.7l2.1-2.1" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>';
    return '<svg viewBox="0 0 24 24"><path d="M14.5 2.5A9.5 9.5 0 1 0 21.5 17 7.6 7.6 0 0 1 14.5 2.5z"/></svg>';
  }
  function getJSON(url, done, timeout) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url); xhr.timeout = timeout || 15000;
    xhr.onload = function () { try { return done(JSON.parse(xhr.responseText)); } catch (_) { done(null); } };
    xhr.onerror = xhr.ontimeout = function () { done(null); };
    xhr.send();
  }
  function loadWeather(force) {
    var c = settings.city, cached = read(WEATHER, null);
    if (cached && cached.city === c.lat + ',' + c.lon) weather = cached;
    if (!settings.weather) return renderHead();
    if (!force && weather && Date.now() - weather.at < 20 * 60000) return renderHead();
    getJSON('https://api.open-meteo.com/v1/forecast?latitude=' + c.lat + '&longitude=' + c.lon + '&current=temperature_2m,weather_code,is_day&daily=temperature_2m_max,temperature_2m_min&forecast_days=1&timezone=auto', function (j) {
      if (j && j.current && j.daily) {
        weather = {city: c.lat + ',' + c.lon, at: Date.now(), t: j.current.temperature_2m, c: j.current.weather_code, day: j.current.is_day === 1, max: j.daily.temperature_2m_max[0], min: j.daily.temperature_2m_min[0]};
        write(WEATHER, weather);
      }
      renderHead();
    });
  }
  function temp(c) { return ar(Math.round(settings.unit === 'f' ? c * 9 / 5 + 32 : c)) + '°'; }

  // ---- service bridge -----------------------------------------------------------------------
  function rpc(uri, payload, cb) {
    var bridge, done = false, timer = setTimeout(function () { finish(null); }, 8000);
    function finish(r) { if (done) return; done = true; clearTimeout(timer); if (bridge) try { bridge.cancel(); } catch (_) {} if (cb) cb(r); }
    try { bridge = new PalmServiceBridge(); bridge.onservicecallback = function (raw) { try { finish(JSON.parse(raw)); } catch (_) { finish(null); } }; bridge.call(uri, JSON.stringify(payload || {})); } catch (_) { finish(null); }
  }
  function syncService() {
    var now = Date.now();
    rpc(SERVICE + 'setSchedule', {
      enabled: settings.alert !== 'off', mode: settings.fullScreen ? settings.alert : 'notify', volume: settings.volume, prealert: settings.preEnabled ? settings.prealert : 0,
      resume: settings.resume, city: settings.city.name,
      events: events().filter(function (e) { return e.ts > now - 3600000 && settings.perPrayer[e.key]; }).map(function (e) { return {id: e.id, name: e.name, ts: e.ts}; })
    });
  }

  // ---- Quran and hadith (offline files, verified source text) ------------------------------------
  function loadLocal(path, done) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', path);
    xhr.onload = function () { try { done(JSON.parse(xhr.responseText)); } catch (_) { done(null); } };
    xhr.onerror = function () { done(null); };
    xhr.send();
  }
  function recentHas(ref) { return read(RECENT, []).indexOf(ref) >= 0; }
  function remember(ref) { var l = read(RECENT, []); l.push(ref); write(RECENT, l.slice(-60)); }
  // Picks a whole ayah or hadith that fits the space; never cuts a text.
  function pickItem(maxLen, done) {
    var type = settings.contentType, wantQuran = type === 'quran' || (type === 'mix' && Math.random() < 0.6);
    if (wantQuran && content.index) return pickAyah(maxLen, done, 0);
    if (!wantQuran && content.hadith) { var h = pickHadith(maxLen); if (h || type === 'hadith') return done(h); }
    if (content.index) return pickAyah(maxLen, done, 0);
    done(null);
  }
  function pickAyah(maxLen, done, tries) {
    var index = content.index, total = 0, i;
    for (i = 0; i < index.length; i++) total += index[i][1];
    var r = Math.floor(Math.random() * total), s = 0;
    for (i = 0; i < index.length; i++) { if (r < index[i][1]) { s = i; break; } r -= index[i][1]; }
    loadLocal('quran/' + ('00' + (s + 1)).slice(-3) + '.json', function (sura) {
      if (!sura) return done(null);
      var options = [];
      sura.a = sura.a.map(function (t, n) { return n === 0 ? ayahText(t, s + 1) : t; });
      sura.a.forEach(function (t, n) { var ref = 'q' + (s + 1) + ':' + (n + 1); if (t.length <= maxLen && t.length >= 25 && !recentHas(ref)) options.push(n); });
      if (!options.length) return tries < 6 ? pickAyah(maxLen, done, tries + 1) : done(null);
      var n = options[Math.floor(Math.random() * options.length)];
      remember('q' + (s + 1) + ':' + (n + 1));
      done({kind: 'quran', t: sura.a[n], num: n + 1, r: 'سورة ' + sura.n + ' ' + ar(s + 1) + ':' + ar(n + 1)});
    });
  }
  // The Tanzil text prefixes the basmala to ayah 1 of each surah (except 1 and 9); hide it when
  // one ayah is shown on its own. The data files stay verbatim.
  function ayahText(t, surah) {
    t = t.replace(/\ufeff/g, '');
    if (surah === 1 || surah === 9) return t;
    var w = t.split(' ');
    var base = w.slice(0, 4).join('').replace(/ٱ/g, 'ا').replace(/[^\u0621-\u064A]/g, '');
    return w.length > 4 && base === 'بسماللهالرحمنالرحيم' ? w.slice(4).join(' ') : t;
  }
  function pickHadith(maxLen) {
    var pool = [];
    ['nawawi', 'qudsi'].forEach(function (k) {
      (content.hadith[k] || []).forEach(function (h) {
        var ref = k + h.n;
        if (h.t.length <= maxLen && !recentHas(ref)) pool.push({kind: k, h: h, ref: ref});
      });
    });
    if (!pool.length) return null;
    var x = pool[Math.floor(Math.random() * pool.length)];
    remember(x.ref);
    var label = x.kind === 'qudsi' ? 'الأحاديث القدسية - حديث ' + ar(x.h.n) : 'الأربعون النووية - حديث ' + ar(x.h.n);
    return {kind: x.kind, t: x.h.t, r: label + (x.h.s ? ' · ' + x.h.s : '')};
  }
  function fitClass(text) { return text.length < 70 ? 'f1' : text.length < 130 ? 'f2' : text.length < 200 ? 'f3' : text.length < 280 ? 'f4' : 'f5'; }
  function fillContent(box, item, fade) {
    function put() {
      box.textContent = '';
      if (!item) { box.style.opacity = '1'; return; }
      var title = el('div', 'v-title'); title.appendChild(el('span', 'v-line'));
      title.appendChild(el('span', 'v-title-text', item.kind === 'quran' ? 'قال الله تعالى' : item.kind === 'qudsi' ? 'حديث قدسي' : 'قال رسول الله ﷺ'));
      title.appendChild(el('span', 'v-line')); box.appendChild(title);
      box.appendChild(el('div', 'p-text ' + (item.kind === 'quran' ? 'quran ' : '') + fitClass(item.t), item.kind === 'quran' ? item.t + ' ﴿' + ar(item.num) + '﴾' : item.t));
      box.appendChild(el('div', 'p-ref', item.r));
      box.style.opacity = '1';
    }
    if (!fade) return put();
    box.style.opacity = '0';
    setTimeout(put, 600);
  }
  function refreshHomeContent(fade) {
    pickItem(190, function (item) { if (item) { homeItem = item; fillContent(byId('pContent'), item, fade); } });
  }

  // ---- wallpapers by time of day -------------------------------------------------------------------
  function periodNow(now) {
    var row = todayRow(); if (!row) { var h = new Date(now).getHours(); return h < 6 ? 'fajr' : h < 16 ? 'day' : h < 19 ? 'maghrib' : 'night'; }
    var t = row.t;
    if (now >= t.Fajr && now < t.Sunrise + 45 * 60000) return 'fajr';
    if (now >= t.Sunrise + 45 * 60000 && now < t.Maghrib - 40 * 60000) return 'day';
    if (now >= t.Maghrib - 40 * 60000 && now < t.Isha) return 'maghrib';
    return 'night';
  }
  function wallsFor(period) { var l = WALLS.filter(function (w) { return w.p === period; }); return l.length ? l : WALLS; }
  function rotating(list, every, salt) { return list.length ? list[(Math.floor(Date.now() / (every * 60000)) + (salt || 0)) % list.length].id : 'none'; }
  function currentWall() {
    if (settings.wallMode === 'none') return 'none';
    if (settings.wallMode === 'fixed') return settings.wallFixed;
    if (settings.wallMode === 'cycle') return rotating(WALLS, settings.wallEvery);
    return rotating(wallsFor(periodNow(Date.now())), settings.wallEvery);
  }
  function ensureWall() {
    if (wallA) return;
    wallA = el('div', 'wall-layer'); wallB = el('div', 'wall-layer'); wallDim = el('div'); wallDim.id = 'wallDim';
    var holder = el('div'); holder.id = 'wallpaper';
    holder.appendChild(wallA); holder.appendChild(wallB); holder.appendChild(wallDim);
    document.body.insertBefore(holder, document.body.firstChild);
  }
  function setWall(id, immediate) {
    ensureWall();
    wallDim.style.opacity = Math.max(0.2, Math.min(0.92, settings.dim));
    var w = wallById(id);
    if (credit) { credit.textContent = w && settings.showCredit ? w.name + ' · ' + w.credit : ''; }
    if (id === wallShown) return;
    wallShown = id;
    var next = wallFront ? wallA : wallB, cur = wallFront ? wallB : wallA;
    next.style.backgroundImage = w ? 'url(wallpapers/' + id + '.jpg)' : 'none';
    next.style.transition = cur.style.transition = immediate ? 'none' : 'opacity 1200ms ease';
    next.style.opacity = '1'; cur.style.opacity = '0';
    wallFront = wallFront ? 0 : 1;
    setTimeout(function () { if (cur.style.opacity === '0') cur.style.backgroundImage = 'none'; }, immediate ? 0 : 1500);
  }

  // ---- home ---------------------------------------------------------------------------------------
  function buildHome() {
    credit = el('div'); credit.id = 'wallCredit'; document.body.appendChild(credit);
    head = el('div'); head.id = 'prayerHead';
    head.innerHTML = '<div class="h-time"><span id="hClock"></span><span class="h-ampm" id="hAmpm"></span></div>' +
      '<div class="h-dates"><div class="h-day" id="hDay"></div><div class="h-date" id="hDate"></div></div><div class="h-sep" id="hSep"></div>' +
      '<div class="h-weather" id="hWeather"><div class="h-wtop"><span id="hTemp"></span><span class="h-wicon" id="hWIcon"></span></div><div class="h-wtext" id="hWText"></div><div class="h-wrange" id="hWRange"></div></div>';
    document.body.appendChild(head);
    card = el('div'); card.id = 'prayerCard';
    card.innerHTML = '<div class="p-row1" id="pTimes"></div><div class="p-row2"><div class="p-box p-verse" id="pContent"></div>' +
      '<div class="p-box p-ramadan"><div class="r-text"><div class="r-label" id="rLabel"></div><div class="r-num"><span id="rNum"></span><span class="r-unit" id="rUnit"></span></div><div class="r-sub" id="rSub"></div></div>' +
      '<svg class="r-icon" viewBox="0 0 64 64"><path d="M30 6a26 26 0 1 0 28 33A21 21 0 0 1 30 6z"/><path d="M46 14l2.4 5 5.4.6-4 3.7 1.1 5.4-4.9-2.8-4.8 2.8 1.1-5.4-4-3.7 5.4-.6z"/></svg></div></div>';
    document.body.appendChild(card);
    setTimeout(function () { card.className = 'in'; head.className = 'in'; }, 60);
  }
  function renderHead() {
    if (!head) return;
    var now = new Date(), f = fmtTime(now.getTime()), row = todayRow();
    byId('hClock').textContent = f.t; byId('hAmpm').textContent = f.long;
    byId('hDay').textContent = DAYS[now.getDay()];
    byId('hDate').textContent = ar(now.getDate()) + ' ' + MONTHS[now.getMonth()] + ' ' + ar(now.getFullYear()) + (settings.showHijri && row ? ' · ' + hijriText(row.h) : '');
    var box = byId('hWeather'), show = settings.weather && weather;
    box.style.display = show ? '' : 'none'; byId('hSep').style.display = show ? '' : 'none';
    if (!show) return;
    byId('hTemp').textContent = temp(weather.t);
    byId('hWIcon').innerHTML = weatherIcon(weather.c, weather.day);
    var stale = Date.now() - weather.at > 60 * 60000;
    byId('hWText').textContent = weatherText(weather.c) + ' · ' + settings.city.name;
    byId('hWRange').textContent = stale ? 'آخر تحديث ' + fmtClock(weather.at) : 'العظمى ' + temp(weather.max) + ' الصغرى ' + temp(weather.min);
  }
  function renderRamadan() {
    var label = byId('rLabel'), num = byId('rNum'), unit = byId('rUnit'), sub = byId('rSub');
    if (!label) return;
    if (!ramadan) { label.textContent = 'رمضان'; num.textContent = '—'; unit.textContent = ''; sub.textContent = ''; return; }
    if (ramadan.inside) { label.textContent = 'رمضان مبارك'; num.textContent = ar(ramadan.day); unit.textContent = ' رمضان'; sub.textContent = 'تقبّل الله صيامكم وقيامكم'; return; }
    var n = ramadan.days, t = ramadan.date;
    label.textContent = 'باقٍ على رمضان'; num.textContent = ar(n);
    unit.textContent = n === 1 ? ' يوم' : n === 2 ? ' يومان' : n <= 10 ? ' أيام' : ' يومًا';
    sub.textContent = 'يوافق ' + DAYS[t.getDay()] + ' ' + ar(t.getDate()) + ' ' + MONTHS[t.getMonth()] + ' تقديريًا حتى الإعلان الرسمي';
  }
  function render() {
    if (!card) return;
    renderHead();
    var now = Date.now(), row = todayRow(), nb = neighbours(now), next = nb.next, times = byId('pTimes');
    if (!row || !next) return;
    var key = row.d + '|' + next.id + '|' + Math.floor(now / 30000);
    if (key === cardKey) return;
    cardKey = key; times.textContent = '';
    ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'].forEach(function (name) {
      var t = row.t[name], isNext = name !== 'Sunrise' && (next.id === row.d + '-' + name || (name === 'Fajr' && next.day !== row.d)), f = fmtTime(t);
      var c = el('div', 'p-card' + (isNext ? ' now' : '') + (name === 'Sunrise' ? ' sunrise' : '') + (t < now && !isNext ? ' past' : ''));
      c.appendChild(el('div', 'p-card-name', NAMES[name]));
      var time = el('div', 'p-card-time'); time.appendChild(el('span', '', isNext && next.day !== row.d ? fmtTime(next.ts).t : f.t)); time.appendChild(el('span', 'p-card-ampm', ' ' + f.s)); c.appendChild(time);
      if (isNext) c.appendChild(el('div', 'p-badge', 'متبقٍ ' + fmtLeft(next.ts - now)));
      times.appendChild(c);
    });
    renderRamadan();
  }

  // ---- alerts and adhan ------------------------------------------------------------------------------
  function firedList() { return read(FIRED, []); }
  function markFired(id) { var l = firedList(); if (l.indexOf(id) < 0) { l.push(id); write(FIRED, l.slice(-40)); } }
  function showBanner(text, ms) {
    if (!banner) { banner = el('div'); banner.id = 'prayerBanner'; document.body.appendChild(banner); }
    banner.textContent = text; banner.className = 'shown';
    clearTimeout(showBanner.t); showBanner.t = setTimeout(function () { banner.className = ''; }, ms || 10000);
  }
  function voiceFor(ev) { return ev.key === 'Fajr' && settings.fajrVoice !== 'same' ? settings.fajrVoice : settings.voice; }
  function startAdhan(ev) {
    if (adhanEvent || (!ev.test && (settings.alert === 'off' || firedList().indexOf(ev.id) >= 0))) return;
    if (!ev.key) ORDER.forEach(function (k) { if (NAMES[k] === ev.name) ev.key = k; });
    if (!ev.test && ev.key && !settings.perPrayer[ev.key]) return;
    markFired(ev.id);
    if (!ev.test && (settings.alert === 'notify' || !settings.fullScreen)) { showBanner('حان الآن موعد صلاة ' + ev.name); return; }
    stopSaver();
    if (panel && !panel.hidden) closePanel();
    if (window.RadioUI) RadioUI.pauseForAdhan();
    adhanEvent = ev;
    if (!overlay) {
      overlay = el('div'); overlay.id = 'adhanOverlay';
      overlay.innerHTML = '<div class="a-bg"></div><div class="a-shade"></div><div class="a-inner"><div class="a-small" id="aSmall"></div><div class="a-name" id="aName"></div><div class="a-city" id="aCity"></div>' +
        '<div class="a-time" id="aTime"></div><div class="a-call">اللهُ أكبرُ اللهُ أكبر</div></div><div class="a-hint">أي زر لإيقاف الأذان والعودة · أزرار الصوت تعمل كالمعتاد</div><div class="a-prog"><div class="a-prog-fill" id="aProg"></div></div>';
      document.body.appendChild(overlay);
    }
    var w = wallsFor(ev.key === 'Fajr' ? 'fajr' : ev.key === 'Maghrib' ? 'maghrib' : ev.key === 'Isha' ? 'night' : 'day');
    overlay.firstChild.style.backgroundImage = w.length ? 'url(wallpapers/' + w[Math.floor(Math.random() * w.length)].id + '.jpg)' : 'none';
    byId('aSmall').textContent = ev.test ? 'اختبار الأذان' : 'حان الآن موعد أذان';
    byId('aName').textContent = ev.name;
    byId('aCity').textContent = settings.city.name;
    byId('aTime').textContent = fmtClock(ev.ts);
    byId('aProg').style.width = '0';
    overlay.className = 'shown';
    rpc(SERVICE + 'adhanStart', {id: ev.id});
    adhanAudio = new Audio('audio/' + voiceFor(ev));
    adhanAudio.volume = Math.max(0.1, Math.min(1, settings.appVolume / 100));
    adhanAudio.onended = function () { setTimeout(finishAdhan, 2000); };
    adhanAudio.onerror = function () { setTimeout(finishAdhan, 15000); };
    adhanAudio.ontimeupdate = function () { if (adhanAudio && adhanAudio.duration) byId('aProg').style.width = (adhanAudio.currentTime / adhanAudio.duration * 100) + '%'; };
    var p = adhanAudio.play(); if (p && p.catch) p.catch(function () {});
  }
  function finishAdhan() {
    if (!adhanEvent) return;
    var ev = adhanEvent; adhanEvent = null;
    if (adhanAudio) { try { adhanAudio.pause(); } catch (_) {} adhanAudio = null; }
    overlay.className = '';
    if (window.RadioUI) RadioUI.resumeAfterAdhan();
    var back = settings.returnPrev ? ev.returnTo || '' : '';
    rpc(SERVICE + 'adhanDone', {id: ev.id, returnTo: back, resume: settings.resume}, function (r) {
      if ((!r || r.returnValue !== true) && back && back !== 'com.gathin.tvhome') rpc('luna://com.webos.applicationManager/launch', {id: back});
    });
  }
  function launchEvent(raw) {
    try {
      var p = typeof raw === 'string' ? JSON.parse(raw) : raw;
      if (p && p.params) p = p.params;
      if (p && p.adhan && p.adhan.id) { p.adhan.test = p.adhan.id.indexOf('test-') === 0; startAdhan(p.adhan); }
      // Home Helper cancelled LG's own screensaver: show ours instead.
      else if (p && p.saver && settings.saver && !adhanEvent && (!panel || panel.hidden)) startSaver();
    } catch (_) {}
  }
  function tick() {
    var now = Date.now();
    ensureData();
    render();
    if (Math.floor(now / 1000) % 30 === 0) setWall(currentWall());
    if (saverOn) updateSaver();
    var wifi = byId('btnWifi'); if (wifi) wifi.classList.toggle('online', !/offline|غير متصل/i.test(byId('wifiLabel').textContent));
    if (settings.alert !== 'off') events().forEach(function (e) {
      if (!settings.perPrayer[e.key]) return;
      if (now >= e.ts && now < e.ts + 90000) startAdhan({id: e.id, key: e.key, name: e.name, ts: e.ts});
      var pre = settings.preEnabled ? settings.prealert * 60000 : 0;
      if (pre && now >= e.ts - pre && now < e.ts - pre + 60000 && sessionStorage.getItem('pre' + e.id) !== '1') {
        try { sessionStorage.setItem('pre' + e.id, '1'); } catch (_) {}
        showBanner('اقترب موعد صلاة ' + e.name + ' — متبقٍ ' + fmtLeft(e.ts - now), 12000);
      }
    });
    if (settings.saver && !saverOn && !adhanEvent && (!panel || panel.hidden) && !document.hidden && now - idleAt > settings.saver * 60000) startSaver();
  }
  function scheduleTest(seconds) {
    clearInterval(testTimer);
    var left = seconds, next = neighbours(Date.now()).next;
    showBanner('سيبدأ اختبار الأذان بعد ' + ar(left) + ' ثانية — يمكنك فتح أي تطبيق الآن', 4000);
    // The service owns the countdown so it still fires while another app is in front.
    rpc(SERVICE + 'fire', {delay: seconds * 1000, name: next ? next.name : 'العصر'}, function (r) {
      if (!r || r.returnValue !== true) showBanner('تعذّر تشغيل خدمة الأذان: ' + ((r && r.errorText) || 'لا يوجد رد'));
    });
    testTimer = setInterval(function () {
      left--; if (left <= 0 || document.hidden) { clearInterval(testTimer); return; }
      if (left % 5 === 0 || left <= 5) showBanner('سيبدأ اختبار الأذان بعد ' + ar(left) + ' ثانية', 3000);
    }, 1000);
  }

  // ---- screensaver -------------------------------------------------------------------------------------
  function buildSaver() {
    saver = el('div'); saver.id = 'prayerSaver';
    saver.innerHTML = '<div class="sv-layer" id="svA"></div><div class="sv-layer" id="svB"></div><div class="sv-dim"></div>' +
      '<div class="sv-frame" id="svFrame"><div class="sv-head"><div class="s-clock"><span id="sClock"></span><span class="s-ampm" id="sAmpm"></span></div><div class="s-dates"><div id="sHijri"></div><div id="sGreg"></div></div></div>' +
      '<div class="sv-foot"><div class="s-content" id="sContent"></div><div class="s-next" id="sNext"></div></div></div>';
    document.body.appendChild(saver);
  }
  function saverWallList() {
    if (settings.saverWallMode === 'fixed') return [settings.saverWall];
    if (settings.saverWallMode === 'cycle') return WALLS.map(function (w) { return w.id; });
    return wallsFor(periodNow(Date.now())).map(function (w) { return w.id; });
  }
  function showSaverWall(id, instant) {
    var a = byId('svA'), b = byId('svB'), next = saverLayer ? a : b, cur = saverLayer ? b : a;
    next.style.backgroundImage = wallById(id) ? 'url(wallpapers/' + id + '.jpg)' : 'none';
    next.className = 'sv-layer'; void next.offsetWidth;
    next.className = 'sv-layer on ' + (Math.random() < 0.5 ? 'kb1' : 'kb2');
    next.style.transition = cur.style.transition = instant ? 'none' : '';
    cur.className = 'sv-layer';
    setTimeout(function () { if (cur.className === 'sv-layer') cur.style.backgroundImage = 'none'; }, instant ? 0 : 2600);
    saverLayer = saverLayer ? 0 : 1;
  }
  function updateSaver() {
    var d = new Date(), row = todayRow(), nb = neighbours(d.getTime()), f = fmtTime(d.getTime());
    byId('sClock').textContent = f.t; byId('sAmpm').textContent = f.long;
    byId('sHijri').textContent = row ? hijriText(row.h) : '';
    byId('sGreg').textContent = DAYS[d.getDay()] + ' ' + ar(d.getDate()) + ' ' + MONTHS[d.getMonth()] + ' ' + ar(d.getFullYear());
    if (nb.next) byId('sNext').textContent = 'صلاة ' + nb.next.name + ' بعد ' + fmtLeft(nb.next.ts - d.getTime());
  }
  // Moves the text a little every cycle so nothing stays in one place on the panel.
  var DRIFT = [[0, 0], [-40, 18], [36, -14], [-24, -22], [30, 20]];
  function saverCycle(first) {
    var list = saverWallList();
    if (first || list.length > 1) showSaverWall(list[saverStep % list.length], first);
    var drift = DRIFT[saverStep % DRIFT.length], frame = byId('svFrame');
    frame.style.webkitTransform = frame.style.transform = 'translate(' + drift[0] + 'px,' + drift[1] + 'px)';
    pickItem(330, function (item) { if (item) fillContent(byId('sContent'), item, !first); });
    saverStep++;
  }
  function startSaver(preview) {
    if (!saver) buildSaver();
    saverOn = true; saver.className = 'shown' + (preview ? ' preview' : ''); document.body.classList.add('saver-on');
    saverStep = Math.floor(Math.random() * 20);
    updateSaver(); saverCycle(true);
    clearInterval(saverTimer);
    saverTimer = setInterval(function () { saverCycle(false); }, 45000);
  }
  function stopSaver() {
    if (!saver || !saverOn) return;
    clearInterval(saverTimer); saverOn = false; saver.className = ''; document.body.classList.remove('saver-on');
    byId('svA').style.backgroundImage = byId('svB').style.backgroundImage = 'none';
  }

  // ---- cities -------------------------------------------------------------------------------------------
  var regionNames = null;
  function countryName(cc) {
    try { regionNames = regionNames || new Intl.DisplayNames(['ar'], {type: 'region'}); return regionNames.of(cc) || cc; } catch (_) { return cc; }
  }
  function loadCities(done) {
    if (cities) return done(cities);
    loadLocal('cities.json', function (j) { if (j) cities = j; done(cities); });
  }
  function cityObject(row) { return {name: row[0] || row[1], en: row[1], country: countryName(row[2]), cc: row[2], lat: row[3], lon: row[4], tz: cities.tz[row[5]]}; }
  function nearestCity(lat, lon) {
    var best = null, bd = 1e9;
    cities.c.forEach(function (r) { var d = Math.pow(r[3] - lat, 2) + Math.pow((r[4] - lon) * Math.cos(lat * Math.PI / 180), 2); if (d < bd) { bd = d; best = r; } });
    return best;
  }
  function autoLocate(done) {
    loadCities(function () {
      if (!cities) return done(null);
      getJSON('https://ipwho.is/', function (j) {
        if (j && j.success !== false && typeof j.latitude === 'number') return done(nearestCity(j.latitude, j.longitude));
        getJSON('https://ipapi.co/json/', function (k) { done(k && typeof k.latitude === 'number' ? nearestCity(k.latitude, k.longitude) : null); }, 10000);
      }, 10000);
    });
  }
  function setCity(row) {
    settings.city = cityObject(row);
    ensureData.key = ''; weather = null; save(); ensureData(); loadWeather(true); setWall(currentWall());
  }

  // ---- settings panel -------------------------------------------------------------------------------------
  function onOff(v) { return v ? 'مفعّل' : 'متوقف'; }
  function cycle(list, value, step) { var i = Math.max(0, list.indexOf(value)); return list[(i + step + list.length) % list.length]; }
  function toggle(label, get, set, extra) { return {label: label, value: function () { return onOff(get()); }, step: function () { set(!get()); changed(extra); }}; }
  function choice(label, list, names, get, set, extra) {
    return {label: label, value: function () { return names(get()); }, step: function (s) { set(cycle(list, get(), s)); changed(extra); }};
  }
  function action(label, value, act) { return {label: label, value: typeof value === 'function' ? value : function () { return value; }, act: act}; }
  function info(label, value) { return {label: label, value: typeof value === 'function' ? value : function () { return value; }, info: true}; }
  function minutes(n) { return n ? (n > 0 ? '+' : '−') + ar(Math.abs(n)) + ' د' : 'بدون تعديل'; }
  var testAudio = null;
  function playTest(file) {
    stopTest();
    testAudio = new Audio('audio/' + file); testAudio.volume = Math.max(0.1, settings.appVolume / 100);
    testAudio.onended = function () { testAudio = null; renderItems(); };
    var p = testAudio.play(); if (p && p.catch) p.catch(function () {});
  }
  function stopTest() { if (testAudio) { try { testAudio.pause(); } catch (_) {} testAudio = null; } }
  function sectionItems() {
    var methods = Object.keys(Calc.METHODS).map(Number);
    var voiceFiles = VOICES.map(function (v) { return v.file; });
    return [
      {name: 'المظهر', items: [
        choice('تعتيم الخلفية', [0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9], function (v) { return ar(Math.round(v * 100)) + '٪'; }, function () { return settings.dim; }, function (v) { settings.dim = v; }, 'wall'),
        choice('حجم النصوص', [90, 100, 110], function (v) { return v === 90 ? 'صغير' : v === 100 ? 'عادي' : 'كبير'; }, function () { return settings.textScale; }, function (v) { settings.textScale = v; }),
        toggle('إظهار اسم المصوّر', function () { return settings.showCredit; }, function (v) { settings.showCredit = v; }, 'wall'),
        info('الخط', 'ثمانية (للواجهة) · Amiri Quran (للآيات)')
      ]},
      {name: 'الخلفيات', items: [
        choice('طريقة تغيير الخلفية', ['time', 'cycle', 'fixed', 'none'], function (v) { return {time: 'حسب وقت اليوم والصلاة', cycle: 'كل الخلفيات بالتناوب', fixed: 'خلفية ثابتة', none: 'بدون خلفية'}[v]; }, function () { return settings.wallMode; }, function (v) { settings.wallMode = v; }, 'wall'),
        action('اختيار الخلفية الثابتة', function () { var w = wallById(settings.wallFixed); return w ? w.name : '—'; }, function () { openPicker('wallFixed'); }),
        choice('مدة التبديل', [10, 20, 30, 60, 120], function (v) { return 'كل ' + ar(v) + ' دقيقة'; }, function () { return settings.wallEvery; }, function (v) { settings.wallEvery = v; }, 'wall'),
        info('الفترة الحالية', function () { return PERIODS[periodNow(Date.now())] + ' · ' + ar(wallsFor(periodNow(Date.now())).length) + ' صور'; })
      ]},
      {name: 'المدينة والموقع', items: [
        action('المدينة', function () { return settings.city.name + ' - ' + settings.city.country; }, function () { openCities(); }),
        action('تحديد الموقع تلقائيًا', 'عبر الإنترنت', function () {
          showBanner('جارٍ تحديد الموقع…', 4000);
          autoLocate(function (row) { if (!row) return showBanner('تعذّر تحديد الموقع تلقائيًا، اختر المدينة يدويًا'); setCity(row); renderItems(); showBanner('تم تحديد المدينة: ' + settings.city.name); });
        }),
        info('الإحداثيات', function () { return ar(settings.city.lat.toFixed(3)) + '، ' + ar(settings.city.lon.toFixed(3)); })
      ]},
      {name: 'مواقيت الصلاة', items: [
        choice('مذهب العصر', [1, 2], function (v) { return v === 1 ? 'الجمهور (الشافعي والمالكي والحنبلي)' : 'الحنفي'; }, function () { return settings.asr; }, function (v) { settings.asr = v; }, 'times')
      ].concat(['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'].map(function (k) {
        return choice('تعديل ' + NAMES[k], [-15, -10, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 10, 15], minutes, function () { return settings.offsets[k]; }, function (v) { settings.offsets[k] = v; }, 'times');
      }))},
      {name: 'طريقة الحساب', items: [
        toggle('اختيار تلقائي حسب الدولة', function () { return settings.autoMethod; }, function (v) { settings.autoMethod = v; }, 'times'),
        choice('الطريقة', methods, function (v) { return Calc.METHODS[v].name; }, function () { return settings.autoMethod ? methodFor() : settings.method; }, function (v) { settings.method = v; settings.autoMethod = false; }, 'times'),
        info('المستخدمة الآن', function () { return Calc.METHODS[methodFor()].name; })
      ]},
      {name: 'إعدادات الأذان', items: [
        choice('عند دخول الوقت', ['adhan', 'notify', 'off'], function (v) { return {adhan: 'تشغيل الأذان', notify: 'إشعار فقط', off: 'إيقاف'}[v]; }, function () { return settings.alert; }, function (v) { settings.alert = v; }),
        toggle('شاشة الأذان الكاملة', function () { return settings.fullScreen; }, function (v) { settings.fullScreen = v; })
      ].concat(ORDER.map(function (k) { return toggle('أذان ' + NAMES[k], function () { return settings.perPrayer[k]; }, function (v) { settings.perPrayer[k] = v; }); })).concat([
        toggle('العودة للمحتوى السابق بعد الأذان', function () { return settings.returnPrev; }, function (v) { settings.returnPrev = v; }),
        toggle('استئناف تشغيل الفيديو', function () { return settings.resume; }, function (v) { settings.resume = v; })
      ])},
      {name: 'أصوات المؤذنين', items: [
        choice('صوت الأذان', voiceFiles, voiceName, function () { return settings.voice; }, function (v) { settings.voice = v; stopTest(); }),
        action('استماع', function () { return testAudio ? 'إيقاف' : 'تشغيل'; }, function () { if (testAudio) stopTest(); else playTest(settings.voice); renderItems(); }),
        info('إضافة أصوات', 'ضع ملفات mp3 في مجلد audio ثم أعد التثبيت')
      ]},
      {name: 'أذان الفجر', items: [
        choice('صوت أذان الفجر', ['same'].concat(voiceFiles), function (v) { return v === 'same' ? 'نفس صوت الأذان' : voiceName(v); }, function () { return settings.fajrVoice; }, function (v) { settings.fajrVoice = v; stopTest(); }),
        action('استماع', function () { return testAudio ? 'إيقاف' : 'تشغيل'; }, function () { if (testAudio) stopTest(); else playTest(settings.fajrVoice === 'same' ? settings.voice : settings.fajrVoice); renderItems(); })
      ]},
      {name: 'تنبيهات الصلاة', items: [
        toggle('تنبيه قبل الصلاة', function () { return settings.preEnabled; }, function (v) { settings.preEnabled = v; }),
        choice('قبل الصلاة بـ', [5, 10, 15, 20, 30], function (v) { return ar(v) + ' دقائق'; }, function () { return settings.prealert; }, function (v) { settings.prealert = v; }),
        info('شكل التنبيه', 'شريط صغير أعلى الشاشة فوق أي تطبيق، لا يوقف الفيديو')
      ]},
      {name: 'اختبار الأذان', items: [
        action('اختبار الأذان بعد ٣٠ ثانية', 'ابدأ العد', function () { closePanel(); scheduleTest(30); }),
        action('اختبار فوري هنا', 'تشغيل الآن', function () { closePanel(); startAdhan({id: 'test-' + Date.now(), test: true, name: 'العصر', key: 'Asr', ts: Date.now()}); }),
        action('اختبار تنبيه ما قبل الصلاة', 'بعد ١٥ ثانية', function () {
          closePanel(); showBanner('سيظهر التنبيه بعد ١٥ ثانية فوق أي تطبيق — افتح تطبيقًا الآن', 6000);
          rpc(SERVICE + 'toast', {message: 'اقترب موعد صلاة المغرب — متبقٍ ١٠ دقائق', delay: 15000});
        })
      ]},
      {name: 'القرآن والأحاديث', items: [
        choice('نوع المحتوى', ['mix', 'quran', 'hadith'], function (v) { return {mix: 'القرآن والأحاديث بالتناوب', quran: 'القرآن فقط', hadith: 'الأحاديث فقط'}[v]; }, function () { return settings.contentType; }, function (v) { settings.contentType = v; }, 'content'),
        info('القرآن الكريم', '١١٤ سورة · ٦٢٣٦ آية · الرسم العثماني (Tanzil)'),
        info('الأحاديث', 'الأربعون النووية (٤٢) · الأحاديث القدسية (٤٠)'),
        action('آية أو حديث جديد الآن', 'تغيير', function () { refreshHomeContent(true); })
      ]},
      {name: 'شاشة التوقف', items: [
        choice('تبدأ بعد', [0, 1, 3, 5, 10, 15], function (v) { return v ? ar(v) + ' دقائق دون استخدام' : 'متوقفة'; }, function () { return settings.saver; }, function (v) { settings.saver = v; }),
        choice('خلفياتها', ['time', 'cycle', 'fixed'], function (v) { return {time: 'حسب وقت اليوم', cycle: 'كل الخلفيات', fixed: 'خلفية ثابتة'}[v]; }, function () { return settings.saverWallMode; }, function (v) { settings.saverWallMode = v; }),
        action('اختيار خلفية ثابتة لها', function () { var w = wallById(settings.saverWall); return w ? w.name : '—'; }, function () { openPicker('saverWall'); }),
        action('معاينة شاشة التوقف', 'عرض الآن', function () { closePanel(); startSaver(); idleAt = Date.now(); })
      ]},
      {name: 'التطبيقات المفضلة', items: [
        info('إدارة التطبيقات', 'اضغط OK مطولًا على أي تطبيق'),
        info('الخيارات', 'نقل · نقل إلى البداية · استبدال · إزالة من الرئيسية · معلومات'),
        info('إضافة تطبيق', 'من مربع + في آخر القائمة'),
        info('ملاحظة', 'الإزالة تخفي الاختصار فقط ولا تحذف التطبيق')
      ]},
      {name: 'الطقس', items: [
        toggle('إظهار الطقس', function () { return settings.weather; }, function (v) { settings.weather = v; }, 'weather'),
        choice('وحدة الحرارة', ['c', 'f'], function (v) { return v === 'c' ? 'مئوية' : 'فهرنهايت'; }, function () { return settings.unit; }, function (v) { settings.unit = v; }, 'weather'),
        info('آخر تحديث', function () { return weather ? fmtClock(weather.at) : 'لم يتم بعد'; }),
        action('تحديث الآن', 'تحديث', function () { loadWeather(true); setTimeout(renderItems, 3000); })
      ]},
      {name: 'التاريخ الهجري', items: [
        info('التقويم', 'أم القرى'),
        choice('تصحيح التاريخ', [-2, -1, 0, 1, 2], function (v) { return v ? (v > 0 ? '+' : '−') + ar(Math.abs(v)) + (Math.abs(v) === 1 ? ' يوم' : ' يومان') : 'بدون تصحيح'; }, function () { return settings.hijriOffset; }, function (v) { settings.hijriOffset = v; }, 'times'),
        toggle('إظهار التاريخ الهجري', function () { return settings.showHijri; }, function (v) { settings.showHijri = v; }),
        info('اليوم', function () { var r = todayRow(); return r ? hijriText(r.h) : '—'; })
      ]},
      {name: 'إعدادات الصوت', items: [
        choice('صوت الأذان داخل الواجهة', [40, 60, 80, 100], function (v) { return ar(v) + '٪'; }, function () { return settings.appVolume; }, function (v) { settings.appVolume = v; }),
        choice('رفع صوت التلفاز للأذان', [0, 10, 15, 20, 25, 30, 40], function (v) { return v ? 'إلى ' + ar(v) : 'بدون تغيير'; }, function () { return settings.volume; }, function (v) { settings.volume = v; }),
        info('بعد الأذان', 'يعود صوت التلفاز إلى مستواه السابق')
      ]},
      {name: 'النسخ الاحتياطي والاستعادة', items: [
        action('حفظ نسخة من الإعدادات', function () { var b = read(BACKUP, null); return b ? 'آخر نسخة ' + fmtClock(b.at) : 'لا توجد نسخة'; }, function () {
          var data = {at: Date.now(), settings: settings, layout: read('tvhome.layout', null)};
          var ok = write(BACKUP, data);
          rpc(SERVICE + 'backup', {data: JSON.stringify(data)});
          showBanner(ok ? 'حُفظت نسخة من إعداداتك وترتيب التطبيقات' : 'تعذّر الحفظ'); renderItems(); }),
        action('استعادة النسخة المحفوظة', 'استعادة', function () {
          function apply(b) { if (!b || !b.settings) return showBanner('لا توجد نسخة محفوظة'); settings = merge(DEFAULTS, b.settings); if (b.layout) write('tvhome.layout', b.layout); save(); showBanner('تمت الاستعادة، ستُعاد تهيئة الواجهة'); setTimeout(function () { location.reload(); }, 1500); }
          var local = read(BACKUP, null);
          if (local) return apply(local);
          rpc(SERVICE + 'restore', {}, function (r) { try { apply(r && r.data ? JSON.parse(r.data) : null); } catch (_) { apply(null); } });
        }),
        action('إعادة الإعدادات الافتراضية', 'إعادة', function () { settings = merge(DEFAULTS, {city: settings.city}); save(); ensureData.key = ''; ensureData(); setWall(currentWall()); renderItems(); showBanner('أُعيدت الإعدادات الافتراضية (مع الإبقاء على مدينتك)'); }),
        action('العودة لواجهة LG الأصلية', 'إعدادات زر الرئيسية', function () { closePanel(); if (window.HomeHelper) window.HomeHelper.open(); }),
        info('ما يُحفظ', 'إعدادات الواجهة وترتيب التطبيقات فقط، وليس نسخة كاملة من التلفاز')
      ]},
      {name: 'معلومات المشروع', items: [
        info('الإصدار', APP_VERSION + ' · مبني على Clean Your TV'),
        info('المواقيت', 'حساب فلكي محلي دون إنترنت'),
        info('قاعدة المدن', ar(8099) + ' مدينة · GeoNames (CC BY 4.0)'),
        info('القرآن', 'نص Tanzil · خط Amiri Quran (OFL)'),
        info('الخط', 'ثمانية · للاستخدام الشخصي'),
        info('الخلفيات', 'ويكيميديا كومنز · أسماء المصورين على الشاشة'),
        info('خدمة الأذان', function () { return serviceStatus; }),
        info('تشخيص', function () { return serviceDiag.slice(0, 220); })
      ]}
    ];
  }
  var sections = [], secIndex = 0, itemIndex = 0, pane = 'cat', view = 'main', serviceStatus = '…', serviceDiag = '';
  var catBox, itemBox, titleBox, listState = {rows: [], index: 0, mode: '', filter: '', country: ''}, searchInput;
  var picker = {target: '', items: [], focus: 0, original: '', tiles: []};
  function changed(extra) {
    save();
    if (extra === 'times') { ensureData.key = ''; ensureData(); cardKey = ''; }
    if (extra === 'wall') setWall(currentWall());
    if (extra === 'weather') loadWeather(false);
    if (extra === 'content') refreshHomeContent(true);
    syncService(); renderItems(); render();
  }
  function buildPanel() {
    panel = el('section', 'prayer-panel'); panel.hidden = true;
    var sheet = el('div', 'set-sheet'); panel.appendChild(sheet);
    var top = el('div', 'set-top'); top.appendChild(el('h1', '', 'الإعدادات')); titleBox = el('div', 'set-hint'); top.appendChild(titleBox); sheet.appendChild(top);
    var body = el('div', 'set-body'); sheet.appendChild(body);
    catBox = el('div', 'set-cats'); itemBox = el('div', 'set-items'); body.appendChild(catBox); body.appendChild(itemBox);
    var strip = el('div', 'p-strip'); strip.hidden = true;
    strip.appendChild(el('div', 'p-strip-name')); strip.appendChild(el('div', 'p-strip-hint', 'يمين / يسار للتنقل · OK للتثبيت · رجوع للإلغاء'));
    var track = el('div', 'p-strip-track'); strip.appendChild(track);
    panel.appendChild(strip); panel.strip = strip; panel.track = track; panel.sheet = sheet;
    document.body.appendChild(panel);
    document.addEventListener('keydown', onKey, true);
  }
  function renderCats() {
    catBox.textContent = '';
    sections.forEach(function (s, i) {
      var r = el('div', 'set-cat' + (i === secIndex ? ' sel' : '') + (pane === 'cat' && i === secIndex ? ' focused' : ''), s.name);
      r.onclick = function () { if (!viaPointer()) return; secIndex = i; itemIndex = 0; pane = 'item'; renderAll(); };
      catBox.appendChild(r);
    });
    scrollInto(catBox, catBox.children[secIndex]);
  }
  function renderItems() {
    if (!panel || panel.hidden || view !== 'main') return;
    itemBox.textContent = '';
    var items = sections[secIndex].items;
    items.forEach(function (it, i) {
      var r = el('div', 'set-item' + (it.info ? ' info' : '') + (pane === 'item' && i === itemIndex ? ' focused' : ''));
      r.appendChild(el('span', 'set-label', it.label));
      var v = el('span', 'set-value', it.value()); if (it.step) { v.className += ' cyc'; } r.appendChild(v);
      r.onclick = function () { if (!viaPointer()) return; pane = 'item'; itemIndex = i; activateItem(); };
      itemBox.appendChild(r);
    });
    scrollInto(itemBox, itemBox.children[itemIndex]);
    titleBox.textContent = pane === 'cat' ? '↑ ↓ للتنقل بين الأقسام · OK أو ← للدخول · رجوع للإغلاق' : '↑ ↓ للتنقل · ← → أو OK لتغيير القيمة · رجوع للأقسام';
  }
  function renderAll() { renderCats(); renderItems(); }
  function scrollInto(box, node) {
    if (!node) return; var top = node.offsetTop - box.offsetTop;
    if (top < box.scrollTop) box.scrollTop = top - 8; else if (top + node.offsetHeight > box.scrollTop + box.clientHeight) box.scrollTop = top + node.offsetHeight - box.clientHeight + 8;
  }
  function activateItem() { var it = sections[secIndex].items[itemIndex]; if (!it || it.info) return; if (it.act) it.act(); else if (it.step) it.step(1); }
  function moveItem(step) {
    var items = sections[secIndex].items, i = itemIndex;
    for (var n = 0; n < items.length; n++) { i = (i + step + items.length) % items.length; if (!items[i].info) { itemIndex = i; return; } }
  }

  // wallpaper picker with live preview
  function openPicker(target) {
    picker.target = target; picker.original = settings[target];
    picker.items = WALLS.map(function (w) { return w.id; });
    picker.focus = Math.max(0, picker.items.indexOf(settings[target]));
    view = 'wall'; panel.className = 'prayer-panel peek'; panel.sheet.className = 'set-sheet away';
    panel.strip.hidden = false; panel.track.textContent = ''; picker.tiles = [];
    picker.items.forEach(function (id, i) {
      var t = el('div', 'p-tile'), img = el('div', 'p-tile-img'), w = wallById(id);
      img.style.backgroundImage = 'url(wallpapers/thumbs/' + id + '.jpg)';
      t.appendChild(img); t.appendChild(el('div', 'p-tile-tag', PERIODS[w.p]));
      t.onclick = function () { if (!viaPointer()) return; picker.focus = i; closePickerView(true); };
      panel.track.appendChild(t); picker.tiles.push(t);
    });
    focusPicker(picker.focus, true);
  }
  function focusPicker(i, instant) {
    picker.focus = Math.max(0, Math.min(picker.items.length - 1, i));
    picker.tiles.forEach(function (t, n) { t.className = 'p-tile' + (n === picker.focus ? ' focused' : ''); });
    var off = picker.focus * 380 - (1920 - 360) / 2 + 20; if (off < 0) off = 0;
    panel.track.style.transition = instant ? 'none' : ''; panel.track.style.webkitTransform = panel.track.style.transform = 'translateX(' + -off + 'px)';
    var id = picker.items[picker.focus], w = wallById(id);
    panel.strip.firstChild.textContent = w.name + ' · ' + PERIODS[w.p];
    if (picker.target === 'saverWall') { if (!saverOn) { startSaver(true); saver.className += ' under'; } showSaverWall(id, false); }
    else setWall(id);
  }
  function closePickerView(apply) {
    var target = picker.target;
    settings[target] = apply ? picker.items[picker.focus] : picker.original;
    if (apply && target === 'wallFixed') settings.wallMode = 'fixed';
    if (apply && target === 'saverWall') settings.saverWallMode = 'fixed';
    if (target === 'saverWall') stopSaver();
    save(); setWall(currentWall());
    view = 'main'; panel.className = 'prayer-panel'; panel.sheet.className = 'set-sheet'; panel.strip.hidden = true;
    renderAll();
  }

  // country and city lists (offline database)
  function openCities() {
    view = 'list'; listState = {rows: [], index: 0, mode: 'country', filter: '', country: ''};
    itemBox.textContent = 'جارٍ تحميل قائمة المدن…';
    loadCities(function (db) {
      if (!db) { itemBox.textContent = 'تعذّر تحميل قائمة المدن'; return; }
      buildList();
    });
  }
  function buildList() {
    var rows = [];
    if (listState.mode === 'country') {
      var seen = {};
      cities.c.forEach(function (r) { if (!seen[r[2]]) seen[r[2]] = {cc: r[2], name: countryName(r[2]), n: 0}; seen[r[2]].n++; });
      rows = Object.keys(seen).map(function (k) { return seen[k]; }).sort(function (a, b) { return a.cc === settings.city.cc ? -1 : b.cc === settings.city.cc ? 1 : a.name.localeCompare(b.name, 'ar'); });
      rows = rows.map(function (c) { return {label: c.name, sub: ar(c.n) + ' مدينة', cc: c.cc}; });
    } else {
      cities.c.forEach(function (r) { if ((listState.country && r[2] === listState.country) || (!listState.country && listState.filter)) rows.push({label: r[0] || r[1], sub: listState.country ? (r[0] ? r[1] : '') : countryName(r[2]), row: r}); });
    }
    var f = listState.filter.trim();
    if (f) rows = rows.filter(function (x) { return x.label.indexOf(f) >= 0 || (x.sub && x.sub.toLowerCase().indexOf(f.toLowerCase()) >= 0); });
    listState.rows = rows.slice(0, 400); listState.index = Math.min(listState.index, Math.max(0, listState.rows.length - 1));
    renderList();
  }
  function renderList() {
    itemBox.textContent = '';
    var bar = el('div', 'set-search');
    searchInput = el('input'); searchInput.type = 'text'; searchInput.dir = 'rtl'; searchInput.value = listState.filter;
    searchInput.placeholder = listState.mode === 'country' ? 'ابحث عن دولة أو اكتب اسم مدينة' : 'ابحث عن مدينة';
    searchInput.addEventListener('input', function () {
      listState.filter = searchInput.value; listState.index = 0;
      if (listState.mode === 'country' && listState.filter.length >= 2) {
        var anyCountry = false; cities.c.some(function (r) { if (countryName(r[2]).indexOf(listState.filter) >= 0) { anyCountry = true; return true; } return false; });
        if (!anyCountry) { listState.mode = 'city'; listState.country = ''; }
      }
      buildListKeepInput();
    });
    searchInput.addEventListener('keydown', function (e) {
      if (e.keyCode === 40 || e.keyCode === 13) { e.preventDefault(); e.stopPropagation(); searchInput.blur(); listState.index = 0; markList(); }
      else if (e.keyCode === 461 || e.keyCode === 27) { e.preventDefault(); e.stopPropagation(); searchInput.blur(); listBack(); }
    });
    bar.appendChild(searchInput); itemBox.appendChild(bar);
    itemBox.appendChild(el('div', 'set-list-head', listState.mode === 'country' ? 'اختر الدولة' : listState.country ? 'مدن ' + countryName(listState.country) : 'نتائج البحث'));
    var list = el('div', 'set-list'); list.id = 'setList';
    listState.rows.forEach(function (x, i) {
      var r = el('div', 'set-item'); r.appendChild(el('span', 'set-label', x.label)); r.appendChild(el('span', 'set-value', x.sub || ''));
      r.onclick = function () { if (!viaPointer()) return; listState.index = i; chooseList(); };
      list.appendChild(r);
    });
    if (!listState.rows.length) list.appendChild(el('div', 'set-empty', 'لا توجد نتائج'));
    itemBox.appendChild(list);
    titleBox.textContent = '↑ ↓ للتنقل · ← → للقفز ١٠ · OK للاختيار · ↑ من أول القائمة للبحث · رجوع للخلف';
    markList();
  }
  function buildListKeepInput() { var pos = searchInput.selectionStart; buildList(); searchInput.focus(); try { searchInput.setSelectionRange(pos, pos); } catch (_) {} }
  function markList() {
    var list = byId('setList'); if (!list) return;
    Array.prototype.forEach.call(list.children, function (c, i) { if (c.classList.contains('set-item')) c.classList.toggle('focused', i === listState.index && document.activeElement !== searchInput); });
    scrollInto(list, list.children[listState.index]);
  }
  function chooseList() {
    var x = listState.rows[listState.index]; if (!x) return;
    if (listState.mode === 'country') { listState = {rows: [], index: 0, mode: 'city', filter: '', country: x.cc}; buildList(); return; }
    setCity(x.row); showBanner('المدينة الآن: ' + settings.city.name + ' · ' + settings.city.country);
    view = 'main'; renderAll();
  }
  function listBack() {
    if (listState.mode === 'city' && listState.country) { listState = {rows: [], index: 0, mode: 'country', filter: '', country: ''}; buildList(); return; }
    if (listState.mode === 'city') { listState.mode = 'country'; listState.filter = ''; buildList(); return; }
    view = 'main'; renderAll();
  }
  var NAV = [13, 27, 37, 38, 39, 40, 461];
  // The OK key also produces a click wherever the hidden pointer rests; only real pointer clicks count.
  var okAt = 0;
  function viaPointer() { return Date.now() - okAt > 800; }
  function onKey(e) {
    if (e.keyCode === 13) okAt = Date.now();
    if (!panel || panel.hidden) return;
    var k = e.keyCode;
    if (view === 'list') {
      if (document.activeElement === searchInput) return;
      if (NAV.indexOf(k) < 0) return;
      e.preventDefault(); e.stopImmediatePropagation();
      if (k === 461 || k === 27) return listBack();
      if (k === 13) return chooseList();
      if (k === 38) { if (listState.index === 0) { searchInput.focus(); markList(); return; } listState.index--; }
      else if (k === 40) listState.index = Math.min(listState.rows.length - 1, listState.index + 1);
      else if (k === 37) listState.index = Math.min(listState.rows.length - 1, listState.index + 10);
      else if (k === 39) listState.index = Math.max(0, listState.index - 10);
      return markList();
    }
    if (NAV.indexOf(k) < 0) return;
    e.preventDefault(); e.stopImmediatePropagation();
    if (view === 'wall') {
      if (k === 461 || k === 27) return closePickerView(false);
      if (k === 13) { if (!e.repeat) closePickerView(true); return; }
      return focusPicker(picker.focus + (k === 37 || k === 38 ? -1 : 1));
    }
    if (pane === 'cat') {
      if (k === 461 || k === 27) return closePanel();
      if (k === 38) secIndex = (secIndex + sections.length - 1) % sections.length;
      else if (k === 40) secIndex = (secIndex + 1) % sections.length;
      else if (k === 13 || k === 37) { pane = 'item'; itemIndex = -1; moveItem(1); if (itemIndex < 0) itemIndex = 0; }
      else if (k === 39) return;
      if (pane === 'cat') itemIndex = 0;
      stopTest();
      return renderAll();
    }
    var it = sections[secIndex].items[itemIndex];
    if (k === 461 || k === 27 || (k === 39 && !(it && it.step))) { pane = 'cat'; stopTest(); return renderAll(); }
    if (k === 38) moveItem(-1);
    else if (k === 40) moveItem(1);
    else if (k === 13) { if (!e.repeat) activateItem(); }
    else if (it && it.step) it.step(k === 37 ? 1 : -1);
    renderAll();
  }
  function openPanel() {
    if (!panel) buildPanel();
    sections = sectionItems(); view = 'main'; pane = 'cat'; secIndex = 0; itemIndex = 0;
    panel.className = 'prayer-panel'; panel.sheet.className = 'set-sheet'; panel.strip.hidden = true; panel.hidden = false;
    renderAll();
    rpc(SERVICE + 'status', {probe: true}, function (r) { serviceStatus = r && r.returnValue ? 'تعمل · ' + ar(r.events) + ' موعدًا مجدولًا' : 'غير متاحة'; serviceDiag = r ? JSON.stringify({p: r.probe, d: r.diag}) : 'no reply'; renderItems(); });
  }
  function closePanel() {
    stopTest();
    if (view === 'wall') closePickerView(false);
    view = 'main'; if (panel) panel.hidden = true;
  }

  // ---- start ------------------------------------------------------------------------------------------------
  function init() {
    var firstRun = read(STORE, null) === null;
    settings = loadSettings(); save();
    // First start on a new TV: find the city from the internet once; Makkah until then.
    if (firstRun) setTimeout(function () {
      autoLocate(function (row) { if (row) { setCity(row); showBanner('تم تحديد مدينتك تلقائيًا: ' + settings.city.name + ' · يمكنك تغييرها من الإعدادات', 9000); } });
    }, 2500);
    buildHome();
    ensureData();
    setWall(currentWall(), true);
    render();
    setTimeout(function () {
      loadWeather(false);
      loadLocal('quran/index.json', function (j) { content.index = j; refreshHomeContent(false); });
      loadLocal('hadith.json', function (j) { content.hadith = j; });
    }, 300);
    setInterval(tick, 1000);
    setInterval(function () { loadWeather(false); }, 20 * 60000);
    setInterval(function () { if (!document.hidden && !saverOn) refreshHomeContent(true); }, 10 * 60000);
    document.addEventListener('keydown', function (e) {
      idleAt = Date.now();
      if (adhanEvent) {
        if (PASS_KEYS.indexOf(e.keyCode) >= 0) return;
        e.preventDefault(); e.stopImmediatePropagation();
        finishAdhan();
      } else if (saverOn && (!panel || panel.hidden)) {
        e.preventDefault(); e.stopImmediatePropagation();
        if (e.keyCode !== 403) stopSaver(); // RED is the key Helper presses to cancel LG's screensaver
      }
    }, true);
    document.addEventListener('webOSRelaunch', function (e) { idleAt = Date.now(); if (!panel || panel.hidden) stopSaver(); launchEvent(e && e.detail); });
    // EXIT closes our window: stop the adhan and go back. Coming back to Home shows a fresh verse.
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { if (adhanEvent) finishAdhan(); }
      else { idleAt = Date.now(); ensureData(); render(); if (content.index && !adhanEvent) refreshHomeContent(true); setWall(currentWall()); }
    });
    try { var raw = window.PalmSystem && window.PalmSystem.launchParams; if (raw) launchEvent(raw); } catch (_) {}
    window.PrayerUI = {open: openPanel, startAdhan: startAdhan};
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
}());
