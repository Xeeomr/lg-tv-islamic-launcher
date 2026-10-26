/* Quran hub: live Quran radio stations, an audio mushaf read ayah by ayah with khatma tracking, and the
   live broadcasts from Makkah and Madinah. Shared sleep timer, screen-off listening and a pause for the adhan.
   Sources: Radio Quran Cairo and Saudi Quran (radiojar), mp3quran.net radios, everyayah.com recitations,
   and the Saudi broadcasting authority's Quran and Sunnah channels. */
(function () {
  'use strict';
  var STORE = 'tvhome.radio.v1', SERVICE = 'luna://com.gathin.tvhome.prayer/';
  var Q = 'https://qurango.net/radio/', QB = 'https://backup.qurango.net/radio/', AYAH = 'https://everyayah.com/data/';
  function mp3quran(id, name, sub) { return {id: id, name: name, sub: sub, urls: [Q + id, QB + id]}; }
  var STATIONS = [
    {id: 'cairo', name: 'إذاعة القرآن الكريم من القاهرة', sub: 'بث مباشر', urls: ['https://stream.radiojar.com/8s5u5tpdtwzuv']},
    {id: 'saudi', name: 'إذاعة القرآن الكريم السعودية', sub: 'بث مباشر', urls: ['https://stream.radiojar.com/0tpy1h0kxtzuv']},
    mp3quran('mahmoud_khalil_alhussary', 'محمود خليل الحصري', 'مرتل'),
    mp3quran('mahmoud_khalil_alhussary_mojawwad', 'محمود خليل الحصري', 'مجود'),
    mp3quran('abdulbasit_abdulsamad', 'عبد الباسط عبد الصمد', 'مرتل'),
    mp3quran('abdulbasit_abdulsamad_mojawwad', 'عبد الباسط عبد الصمد', 'مجود'),
    mp3quran('mohammed_siddiq_alminshawi', 'محمد صديق المنشاوي', 'مرتل'),
    mp3quran('mohammed_siddiq_alminshawi_mojawwad', 'محمد صديق المنشاوي', 'مجود'),
    mp3quran('mustafa_ismail', 'مصطفى إسماعيل', 'مرتل'),
    mp3quran('mohammad_altablaway', 'محمد محمود الطبلاوي', 'مرتل'),
    mp3quran('mishary_alafasi', 'مشاري العفاسي', 'مرتل'),
    mp3quran('maher', 'ماهر المعيقلي', 'مرتل'),
    mp3quran('abdulrahman_alsudaes', 'عبد الرحمن السديس', 'مرتل'),
    mp3quran('saud_alshuraim', 'سعود الشريم', 'مرتل'),
    mp3quran('tarateel', 'تراتيل قصيرة متميزة', 'متعدد القراء'),
    mp3quran('tafseer', 'تفسير القرآن الكريم', 'تفسير'),
    mp3quran('mukhtasartafsir', 'المختصر في تفسير القرآن', 'تفسير'),
    mp3quran('roqiah', 'الرقية الشرعية', 'رقية'),
    mp3quran('athkar_sabah', 'أذكار الصباح', 'أذكار'),
    mp3quran('athkar_masa', 'أذكار المساء', 'أذكار')
  ];
  var RECITERS = [
    {id: 'Alafasy_128kbps', name: 'مشاري العفاسي'},
    {id: 'Husary_128kbps', name: 'محمود خليل الحصري'},
    {id: 'Husary_128kbps_Mujawwad', name: 'الحصري · مجود'},
    {id: 'Abdul_Basit_Murattal_64kbps', name: 'عبد الباسط عبد الصمد'},
    {id: 'Abdul_Basit_Mujawwad_128kbps', name: 'عبد الباسط · مجود'},
    {id: 'Minshawy_Murattal_128kbps', name: 'محمد صديق المنشاوي'},
    {id: 'Minshawy_Mujawwad_192kbps', name: 'المنشاوي · مجود'},
    {id: 'Mustafa_Ismail_48kbps', name: 'مصطفى إسماعيل'},
    {id: 'Mohammad_al_Tablaway_128kbps', name: 'محمد محمود الطبلاوي'},
    {id: 'MaherAlMuaiqly128kbps', name: 'ماهر المعيقلي'},
    {id: 'Abdurrahmaan_As-Sudais_192kbps', name: 'عبد الرحمن السديس'},
    {id: 'Saood_ash-Shuraym_128kbps', name: 'سعود الشريم'},
    {id: 'Yasser_Ad-Dussary_128kbps', name: 'ياسر الدوسري'},
    {id: 'Nasser_Alqatami_128kbps', name: 'ناصر القطامي'}
  ];
  var LIVE = [
    {id: 'makkah', name: 'المسجد الحرام', sub: 'مكة المكرمة · بث مباشر', wall: 'kaaba', url: 'https://win.holol.com/live/quran/playlist.m3u8'},
    {id: 'madinah', name: 'المسجد النبوي', sub: 'المدينة المنورة · بث مباشر', wall: 'madinah-haram', url: 'https://win.holol.com/live/sunnah/playlist.m3u8'}
  ];
  var TABS = [{id: 'radio', name: 'الإذاعات'}, {id: 'mushaf', name: 'المصحف المسموع'}, {id: 'live', name: 'البث المباشر'}];
  var BASMALA = 'بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ';
  var SLEEP = [0, 15, 30, 60, 90, 120, 180, 240];
  var state = {station: 'cairo', sleep: 0, powerOff: false, aliveAt: 0, source: null, reciter: 'Alafasy_128kbps', khatma: {s: 1, a: 1}, tab: 'radio'};
  var index = null, totals = [0], surahCache = {};

  // Playing source: {kind:'radio', id} or {kind:'mushaf', s, a, basmala}
  var source = null, pausedForAdhan = false, sleepAt = 0, sleepTimer = 0;
  var audio = null, heardAt = 0, urlIndex = 0, retry = 0, retryTimer = 0, preload = null;

  function ar(n) { return String(n).replace(/\d/g, function (d) { return '٠١٢٣٤٥٦٧٨٩'.charAt(d); }); }
  function pad3(n) { return ('00' + n).slice(-3); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function load() { try { var s = JSON.parse(localStorage.getItem(STORE)); if (s) Object.keys(state).forEach(function (k) { if (s[k] !== undefined) state[k] = s[k]; }); } catch (_) {} }
  function save() { try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (_) {} }
  function station(id) { return STATIONS.filter(function (s) { return s.id === id; })[0] || STATIONS[0]; }
  function reciter(id) { return RECITERS.filter(function (r) { return r.id === id; })[0] || RECITERS[0]; }
  function live(id) { return LIVE.filter(function (l) { return l.id === id; })[0] || LIVE[0]; }
  function rpc(method, payload) {
    try { var b = new PalmServiceBridge(); b.onservicecallback = function () {}; b.call(SERVICE + method, JSON.stringify(payload || {})); } catch (_) {}
  }
  function getJSON(path, done) {
    var xhr = new XMLHttpRequest(); xhr.open('GET', path);
    xhr.onload = function () { try { done(JSON.parse(xhr.responseText)); } catch (_) { done(null); } };
    xhr.onerror = function () { done(null); }; xhr.send();
  }
  function loadIndex(done) {
    if (index) return done && done();
    getJSON('quran/index.json', function (j) {
      if (j) { index = j; totals = [0]; j.forEach(function (x, i) { totals.push(totals[i] + x[1]); }); }
      if (done) done();
    });
  }
  function surahText(s, done) {
    if (surahCache[s]) return done(surahCache[s]);
    getJSON('quran/' + pad3(s) + '.json', function (j) { if (j) surahCache[s] = j; done(j); });
  }
  // Tanzil keeps the basmala inside the first ayah; the text itself is never changed, only shown without it.
  function ayahText(t, s) {
    t = t.replace(/﻿/g, '');
    if (s === 1 || s === 9) return t;
    var w = t.split(' '), base = w.slice(0, 4).join('').replace(/ٱ/g, 'ا').replace(/[^ء-ي]/g, '');
    return w.length > 4 && base === 'بسماللهالرحمنالرحيم' ? w.slice(4).join(' ') : t;
  }
  function surahName(s) { return index ? index[s - 1][0] : 'سورة ' + ar(s); }
  function percent(s, a) { return index ? Math.floor((totals[s - 1] + a - 1) / totals[114] * 100) : 0; }

  // ---- audio engine --------------------------------------------------------------------------------
  function ensureAudio() {
    if (audio) return;
    audio = new Audio(); audio.preload = 'none';
    audio.addEventListener('playing', function () { retry = 0; render(); showAyah(); });
    audio.addEventListener('pause', function () { render(); });
    audio.addEventListener('timeupdate', function () { heardAt = Date.now(); });
    audio.addEventListener('ended', function () { if (!source || pausedForAdhan) return; if (source.kind === 'mushaf') advance(); else reconnect(); });
    audio.addEventListener('error', function () { if (source && !pausedForAdhan) reconnect(); });
  }
  function urlFor(src) {
    if (src.kind === 'radio') { var st = station(src.id); return st.urls[urlIndex % st.urls.length]; }
    return AYAH + state.reciter + '/' + (src.basmala ? '001001' : pad3(src.s) + pad3(src.a)) + '.mp3';
  }
  function connect() {
    ensureAudio(); clearTimeout(retryTimer); retryTimer = 0;
    heardAt = Date.now();
    var url = urlFor(source);
    if (audio.src !== url) audio.src = url;
    var p = audio.play(); if (p && p.catch) p.catch(function () { if (source && !pausedForAdhan) reconnect(); });
    if (source.kind === 'mushaf') { prepareNext(); showAyah(); }
    render();
  }
  // Night listening must survive dropped connections: retry with backoff, alternating to the backup address.
  function reconnect() {
    clearTimeout(retryTimer);
    retry++; urlIndex++;
    render();
    retryTimer = setTimeout(function () {
      retryTimer = 0;
      if (!source || pausedForAdhan) return;
      if (source.kind === 'mushaf' && retry > 4) { retry = 0; advance(); } else connect();
    }, Math.min(30000, 2000 * retry));
  }
  setInterval(function () {
    // A live stream can hang without an error; reconnect when nothing advanced for 25 seconds.
    if (source && source.kind === 'radio' && !pausedForAdhan && !retryTimer && Date.now() - heardAt > 25000) reconnect();
  }, 10000);
  function nextOf(src) {
    if (src.basmala) return {kind: 'mushaf', s: src.s, a: src.a};
    var count = index ? index[src.s - 1][1] : 0;
    if (src.a < count) return {kind: 'mushaf', s: src.s, a: src.a + 1};
    if (src.s < 114) return {kind: 'mushaf', s: src.s + 1, a: 1, basmala: src.s + 1 !== 9};
    return null;
  }
  // Fetch the next ayah while this one plays so recitation flows without gaps.
  function prepareNext() {
    var n = nextOf(source);
    if (!n) return;
    if (!preload) { preload = new Audio(); preload.preload = 'auto'; preload.muted = true; }
    var url = urlFor(n);
    if (preload.src !== url) { preload.src = url; try { preload.load(); } catch (_) {} }
    surahText(n.s, function () {});
  }
  function advance() {
    var n = nextOf(source);
    if (!n) { stop(); return; }
    source = n; retry = 0;
    if (!n.basmala) state.khatma = {s: n.s, a: n.a};
    state.source = source; save();
    connect();
  }
  function startSource(src) {
    closeLive();
    source = src; urlIndex = 0; retry = 0; pausedForAdhan = false;
    state.source = src; state.aliveAt = Date.now(); save();
    connect();
    if (!sleepAt) setSleep(state.sleep, true);
  }
  function play(id) { state.station = station(id).id; startSource({kind: 'radio', id: state.station}); }
  function playMushaf(s, a, rec, quiet) {
    if (rec) state.reciter = reciter(rec).id;
    loadIndex(function () {
      s = Math.max(1, Math.min(114, s || state.khatma.s)); a = Math.max(1, a || 1);
      if (index && a > index[s - 1][1]) a = 1;
      state.khatma = {s: s, a: a};
      startSource({kind: 'mushaf', s: s, a: a, basmala: a === 1 && s !== 1 && s !== 9});
      if (!quiet) openView();
    });
  }
  function stop() {
    source = null; pausedForAdhan = false; clearTimeout(retryTimer); retryTimer = 0;
    state.aliveAt = 0; state.source = null; save();
    if (audio) { audio.pause(); audio.removeAttribute('src'); try { audio.load(); } catch (_) {} }
    if (preload) preload.removeAttribute('src');
    if (!liveOn) { clearTimeout(sleepTimer); sleepAt = 0; }
    hideView();
    render();
  }
  function togglePause() {
    if (liveOn && video) { if (video.paused) video.play(); else video.pause(); return; }
    if (!source || !audio) return;
    if (audio.paused) { var p = audio.play(); if (p && p.catch) p.catch(function () {}); } else audio.pause();
    render(); showAyah();
  }
  function setSleep(minutes, quiet) {
    state.sleep = minutes; save();
    clearTimeout(sleepTimer); sleepAt = 0;
    if (minutes && (source || liveOn)) {
      sleepAt = Date.now() + minutes * 60000;
      sleepTimer = setTimeout(function () {
        var off = state.powerOff;
        stop(); closeLive();
        if (off) rpc('power', {action: 'off'});
      }, minutes * 60000);
    }
    if (!quiet) render();
  }

  // ---- adhan hooks (called by the prayer module) -------------------------------------------------
  function pauseForAdhan() {
    if (source && audio && !audio.paused) { pausedForAdhan = true; audio.pause(); }
    if (liveOn && video && !video.paused) { pausedForAdhan = true; video.pause(); }
  }
  function resumeAfterAdhan() {
    if (!pausedForAdhan) return;
    pausedForAdhan = false;
    if (source) connect();
    if (liveOn && video) { var p = video.play(); if (p && p.catch) p.catch(function () {}); }
  }

  // ---- mushaf view ---------------------------------------------------------------------------------
  var view;
  function openView() {
    if (!view) {
      view = el('section'); view.id = 'mushafView'; view.hidden = true;
      view.innerHTML = '<div class="mv-shade"></div><div class="mv-top"><div class="mv-surah" id="mvSurah"></div><div class="mv-meta" id="mvMeta"></div></div>' +
        '<div class="mv-ayah" id="mvAyah"></div><div class="mv-next" id="mvNext"></div>' +
        '<div class="mv-foot"><div class="mv-bar"><div class="mv-fill" id="mvFill"></div></div><div class="mv-hint">OK إيقاف مؤقت أو متابعة · ◀ الآية التالية · ▶ السابقة · رجوع للخروج والتلاوة مستمرة</div></div>';
      document.body.appendChild(view);
    }
    close();
    view.hidden = false; document.body.classList.add('quran-view');
    showAyah();
  }
  function hideView() { if (view) view.hidden = true; if (!liveOn) document.body.classList.remove('quran-view'); }
  function viewOpen() { return !!view && !view.hidden; }
  function showAyah() {
    if (!viewOpen() || !source || source.kind !== 'mushaf') return;
    var src = source;
    surahText(src.s, function (j) {
      if (source !== src || !j) return;
      var t = src.basmala ? BASMALA : ayahText(j.a[src.a - 1] || '', src.s);
      var box = document.getElementById('mvAyah');
      box.textContent = t + (src.basmala ? '' : ' ﴿' + ar(src.a) + '﴾');
      box.className = 'mv-ayah' + (t.length > 420 ? ' f4' : t.length > 260 ? ' f3' : t.length > 140 ? ' f2' : '');
      var n = nextOf(src);
      document.getElementById('mvNext').textContent = n && n.s === src.s && !n.basmala && !src.basmala ? ayahText(j.a[n.a - 1] || '', n.s) : '';
      document.getElementById('mvSurah').textContent = 'سورة ' + surahName(src.s);
      document.getElementById('mvMeta').textContent = reciter(state.reciter).name + ' · الآية ' + ar(src.a) + ' من ' + ar(index ? index[src.s - 1][1] : 0) +
        (audio && audio.paused ? ' · متوقف مؤقتًا' : '') + ' · الختمة ' + ar(percent(src.s, src.a)) + '٪';
      document.getElementById('mvFill').style.width = (index ? src.a / index[src.s - 1][1] * 100 : 0) + '%';
    });
  }
  function step(delta) {
    if (!source || source.kind !== 'mushaf' || !index) return;
    var s = source.s, a = source.a + delta;
    if (a < 1) { if (s > 1) { s--; a = index[s - 1][1]; } else a = 1; }
    else if (a > index[s - 1][1]) { if (s < 114) { s++; a = 1; } else return; }
    state.khatma = {s: s, a: a};
    startSource({kind: 'mushaf', s: s, a: a, basmala: false});
  }

  // ---- live broadcasts -----------------------------------------------------------------------------
  var liveBox, video, liveOn = false, liveId = 'makkah', liveTimer = 0;
  function openLive(id) {
    if (source) stop();
    liveId = live(id).id;
    if (!liveBox) {
      liveBox = el('section'); liveBox.id = 'liveView'; liveBox.hidden = true;
      video = document.createElement('video'); video.setAttribute('autoplay', '');
      liveBox.appendChild(video);
      liveBox.appendChild(el('div', 'lv-title')); liveBox.appendChild(el('div', 'lv-state'));
      video.addEventListener('playing', function () { liveState(''); });
      video.addEventListener('waiting', function () { liveState('جارٍ التحميل…'); });
      video.addEventListener('error', function () {
        liveState('تعذّر تشغيل البث، جارٍ إعادة المحاولة…');
        clearTimeout(liveTimer); liveTimer = setTimeout(function () { if (liveOn) startVideo(); }, 5000);
      });
      document.body.appendChild(liveBox);
    }
    close(); hideView();
    liveOn = true; liveBox.hidden = false; document.body.classList.add('quran-view');
    startVideo();
    if (!sleepAt) setSleep(state.sleep, true);
    render();
  }
  function startVideo() {
    var l = live(liveId), title = liveBox.querySelector('.lv-title');
    title.innerHTML = '<b></b><span></span><i>◀ ▶ تبديل البث · رجوع للخروج</i>';
    title.firstChild.textContent = l.name; title.children[1].textContent = l.sub;
    title.className = 'lv-title shown';
    clearTimeout(startVideo.t); startVideo.t = setTimeout(function () { title.className = 'lv-title'; }, 5000);
    liveState('جارٍ التحميل…');
    video.src = l.url;
    var p = video.play(); if (p && p.catch) p.catch(function () {});
  }
  function liveState(t) { if (liveBox) { var s = liveBox.querySelector('.lv-state'); s.textContent = t; s.style.display = t ? '' : 'none'; } }
  function closeLive() {
    if (!liveOn) return;
    liveOn = false; clearTimeout(liveTimer);
    try { video.pause(); video.removeAttribute('src'); video.load(); } catch (_) {}
    liveBox.hidden = true; if (!viewOpen()) document.body.classList.remove('quran-view');
    if (!source) { clearTimeout(sleepTimer); sleepAt = 0; }
    render();
  }

  // ---- hub panel -----------------------------------------------------------------------------------
  var panel, tabsRow, grid, side, status, chip, zone = 'grid', tab = 0, focus = 0, sideFocus = 0, items = [], sideItems = [], previous;
  function cols() { return TABS[tab].id === 'mushaf' ? 3 : 2; }
  function minutesLeft() { return ar(Math.max(1, Math.round((sleepAt - Date.now()) / 60000))); }
  function nowPlaying() {
    if (liveOn) return 'بث مباشر · ' + live(liveId).name;
    if (!source) return '';
    if (source.kind === 'radio') { var s = station(source.id); return s.name + (s.sub && s.sub !== 'بث مباشر' ? ' · ' + s.sub : ''); }
    return 'سورة ' + surahName(source.s) + (source.basmala ? '' : ' · الآية ' + ar(source.a)) + ' · ' + reciter(state.reciter).name;
  }
  function render() {
    if (!chip) { chip = el('div'); chip.id = 'radioChip'; document.body.appendChild(chip); }
    var np = nowPlaying();
    if (np && !liveOn) {
      chip.textContent = '';
      chip.appendChild(el('span', 'rc-dot' + (audio && !audio.paused && !retry ? ' live' : '')));
      chip.appendChild(el('span', 'rc-name', np));
      if (sleepAt) chip.appendChild(el('span', 'rc-sleep', 'يتوقف بعد ' + minutesLeft() + ' د'));
      chip.className = 'shown';
    } else chip.className = '';
    publish();
    if (!panel || panel.hidden) return;
    status.textContent = !np ? 'اختر ما تريد الاستماع إليه' : retry ? 'جارٍ إعادة الاتصال…' : (audio && audio.paused && !liveOn ? 'متوقف · ' : 'يعمل الآن: ') + np;
    Array.prototype.forEach.call(tabsRow.children, function (t, i) { t.className = 'rd-tab' + (i === tab ? ' sel' : '') + (zone === 'tabs' && i === tab ? ' focused' : ''); });
    items.forEach(function (b, i) {
      var on = b.kind === 'radio' ? source && source.kind === 'radio' && source.id === b.id : b.kind === 'surah' ? source && source.kind === 'mushaf' && source.s === b.s : liveOn && liveId === b.id;
      b.el.className = b.cls + (on ? ' playing' : '') + (zone === 'grid' && i === focus ? ' focused' : '');
    });
    sideItems.forEach(function (b, i) {
      if (b.value) b.el.lastChild.textContent = b.value();
      b.el.className = 'rd-btn' + (zone === 'side' && i === sideFocus ? ' focused' : '');
    });
  }
  function addSide(label, value, act, stepFn) {
    var b = el('div', 'rd-btn'), item = {el: b, value: value, act: act, step: stepFn};
    b.appendChild(el('span', 'rd-label', label)); if (value) b.appendChild(el('span', 'rd-value', ''));
    b.onclick = function () { pointerAct(function () { zone = 'side'; sideFocus = sideItems.indexOf(item); act(); render(); }); };
    side.appendChild(b); sideItems.push(item);
  }
  function build() {
    panel = el('section', 'radio-panel'); panel.hidden = true;
    var sheet = el('div', 'rd-sheet'); panel.appendChild(sheet);
    var head = el('div', 'rd-head'); head.appendChild(el('h1', '', 'القرآن الكريم')); status = el('div', 'rd-status'); head.appendChild(status); sheet.appendChild(head);
    tabsRow = el('div', 'rd-tabs'); sheet.appendChild(tabsRow);
    TABS.forEach(function (t, i) { var d = el('div', 'rd-tab', t.name); d.onclick = function () { pointerAct(function () { setTab(i); zone = 'grid'; render(); }); }; tabsRow.appendChild(d); });
    grid = el('div', 'rd-grid'); sheet.appendChild(grid);
    side = el('div', 'rd-side'); sheet.appendChild(side);
    document.body.appendChild(panel);
  }
  function setTab(i) {
    tab = i; state.tab = TABS[i].id; save();
    grid.textContent = ''; items = []; focus = 0; grid.scrollTop = 0;
    var id = TABS[i].id;
    grid.className = 'rd-grid c' + cols();
    if (id === 'radio') STATIONS.forEach(function (s) {
      var b = el('div'); b.appendChild(el('div', 'rd-st-name', s.name)); b.appendChild(el('div', 'rd-st-sub', s.sub));
      items.push({el: b, cls: 'rd-station', kind: 'radio', id: s.id});
    });
    if (id === 'mushaf') (index || []).forEach(function (x, k) {
      var b = el('div'); b.appendChild(el('div', 'rd-st-name', ar(k + 1) + ' · ' + x[0])); b.appendChild(el('div', 'rd-st-sub', ar(x[1]) + ' آية'));
      items.push({el: b, cls: 'rd-station', kind: 'surah', s: k + 1});
    });
    if (id === 'live') LIVE.forEach(function (l) {
      var b = el('div'); b.style.backgroundImage = 'url(wallpapers/thumbs/' + l.wall + '.jpg)';
      b.appendChild(el('div', 'rd-live-name', l.name)); b.appendChild(el('div', 'rd-st-sub', l.sub));
      items.push({el: b, cls: 'rd-live', kind: 'live', id: l.id});
    });
    items.forEach(function (it, k) { it.el.onclick = function () { pointerAct(function () { zone = 'grid'; focus = k; act(); }); }; grid.appendChild(it.el); });
    if (id === 'radio') focus = Math.max(0, STATIONS.map(function (s) { return s.id; }).indexOf(source && source.kind === 'radio' ? source.id : state.station));
    if (id === 'mushaf') focus = (source && source.kind === 'mushaf' ? source.s : state.khatma.s) - 1;
    buildSide();
    scrollToFocus();
  }
  function buildSide() {
    side.textContent = ''; sideItems = []; sideFocus = 0;
    if (TABS[tab].id === 'mushaf') {
      addSide('متابعة الختمة', function () { return 'سورة ' + surahName(state.khatma.s) + ' · الآية ' + ar(state.khatma.a) + ' · ' + ar(percent(state.khatma.s, state.khatma.a)) + '٪'; },
        function () { close(); playMushaf(state.khatma.s, state.khatma.a); });
      var cycleReciter = function (d) {
        var i = RECITERS.map(function (r) { return r.id; }).indexOf(state.reciter);
        state.reciter = RECITERS[(i + (d || 1) + RECITERS.length) % RECITERS.length].id; save();
        if (source && source.kind === 'mushaf') connect();
        render();
      };
      addSide('القارئ', function () { return reciter(state.reciter).name; }, cycleReciter, cycleReciter);
      addSide('عرض الآيات على الشاشة', null, function () { if (source && source.kind === 'mushaf') { close(); openView(); } });
    }
    addSide('إيقاف التشغيل', null, function () { stop(); closeLive(); });
    var cycleSleep = function () { setSleep(SLEEP[(SLEEP.indexOf(state.sleep) + 1) % SLEEP.length]); };
    addSide('مؤقت النوم', function () { return state.sleep ? ar(state.sleep) + ' دقيقة' + (sleepAt ? ' (متبقٍ ' + minutesLeft() + ')' : '') : 'بدون'; }, cycleSleep, cycleSleep);
    addSide('إطفاء التلفاز عند انتهاء المؤقت', function () { return state.powerOff ? 'نعم' : 'لا'; }, function () { state.powerOff = !state.powerOff; save(); render(); });
    addSide('إطفاء الشاشة والصوت مستمر', null, function () { close(); rpc('power', {action: 'screenOff'}); });
    if (sideItems.length < 6) side.appendChild(el('div', 'rd-note', 'أي زر في الريموت يعيد الشاشة. تتوقف التلاوة وقت الأذان ثم تعود.'));
  }
  // The OK key also produces a click wherever the hidden pointer rests; only real pointer clicks count.
  var okAt = 0;
  function pointerAct(fn) { if (Date.now() - okAt < 800) return; fn(); }
  function act() {
    var b = items[focus]; if (!b) return;
    if (b.kind === 'radio') play(b.id);
    else if (b.kind === 'surah') { close(); playMushaf(b.s, 1); }
    else if (b.kind === 'live') { close(); openLive(b.id); }
    render();
  }
  function scrollToFocus() {
    var f = items[focus]; if (!f) return;
    var top = f.el.offsetTop;
    if (top < grid.scrollTop) grid.scrollTop = top - 10;
    else if (top + f.el.offsetHeight > grid.scrollTop + grid.clientHeight) grid.scrollTop = top + f.el.offsetHeight - grid.clientHeight + 10;
  }
  var KEYS = [13, 27, 37, 38, 39, 40, 461];
  function onKey(e) {
    var k = e.keyCode, panelOpen = panel && !panel.hidden;
    if (k === 13) okAt = Date.now();
    if (liveOn && !panelOpen) {
      if (KEYS.indexOf(k) < 0) return;
      e.preventDefault(); e.stopImmediatePropagation();
      if (k === 461 || k === 27) return closeLive();
      if (k === 37 || k === 39) { liveId = LIVE[(LIVE.map(function (l) { return l.id; }).indexOf(liveId) + 1) % LIVE.length].id; startVideo(); render(); }
      else if (k === 13 && !e.repeat) startVideo();
      return;
    }
    if (viewOpen() && !panelOpen) {
      if (KEYS.indexOf(k) < 0) return;
      e.preventDefault(); e.stopImmediatePropagation();
      if (k === 461 || k === 27) return hideView();
      if (k === 13) { if (!e.repeat) togglePause(); return; }
      if (k === 37) step(1); else if (k === 39) step(-1); // right to left: Left moves forward
      else { hideView(); open('mushaf'); }
      return;
    }
    if (!panelOpen || KEYS.indexOf(k) < 0) return;
    e.preventDefault(); e.stopImmediatePropagation();
    if (k === 461 || k === 27) return close();
    var n = items.length, c = cols();
    if (zone === 'tabs') {
      if (k === 37 && tab < TABS.length - 1) setTab(tab + 1);
      else if (k === 39 && tab > 0) setTab(tab - 1);
      else if (k === 40 || k === 13) zone = n ? 'grid' : 'side';
    } else if (zone === 'grid') {
      var col = focus % c;
      if (k === 13) { if (!e.repeat) act(); return; }
      if (k === 38) { if (focus < c) zone = 'tabs'; else focus -= c; }
      else if (k === 40) { if (focus + c < n) focus += c; else if (Math.floor(focus / c) < Math.floor((n - 1) / c)) focus = n - 1; }
      else if (k === 39) { if (col > 0) focus--; }
      else if (k === 37) { if (col < c - 1 && focus + 1 < n) focus++; else { zone = 'side'; sideFocus = 0; } }
      scrollToFocus();
    } else {
      var it = sideItems[sideFocus];
      if (k === 13) { if (!e.repeat && it) it.act(); }
      else if (k === 38) { if (sideFocus > 0) sideFocus--; else zone = 'tabs'; }
      else if (k === 40) { if (sideFocus < sideItems.length - 1) sideFocus++; }
      else if (k === 39) zone = n ? 'grid' : 'tabs';
      else if (k === 37 && it && it.step) it.step(1);
    }
    render();
  }
  function open(tabId) {
    if (!panel) build();
    previous = document.activeElement;
    loadIndex(function () {
      var i = TABS.map(function (t) { return t.id; }).indexOf(tabId || state.tab);
      setTab(i < 0 ? 0 : i); zone = 'grid';
      panel.hidden = false; render();
    });
  }
  function close() { if (panel) panel.hidden = true; if (previous && previous.focus) previous.focus(); }

  // ---- state for the phone remote -----------------------------------------------------------------
  function publish() {
    clearTimeout(publish.t);
    publish.t = setTimeout(function () { if (window.XeeRemote) window.XeeRemote.publish(); }, 400);
  }
  function snapshot() {
    return {nowPlaying: nowPlaying(), kind: liveOn ? 'live' : source ? source.kind : '', paused: !!(audio && audio.paused && source),
      station: source && source.kind === 'radio' ? source.id : '', surah: source && source.kind === 'mushaf' ? source.s : 0, ayah: source && source.kind === 'mushaf' ? source.a : 0,
      live: liveOn ? liveId : '', reciter: state.reciter, khatma: state.khatma, khatmaPercent: percent(state.khatma.s, state.khatma.a),
      sleep: state.sleep, sleepLeft: sleepAt ? Math.round((sleepAt - Date.now()) / 60000) : 0, powerOff: state.powerOff};
  }

  load();
  loadIndex();
  document.addEventListener('keydown', onKey, true);
  document.addEventListener('webOSRelaunch', function (e) {
    // A plain relaunch is the Home or EXIT key: leave full-screen views. Commands from the phone keep them.
    var d = e && e.detail; try { d = typeof d === 'string' ? JSON.parse(d) : d; } catch (_) { d = null; }
    if (d && (d.remote || (d.params && d.params.remote))) return;
    closeLive(); hideView();
  });
  // If Home was restarted by the system while something played, carry on; an old session (TV turned off) stays quiet.
  var resumeAudio = state.aliveAt && Date.now() - state.aliveAt < 180000 && state.source;
  state.aliveAt = 0; save();
  if (resumeAudio) setTimeout(function () { loadIndex(function () { startSource(resumeAudio); }); }, 1500);
  setInterval(function () {
    if (source) { state.aliveAt = Date.now(); save(); }
    if (sleepAt) render();
  }, 30000);
  window.RadioUI = {
    open: open, play: play, playMushaf: playMushaf, openLive: openLive, stop: function () { stop(); closeLive(); },
    togglePause: togglePause, next: function () { step(1); }, prev: function () { step(-1); },
    setSleep: function (m) { setSleep(+m || 0); }, setPowerOff: function (v) { state.powerOff = !!v; save(); render(); },
    setReciter: function (id) { state.reciter = reciter(id).id; save(); if (source && source.kind === 'mushaf') connect(); render(); },
    pauseForAdhan: pauseForAdhan, resumeAfterAdhan: resumeAfterAdhan, nowPlaying: nowPlaying, snapshot: snapshot,
    blocksSaver: function () { return liveOn || viewOpen(); },
    playing: function () { return !!source || liveOn; },
    catalog: function () {
      return {stations: STATIONS.map(function (s) { return {id: s.id, name: s.name, sub: s.sub}; }), reciters: RECITERS,
        live: LIVE.map(function (l) { return {id: l.id, name: l.name, sub: l.sub}; }), surahs: index || [], sleep: SLEEP};
    }
  };
}());
