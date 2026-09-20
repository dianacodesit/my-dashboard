/* Land on today as soon as that day-block exists in the DOM — during HTML
   parse, not after the rest of the 70k-line page finishes. Never wait for
   collage tiles / packing. Never wipe localStorage. */
(function () {
  try {
    if (document.documentElement.classList.contains('prototypes-page')) return;
    try { if (history.scrollRestoration) history.scrollRestoration = 'manual'; } catch (eR) {}
    try { document.documentElement.style.setProperty('overflow-anchor', 'none'); } catch (eA) {}
    try { document.documentElement.classList.add('btm-today-hold'); } catch (eH) {}

    var pad = function (n) { return String(n).padStart(2, '0'); };
    var isoNow = function () {
      var t = new Date();
      return t.getFullYear() + '-' + pad(t.getMonth() + 1) + '-' + pad(t.getDate());
    };

    var pinnedOnce = false;
    var pinUntil = Date.now() + 1200;
    var userMoved = false;
    var mo = null;
    var collapsePassDone = false;
    var pinScheduled = false;

    function releaseHold() {
      try {
        document.documentElement.classList.remove('btm-today-hold', 'btm-today-first');
        document.documentElement.classList.add('btm-today-pinned', 'btm-collage-ready');
      } catch (e) {}
    }

    function collapseOthers(iso, block) {
      if (collapsePassDone) return;
      try {
        document.querySelectorAll('.day-block[data-date]').forEach(function (b) {
          if (b === block) return;
          var d = b.getAttribute('data-date') || '';
          if (d === 'doha' || d === 'archive' || b.classList.contains('archive-block')) {
            if (!b.classList.contains('collapsed')) b.classList.add('collapsed');
            return;
          }
          if (/^\d{4}-\d{2}-\d{2}$/.test(d) && d !== iso) {
            if (!b.classList.contains('collapsed')) b.classList.add('collapsed');
          }
        });
        collapsePassDone = true;
      } catch (eCol) {}
    }

    function pinTodayCard() {
      if (document.documentElement.classList.contains('prototypes-page')) return false;
      if (document.body && document.body.classList.contains('prototypes-page')) return false;
      if (userMoved && Date.now() > pinUntil) return false;

      var iso = isoNow();
      var block = document.querySelector('.day-block[data-date="' + iso + '"]')
        || document.querySelector('.day-block.today-block');
      /* Jump on the day shell itself — do NOT wait for .vision-tile / pack. */
      if (!block) return false;

      document.querySelectorAll('.day-block.today-block').forEach(function (b) {
        if (b !== block) b.classList.remove('today-block');
      });
      block.classList.add('today-block');
      block.classList.remove('collapsed', 'past');

      /* One pass only — never thrash classList on every MutationObserver tick. */
      collapseOthers(iso, block);

      var card = block.querySelector('.day-card') || block;
      var y = Math.max(0, Math.round(card.getBoundingClientRect().top + (window.scrollY || 0) - 20));
      try { window.scrollTo(0, y); } catch (e3) {}
      try { document.documentElement.scrollTop = y; } catch (e4) {}
      try { if (document.body) document.body.scrollTop = y; } catch (e5) {}

      window.__earlyTodayReady = true;
      releaseHold();
      pinnedOnce = true;
      return true;
    }

    function schedulePin() {
      if (pinScheduled) return;
      pinScheduled = true;
      try {
        requestAnimationFrame(function () {
          pinScheduled = false;
          pinTodayCard();
        });
      } catch (eRaf) {
        pinScheduled = false;
        pinTodayCard();
      }
    }

    function releasePin() {
      userMoved = true;
      pinUntil = 0;
      releaseHold();
    }

    window.__pinTodayCard = pinTodayCard;
    window.__scrollToToday = function () {
      userMoved = false;
      pinUntil = Date.now() + 600;
      collapsePassDone = false;
      return pinTodayCard();
    };

    /* Catch today the moment the parser inserts it (mid-document). */
    try {
      mo = new MutationObserver(function () {
        schedulePin();
      });
      mo.observe(document.documentElement, { childList: true, subtree: true });
    } catch (eMo) {}

    pinTodayCard();

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () {
        pinTodayCard();
        releaseHold();
        try { if (mo) mo.disconnect(); } catch (eD0) {}
      }, { once: true });
    } else {
      pinTodayCard();
      releaseHold();
    }

    window.addEventListener('load', function () {
      pinTodayCard();
      releaseHold();
      try { if (mo) mo.disconnect(); } catch (eD) {}
    }, { once: true });

    /* Short settle passes only — no multi-second cascade. */
    [0, 50, 150, 400].forEach(function (ms) {
      setTimeout(function () {
        pinTodayCard();
        if (ms >= 400) {
          releaseHold();
          try { if (mo) mo.disconnect(); } catch (eD2) {}
        }
      }, ms);
    });

    /* Safety: never leave the rail invisible if today is missing. */
    setTimeout(function () {
      releaseHold();
      try { if (mo) mo.disconnect(); } catch (eD3) {}
    }, 1600);

    window.addEventListener('wheel', releasePin, { passive: true, once: true });
    window.addEventListener('touchmove', releasePin, { passive: true, once: true });
    window.addEventListener('keydown', function (e) {
      if (e.key === 'PageDown' || e.key === 'PageUp' || e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Home' || e.key === 'End' || e.key === ' ') releasePin();
    }, { passive: true });
  } catch (err) {
    try {
      document.documentElement.classList.remove('btm-today-hold', 'btm-today-first');
      document.documentElement.classList.add('btm-collage-ready');
    } catch (e2) {}
  }
})();
