/* Jump to TODAY when the day card is in the page. Prototype is left alone. */
(function () {
  try {
    if (document.documentElement.classList.contains('prototypes-page')) return;
    if (document.body && document.body.classList.contains('prototypes-page')) return;
    var pad = function (n) { return String(n).padStart(2, '0'); };
    var isoNow = function () {
      var t = new Date();
      return t.getFullYear() + '-' + pad(t.getMonth() + 1) + '-' + pad(t.getDate());
    };

    function realToday() {
      var iso = isoNow();
      var nodes = document.querySelectorAll('.day-block[data-date="' + iso + '"]');
      for (var i = 0; i < nodes.length; i++) {
        if (!nodes[i].getAttribute('data-today-stub')) return nodes[i];
      }
      return null;
    }

    function jump() {
      try { if (window.__unnestSwallowedDays) window.__unnestSwallowedDays(); } catch (eU) {}
      var block = realToday() || document.querySelector('.day-block.today-block');
      if (!block) return false;
      block.classList.add('today-block');
      block.setAttribute('data-btm-hydrated', '1');
      block.classList.remove('collapsed', 'past');
      try { block.scrollIntoView({ behavior: 'auto', block: 'start' }); } catch (e) {}
      try { window.scrollTo(0, Math.max(0, block.getBoundingClientRect().top + window.scrollY - 12)); } catch (e2) {}
      window.__earlyTodayReady = true;
      return true;
    }

    window.__scrollToToday = function () {
      return jump();
    };

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', jump);
    else jump();
  } catch (err) {}
})();
