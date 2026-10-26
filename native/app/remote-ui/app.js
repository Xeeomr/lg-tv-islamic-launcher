/* Xee Remote: phone control for Xee Launcher, served by Home Helper on the TV. */
(function () {
  'use strict';
  var TOKEN_KEY = 'xee.remote.token', token = '';
  try { token = localStorage.getItem(TOKEN_KEY) || ''; } catch (e) {}
  var state = null, catalog = null, apps = null, cities = null, quranSeg = 'radio', tab = 'home', pollTimer = 0, failures = 0;
  var NAMES = {Fajr: 'الفجر', Sunrise: 'الشروق', Dhuhr: 'الظهر', Asr: 'العصر', Maghrib: 'المغرب', Isha: 'العشاء'};

  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function ar(n) { return String(n).replace(/\d/g, function (d) { return '٠١٢٣٤٥٦٧٨٩'.charAt(d); }); }
  function clock(ms) { var d = new Date(ms), h = d.getHours(); return ar((h % 12 || 12) + ':' + ('0' + d.getMinutes()).slice(-2)) + ' ' + (h < 12 ? 'ص' : 'م'); }
  function left(ms) { var m = Math.max(0, Math.round(ms / 60000)), h = Math.floor(m / 60); return (h ? ar(h) + ':' + ar(('0' + m % 60).slice(-2)) : ar(m) + ' د'); }
  function toast(t) { var x = $('toast'); x.textContent = t; x.className = 'shown'; clearTimeout(toast.t); toast.t = setTimeout(function () { x.className = ''; }, 2200); }
  function buzz() { try { if (navigator.vibrate) navigator.vibrate(12); } catch (e) {} }

  function call(route, body, cb) {
    var x = new XMLHttpRequest();
    x.open(body ? 'POST' : 'GET', '/api/' + route);
    x.setRequestHeader('Content-Type', 'application/json');
    if (token) x.setRequestHeader('X-Xee-Token', token);
    x.timeout = 10000;
    x.onload = function () {
      var r = null; try { r = JSON.parse(x.responseText); } catch (e) {}
      if (x.status === 401) { setToken(''); showPair(); return; }
      if (cb) cb(r, x.status);
    };
    x.onerror = x.ontimeout = function () { if (cb) cb(null, 0); };
    x.send(body ? JSON.stringify(body) : null);
  }
  function setToken(t) { token = t; try { if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY); } catch (e) {} }
  function home(cmd, msg) { buzz(); call('home', {cmd: cmd}, function (r) { if (r && r.queued) toast('سيُطبَّق عند فتح الواجهة'); else if (msg) toast(msg); setTimeout(poll, 700); }); }
  function setting(key, value) { home({type: 'setting', key: key, value: value}, 'تم الحفظ'); if (state && state.settings) state.settings[key] = value; }

  // ---- pairing -------------------------------------------------------------------------------
  function showPair() { $('app').hidden = true; $('pair').hidden = false; clearInterval(pollTimer); }
  $('pairStart').onclick = function () {
    $('pairError').textContent = '';
    call('pair', {}, function (r, st) {
      if (r && r.returnValue) { $('pairCode').hidden = false; $('pairStart').hidden = true; $('codeInput').focus(); }
      else $('pairError').textContent = st === 429 ? 'انتظر قليلًا ثم حاول مجددًا' : 'تعذّر الاتصال بالتلفاز';
    });
  };
  $('pairConfirm').onclick = function () {
    call('pair/confirm', {code: $('codeInput').value.replace(/[٠-٩]/g, function (d) { return '٠١٢٣٤٥٦٧٨٩'.indexOf(d); }), name: navigator.platform || 'هاتف'}, function (r) {
      if (r && r.token) { setToken(r.token); start(); }
      else $('pairError').textContent = r && r.errorText === 'expired' ? 'انتهت صلاحية الرمز، اطلب رمزًا جديدًا' : 'الرمز غير صحيح';
      if (r && (r.errorText === 'expired' || r.errorText === 'too-many')) { $('pairCode').hidden = true; $('pairStart').hidden = false; }
    });
  };

  // ---- status --------------------------------------------------------------------------------
  function poll() {
    call('status', null, function (r) {
      if (!r || !r.returnValue) { if (++failures > 1) $('conn').className = 'conn off', $('conn').textContent = 'غير متصل'; return; }
      failures = 0; $('conn').className = 'conn'; $('conn').textContent = 'متصل';
      state = r.home || null; state = state || {}; state.tv = r.tv; state.update = r.update;
      renderHome();
      if (tab === 'quran') renderQuranState();
      if (tab === 'settings' && !renderSettings.done) renderSettings();
    });
  }
  function renderHome() {
    var s = state || {};
    $('cityLine').textContent = s.city ? s.city.name + (s.city.country ? '، ' + s.city.country : '') : 'افتح الواجهة على التلفاز مرة واحدة';
    $('hijriLine').textContent = s.hijri || '';
    if (s.next) { $('nextLine').textContent = 'صلاة ' + s.next.name + ' ' + clock(s.next.ts); $('countdown').textContent = left(s.next.ts - Date.now()); }
    var row = $('timesRow'); row.textContent = '';
    (s.today || []).forEach(function (t) {
      var d = el('div', s.next && s.next.name === t.name ? 'on' : '', t.name); d.appendChild(el('b', '', clock(t.ts).replace(/ [صم]$/, ''))); row.appendChild(d);
    });
    var v = s.tv && s.tv.volume; $('volValue').textContent = v === null || v === undefined ? '—' : ar(v) + (s.tv.muted ? ' · مكتوم' : '');
    var rd = s.radio || {};
    $('nowCard').hidden = !rd.nowPlaying;
    $('nowTitle').textContent = rd.nowPlaying || '';
    var m = rd.kind === 'mushaf';
    $('btnPrev').hidden = $('btnNext').hidden = !m; $('btnPause').hidden = !m;
    $('btnPause').textContent = rd.paused ? '▶︎' : '❚❚';
  }

  // ---- remote --------------------------------------------------------------------------------
  function bindAll(sel, fn) { Array.prototype.forEach.call(document.querySelectorAll(sel), function (b) { b.addEventListener('click', function () { fn(b); }); }); }
  bindAll('[data-key]', function (b) { buzz(); call('key', {key: b.getAttribute('data-key')}); });
  bindAll('[data-vol]', function (b) { buzz(); call('volume', {action: b.getAttribute('data-vol')}, function () { setTimeout(poll, 300); }); });
  $('muteBtn').onclick = function () { buzz(); call('volume', {action: 'mute', value: !(state && state.tv && state.tv.muted)}, function () { setTimeout(poll, 300); }); };
  bindAll('[data-power]', function (b) {
    var a = b.getAttribute('data-power');
    if (a === 'off' && !confirm('إطفاء التلفاز الآن؟')) return;
    buzz(); call('power', {action: a}, function () { toast(a === 'off' ? 'تم إطفاء التلفاز' : a === 'screenOff' ? 'أُطفئت الشاشة والصوت مستمر' : 'تم تشغيل الشاشة'); });

  });
  bindAll('[data-home]', function (b) { home({type: b.getAttribute('data-home')}); });
  function sendText(enter) { var v = $('typeInput').value; if (!v) return; call('text', {text: v, enter: enter}, function (r) { toast(r && r.returnValue !== false ? 'أُرسل النص' : 'افتح خانة الكتابة على التلفاز أولًا'); }); $('typeInput').value = ''; }
  $('typeSend').onclick = function () { sendText(true); };
  $('typeInput').addEventListener('keydown', function (e) { if (e.key === 'Enter') sendText(true); });

  // ---- tabs ----------------------------------------------------------------------------------
  bindAll('.tabs button', function (b) {
    tab = b.getAttribute('data-tab');
    Array.prototype.forEach.call(document.querySelectorAll('.tabs button'), function (x) { x.className = x === b ? 'sel' : ''; });
    ['home', 'quran', 'apps', 'settings'].forEach(function (t) { $('tab-' + t).hidden = t !== tab; });
    if (tab === 'quran') renderQuran();
    if (tab === 'apps') renderApps();
    if (tab === 'settings') renderSettings();
    window.scrollTo(0, 0);
  });

  // ---- Quran ---------------------------------------------------------------------------------
  function loadCatalog(cb) {
    if (catalog && catalog.quran) return cb();
    call('catalog', null, function (r) { if (r && r.quran) catalog = r; cb(); });
  }
  bindAll('#quranSeg button', function (b) {
    quranSeg = b.getAttribute('data-seg');
    Array.prototype.forEach.call(document.querySelectorAll('#quranSeg button'), function (x) { x.className = x === b ? 'sel' : ''; });
    ['radio', 'mushaf', 'live'].forEach(function (s) { $('seg-' + s).hidden = s !== quranSeg; });
  });
  function item(title, sub, on, fn) {
    var d = el('div', 'item' + (on ? ' on' : '')), t = el('div'); t.appendChild(el('div', 't', title)); t.appendChild(el('div', 's', sub));
    d.appendChild(t); d.appendChild(el('div', 'go', '▶︎')); d.onclick = fn; return d;
  }
  function renderQuran() {
    loadCatalog(function () {
      if (!catalog || !catalog.quran) { $('seg-radio').textContent = 'افتح Xee Launcher على التلفاز مرة واحدة لتظهر القائمة.'; return; }
      var q = catalog.quran;
      var chips = $('sleepChips'); chips.textContent = '';
      q.sleep.forEach(function (m) { var c = el('button', 'chip', m ? ar(m) + ' د' : 'بدون'); c.setAttribute('data-m', m); c.onclick = function () { home({type: 'radio.sleep', minutes: m}, m ? 'سيتوقف بعد ' + ar(m) + ' دقيقة' : 'أُلغي المؤقت'); }; chips.appendChild(c); });
      $('powerOffToggle').onchange = function () { home({type: 'radio.powerOff', value: this.checked}); };
      var sel = $('reciterSelect'); if (!sel.options.length) q.reciters.forEach(function (r) { var o = el('option', '', r.name); o.value = r.id; sel.appendChild(o); });
      sel.onchange = function () { home({type: 'mushaf.reciter', id: sel.value}, 'تم تغيير القارئ'); };
      $('continueKhatma').onclick = function () { home({type: 'mushaf.continue', reciter: sel.value, quiet: !$('showAyat').checked}, 'متابعة الختمة'); };
      renderQuranState();
      renderSurahs();
      var live = $('seg-live'); live.textContent = '';
      q.live.forEach(function (l) { var c = el('button', 'live-card'); c.appendChild(el('b', '', l.name)); c.appendChild(el('span', '', l.sub)); c.onclick = function () { home({type: 'live.open', id: l.id}, 'جارٍ فتح البث على التلفاز'); }; live.appendChild(c); });
    });
  }
  function renderQuranState() {
    if (!catalog || !catalog.quran) return;
    var rd = state && state.radio || {}, list = $('seg-radio');
    list.textContent = '';
    catalog.quran.stations.forEach(function (s) { list.appendChild(item(s.name, s.sub, rd.station === s.id, function () { home({type: 'radio.play', id: s.id}, 'يعمل الآن على التلفاز'); })); });
    Array.prototype.forEach.call(document.querySelectorAll('#sleepChips .chip'), function (c) { c.className = 'chip' + (+c.getAttribute('data-m') === (rd.sleep || 0) ? ' sel' : ''); });
    $('powerOffToggle').checked = !!rd.powerOff;
    if (rd.reciter) $('reciterSelect').value = rd.reciter;
    if (rd.khatma) $('continueKhatma').textContent = 'متابعة الختمة · سورة ' + (catalog.quran.surahs[rd.khatma.s - 1] || [''])[0] + ' · الآية ' + ar(rd.khatma.a) + ' (' + ar(rd.khatmaPercent || 0) + '٪)';
  }
  function renderSurahs() {
    var box = $('surahList'), q = ($('surahSearch').value || '').trim(), rd = state && state.radio || {};
    box.textContent = '';
    catalog.quran.surahs.forEach(function (x, i) {
      if (q && x[0].indexOf(q) < 0 && String(i + 1) !== q) return;
      box.appendChild(item(ar(i + 1) + ' · سورة ' + x[0], ar(x[1]) + ' آية', rd.surah === i + 1, function () { home({type: 'mushaf.play', s: i + 1, a: 1, reciter: $('reciterSelect').value, quiet: !$('showAyat').checked}, 'سورة ' + x[0]); }));
    });
  }
  $('surahSearch').addEventListener('input', function () { if (catalog) renderSurahs(); });

  // ---- apps ----------------------------------------------------------------------------------
  function renderApps() {
    if (apps) return;
    call('apps', null, function (r) {
      apps = r && r.apps || [];
      var g = $('appsGrid'); g.textContent = '';
      apps.forEach(function (a) {
        var b = el('button', 'app'), img = el('img');
        img.src = '/api/icon?id=' + encodeURIComponent(a.id) + '&t=' + token; img.alt = '';
        img.onerror = function () { img.style.visibility = 'hidden'; };
        b.appendChild(img); b.appendChild(el('span', '', a.title));
        b.onclick = function () { buzz(); call('launch', {id: a.id}, function () { toast('جارٍ فتح ' + a.title); }); };
        g.appendChild(b);
      });
    });
  }

  // ---- settings ------------------------------------------------------------------------------
  function group(title) { var g = el('div', 'set-group'); g.appendChild(el('h3', '', title)); $('settingsBox').appendChild(g); return g; }
  function row(g, label, control) { var r = el('div', 'set-row'); r.appendChild(el('span', '', label)); if (control) r.appendChild(control); g.appendChild(r); return r; }
  function check(g, label, key) {
    var c = el('input'); c.type = 'checkbox'; c.checked = !!state.settings[key];
    c.onchange = function () { setting(key, c.checked); }; return row(g, label, c);
  }
  function pick(g, label, key, options, isNumber) {
    var sel = el('select');
    options.forEach(function (o) { var op = el('option', '', o[1]); op.value = o[0]; sel.appendChild(op); });
    sel.value = String(state.settings[key]);
    sel.onchange = function () { setting(key, isNumber ? +sel.value : sel.value); }; return row(g, label, sel);
  }
  function button(g, label, text, fn) { var b = el('button', '', text); b.onclick = fn; return row(g, label, b); }
  function renderSettings() {
    var box = $('settingsBox');
    if (!state || !state.settings) { box.textContent = 'افتح Xee Launcher على التلفاز مرة واحدة لتظهر الإعدادات.'; return; }
    loadCatalog(function () {
      renderSettings.done = true; box.textContent = '';
      var s = state.settings, g;
      g = group('المدينة');
      var input = el('input', 'search'); input.placeholder = 'ابحث عن مدينتك…'; g.appendChild(input);
      var results = el('div', 'list city-results'); g.appendChild(results);
      row(g, 'الحالية', el('span', 'muted', state.city ? state.city.name : '—'));
      input.addEventListener('input', function () {
        var q = input.value.trim(); results.textContent = '';
        if (q.length < 2) return;
        loadCities(function () {
          var n = 0;
          cities.c.some(function (c) {
            if (c[0].indexOf(q) < 0 && String(c[1]).toLowerCase().indexOf(q.toLowerCase()) < 0) return false;
            results.appendChild(item(c[0] || c[1], c[1] + ' · ' + c[2], false, function () { home({type: 'city', row: c}, 'تم تغيير المدينة'); results.textContent = ''; input.value = ''; }));
            return ++n >= 12;
          });
        });
      });
      g = group('الأذان');
      pick(g, 'عند دخول الوقت', 'alert', [['adhan', 'أذان كامل'], ['notify', 'تنبيه فقط'], ['off', 'متوقف']]);
      var voices = (catalog && catalog.voices || []).map(function (v) { return [v.file, v.name]; });
      if (voices.length) pick(g, 'صوت المؤذن', 'voice', voices);
      if (voices.length) pick(g, 'أذان الفجر', 'fajrVoice', [['same', 'نفس الصوت']].concat(voices));
      pick(g, 'رفع صوت التلفاز للأذان', 'volume', [[0, 'بدون تغيير'], [10, '١٠'], [15, '١٥'], [20, '٢٠'], [25, '٢٥'], [30, '٣٠'], [40, '٤٠']], true);
      pick(g, 'تنبيه قبل الصلاة', 'prealert', [[5, '٥ دقائق'], [10, '١٠ دقائق'], [15, '١٥ دقيقة'], [20, '٢٠ دقيقة'], [30, '٣٠ دقيقة']], true);
      ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'].forEach(function (k) {
        var c = el('input'); c.type = 'checkbox'; c.checked = !!(s.perPrayer && s.perPrayer[k]);
        c.onchange = function () { var v = {}; v[k] = c.checked; setting('perPrayer', v); };
        row(g, 'أذان ' + NAMES[k], c);
      });
      button(g, 'تجربة الأذان على التلفاز', 'تشغيل', function () { home({type: 'adhan.test'}, 'بدأ الأذان على التلفاز'); });
      if (catalog && catalog.methods) pick(g, 'طريقة الحساب', 'method', catalog.methods.map(function (m) { return [m.id, m.name]; }), true);
      check(g, 'اختيار الطريقة تلقائيًا حسب الدولة', 'autoMethod');
      g = group('الأذكار والتذكيرات');
      pick(g, 'أذكار الصباح والمساء', 'athkar', [['auto', 'تلقائيًا في وقتها'], ['remind', 'تذكير فقط'], ['off', 'متوقفة']]);
      pick(g, 'أذكار الصباح بعد الفجر', 'morningAfter', [[10, '١٠ دقائق'], [20, '٢٠ دقيقة'], [30, '٣٠ دقيقة'], [45, '٤٥ دقيقة'], [60, 'ساعة']], true);
      pick(g, 'أذكار المساء بعد العصر', 'eveningAfter', [[0, 'مع الأذان'], [15, '١٥ دقيقة'], [30, '٣٠ دقيقة'], [45, '٤٥ دقيقة'], [60, 'ساعة']], true);
      check(g, 'تذكير الجمعة وسورة الكهف', 'friday');
      check(g, 'صيام عرفة وعاشوراء والأيام البيض', 'fasting');
      check(g, 'صيام الاثنين والخميس', 'monThu');
      g = group('الشاشة');
      check(g, 'وضع الليل بعد العشاء', 'nightMode');
      pick(g, 'الخلفيات', 'wallMode', [['time', 'حسب وقت اليوم'], ['cycle', 'كل الخلفيات'], ['fixed', 'خلفية ثابتة'], ['none', 'بدون']]);
      pick(g, 'تعتيم الخلفية', 'dim', [[0.5, '٥٠٪'], [0.6, '٦٠٪'], [0.7, '٧٠٪'], [0.75, '٧٥٪'], [0.8, '٨٠٪'], [0.85, '٨٥٪'], [0.9, '٩٠٪']], true);
      pick(g, 'شاشة التوقف', 'saver', [[0, 'متوقفة'], [1, 'بعد دقيقة'], [3, 'بعد ٣ دقائق'], [5, 'بعد ٥ دقائق'], [10, 'بعد ١٠ دقائق'], [15, 'بعد ١٥ دقيقة']], true);
      pick(g, 'المحتوى', 'contentType', [['mix', 'القرآن والأحاديث'], ['quran', 'القرآن فقط'], ['hadith', 'الأحاديث فقط']]);
      check(g, 'إظهار الطقس', 'weather');
      g = group('التحديثات');
      var u = state.update || {};
      row(g, 'الإصدار', el('span', 'muted', state.version || '—'));
      row(g, 'الحالة', el('span', 'muted', u.available ? 'يتوفر ' + u.latest : u.checkedAt ? 'لديك أحدث إصدار' : 'لم يتم الفحص'));
      check(g, 'التحديث التلقائي', 'autoUpdate');
      button(g, 'البحث عن تحديث', 'تحقق', function () { call('update', {action: 'check'}, function () { toast('جارٍ البحث…'); setTimeout(function () { renderSettings.done = false; poll(); }, 6000); }); });
      if (u.available) button(g, 'تثبيت ' + u.latest, 'ثبّت الآن', function () { call('update', {action: 'install'}, function () { toast('بدأ التحديث على التلفاز'); }); });
      g = group('هذا الموبايل');
      button(g, 'فتح الإعدادات على التلفاز', 'فتح', function () { home({type: 'open.settings'}); });
      button(g, 'إلغاء ربط هذا الموبايل', 'إلغاء', function () { if (!confirm('إلغاء ربط هذا الموبايل؟')) return; call('unpair', {}, function () { setToken(''); showPair(); }); });
    });
  }
  function loadCities(cb) {
    if (cities) return cb();
    var x = new XMLHttpRequest(); x.open('GET', '/cities.json');
    x.onload = function () { try { cities = JSON.parse(x.responseText); cb(); } catch (e) {} };
    x.send();
  }

  function start() {
    $('pair').hidden = true; $('app').hidden = false;
    poll(); clearInterval(pollTimer);
    pollTimer = setInterval(function () { if (!document.hidden) poll(); }, 4000);
    setInterval(function () { if (state && state.next) $('countdown').textContent = left(state.next.ts - Date.now()); }, 15000);
  }
  document.addEventListener('visibilitychange', function () { if (!document.hidden && token) poll(); });
  if (token) start(); else showPair();
}());
