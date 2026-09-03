/* Seed localStorage from baked-data.json only when empty. Never blocks first paint. */
(function () {
  try {
    if (localStorage.getItem('btm_baked_applied_v1')) return;
    if (localStorage.getItem('btm_added_v1') !== null) {
      localStorage.setItem('btm_baked_applied_v1', '1');
      return;
    }
  } catch (e) {
    return;
  }
  var run = function () {
    fetch('baked-data.json')
      .then(function (r) { return r.json(); })
      .then(function (D) {
        try {
          for (var k in D) {
            if (localStorage.getItem(k) === null) localStorage.setItem(k, D[k]);
          }
          localStorage.setItem('btm_baked_applied_v1', '1');
        } catch (e2) {}
      })
      .catch(function () {});
  };
  if (typeof requestIdleCallback === 'function') requestIdleCallback(run, { timeout: 2500 });
  else setTimeout(run, 1);
})();
