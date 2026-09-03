/* Jump to today once, after the first layout. No hold, no observers, no retries. */
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
      if (window.__earlyTodayReady) return;
      var iso = isoNow();
      var block = document.querySelector('.day-block[data-date="' + iso + '"]')
        || document.querySelector('.day-block.today-block');
      if (!block) return;
      block.classList.add('today-block');
      block.classList.remove('collapsed', 'past');
      try { block.scrollIntoView({ behavior: 'auto', block: 'start' }); } catch (e) {}
      try {
        var y = Math.max(0, block.getBoundingClientRect().top + (window.scrollY || 0) - 12);
        window.scrollTo(0, y);
      } catch (e2) {}
      window.__earlyTodayReady = true;
    }

    function afterLayout() {
      requestAnimationFrame(function () { requestAnimationFrame(jump); });
    }

    window.__scrollToToday = jump;
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', afterLayout);
    else afterLayout();
  } catch (err) {}
})();
