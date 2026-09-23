/* Pin today as soon as its day-block exists. NEVER hide the page waiting —
   that was not a fix and made load feel endless. Collapsed-day photo parking
   stays (stops the fetch storm). Never wipe localStorage here.
   Load flash cascades are banned forever — see .cursor/rules/no-load-flash-cascades.mdc
   and window.__BTM_NO_LOAD_CASCADE in everything.html. */
(function () {
  try {
    if (document.documentElement.classList.contains('prototypes-page')) return;
    try { if (history.scrollRestoration) history.scrollRestoration = 'manual'; } catch (eR) {}
    try { document.documentElement.style.setProperty('overflow-anchor', 'none'); } catch (eA) {}
    /* Explicitly clear any leftover hold from older builds. */
    try {
      document.documentElement.classList.remove('btm-today-hold', 'btm-today-first');
      document.documentElement.classList.add('btm-today-pinned', 'btm-collage-ready');
    } catch (eClear) {}

    (function interceptCollapsedImgSrc() {
      function inParkedDay(img) {
        try {
          var blk = img && img.closest && img.closest('.day-block');
          return !!(blk && blk.classList.contains('collapsed') && !blk.classList.contains('today-block'));
        } catch (e) { return false; }
      }
      function parkInstead(img, url) {
        if (!img || !url) return;
        try {
          img.setAttribute('data-park-src', String(url));
          img.setAttribute('loading', 'lazy');
          if (img.hasAttribute('src')) img.removeAttribute('src');
        } catch (eP) {}
      }
      try {
        var proto = window.HTMLImageElement && HTMLImageElement.prototype;
        if (proto) {
          var desc = Object.getOwnPropertyDescriptor(proto, 'src');
          if (desc && desc.set && !proto.__btmParkSrcHooked) {
            proto.__btmParkSrcHooked = true;
            Object.defineProperty(proto, 'src', {
              configurable: true,
              enumerable: desc.enumerable,
              get: desc.get,
              set: function (v) {
                if (inParkedDay(this)) {
                  parkInstead(this, v);
                  return;
                }
                return desc.set.call(this, v);
              }
            });
          }
          if (!proto.__btmParkSetAttrHooked) {
            proto.__btmParkSetAttrHooked = true;
            var origSet = proto.setAttribute;
            proto.setAttribute = function (name, val) {
              if (String(name).toLowerCase() === 'src' && inParkedDay(this)) {
                parkInstead(this, val);
                return;
              }
              return origSet.apply(this, arguments);
            };
          }
        }
      } catch (eHook) {}
    })();

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
      /* Never pin a stale baked today-block (yesterday) — that left Sep 22
         expanded and unpositioned, so load flashed the title-only grid. */
      var block = document.querySelector('.day-block[data-date="' + iso + '"]');
      if (!block) return false;

      document.querySelectorAll('.day-block.today-block').forEach(function (b) {
        if (b !== block) b.classList.remove('today-block');
      });
      block.classList.add('today-block');
      block.classList.remove('collapsed', 'past');

      collapseOthers(iso, block);

      var card = block.querySelector('.day-card') || block;
      var y = Math.max(0, Math.round(card.getBoundingClientRect().top + (window.scrollY || 0) - 20));
      try { window.scrollTo(0, y); } catch (e3) {}
      try { document.documentElement.scrollTop = y; } catch (e4) {}
      try { if (document.body) document.body.scrollTop = y; } catch (e5) {}

      window.__earlyTodayReady = true;
      try {
        document.documentElement.classList.remove('btm-today-hold', 'btm-today-first');
        document.documentElement.classList.add('btm-today-pinned', 'btm-collage-ready');
      } catch (eCls) {}
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
    }

    function parkCollapsedImgs(root) {
      try {
        var scope = root || document;
        var blocks = scope.querySelectorAll
          ? (scope.matches && scope.matches('.day-block.collapsed:not(.today-block)')
              ? [scope]
              : scope.querySelectorAll('.day-block.collapsed:not(.today-block)'))
          : [];
        [].forEach.call(blocks, function (blk) {
          blk.querySelectorAll('img[src]').forEach(function (img) {
            if (img.getAttribute('data-park-src')) return;
            var src = img.getAttribute('src') || '';
            if (!src || src.indexOf('data:') === 0) return;
            img.setAttribute('data-park-src', src);
            img.removeAttribute('src');
            img.setAttribute('loading', 'lazy');
          });
          /* Do not strip --tile-photo. That strip is the title-only grid. */
        });
        // #region agent log
        try {
          var s22 = document.querySelector('.day-block[data-date="2026-09-22"]');
          var tiles = s22 ? s22.querySelectorAll('.vision-hero > .vision-tile') : [];
          var live = 0, parked = 0;
          [].forEach.call(tiles, function (t) {
            if (t.style.getPropertyValue('--tile-photo')) live++;
            if (t.getAttribute('data-park-tile-photo')) parked++;
          });
          fetch('http://127.0.0.1:7377/ingest/ef4f74e3-93fd-4fda-b1d5-ff8477f18dd9',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'013c46'},body:JSON.stringify({sessionId:'013c46',runId:'post-fix-keep-photo',hypothesisId:'P',location:'boot-today.js:park',message:'sep22-photos',data:{n:tiles.length,live:live,parked:parked,collapsed:!!(s22&&s22.classList.contains('collapsed'))},timestamp:Date.now()})}).catch(function(){});
        } catch (eLog) {}
        // #endregion
      } catch (ePark) {}
    }
    function restoreDayImgs(blk) {
      if (!blk) return;
      try {
        blk.classList.remove('collapsed');
        blk.querySelectorAll('img[data-park-src]').forEach(function (img) {
          var src = img.getAttribute('data-park-src');
          if (!src) return;
          img.removeAttribute('data-park-src');
          img.src = src;
        });
        blk.querySelectorAll('[data-park-tile-photo], [data-park-sub-photo]').forEach(function (el) {
          var tile = el.getAttribute('data-park-tile-photo');
          var sub = el.getAttribute('data-park-sub-photo');
          if (tile) {
            try { el.style.setProperty('--tile-photo', tile); } catch (eT) {}
            el.removeAttribute('data-park-tile-photo');
          }
          if (sub) {
            try { el.style.setProperty('--sub-photo', sub); } catch (eS) {}
            el.removeAttribute('data-park-sub-photo');
          }
        });
      } catch (eRest) {}
    }
    window.__parkCollapsedImgs = parkCollapsedImgs;
    window.__restoreDayImgs = restoreDayImgs;
    var parkScheduled = false;
    function schedulePark() {
      if (parkScheduled) return;
      parkScheduled = true;
      try {
        requestAnimationFrame(function () {
          parkScheduled = false;
          parkCollapsedImgs(document);
        });
      } catch (eRafP) {
        parkScheduled = false;
        parkCollapsedImgs(document);
      }
    }

    window.__pinTodayCard = pinTodayCard;
    window.__scrollToToday = function () {
      userMoved = false;
      pinUntil = Date.now() + 800;
      collapsePassDone = false;
      return pinTodayCard();
    };
    window.__releaseTodayHold = function () {
      try {
        document.documentElement.classList.remove('btm-today-hold', 'btm-today-first');
        document.documentElement.classList.add('btm-today-pinned', 'btm-collage-ready');
      } catch (e) {}
    };

    try {
      mo = new MutationObserver(function (muts) {
        schedulePin();
        for (var i = 0; i < muts.length; i++) {
          var nodes = muts[i].addedNodes;
          for (var j = 0; j < nodes.length; j++) {
            var n = nodes[j];
            if (!n || n.nodeType !== 1) continue;
            if (n.matches && n.matches('img[src]')) {
              var blk = n.closest && n.closest('.day-block.collapsed:not(.today-block)');
              if (blk) {
                if (!n.getAttribute('data-park-src')) {
                  var src = n.getAttribute('src') || '';
                  if (src && src.indexOf('data:') !== 0) {
                    n.setAttribute('data-park-src', src);
                    n.removeAttribute('src');
                    n.setAttribute('loading', 'lazy');
                  }
                }
              }
            } else if (n.querySelectorAll) {
              parkCollapsedImgs(n);
            }
          }
        }
        schedulePark();
      });
      mo.observe(document.documentElement, { childList: true, subtree: true });
    } catch (eMo) {}

    pinTodayCard();
    parkCollapsedImgs(document);

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () {
        pinTodayCard();
        parkCollapsedImgs(document);
        try { if (mo) mo.disconnect(); } catch (eD0) {}
      }, { once: true });
    } else {
      pinTodayCard();
      parkCollapsedImgs(document);
    }

    window.addEventListener('load', function () {
      pinTodayCard();
      parkCollapsedImgs(document);
      try { if (mo) mo.disconnect(); } catch (eD) {}
    }, { once: true });

    [0, 50, 150, 400].forEach(function (ms) {
      setTimeout(function () {
        pinTodayCard();
        parkCollapsedImgs(document);
        if (ms >= 400) {
          try { if (mo) mo.disconnect(); } catch (eD2) {}
        }
      }, ms);
    });

    window.addEventListener('wheel', releasePin, { passive: true, once: true });
    window.addEventListener('touchmove', releasePin, { passive: true, once: true });
    window.addEventListener('keydown', function (e) {
      if (e.key === 'PageDown' || e.key === 'PageUp' || e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Home' || e.key === 'End' || e.key === ' ') releasePin();
    }, { passive: true });

    document.addEventListener('click', function (e) {
      var hdr = e.target && e.target.closest && e.target.closest('.day-card-header');
      if (!hdr) return;
      var blk = hdr.closest('.day-block');
      if (!blk) return;
      setTimeout(function () {
        if (blk.classList.contains('collapsed') && !blk.classList.contains('today-block')) {
          parkCollapsedImgs(blk);
        } else {
          restoreDayImgs(blk);
        }
      }, 0);
    }, true);
  } catch (err) {
    try {
      document.documentElement.classList.remove('btm-today-hold', 'btm-today-first');
      document.documentElement.classList.add('btm-collage-ready', 'btm-today-pinned');
    } catch (e2) {}
  }
})();
