/* Wrap grids cards into sections and scatter them freeform. */
(function () {
  var POS_KEY = "grids_freeform_pos_v1";
  var zTop = 6;

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

  function scatterCanvas(canvas, saved) {
    var cards = Array.from(canvas.querySelectorAll(":scope > .card, :scope > .collapsible-content > .card"));
    if (!cards.length) {
      canvas.style.minHeight = "0px";
      canvas.style.height = "0px";
      return;
    }
    var W = Math.max(canvas.clientWidth || 0, 320);
    var placed = [];
    var maxB = 0;
    cards.forEach(function (card, i) {
      var id = card.id || ("anon-" + i);
      var rnd = rng(hash(id));
      var prev = saved[id];
      var w = prev && prev.w ? prev.w : (248 + Math.floor(rnd() * 80));
      if (W < 420) w = Math.min(w, W - 16);
      card.style.width = w + "px";
      card.style.position = "absolute";
      var h = Math.max(card.offsetHeight || 180, 140);
      var rot = prev && typeof prev.r === "number" ? prev.r : (rnd() * 8.4) - 3.6;
      var x, y, ok = false;
      if (prev && typeof prev.x === "number" && typeof prev.y === "number") {
        x = prev.x;
        y = prev.y;
        ok = true;
      } else {
        var spreadH = Math.max(h + 48, 90 + cards.length * 88);
        for (var t = 0; t < 70; t++) {
          x = 8 + rnd() * Math.max(12, W - w - 16);
          y = 10 + rnd() * spreadH;
          if (!overlaps({ x: x, y: y, w: w, h: h }, placed, 16)) { ok = true; break; }
        }
        if (!ok) {
          x = 12 + (i % 3) * Math.max(40, (W - w - 24) / 2) + (rnd() * 36 - 18);
          y = maxB + 20 + rnd() * 18;
        }
      }
      x = Math.max(4, x);
      y = Math.max(6, y);
      card.style.left = x + "px";
      card.style.top = y + "px";
      card.style.setProperty("--card-rot", rot.toFixed(2) + "deg");
      saved[id] = { x: x, y: y, r: rot, w: w };
      placed.push({ x: x, y: y, w: w, h: h });
      maxB = Math.max(maxB, y + h);
    });
    canvas.style.height = (maxB + 32) + "px";
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
        dy: e.clientY - rect.top
      };
      card.classList.add("is-dragging");
      card.style.zIndex = String(++zTop);
      try { card.setPointerCapture(e.pointerId); } catch (err) {}
      e.preventDefault();
    });
    grid.addEventListener("pointermove", function (e) {
      if (!dragging) return;
      var crect = dragging.canvas.getBoundingClientRect();
      var x = e.clientX - crect.left - dragging.dx;
      var y = e.clientY - crect.top - dragging.dy;
      x = Math.max(-20, x);
      y = Math.max(0, y);
      dragging.card.style.left = x + "px";
      dragging.card.style.top = y + "px";
      var bottom = y + dragging.card.offsetHeight + 28;
      if (bottom > dragging.canvas.offsetHeight) dragging.canvas.style.height = bottom + "px";
    });
    function endDrag(e) {
      if (!dragging) return;
      var card = dragging.card;
      var canvas = dragging.canvas;
      card.classList.remove("is-dragging");
      var saved = loadPos();
      var id = card.id;
      if (id) {
        saved[id] = {
          x: parseFloat(card.style.left) || 0,
          y: parseFloat(card.style.top) || 0,
          r: parseFloat((card.style.getPropertyValue("--card-rot") || "0").replace("deg", "")) || 0,
          w: parseFloat(card.style.width) || card.offsetWidth
        };
        savePos(saved);
      }
      var maxB = 0;
      Array.from(canvas.querySelectorAll(".card")).forEach(function (c) {
        maxB = Math.max(maxB, (parseFloat(c.style.top) || 0) + c.offsetHeight);
      });
      canvas.style.height = (maxB + 32) + "px";
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
