/* Wrap grids cards into sections. Each section is a force-directed
   cluster: cards stay linked, and moving one reflows the others. */
(function () {
  var POS_KEY = "grids_freeform_pos_v3";
  var SEC_KEY = "grids_card_section_v1";
  var zTop = 6;
  var GAP = 16;
  var FOLLOW_R = 780;

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
  function loadSections() {
    try { return JSON.parse(localStorage.getItem(SEC_KEY) || "{}") || {}; }
    catch (e) { return {}; }
  }
  function saveSections(map) {
    try { localStorage.setItem(SEC_KEY, JSON.stringify(map)); } catch (e) {}
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

  function unwrapSoloRows(grid) {
    if (!grid) return;
    Array.from(grid.querySelectorAll(".grid-solo-row")).forEach(function (row) {
      var parent = row.parentNode;
      if (!parent) return;
      Array.from(row.children).forEach(function (sec) {
        parent.insertBefore(sec, row);
      });
      row.remove();
    });
  }

  function clearColumnCard(card) {
    if (!card) return;
    card.classList.remove("is-column-card");
  }

  function applyColumnCard(card) {
    if (!card) return;
    card.classList.add("is-column-card");
    card.style.position = "";
    card.style.left = "";
    card.style.top = "";
    card.style.width = "";
  }

  function liftColumnCard(card, canvas) {
    if (!card || !canvas) return;
    var cr = card.getBoundingClientRect();
    var pr = canvas.getBoundingClientRect();
    card.classList.remove("is-column-card");
    card.style.position = "absolute";
    card.style.width = Math.max(160, cr.width) + "px";
    card.style.left = (cr.left - pr.left) + "px";
    card.style.top = (cr.top - pr.top) + "px";
  }

  function promoteFromSolo(canvas) {
    var sec = canvas && canvas.closest(".grid-section");
    if (!sec || !sec.classList.contains("is-solo")) return;
    sec.classList.remove("is-solo");
    var cards = queryCards(canvas);
    var W = canvasWidth(canvas);
    cards.forEach(function (card, i) {
      clearColumnCard(card);
      var abs = card.style.position === "absolute" && card.style.left;
      if (!abs) {
        card.style.position = "absolute";
        card.style.width = Math.min(280, Math.max(200, W - 32)) + "px";
        card.style.left = (16 + i * 36) + "px";
        card.style.top = (10 + i * 20) + "px";
      }
    });
  }

  function applySoloMode(sec) {
    var canvas = sec && sec.querySelector(":scope > .grid-section-cards");
    var cards = canvas ? queryCards(canvas) : [];
    var solo = cards.length === 1;
    sec.classList.toggle("is-solo", solo);
    if (solo) {
      applyColumnCard(cards[0]);
      canvas.style.height = "";
      canvas.style.minHeight = "";
    } else {
      cards.forEach(clearColumnCard);
    }
  }

  function packSoloRows(grid) {
    if (!grid) return;
    unwrapSoloRows(grid);
    var kids = Array.from(grid.children);
    var i = 0;
    while (i < kids.length) {
      var el = kids[i];
      if (el.classList && el.classList.contains("grid-section") && el.classList.contains("is-solo")) {
        var run = [el];
        var j = i + 1;
        while (j < kids.length && kids[j].classList && kids[j].classList.contains("grid-section") && kids[j].classList.contains("is-solo")) {
          run.push(kids[j]);
          j++;
        }
        var row = document.createElement("div");
        row.className = "grid-solo-row";
        grid.insertBefore(row, run[0]);
        run.forEach(function (sec) { row.appendChild(sec); });
        kids = Array.from(grid.children);
        i = kids.indexOf(row) + 1;
        continue;
      }
      i++;
    }
  }

  function syncSoloColumns(grid) {
    if (!grid) return;
    unwrapSoloRows(grid);
    Array.from(grid.querySelectorAll(":scope > .grid-section")).forEach(applySoloMode);
    packSoloRows(grid);
  }

  function unwrapPanes(grid) {
    if (!grid) return;
    unwrapSoloRows(grid);
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

  function packTwoAcross(cards, W, saved) {
    var gap = 20;
    var pad = 16;
    var avail = Math.max(280, W - pad * 2 - gap);
    var w = Math.min(340, Math.max(220, Math.floor(avail / 2)));
    if (W < 520) w = Math.min(w, W - 24);
    cards.forEach(function (card, i) {
      clearColumnCard(card);
      var prev = saved && card.id ? saved[card.id] : null;
      var rot = prev && typeof prev.r === "number" ? prev.r : 0;
      var x = pad + i * (w + gap);
      var y = 10;
      if (W < 520) {
        x = pad;
        y = 10 + i * 8;
      }
      x = clampX(x, w, W);
      card.style.position = "absolute";
      card.style.width = w + "px";
      card.style.left = x + "px";
      card.style.top = y + "px";
      card.style.setProperty("--card-rot", rot.toFixed(2) + "deg");
      if (saved && card.id) saved[card.id] = { x: x, y: y, r: rot, w: w };
    });
  }

  function savedPairIsStacked(cards, saved) {
    if (cards.length !== 2 || !saved) return false;
    var a = saved[cards[0].id];
    var b = saved[cards[1].id];
    if (!a || !b || typeof a.x !== "number" || typeof b.x !== "number") return false;
    var minW = Math.min(a.w || 248, b.w || 248);
    return Math.abs(a.x - b.x) < minW * 0.5 && Math.abs((a.y || 0) - (b.y || 0)) > 70;
  }

  function findPackSlot(placed, w, h, W, originX, originY, rnd) {
    if (!placed.length) return { x: originX, y: originY };
    if (placed.length === 1 && W >= w + placed[0].w + GAP + 24) {
      return {
        x: clampX(placed[0].x + placed[0].w + GAP, w, W),
        y: placed[0].y
      };
    }

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

  function fitCanvas(canvas, nodes, ignoreEl) {
    var maxB = 0;
    (nodes || readNodes(canvas)).forEach(function (n) {
      if (ignoreEl && n.el === ignoreEl) return;
      maxB = Math.max(maxB, n.y + n.h);
    });
    canvas.style.height = Math.max(160, maxB + 32) + "px";
  }

  function persistCanvas(canvas) {
    var saved = loadPos();
    var secs = loadSections();
    var title = sectionTitle(canvas);
    queryCards(canvas).forEach(function (card) {
      if (!card.id) return;
      saved[card.id] = {
        x: parseFloat(card.style.left) || 0,
        y: parseFloat(card.style.top) || 0,
        r: parseFloat((card.style.getPropertyValue("--card-rot") || "0").replace("deg", "")) || 0,
        w: parseFloat(card.style.width) || card.offsetWidth
      };
      if (title) secs[card.id] = title;
    });
    savePos(saved);
    saveSections(secs);
  }

  function forcePairedCards(grid) {
    var pairs = [
      { ids: ["c5", "c12"], title: "storage" },
      { ids: ["c7", "c8"], title: "devices repairs" }
    ];
    var byTitle = {};
    Array.from(grid.querySelectorAll(".grid-section")).forEach(function (sec) {
      var canvas = sec.querySelector(":scope > .grid-section-cards");
      var title = sectionTitle(canvas);
      if (canvas && title) byTitle[title.toLowerCase()] = canvas;
    });
    pairs.forEach(function (pair) {
      var dest = byTitle[pair.title];
      if (!dest) return;
      pair.ids.forEach(function (id) {
        var card = document.getElementById(id);
        if (card) dest.appendChild(card);
      });
    });
  }

  function applySavedSections(grid) {
    var secs = loadSections();
    if (!secs || !Object.keys(secs).length) return;
    var byTitle = {};
    Array.from(grid.querySelectorAll(".grid-section")).forEach(function (sec) {
      var canvas = sec.querySelector(":scope > .grid-section-cards");
      var title = sectionTitle(canvas);
      if (canvas && title) byTitle[title.toLowerCase()] = canvas;
    });
    Object.keys(secs).forEach(function (id) {
      var card = document.getElementById(id);
      if (!card || !grid.contains(card)) return;
      var want = String(secs[id] || "").toLowerCase();
      var dest = byTitle[want];
      if (!dest) return;
      if (card.closest(".grid-section-cards") === dest) return;
      dest.appendChild(card);
      setCardSectionLabel(card, dest);
    });
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
          if (edgeGap > 16) {
            var pull = Math.min(36, (edgeGap - 12) * 0.16);
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

  function visualSort(cards) {
    return cards.slice().sort(function (a, b) {
      var ay = parseFloat(a.style.top) || 0;
      var by = parseFloat(b.style.top) || 0;
      if (Math.abs(ay - by) > 36) return ay - by;
      return (parseFloat(a.style.left) || 0) - (parseFloat(b.style.left) || 0);
    });
  }

  function clusterHasHole(nodes, W) {
    if (!nodes || nodes.length < 2) return false;
    var minW = nodes.reduce(function (m, n) { return Math.min(m, n.w || 248); }, 248);
    var rows = [];
    nodes.forEach(function (n) {
      var row = null;
      for (var i = 0; i < rows.length; i++) {
        if (Math.abs(rows[i].y - n.y) < Math.min(rows[i].h, n.h) * 0.5) {
          row = rows[i];
          break;
        }
      }
      if (!row) {
        rows.push({ y: n.y, h: n.h, items: [n] });
      } else {
        row.items.push(n);
        row.h = Math.max(row.h, n.h);
      }
    });
    for (var r = 0; r < rows.length; r++) {
      var items = rows[r].items.slice().sort(function (a, b) { return a.x - b.x; });
      if (items[0].x > 28 + minW * 0.45) return true;
      for (var i = 0; i < items.length - 1; i++) {
        if (items[i + 1].x - (items[i].x + items[i].w) > minW * 0.5) return true;
      }
      var last = items[items.length - 1];
      var slack = W - 16 - (last.x + last.w);
      if (r < rows.length - 1 && slack > minW + GAP) return true;
    }
    return false;
  }

  function packCluster(canvas, saved) {
    var cards = queryCards(canvas);
    if (!cards.length) {
      canvas.style.minHeight = "0px";
      canvas.style.height = "0px";
      return;
    }
    if (cards.length === 1) {
      applyColumnCard(cards[0]);
      canvas.style.height = "";
      canvas.style.minHeight = "";
      return;
    }
    var W = canvasWidth(canvas);
    if (cards.length === 2 && W >= 520) {
      packTwoAcross(cards, W, saved);
      fitCanvas(canvas, readNodes(canvas));
      return;
    }
    var ordered = visualSort(cards);
    var cols = W >= 980 ? 3 : W >= 520 ? 2 : 1;
    var gap = 20;
    var pad = 16;
    var w = Math.min(340, Math.max(220, Math.floor((W - pad * 2 - gap * (cols - 1)) / cols)));
    if (W < 420) w = Math.min(w, W - 24);
    ordered.forEach(function (card) {
      clearColumnCard(card);
      card.style.position = "absolute";
      card.style.width = w + "px";
    });
    var x = pad;
    var y = 10;
    var col = 0;
    var rowH = 0;
    ordered.forEach(function (card) {
      var h = Math.max(card.offsetHeight || 180, 140);
      if (col >= cols) {
        x = pad;
        y += rowH + gap;
        col = 0;
        rowH = 0;
      }
      x = clampX(x, w, W);
      var prev = saved && card.id ? saved[card.id] : null;
      var rot = prev && typeof prev.r === "number" ? prev.r : 0;
      card.style.left = x + "px";
      card.style.top = y + "px";
      card.style.setProperty("--card-rot", rot.toFixed(2) + "deg");
      if (saved && card.id) saved[card.id] = { x: x, y: y, r: rot, w: w };
      x += w + gap;
      col += 1;
      rowH = Math.max(rowH, h);
    });
    fitCanvas(canvas, readNodes(canvas));
  }

  function withSettleAnim(canvas, fn) {
    if (!canvas) return;
    var cards = queryCards(canvas);
    cards.forEach(function (c) { c.classList.add("is-settling"); });
    fn();
    window.setTimeout(function () {
      cards.forEach(function (c) { c.classList.remove("is-settling"); });
    }, 420);
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
      n.x += dx * infl * 0.86;
      n.y += dy * infl * 0.86;
    });
  }

  function scatterCanvas(canvas, saved) {
    var cards = queryCards(canvas);
    if (!cards.length) {
      canvas.style.minHeight = "0px";
      canvas.style.height = "0px";
      return;
    }
    if (cards.length === 1) {
      applyColumnCard(cards[0]);
      canvas.style.height = "";
      canvas.style.minHeight = "";
      return;
    }
    var W = canvasWidth(canvas);
    if (cards.length === 2 && (W >= 520 || savedPairIsStacked(cards, saved))) {
      packTwoAcross(cards, W, saved);
      fitCanvas(canvas, readNodes(canvas));
      return;
    }
    if (cards.length >= 3) {
      var probe = [];
      var holey = false;
      cards.forEach(function (card) {
        var prev = saved && card.id ? saved[card.id] : null;
        if (prev && typeof prev.x === "number" && typeof prev.y === "number") {
          probe.push({
            x: prev.x,
            y: prev.y,
            w: prev.w || 248,
            h: Math.max(card.offsetHeight || 180, 140)
          });
        }
      });
      if (probe.length === cards.length) holey = clusterHasHole(probe, W);
      if (holey || probe.length !== cards.length) {
        packCluster(canvas, saved);
        return;
      }
    }
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
    Array.from(grid.querySelectorAll(".grid-section > .grid-section-cards")).forEach(function (canvas) {
      scatterCanvas(canvas, saved);
    });
    savePos(saved);
    syncSoloColumns(grid);
  }

  function sectionTitle(canvas) {
    var sec = canvas && canvas.closest(".grid-section");
    var label = sec && sec.querySelector(".section-label");
    if (!label) return "";
    return String(label.textContent || "")
      .replace(/[▾▾▲△]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function setCardSectionLabel(card, canvas) {
    var title = sectionTitle(canvas);
    if (!title) return;
    var num = card.querySelector(".task-num");
    if (num) num.textContent = title;
  }

  function clearDropTargets(grid) {
    Array.from(grid.querySelectorAll(".grid-section-cards.is-drop-target")).forEach(function (el) {
      el.classList.remove("is-drop-target");
    });
  }

  // Section ownership by label midpoints — never by canvas height.
  // Growing a section while dragging used to push the next label down forever.
  function canvasAtPoint(grid, clientX, clientY) {
    var sections = Array.from(grid.querySelectorAll(".grid-section"));
    if (!sections.length) return null;
    var hit = null;
    var bestArea = 1e15;
    sections.forEach(function (sec) {
      var canvas = sec.querySelector(":scope > .grid-section-cards");
      if (!canvas) return;
      var r = sec.getBoundingClientRect();
      var padX = 22;
      var padY = 28;
      if (clientX >= r.left - padX && clientX <= r.right + padX &&
          clientY >= r.top - padY && clientY <= r.bottom + padY) {
        var area = Math.max(1, r.width * r.height);
        if (area < bestArea) {
          bestArea = area;
          hit = canvas;
        }
      }
    });
    if (hit) return hit;
    var nearest = null;
    var nd = 1e12;
    sections.forEach(function (sec) {
      var canvas = sec.querySelector(":scope > .grid-section-cards");
      if (!canvas) return;
      var r = sec.getBoundingClientRect();
      var cx = (r.left + r.right) / 2;
      var cy = (r.top + r.bottom) / 2;
      var d = Math.hypot(clientX - cx, clientY - cy);
      if (d < nd) {
        nd = d;
        nearest = canvas;
      }
    });
    return nearest;
  }

  function settleCanvas(canvas, pinnedEl) {
    if (!canvas) return;
    var cards = queryCards(canvas);
    if (cards.length <= 1) {
      persistCanvas(canvas);
      var gridSolo = canvas.closest(".icon-task-grid") || canvas.closest(".grid");
      if (gridSolo) syncSoloColumns(gridSolo);
      return;
    }
    var W = canvasWidth(canvas);
    if (cards.length === 2 && W >= 520) {
      withSettleAnim(canvas, function () {
        packTwoAcross(cards, W, loadPos());
        persistCanvas(canvas);
        fitCanvas(canvas, readNodes(canvas));
      });
      var gridPair = canvas.closest(".icon-task-grid") || canvas.closest(".grid");
      if (gridPair) syncSoloColumns(gridPair);
      return;
    }
    var nodes = readNodes(canvas);
    if (!pinnedEl || clusterHasHole(nodes, W)) {
      withSettleAnim(canvas, function () {
        packCluster(canvas, loadPos());
        persistCanvas(canvas);
      });
      var gridPack = canvas.closest(".icon-task-grid") || canvas.closest(".grid");
      if (gridPack) syncSoloColumns(gridPack);
      return;
    }
    var k;
    for (k = 0; k < 14; k++) stepForces(nodes, pinnedEl || null, W, { pad: GAP, attract: true });
    applyNodes(nodes);
    persistCanvas(canvas);
    fitCanvas(canvas, nodes);
    var grid = canvas.closest(".icon-task-grid") || canvas.closest(".grid");
    if (grid) syncSoloColumns(grid);
  }

  function transferCard(card, fromCanvas, toCanvas, clientX, clientY, grabDx, grabDy) {
    if (!card || !toCanvas || fromCanvas === toCanvas) return fromCanvas;
    if (fromCanvas) {
      queryCards(fromCanvas).forEach(function (c) { c.classList.remove("is-relating"); });
    }
    toCanvas.appendChild(card);
    if (fromCanvas) {
      withSettleAnim(fromCanvas, function () {
        packCluster(fromCanvas, loadPos());
        persistCanvas(fromCanvas);
      });
    }
    if (queryCards(toCanvas).length >= 2) promoteFromSolo(toCanvas);
    setCardSectionLabel(card, toCanvas);
    var crect = toCanvas.getBoundingClientRect();
    var x = clientX - crect.left - grabDx;
    var y = clientY - crect.top - grabDy;
    x = Math.max(-20, Math.min(x, Math.max(4, canvasWidth(toCanvas) - 40)));
    // Keep drop near the top of the destination cluster — don't stretch it
    y = Math.max(0, Math.min(y, 220));
    card.style.left = x + "px";
    card.style.top = y + "px";
    queryCards(toCanvas).forEach(function (c) {
      if (c !== card) c.classList.add("is-relating");
    });
    return toCanvas;
  }

  function bindDrag(grid) {
    if (grid.getAttribute("data-drag") === "1") return;
    grid.setAttribute("data-drag", "1");
    var dragging = null;
    var activePointerId = null;

    function onMove(e) {
      if (!dragging) return;
      if (activePointerId != null && e.pointerId !== activePointerId) return;
      e.preventDefault();

      var target = canvasAtPoint(grid, e.clientX, e.clientY) || dragging.canvas;
      if (target !== dragging.canvas) {
        dragging.canvas = transferCard(
          dragging.card,
          dragging.canvas,
          target,
          e.clientX,
          e.clientY,
          dragging.dx,
          dragging.dy
        );
      }
      clearDropTargets(grid);
      if (target && target !== dragging.originCanvas) {
        target.classList.add("is-drop-target");
      }

      var canvas = dragging.canvas;
      var W = canvasWidth(canvas);
      var crect = canvas.getBoundingClientRect();
      var x = e.clientX - crect.left - dragging.dx;
      var y = e.clientY - crect.top - dragging.dy;
      x = Math.max(-20, x);
      // While still in the origin section, allow free placement but do not
      // let the canvas height chase the pointer (exclude card from fit).
      if (canvas === dragging.originCanvas) {
        y = Math.max(0, y);
      } else {
        y = Math.max(0, Math.min(y, Math.max(80, crect.height - 40)));
      }

      var nodes = readNodes(canvas);
      var pinned = null;
      nodes.forEach(function (n) { if (n.el === dragging.card) pinned = n; });
      if (!pinned) {
        dragging.card.style.left = x + "px";
        dragging.card.style.top = y + "px";
        fitCanvas(canvas, readNodes(canvas), dragging.card);
        return;
      }

      var dx = x - pinned.x;
      var dy = y - pinned.y;
      pinned.x = x;
      pinned.y = y;
      // Only shove neighbors while staying inside the same section
      if (canvas === dragging.originCanvas) {
        followPinned(nodes, pinned, dx, dy);
        var k;
        for (k = 0; k < 5; k++) stepForces(nodes, pinned.el, W, { pad: 12, attract: false });
      }
      applyNodes(nodes);
      fitCanvas(canvas, nodes, dragging.card);
      dragging.lastX = pinned.x;
      dragging.lastY = pinned.y;
    }

    function endDrag(e) {
      if (!dragging) return;
      if (e && activePointerId != null && e.pointerId !== activePointerId) return;
      var card = dragging.card;
      var canvas = dragging.canvas;
      var origin = dragging.originCanvas;
      clearDropTargets(grid);
      card.classList.remove("is-dragging");
      queryCards(canvas).forEach(function (c) { c.classList.remove("is-relating"); });
      if (origin && origin !== canvas) {
        queryCards(origin).forEach(function (c) { c.classList.remove("is-relating"); });
        settleCanvas(origin, null);
      }
      settleCanvas(canvas, card);
      dragging = null;
      activePointerId = null;
      document.removeEventListener("pointermove", onMove, true);
      document.removeEventListener("pointerup", endDrag, true);
      document.removeEventListener("pointercancel", endDrag, true);
    }

    grid.addEventListener("pointerdown", function (e) {
      if (e.button && e.button !== 0) return;
      if (e.target.closest("input, button, a, label, [contenteditable]")) return;
      var card = e.target.closest(".card");
      if (!card || !grid.contains(card)) return;
      var canvas = card.closest(".grid-section-cards");
      if (!canvas) return;
      var home = canvas.closest(".grid-section");
      if (home && home.classList.contains("is-solo")) liftColumnCard(card, canvas);
      if (dragging) endDrag(null);
      var rect = card.getBoundingClientRect();
      dragging = {
        card: card,
        canvas: canvas,
        originCanvas: canvas,
        dx: e.clientX - rect.left,
        dy: e.clientY - rect.top,
        lastX: parseFloat(card.style.left) || 0,
        lastY: parseFloat(card.style.top) || 0
      };
      activePointerId = e.pointerId;
      card.classList.add("is-dragging");
      queryCards(canvas).forEach(function (c) {
        if (c !== card) c.classList.add("is-relating");
      });
      card.style.zIndex = String(++zTop);
      // No setPointerCapture — moving the card between sections breaks capture
      // and left later drags dead until refresh.
      document.addEventListener("pointermove", onMove, true);
      document.addEventListener("pointerup", endDrag, true);
      document.addEventListener("pointercancel", endDrag, true);
      e.preventDefault();
    });
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
    applySavedSections(grid);
    forcePairedCards(grid);
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
