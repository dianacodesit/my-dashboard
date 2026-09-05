/* Pin the viewport to today as soon as that day-block exists — do not wait for EOF scripts. */
(function () {
  try {
    if (document.documentElement.classList.contains('prototypes-page')) return;
    try { if (history.scrollRestoration) history.scrollRestoration = 'manual'; } catch (eR) {}

    var pad = function (n) { return String(n).padStart(2, '0'); };
    var isoNow = function () {
      var t = new Date();
      return t.getFullYear() + '-' + pad(t.getMonth() + 1) + '-' + pad(t.getDate());
    };

    var raf = 0;
    var obs = null;
    var until = 0;

    function jump() {
      if (document.documentElement.classList.contains('prototypes-page')) return false;
      if (document.body && document.body.classList.contains('prototypes-page')) return false;
      var iso = isoNow();
      var block = document.querySelector('.day-block[data-date="' + iso + '"]');
      if (!block) return false;
      document.querySelectorAll('.day-block.today-block').forEach(function (b) {
        if (b !== block) b.classList.remove('today-block');
      });
      block.classList.add('today-block');
      block.classList.remove('collapsed', 'past');
      try { block.scrollIntoView({ behavior: 'instant', block: 'start' }); } catch (e) {
        try { block.scrollIntoView({ behavior: 'auto', block: 'start' }); } catch (e2) {}
      }
      try {
        var y = Math.max(0, block.getBoundingClientRect().top + (window.scrollY || 0) - 12);
        window.scrollTo(0, y);
      } catch (e3) {}
      window.__earlyTodayReady = true;
      return true;
    }

    function schedule() {
      if (until && Date.now() > until) {
        if (obs) try { obs.disconnect(); } catch (eD) {}
        return;
      }
      if (raf) return;
      raf = requestAnimationFrame(function () {
        raf = 0;
        jump();
      });
    }

    window.__scrollToToday = jump;
    jump();
    until = Date.now() + 6000;
    try {
      obs = new MutationObserver(schedule);
      obs.observe(document.documentElement, { childList: true, subtree: true });
    } catch (eM) {}
    window.addEventListener('load', function () {
      jump();
      setTimeout(function () {
        until = 0;
        if (obs) try { obs.disconnect(); } catch (eD) {}
      }, 200);
    }, { once: true });
  } catch (err) {}
})();
