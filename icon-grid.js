/* Wrap grids cards into sections. Pack each section as a cluster —
   cards stay close, and dragging one makes the others accommodate. */
(function () {
  var POS_KEY = "grids_freeform_pos_v3";
  var zTop = 6;
  var GAP = 16;
  var FOLLOW_R = 560;

  function hash(s) {
    var h = 2166136261;
    s = String(s || "");
    for (var i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
    return h >>> 0;
  }
  function rng(seed) {
    var x = seed || 1;
    return function () {
      x = (x * 1664525 + 1013904223) >>> 0;
      return x / 4294967296;
    };
  }
  function loadPos() {
    try { return JSON.parse(localStorage.getItem(POS_KEY) || "{}") || {}; }
    catch (e) { return {}; }
  }
  function savePos(map) {
    try { localStorage.setItem(POS_KEY, JSON.stringify(map)); } catch (e) {}
  }

  function findGrid() {
    var byId = document.getElementById("iconTaskGrid");
    if (byId) return byId;
    var host = document.getElementById("icon-grid-host");
    if (host) return host.querySelector(".grid");
    return null;
  }

  function queryCards(canvas) {
    return Array.from(canvas.querySelectorAll(":scope > .card, :scope > .collapsible-content > .card"));
  }

  function canvasWidth(canvas) {
    return Math.max(canvas.clientWidth || 0, 320);
  }

  function clampX(x, w, W) {
    return Math.max(4, Math.min(x, Math.max(4, W - w - 8)));
  }

  function unwrapPanes(grid) {
    if (!grid) return;
    Array.from(grid.querySelectorAll(":scope > .grid-section")).forEach(function (sec) {
      var cards = sec.querySelector(":scope > .grid-section-cards");
      var kids = [];
      Array.from(sec.children).forEach(function (child) {
        if (child === cards) {
          Array.from(child.children).forEach(function (card) { kids.push(card); });
        } else {
          kids.push(child);
        }
      });
      kids.forEach(function (el) { grid.insertBefore(el, sec); });
      sec.remove();
    });
    grid.removeAttribute("data-freeform");
  }

  function wrapIntoSections(grid) {
    if (!grid || grid.getAttribute("data-freeform") === "1") return;
    unwrapPanes(grid);
    var kids = Array.from(grid.children);
    var current = null;
    function startSection(label) {
      var sec = document.createElement("div");
      sec.className = "grid-section";
      var canvas = document.createElement("div");
      canvas.className = "grid-section-cards";
      sec.appendChild(label);
      sec.appendChild(canvas);
      grid.appendChild(sec);
      current = canvas;
    }
    kids.forEach(function (el) {
      if (el.classList.contains("section-label")) {
        startSection(el);
      } else if (el.classList.contains("card") || el.classList.contains("collapsible-content")) {
        if (!current) startSection(document.createElement("div"));
        current.appendChild(el);
      } else {
        grid.appendChild(el);
      }
    });
    grid.setAttribute("data-freeform", "1");
  }

  function overlaps(a, list, pad) {
    for (var i = 0; i < list.length; i++) {
      var b = list[i];
      if (a.x < b.x + b.w + pad && a.x + a.w + pad > b.x &&
          a.y < b.y + b.h + pad && a.y + a.h + pad > b.y) return true;
    }
    return false;
  }

  function sectionSeed(canvas) {
    var sec = canvas.closest(".grid-section");
    var label = sec && sec.querySelector(".section-label");
    return hash(label ? label.textContent : "section");
  }

  function findPackSlot(placed, w, h, W, originX, originY, rnd) {
    if (!placed.length) return { x: originX, y: originY };

    var cx = 0, cy = 0;
    placed.forEach(function (p) {
      cx += p.x + p.w / 2;
      cy += p.y + p.h / 2;
    });
    cx /= placed.length;
    cy /= placed.length;

    var best = null;
    var bestScore = 1e12;

    function consider(x, y) {
      x = clampX(x, w, W);
      y = Math.max(6, y);
      if (overlaps({ x: x, y: y, w: w, h: h }, placed, GAP - 2)) return;
      var mx = x + w / 2;
      var my = y + h / 2;
      var d = (mx - cx) * (mx - cx) + (my - cy) * (my - cy);
      var rightBias = Math.max(0, x - (cx + 80));
      var score = d + rightBias * rightBias * 0.15;
      if (score < bestScore) {
        bestScore = score;
        best = { x: x, y: y };
      }
    }

    placed.forEach(function (p) {
      var jx = rnd() * 24 - 8;
      var jy = rnd() * 32 - 12;
      consider(p.x + p.w + GAP + jx, p.y + jy);
      consider(p.x + jx, p.y + p.h + GAP + jy);
      consider(p.x + p.w * 0.4 + jx, p.y + p.h + GAP - 6 + jy);
      consider(p.x - w - GAP + jx, p.y + jy);
      consider(p.x + p.w * 0.15 + jx, p.y - h - GAP + jy);
      consider(p.x + p.w + GAP - 6 + jx, p.y + p.h * 0.28 + jy);
    });

    if (best) return best;

    var maxB = 0;
    var minX = originX;
    placed.forEach(function (p) {
      maxB = Math.max(maxB, p.y + p.h);
      minX = Math.min(minX, p.x);
    });
    return { x: minX, y: maxB + GAP + 6 };
  }

  function readNodes(canvas) {
    return queryCards(canvas).map(function (el) {
      return {
        el: el,
        x: parseFloat(el.style.left) || 0,
        y: parseFloat(el.style.top) || 0,
        w: el.offsetWidth || parseFloat(el.style.width) || 248,
        h: el.offsetHeight || 180
      };
    });
  }

  function applyNodes(nodes) {
    nodes.forEach(function (n) {
      n.el.style.left = n.x + "px";
      n.el.style.top = n.y + "px";
    });
  }

  function pinCluster(nodes, originX, originY, W) {
    if (!nodes.length) return;
    var minX = Infinity;
    var minY = Infinity;
    var maxX = 0;
    nodes.forEach(function (n) {
      minX = Math.min(minX, n.x);
      minY = Math.min(minY, n.y);
      maxX = Math.max(maxX, n.x + n.w);
    });
    var dx = originX - minX;
    var dy = originY - minY;
    if (maxX + dx > W - 8) dx = (W - 8) - maxX;
    if (minX + dx < 4) dx = 4 - minX;
    nodes.forEach(function (n) {
      n.x += dx;
      n.y = Math.max(6, n.y + dy);
    });
  }

  function fitCanvas(canvas, nodes) {
    var maxB = 0;
    (nodes || readNodes(canvas)).forEach(function (n) {
      maxB = Math.max(maxB, n.y + n.h);
    });
    canvas.style.height = (maxB + 32) + "px";
  }

  function persistCanvas(canvas) {
    var saved = loadPos();
    queryCards(canvas).forEach(function (card) {
      if (!card.id) return;
      saved[card.id] = {
        x: parseFloat(card.style.left) || 0,
        y: parseFloat(card.style.top) || 0,
        r: parseFloat((card.style.getPropertyValue("--card-rot") || "0").replace("deg", "")) || 0,
        w: parseFloat(card.style.width) || card.offsetWidth
      };
    });
    savePos(saved);
  }

  function stepForces(nodes, pinnedEl, W, opts) {
    var pad = opts && opts.pad != null ? opts.pad : GAP;
    var attract = opts && opts.attract;
    var n = nodes.length;
    if (n < 2) return;
    var vx = new Array(n);
    var vy = new Array(n);
    var i, j;
    for (i = 0; i < n; i++) { vx[i] = 0; vy[i] = 0; }

    for (i = 0; i < n; i++) {
      for (j = i + 1; j < n; j++) {
        var a = nodes[i];
        var b = nodes[j];
        var dx = (b.x + b.w / 2) - (a.x + a.w / 2);
        var dy = (b.y + b.h / 2) - (a.y + a.h / 2);
        var dist = Math.hypot(dx, dy) || 0.001;
        var nx = dx / dist;
        var ny = dy / dist;
        var gapX = (a.w + b.w) / 2 + pad - Math.abs(dx);
        var gapY = (a.h + b.h) / 2 + pad - Math.abs(dy);
        if (gapX > 0 && gapY > 0) {
          var push = Math.min(gapX, gapY) * 0.52;
          vx[i] -= nx * push;
          vy[i] -= ny * push;
          vx[j] += nx * push;
          vy[j] += ny * push;
        } else if (attract) {
          var edgeGap = Math.max(
            Math.abs(dx) - (a.w + b.w) / 2,
            Math.abs(dy) - (a.h + b.h) / 2
          );
          if (edgeGap > 22 && edgeGap < 130) {
            var pull = Math.min(16, (edgeGap - 18) * 0.09);
            vx[i] += nx * pull;
            vy[i] += ny * pull;
            vx[j] -= nx * pull;
            vy[j] -= ny * pull;
          }
        }
      }
    }

    for (i = 0; i < n; i++) {
      if (nodes[i].el === pinnedEl) continue;
      nodes[i].x += vx[i];
      nodes[i].y += vy[i];
      nodes[i].x = clampX(nodes[i].x, nodes[i].w, W);
      nodes[i].y = Math.max(6, nodes[i].y);
    }
  }

  function followPinned(nodes, pinned, dx, dy) {
    var pcx = pinned.x + pinned.w / 2;
    var pcy = pinned.y + pinned.h / 2;
    nodes.forEach(function (n) {
      if (n.el === pinned.el) return;
      var cx = n.x + n.w / 2;
      var cy = n.y + n.h / 2;
      var d = Math.hypot(cx - pcx, cy - pcy);
      var infl = Math.max(0, 1 - d / FOLLOW_R);
      infl = infl * infl;
      n.x += dx * infl * 0.68;
      n.y += dy * infl * 0.68;
    });
  }

  function scatterCanvas(canvas, saved) {
    var cards = queryCards(canvas);
    if (!cards.length) {
      canvas.style.minHeight = "0px";
      canvas.style.height = "0px";
      return;
    }
    var W = canvasWidth(canvas);
    var rnd = rng(sectionSeed(canvas));
    var originX = 16 + Math.floor(rnd() * 28);
    var originY = 10 + Math.floor(rnd() * 8);
    var placed = [];
    var fresh = 0;

    cards.forEach(function (card, i) {
      var id = card.id || ("anon-" + i);
      var crnd = rng(hash(id));
      var prev = saved[id];
      var w = prev && prev.w ? prev.w : (248 + Math.floor(crnd() * 56));
      if (W < 420) w = Math.min(w, W - 16);
      card.style.width = w + "px";
      card.style.position = "absolute";
      var h = Math.max(card.offsetHeight || 180, 140);
      var rot = prev && typeof prev.r === "number" ? prev.r : (crnd() * 6.4) - 2.8;
      var x, y;
      if (prev && typeof prev.x === "number" && typeof prev.y === "number") {
        x = prev.x;
        y = prev.y;
      } else {
        fresh += 1;
        var slot = findPackSlot(placed, w, h, W, originX, originY, crnd);
        x = slot.x;
        y = slot.y;
      }
      x = clampX(x, w, W);
      y = Math.max(6, y);
      card.style.left = x + "px";
      card.style.top = y + "px";
      card.style.setProperty("--card-rot", rot.toFixed(2) + "deg");
      saved[id] = { x: x, y: y, r: rot, w: w };
      placed.push({ x: x, y: y, w: w, h: h });
    });

    var nodes = readNodes(canvas);
    var k;
    if (fresh) {
      for (k = 0; k < 8; k++) stepForces(nodes, null, W, { pad: GAP, attract: true });
      pinCluster(nodes, originX, originY, W);
    } else {
      for (k = 0; k < 4; k++) stepForces(nodes, null, W, { pad: 8, attract: false });
    }
    applyNodes(nodes);
    nodes.forEach(function (n) {
      if (!n.el.id) return;
      var cur = saved[n.el.id] || {};
      saved[n.el.id] = { x: n.x, y: n.y, r: cur.r || 0, w: cur.w || n.w };
    });
    fitCanvas(canvas, nodes);
  }

  function scatterAll(grid) {
    var saved = loadPos();
    Array.from(grid.querySelectorAll(":scope > .grid-section > .grid-section-cards")).forEach(function (canvas) {
      scatterCanvas(canvas, saved);
    });
    savePos(saved);
  }

  function bindDrag(grid) {
    if (grid.getAttribute("data-drag") === "1") return;
    grid.setAttribute("data-drag", "1");
    var dragging = null;
    grid.addEventListener("pointerdown", function (e) {
      if (e.button && e.button !== 0) return;
      if (e.target.closest("input, button, a, label, [contenteditable]")) return;
      var card = e.target.closest(".card");
      if (!card || !grid.contains(card)) return;
      var canvas = card.closest(".grid-section-cards");
      if (!canvas) return;
      var rect = card.getBoundingClientRect();
      dragging = {
        card: card,
        canvas: canvas,
        dx: e.clientX - rect.left,
        dy: e.clientY - rect.top,
        lastX: parseFloat(card.style.left) || 0,
        lastY: parseFloat(card.style.top) || 0
      };
      card.classList.add("is-dragging");
      queryCards(canvas).forEach(function (c) {
        if (c !== card) c.classList.add("is-relating");
      });
      card.style.zIndex = String(++zTop);
      try { card.setPointerCapture(e.pointerId); } catch (err) {}
      e.preventDefault();
    });
    grid.addEventListener("pointermove", function (e) {
      if (!dragging) return;
      var canvas = dragging.canvas;
      var W = canvasWidth(canvas);
      var crect = canvas.getBoundingClientRect();
      var x = e.clientX - crect.left - dragging.dx;
      var y = e.clientY - crect.top - dragging.dy;
      x = Math.max(-20, x);
      y = Math.max(0, y);

      var nodes = readNodes(canvas);
      var pinned = null;
      nodes.forEach(function (n) { if (n.el === dragging.card) pinned = n; });
      if (!pinned) return;

      var dx = x - pinned.x;
      var dy = y - pinned.y;
      pinned.x = x;
      pinned.y = y;
      followPinned(nodes, pinned, dx, dy);
      var k;
      for (k = 0; k < 5; k++) stepForces(nodes, pinned.el, W, { pad: 12, attract: false });
      applyNodes(nodes);
      fitCanvas(canvas, nodes);
      dragging.lastX = pinned.x;
      dragging.lastY = pinned.y;
    });
    function endDrag() {
      if (!dragging) return;
      var card = dragging.card;
      var canvas = dragging.canvas;
      var W = canvasWidth(canvas);
      card.classList.remove("is-dragging");
      queryCards(canvas).forEach(function (c) { c.classList.remove("is-relating"); });
      var nodes = readNodes(canvas);
      var k;
      for (k = 0; k < 14; k++) stepForces(nodes, card, W, { pad: GAP, attract: true });
      applyNodes(nodes);
      persistCanvas(canvas);
      fitCanvas(canvas, nodes);
      dragging = null;
    }
    grid.addEventListener("pointerup", endDrag);
    grid.addEventListener("pointercancel", endDrag);
  }

  function wrapGrid(grid) {
    if (!grid) return;
    if (!document.body.classList.contains("icon-grid-page")) return;
    grid.classList.add("icon-task-grid");
    if (!grid.id) grid.id = "iconTaskGrid";
    if (!grid.parentElement || grid.parentElement.id !== "icon-grid-host") {
      var host = document.createElement("div");
      host.id = "icon-grid-host";
      grid.parentNode.insertBefore(host, grid);
      host.appendChild(grid);
    }
    wrapIntoSections(grid);
    scatterAll(grid);
    bindDrag(grid);
  }

  function run() {
    wrapGrid(findGrid());
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      run();
      requestAnimationFrame(run);
    });
  } else {
    run();
    requestAnimationFrame(run);
  }
  window.addEventListener("resize", function () {
    var grid = findGrid();
    if (!grid || grid.getAttribute("data-freeform") !== "1") return;
    scatterAll(grid);
  });
})();
