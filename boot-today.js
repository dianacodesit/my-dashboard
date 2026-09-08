/* Land on the top of today's frosted card. Re-pin while the collage packs.
   Never wipe localStorage — that deleted adds and caused a second paint. */
(function () {
  try {
    if (document.documentElement.classList.contains('prototypes-page')) return;
    try { if (history.scrollRestoration) history.scrollRestoration = 'manual'; } catch (eR) {}
    try { document.documentElement.style.setProperty('overflow-anchor', 'none'); } catch (eA) {}

    var pad = function (n) { return String(n).padStart(2, '0'); };
    var isoNow = function () {
      var t = new Date();
      return t.getFullYear() + '-' + pad(t.getMonth() + 1) + '-' + pad(t.getDate());
    };

    var pinUntil = Date.now() + 1800;
    var userMoved = false;

    function heroReady(block) {
      if (!block) return false;
      var hero = block.querySelector('.vision-hero');
      if (!hero) return false;
      return !!hero.querySelector(':scope > .vision-tile');
    }

    function pinTodayCard() {
      if (document.documentElement.classList.contains('prototypes-page')) return false;
      if (document.body && document.body.classList.contains('prototypes-page')) return false;
      if (userMoved && Date.now() > pinUntil) return false;
      var iso = isoNow();
      var block = document.querySelector('.day-block[data-date="' + iso + '"]')
        || document.querySelector('.day-block.today-block');
      if (!heroReady(block)) return false;
      document.querySelectorAll('.day-block.today-block').forEach(function (b) {
        if (b !== block) b.classList.remove('today-block');
      });
      block.classList.add('today-block');
      block.classList.remove('collapsed', 'past');
      var card = block.querySelector('.day-card') || block;
      var y = Math.max(0, Math.round(card.getBoundingClientRect().top + (window.scrollY || 0) - 20));
      try { window.scrollTo(0, y); } catch (e3) {}
      try { document.documentElement.scrollTop = y; } catch (e4) {}
      window.__earlyTodayReady = true;
      try { document.documentElement.classList.add('btm-collage-ready'); } catch (eRdy) {}
      return true;
    }

    function releasePin() {
      userMoved = true;
      pinUntil = 0;
    }

    window.__pinTodayCard = pinTodayCard;
    window.__scrollToToday = function () {
      userMoved = false;
      pinUntil = Date.now() + 800;
      return pinTodayCard();
    };

    pinTodayCard();
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () { pinTodayCard(); }, { once: true });
    }
    window.addEventListener('load', function () { pinTodayCard(); }, { once: true });
    [80, 220, 500, 900, 1400].forEach(function (ms) {
      setTimeout(pinTodayCard, ms);
    });
    window.addEventListener('wheel', releasePin, { passive: true, once: true });
    window.addEventListener('touchmove', releasePin, { passive: true, once: true });
    window.addEventListener('keydown', function (e) {
      if (e.key === 'PageDown' || e.key === 'PageUp' || e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Home' || e.key === 'End' || e.key === ' ') releasePin();
    }, { passive: true });
  } catch (err) {}
})();
