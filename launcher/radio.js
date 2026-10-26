/* Quran radio: live stations with automatic reconnect, a sleep timer, screen-off listening, and a pause
   while the adhan plays. Streams: Radio Quran Cairo and Saudi Quran (radiojar) and mp3quran.net radios. */
(function () {
  'use strict';
  var STORE = 'tvhome.radio.v1', SERVICE = 'luna://com.gathin.tvhome.prayer/';
  var Q = 'https://qurango.net/radio/', QB = 'https://backup.qurango.net/radio/';
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
  var SLEEP = [0, 15, 30, 60, 90, 120, 180, 240];
  var state = {station: 'cairo', sleep: 0, powerOff: false, aliveAt: 0};
  var audio = null, heardAt = 0, playing = null, urlIndex = 0, retry = 0, retryTimer = 0, sleepAt = 0, sleepTimer = 0, pausedForAdhan = false;
  var panel, grid, status, chip, focus = 0, buttons = [], previous;

  function ar(n) { return String(n).replace(/\d/g, function (d) { return '٠١٢٣٤٥٦٧٨٩'.charAt(d); }); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }
  function load() { try { var s = JSON.parse(localStorage.getItem(STORE)); if (s) Object.keys(state).forEach(function (k) { if (s[k] !== undefined) state[k] = s[k]; }); } catch (_) {} }
  function save() { try { localStorage.setItem(STORE, JSON.stringify(state)); } catch (_) {} }
  function station(id) { return STATIONS.filter(function (s) { return s.id === id; })[0] || STATIONS[0]; }
  function rpc(method, payload) {
    try { var b = new PalmServiceBridge(); b.onservicecallback = function () {}; b.call(SERVICE + method, JSON.stringify(payload || {})); } catch (_) {}
  }

  // ---- playback with reconnect ---------------------------------------------------------------
  function connect() {
    var s = station(playing);
    clearTimeout(retryTimer); retryTimer = 0;
    if (!audio) {
      audio = new Audio();
      audio.preload = 'none';
      audio.addEventListener('playing', function () { retry = 0; render(); });
      audio.addEventListener('timeupdate', function () { heardAt = Date.now(); });
      ['error', 'ended'].forEach(function (ev) { audio.addEventListener(ev, function () { if (playing && !pausedForAdhan) reconnect(); }); });
    }
    heardAt = Date.now();
    audio.src = s.urls[urlIndex % s.urls.length];
    var p = audio.play(); if (p && p.catch) p.catch(function () { if (playing && !pausedForAdhan) reconnect(); });
    render();
  }
  // Night listening must survive dropped streams: retry with backoff, alternating to the backup address.
  function reconnect() {
    clearTimeout(retryTimer);
    retry++; urlIndex++;
    render();
    retryTimer = setTimeout(function () { retryTimer = 0; if (playing && !pausedForAdhan) connect(); }, Math.min(30000, 2000 * retry));
  }
  // A live stream can hang without firing an error; reconnect when no audio has advanced for 25 seconds.
  setInterval(function () {
    if (playing && !pausedForAdhan && !retryTimer && Date.now() - heardAt > 25000) reconnect();
  }, 10000);
  function play(id) {
    playing = id; state.station = id; state.aliveAt = Date.now(); save();
    urlIndex = 0; retry = 0; pausedForAdhan = false;
    connect();
    if (!sleepAt) setSleep(state.sleep); // the chosen sleep timer applies every time a station starts
  }
  function stop() {
    playing = null; pausedForAdhan = false; clearTimeout(retryTimer); retryTimer = 0; state.aliveAt = 0; save();
    if (audio) { audio.pause(); audio.removeAttribute('src'); try { audio.load(); } catch (_) {} }
    clearTimeout(sleepTimer); sleepAt = 0;
    render();
  }
  function setSleep(minutes, quiet) {
    state.sleep = minutes; save();
    clearTimeout(sleepTimer); sleepAt = 0;
    if (minutes && playing) {
      sleepAt = Date.now() + minutes * 60000;
      sleepTimer = setTimeout(function () {
        var off = state.powerOff;
        stop();
        if (off) rpc('power', {action: 'off'});
      }, minutes * 60000);
    }
    if (!quiet) render();
  }

  // ---- adhan hooks (called by the prayer module) -------------------------------------------------
  function pauseForAdhan() { if (playing && audio && !audio.paused) { pausedForAdhan = true; audio.pause(); } }
  function resumeAfterAdhan() { if (pausedForAdhan && playing) { pausedForAdhan = false; connect(); } }

  // ---- UI -----------------------------------------------------------------------------------------
  function render() {
    if (!chip) { chip = el('div'); chip.id = 'radioChip'; document.body.appendChild(chip); }
    if (playing) {
      var s = station(playing);
      chip.textContent = '';
      chip.appendChild(el('span', 'rc-dot' + (audio && !audio.paused && !retry ? ' live' : '')));
      chip.appendChild(el('span', 'rc-name', s.name + (s.sub && s.sub !== 'بث مباشر' ? ' · ' + s.sub : '')));
      if (sleepAt) chip.appendChild(el('span', 'rc-sleep', 'يتوقف بعد ' + ar(Math.max(1, Math.round((sleepAt - Date.now()) / 60000))) + ' د'));
      chip.className = 'shown';
    } else chip.className = '';
    if (!panel || panel.hidden) return;
    buttons.forEach(function (b) {
      if (b.station) b.className = 'rd-station' + (b.station === playing ? ' playing' : '') + (buttons.indexOf(b) === focus ? ' focused' : '');
      else b.className = 'rd-btn' + (buttons.indexOf(b) === focus ? ' focused' : '');
    });
    stopBtn.textContent = playing ? 'إيقاف الراديو' : 'لا يعمل شيء الآن';
    sleepBtn.lastChild.textContent = state.sleep ? ar(state.sleep) + ' دقيقة' + (sleepAt ? ' (متبقٍ ' + ar(Math.max(1, Math.round((sleepAt - Date.now()) / 60000))) + ')' : '') : 'بدون';
    powerBtn.lastChild.textContent = state.powerOff ? 'نعم' : 'لا';
    status.textContent = !playing ? 'اختر محطة للتشغيل' : retry ? 'جارٍ إعادة الاتصال بالبث…' : audio && audio.paused ? 'جارٍ الاتصال…' : 'يعمل الآن: ' + station(playing).name;
  }
  var stopBtn, sleepBtn, powerBtn, screenBtn;
  function button(cls, label, value) {
    var b = el('div', cls); b.appendChild(el('span', 'rd-label', label)); if (value !== undefined) b.appendChild(el('span', 'rd-value', value)); return b;
  }
  function build() {
    panel = el('section', 'radio-panel'); panel.hidden = true;
    var sheet = el('div', 'rd-sheet'); panel.appendChild(sheet);
    var head = el('div', 'rd-head'); head.appendChild(el('h1', '', 'إذاعات القرآن الكريم')); status = el('div', 'rd-status'); head.appendChild(status); sheet.appendChild(head);
    grid = el('div', 'rd-grid'); sheet.appendChild(grid);
    var side = el('div', 'rd-side'); sheet.appendChild(side);
    buttons = [];
    STATIONS.forEach(function (s) {
      var b = el('div', 'rd-station'); b.station = s.id;
      b.appendChild(el('div', 'rd-st-name', s.name)); b.appendChild(el('div', 'rd-st-sub', s.sub));
      b.onclick = function () { pointerAct(b); };
      grid.appendChild(b); buttons.push(b);
    });
    stopBtn = button('rd-btn', 'إيقاف الراديو'); stopBtn.act = stop;
    sleepBtn = button('rd-btn', 'مؤقت النوم', ''); sleepBtn.act = function () { setSleep(SLEEP[(SLEEP.indexOf(state.sleep) + 1) % SLEEP.length]); }; sleepBtn.step = sleepBtn.act;
    powerBtn = button('rd-btn', 'إطفاء التلفاز عند انتهاء المؤقت', ''); powerBtn.act = function () { state.powerOff = !state.powerOff; save(); render(); };
    screenBtn = button('rd-btn', 'إطفاء الشاشة والصوت مستمر'); screenBtn.act = function () { close(); rpc('power', {action: 'screenOff'}); };
    [stopBtn, sleepBtn, powerBtn, screenBtn].forEach(function (b) { b.onclick = function () { pointerAct(b); }; side.appendChild(b); buttons.push(b); });
    side.appendChild(el('div', 'rd-note', 'أي زر في الريموت يعيد تشغيل الشاشة. يتوقف الراديو وقت الأذان ثم يعود.'));
    document.body.appendChild(panel);
    document.addEventListener('keydown', onKey, true);
  }
  // The OK key also produces a click wherever the hidden pointer rests; only real pointer clicks count.
  var okAt = 0;
  function pointerAct(b) { if (Date.now() - okAt < 800) return; focus = buttons.indexOf(b); act(); }
  function act() { var b = buttons[focus]; if (b.station) play(b.station); else if (b.act) b.act(); render(); }
  var COLS = 2;
  function onKey(e) {
    if (!panel || panel.hidden) return;
    var k = e.keyCode, n = STATIONS.length;
    if ([13, 27, 37, 38, 39, 40, 461].indexOf(k) < 0) return;
    e.preventDefault(); e.stopImmediatePropagation();
    if (k === 461 || k === 27) return close();
    if (k === 13) { okAt = Date.now(); if (!e.repeat) act(); return; }
    if (focus < n) {
      // Station grid: two columns, right to left; Left from the last column moves to the side buttons.
      var col = focus % COLS;
      if (k === 38) focus = Math.max(0, focus - COLS);
      else if (k === 40) focus = Math.min(n - 1, focus + COLS);
      else if (k === 39) { if (col > 0) focus--; }
      else if (k === 37) { if (col < COLS - 1 && focus + 1 < n) focus++; else focus = n; }
    } else {
      if (k === 38) focus = Math.max(n, focus - 1);
      else if (k === 40) focus = Math.min(buttons.length - 1, focus + 1);
      else if (k === 39) focus = Math.max(0, n - COLS);
      else if (k === 37 && buttons[focus].step) buttons[focus].step();
    }
    var f = buttons[focus];
    if (f && f.station) { var top = f.offsetTop; if (top < grid.scrollTop) grid.scrollTop = top - 10; else if (top + f.offsetHeight > grid.scrollTop + grid.clientHeight) grid.scrollTop = top + f.offsetHeight - grid.clientHeight + 10; }
    render();
  }
  function open() {
    if (!panel) build();
    previous = document.activeElement;
    focus = Math.max(0, STATIONS.map(function (s) { return s.id; }).indexOf(playing || state.station));
    panel.hidden = false; render();
  }
  function close() { if (panel) panel.hidden = true; if (previous && previous.focus) previous.focus(); }

  load();
  // If Home was restarted by the system while the radio played, carry on; an old session (TV turned off) stays quiet.
  var resumeRadio = state.aliveAt && Date.now() - state.aliveAt < 180000;
  state.aliveAt = 0; save();
  if (resumeRadio) setTimeout(function () { play(state.station); }, 1500);
  setInterval(function () {
    if (playing) { state.aliveAt = Date.now(); save(); }
    if (playing && sleepAt) render();
  }, 30000);
  window.RadioUI = {open: open, pauseForAdhan: pauseForAdhan, resumeAfterAdhan: resumeAfterAdhan, nowPlaying: function () { return playing ? station(playing).name : ''; }};
}());
