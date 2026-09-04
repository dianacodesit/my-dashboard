/* Land on today as soon as it exists; correct after collapse + fonts. */
(function () {
  try {
    if (document.documentElement.classList.contains('prototypes-page')) return;
    if (document.body && document.body.classList.contains('prototypes-page')) return;
    try { if (history.scrollRestoration) history.scrollRestoration = 'manual'; } catch (eR) {}

    var pad = function (n) { return String(n).padStart(2, '0'); };
    var isoNow = function () {
      var t = new Date();
      return t.getFullYear() + '-' + pad(t.getMonth() + 1) + '-' + pad(t.getDate());
    };

    function jump() {
      var iso = isoNow();
      var block = document.querySelector('.day-block[data-date="' + iso + '"]')
        || document.querySelector('.day-block.today-block');
      if (!block) return;
      block.classList.add('today-block');
      block.classList.remove('collapsed', 'past');
      try { block.scrollIntoView({ behavior: 'instant', block: 'start' }); } catch (e) {
        try { block.scrollIntoView({ behavior: 'auto', block: 'start' }); } catch (e2) {}
      }
      try {
        var y = Math.max(0, block.getBoundingClientRect().top + (window.scrollY || 0) - 12);
        window.scrollTo({ top: y, behavior: 'instant' });
      } catch (e3) {}
      window.__earlyTodayReady = true;
    }

    window.__scrollToToday = jump;
    if (!window.__earlyTodayReady) jump();

    function correct() {
      requestAnimationFrame(function () { jump(); });
    }
    if (document.readyState === 'complete') correct();
    else document.addEventListener('DOMContentLoaded', correct);
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () { jump(); }).catch(function () {});
    }
  } catch (err) {}
})();
