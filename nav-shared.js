(function(){
  if (window.__navSharedWired) return;
  window.__navSharedWired = 1;

  var STORE = 'nav_page_layout_v1';
  var ARCHIVED_PAGES_KEY = 'btm_archived_pages_v1';
  var ARCHIVE_INDEX = {
    'archived-pages.html': 1,
    'archived-sections.html': 1
  };
  var LINKS = [
    { href: 'index.html', label: 'start over', group: 'top' },
    { href: 'narrative.html', label: 'narrative', group: 'top', parent: 'index.html' },
    { href: 'today.html', label: 'today', group: 'wip' },

    { href: 'tasks-obsidian-v1127.html', label: 'taskboard', group: 'wip' },
    { href: 'identity.html', label: 'identity', group: 'wip' },
    { href: 'goals.html', label: 'goals', group: 'wip' },
    { href: 'projects.html', label: 'projects', group: 'wip' },
    { href: 'lifestyle.html', label: 'lifestyle', group: 'wip' },
    { href: 'planner.html', label: 'timelapses', group: 'main' },
    { href: 'accomplishments.html', label: 'accomplishments', group: 'main' },
    { href: 'striving.html', label: 'striving', group: 'main' },
    { href: 'deen.html', label: 'deen', group: 'main' },
    { href: 'quran.html', label: 'Quran', group: 'main', parent: 'deen.html' },
    { href: 'sabr.html', label: 'sabr', group: 'main', parent: 'quran.html' },
    { href: 'shukr.html', label: 'shukr', group: 'main', parent: 'quran.html' },
    { href: 'duaa.html', label: "Dua'a", group: 'main', parent: 'deen.html' },
    { href: 'tauba.html', label: 'Tauba', group: 'main', parent: 'deen.html' },
    { href: 'surrender.html', label: 'Surrender', group: 'main', parent: 'deen.html' },
    { href: 'al-ghayb.html', label: 'al-Ghayb', group: 'main', parent: 'deen.html' },
    { href: 'qudra.html', label: 'Qudra', group: 'main', parent: 'deen.html' },
    { href: 'lataif-al-sitta.html', label: 'Lataif-al Sitta', group: 'main', parent: 'qudra.html' },
    { href: 'dimensions.html', label: 'dimensions', group: 'main' },
    { href: 'grids.html', label: 'grids', group: 'main' },
    { href: 'everything.html', label: 'everything', group: 'main' },
    { href: 'prototype.html', label: 'prototype', group: 'main' },
    { href: 'dashboard.html', label: 'dashboard', group: 'main' },
    { href: 'brain-dump.html', label: 'brain dump', group: 'main' },
    { href: 'adhd.html', label: 'ADHD / neurodiversity', group: 'main' },
    { href: 'pepperdine.html', label: 'Pepperdine', group: 'main' },
    { href: 'research-proposals.html', label: 'research proposals', group: 'main', parent: 'pepperdine.html' },
    { href: 'diana-jundi.html', label: 'Diana Jundi', group: 'main' },
    { href: 'curriculum-vitae.html', label: 'Curriculum Vitae', group: 'main', parent: 'diana-jundi.html' },
    { href: 'business-ideas.html', label: 'business ideas', group: 'main' },
    { href: 'power-opportunities.html', label: 'power opportunities', group: 'main' },
    { href: 'victory-docket.html', label: 'victory docket', group: 'main' },
    { href: 'quantum-consciousness.html', label: 'quantum consciousness', group: 'main' },
    { href: 'delusion.html', label: 'delusion', group: 'main', parent: 'quantum-consciousness.html' },
    { href: 'attraction.html', label: 'attraction', group: 'main', parent: 'quantum-consciousness.html' },
    { href: 'failures.html', label: 'failures', group: 'main', parent: 'quantum-consciousness.html' },
    { href: 'transmutation.html', label: 'transmutation', group: 'main', parent: 'quantum-consciousness.html' },
    { href: 'alchemy.html', label: 'alchemy', group: 'main', parent: 'quantum-consciousness.html' },
    { href: 'manifestation.html', label: 'manifestation', group: 'main', parent: 'quantum-consciousness.html' },
    { href: 'self.html', label: 'Self', group: 'main' },
    { href: 'center.html', label: 'center', group: 'main', parent: 'self.html' },
    { href: 'priming.html', label: 'priming & prompting', group: 'main' },
    { href: 'prosperity.html', label: 'prosperity', group: 'main' },
    { href: 'banking-matters.html', label: 'banking matters', group: 'main', parent: 'prosperity.html' },
    { href: 'parallel-timelines.html', label: 'parallel timelines', group: 'main' },
    { href: '2030.html', label: '2030', group: 'main' },
    { href: 'archived-pages.html', label: 'pages', group: 'archived' },
    { href: 'archived-sections.html', label: 'sections', group: 'archived' },
    { href: 'palettes.html', label: 'color palettes', group: 'design' },
    { href: 'backgrounds.html', label: 'background images', group: 'design' },
    { href: 'colors.html', label: 'individual colors', group: 'design' },
    { href: 'fonts.html', label: 'editorial fonts', group: 'design' },
    { href: 'flow-fonts.html', label: 'cursive flow fonts', group: 'design' },
    { href: 'deadline-fonts.html', label: 'deadline pill fonts', group: 'design' },
    { href: 'flow-styles.html', label: 'flow chart designs', group: 'design' },
    { href: 'arrows.html', label: 'arrow formations', group: 'design' },
    { href: 'transitions.html', label: 'transition styles', group: 'design' }
  ];
  var GROUPS = [
    { id: 'top', title: '' },
    { id: 'main', title: 'main' },
    { id: 'wip', title: 'work in progress', details: true },
    { id: 'archived', title: 'archived', details: true },
    { id: 'design', title: 'design previews', details: true }
  ];

  function fileOf(href){
    return String(href || '').split('/').pop();
  }
  function currentFile(){
    var path = (window.location.pathname || '').split('/').pop();
    return path || 'index.html';
  }
  function loadLayout(){
    try {
      var raw = JSON.parse(localStorage.getItem(STORE) || '[]');
      return Array.isArray(raw) ? raw : [];
    } catch (e) { return []; }
  }
  function loadArchivedPages(){
    try {
      var raw = JSON.parse(localStorage.getItem(ARCHIVED_PAGES_KEY) || '[]');
      return Array.isArray(raw) ? raw : [];
    } catch (e) { return []; }
  }
  function saveArchivedPages(list){
    try { localStorage.setItem(ARCHIVED_PAGES_KEY, JSON.stringify(list || [])); } catch (e) {}
  }
  function archivedHrefSet(){
    var set = {};
    loadArchivedPages().forEach(function(it){
      if (!it || !it.href) return;
      set[fileOf(it.href)] = 1;
      set[it.href] = 1;
    });
    return set;
  }
  function isArchiveIndex(href){
    return !!ARCHIVE_INDEX[fileOf(href)];
  }
  function archiveNavPage(href, label){
    href = fileOf(href);
    if (!href || isArchiveIndex(href)) return false;
    var byHref = byHrefMap();
    var meta = byHref[href];
    var list = loadArchivedPages().filter(function(it){
      return it && it.href && fileOf(it.href) !== href;
    });
    list.unshift({
      href: href,
      label: label || (meta && meta.label) || href,
      archivedAt: Date.now()
    });
    saveArchivedPages(list);
    // Drop from live layout; clear any parent pointers at this href.
    var layout = resolvedLinks().map(function(it){
      return { href: it.href, group: it.group, parent: it.parent || null };
    }).filter(function(it){
      return fileOf(it.href) !== href;
    }).map(function(it){
      if (it.parent && fileOf(it.parent) === href) it.parent = null;
      return it;
    });
    try { localStorage.setItem(STORE, JSON.stringify(layout)); } catch (e) {}
    return true;
  }
  window.__archiveNavPage = archiveNavPage;
  window.__rebuildNav = function(){ rebuildNav(); };
  function byHrefMap(){
    var byHref = {};
    LINKS.forEach(function(x){
      byHref[x.href] = { href: x.href, label: x.label, group: x.group, parent: x.parent || null };
    });
    return byHref;
  }
  function saveLayout(){
    var byHref = byHrefMap();
    var out = [];
    var seen = {};
    document.querySelectorAll('#nav-sidebar .nav-bucket').forEach(function(bucket){
      var group = bucket.getAttribute('data-group');
      var nav = bucket.querySelector(':scope > nav');
      if (!nav) return;
      function walk(nodeList, parentHref){
        [].slice.call(nodeList).forEach(function(node){
          if (node.matches && node.matches('details.nav-parent')) {
            var pa = node.querySelector(':scope > summary a');
            if (!pa) return;
            var href = pa.getAttribute('href');
            if (!href || seen[href]) return;
            seen[href] = 1;
            out.push({ href: href, group: group, parent: parentHref || null });
            var kids = node.querySelector(':scope > .nav-kids');
            if (kids) walk(kids.children, href);
            return;
          }
          if (node.tagName === 'A') {
            var href2 = node.getAttribute('href');
            if (!href2 || seen[href2]) return;
            seen[href2] = 1;
            out.push({ href: href2, group: group, parent: parentHref || null });
          }
        });
      }
      walk(nav.children, null);
    });
    // Keep any known links not currently rendered (safety).
    var archived = archivedHrefSet();
    Object.keys(byHref).forEach(function(href){
      if (seen[href]) return;
      if (archived[href] || archived[fileOf(href)]) return;
      out.push({ href: href, group: byHref[href].group, parent: byHref[href].parent || null });
    });
    try { localStorage.setItem(STORE, JSON.stringify(out)); } catch (e) {}
  }
  function resolvedLinks(){
    var byHref = byHrefMap();
    var archived = archivedHrefSet();
    var saved = loadLayout();
    var order = [];
    var seen = {};
    saved.forEach(function(s){
      if (!s || !byHref[s.href] || seen[s.href]) return;
      if (archived[s.href] || archived[fileOf(s.href)]) return;
      if (s.group) byHref[s.href].group = s.group;
      if ('parent' in s) byHref[s.href].parent = s.parent || null;
      order.push(s.href);
      seen[s.href] = 1;
    });
    LINKS.forEach(function(x){
      if (archived[x.href] || archived[fileOf(x.href)]) return;
      if (!seen[x.href]) {
        order.push(x.href);
        seen[x.href] = 1;
      }
    });
    // Prevent cycles: if parent chain loops, clear parent.
    order.forEach(function(href){
      var item = byHref[href];
      var guard = {};
      var p = item.parent;
      while (p) {
        if (p === href || guard[p] || archived[p] || archived[fileOf(p)]) { item.parent = null; break; }
        guard[p] = 1;
        p = byHref[p] ? byHref[p].parent : null;
      }
    });
    return order.map(function(h){ return byHref[h]; });
  }
  function aTag(item, cur, depth){
    var cls = [];
    if (depth > 0) cls.push('nav-sub');
    if (depth > 1) cls.push('nav-sub-2');
    if (depth > 2) cls.push('nav-sub-3');
    if (fileOf(item.href) === cur) cls.push('current');
    var attr = cls.length ? ' class="'+cls.join(' ')+'"' : '';
    return '<a href="'+item.href+'"'+attr+' draggable="false" data-nav-href="'+item.href+'">'+item.label+'</a>';
  }
  function childrenOf(parentHref, group, items){
    return items.filter(function(x){
      return x.group === group && x.parent === parentHref;
    });
  }
  function branchContainsCurrent(item, group, items, cur){
    if (fileOf(item.href) === cur) return true;
    return childrenOf(item.href, group, items).some(function(child){
      return branchContainsCurrent(child, group, items, cur);
    });
  }
  function linksFor(group, items, cur){
    var html = '';
    function renderBranch(item, depth){
      var kids = childrenOf(item.href, group, items);
      if (kids.length) {
        var open = branchContainsCurrent(item, group, items, cur);
        html += '<details class="nav-parent" data-depth="'+depth+'" data-nav-href="'+item.href+'"'+(open?' open':'')+'>';
        html += '<summary class="nav-parent-sum">'+aTag(item, cur, depth)+'</summary>';
        html += '<div class="nav-kids">';
        kids.forEach(function(child){ renderBranch(child, depth + 1); });
        html += '</div></details>';
        return;
      }
      html += aTag(item, cur, depth);
    }
    items.filter(function(x){ return x.group === group && !x.parent; }).forEach(function(item){
      renderBranch(item, 0);
    });
    return html;
  }
  function sidebarInner(cur){
    var items = resolvedLinks();
    var html = '<button aria-label="close menu" id="nav-close" type="button">×</button>';
    GROUPS.forEach(function(g){
      var nav = '<nav>' + linksFor(g.id, items, cur) + '</nav>';
      if (g.details) {
        var inGroup = items.some(function(x){
          return x.group === g.id && (fileOf(x.href) === cur || branchContainsCurrent(x, g.id, items, cur));
        });
        html += '<details class="nav-group nav-bucket" data-group="'+g.id+'"'+(inGroup?' open':'')+'>' +
          '<summary class="nav-section">'+g.title+'</summary>' + nav + '</details>';
        return;
      }
      html += '<section class="nav-bucket" data-group="'+g.id+'">';
      if (g.title) html += '<div class="nav-section">'+g.title+'</div>';
      html += nav + '</section>';
    });
    return html;
  }
  function ensureStyles(){
    if (document.getElementById('nav-drag-css')) return;
    var s = document.createElement('style');
    s.id = 'nav-drag-css';
    s.textContent =
      '#nav-sidebar .nav-bucket nav { min-height: 28px; }' +
      '#nav-sidebar .nav-bucket nav:empty::after { content: "drop a page here"; display: block; padding: 8px 24px 12px; font-family: "Newsreader", Georgia, serif; font-style: italic; font-size: 14px; color: rgba(243,230,208,0.7); }' +
      '#nav-sidebar .nav-bucket.is-drop { background: rgba(138,158,133,0.12); }' +
      '#nav-sidebar nav a { cursor: grab; }' +
      '#nav-sidebar details.nav-parent { display: block; }' +
      '#nav-sidebar details.nav-parent > summary.nav-parent-sum { list-style: none; cursor: pointer; display: flex; align-items: center; gap: 0; }' +
      '#nav-sidebar details.nav-parent > summary.nav-parent-sum::-webkit-details-marker { display: none; }' +
      '#nav-sidebar details.nav-parent > summary.nav-parent-sum::before { content: "\\25B8"; flex: 0 0 auto; width: 14px; margin: 0 2px 0 10px; font-size: 9px; opacity: 0.55; transition: transform 0.2s ease; color: #f3e6d0; }' +
      '#nav-sidebar details.nav-parent[open] > summary.nav-parent-sum::before { transform: rotate(90deg); }' +
      '#nav-sidebar details.nav-parent > summary.nav-parent-sum > a { flex: 1 1 auto; padding-left: 8px !important; }' +
      '#nav-sidebar details.nav-parent[data-depth="1"] > summary.nav-parent-sum::before { margin-left: 28px; }' +
      '#nav-sidebar details.nav-parent[data-depth="1"] > summary.nav-parent-sum > a { padding-left: 8px !important; }' +
      '#nav-sidebar .nav-kids { display: flex; flex-direction: column; }' +
      '#nav-sidebar nav a.nav-sub { cursor: grab; padding-left: 38px !important; font-size: 15px !important; font-style: italic; opacity: 0.92; }' +
      '#nav-sidebar nav a.nav-sub:hover { opacity: 1; }' +
      '#nav-sidebar nav a.nav-sub-2 { padding-left: 54px !important; font-size: 14px !important; opacity: 0.88; }' +
      '#nav-sidebar nav a.nav-sub-2:hover { opacity: 1; }' +
      '#nav-sidebar nav a.nav-sub-3 { padding-left: 70px !important; font-size: 13px !important; opacity: 0.84; }' +
      '#nav-sidebar nav a.is-dragging { opacity: 0.35; }' +
      '#nav-sidebar nav a.is-insert { box-shadow: inset 0 2px 0 #8a9e85; }' +
      '#nav-sidebar nav a.is-nest-target, #nav-sidebar details.nav-parent.is-nest-target > summary a { outline: 1px solid rgba(196,168,130,0.85); background: rgba(138,158,133,0.22) !important; box-shadow: inset 0 0 0 1px rgba(243,230,208,0.25); }' +
      'html body #hamburger-menu, html body.enh-dark #hamburger-menu { background: transparent !important; box-shadow: none !important; }' +
      'html body #hamburger-menu span, html body.enh-dark #hamburger-menu span { box-shadow: none !important; }' +
      'html body #nav-sidebar, html body.enh-dark #nav-sidebar { background: linear-gradient(180deg, rgba(48, 28, 38, 0.38) 0%, rgba(32, 20, 28, 0.32) 100%) !important; box-shadow: 8px 0 28px rgba(8, 4, 2, 0.28) !important; border-right: 1px solid rgba(243, 230, 208, 0.18) !important; backdrop-filter: blur(5px) saturate(1.05) !important; -webkit-backdrop-filter: blur(5px) saturate(1.05) !important; }' +
      'html body #nav-sidebar nav a, html body.enh-dark #nav-sidebar nav a { color: #f3e6d0 !important; text-shadow: 0 1px 2px rgba(20,12,6,0.5), 0 2px 8px rgba(20,12,6,0.3); }' +
      'html body #nav-sidebar h2 { display: none !important; }' +
      '.nav-drag-ghost { position: fixed; z-index: 200040; pointer-events: none; padding: 8px 16px; background: #F5F0E8; border: 1px solid rgba(196,168,130,0.55); box-shadow: 0 10px 24px rgba(20,12,6,0.18); font-family: "Newsreader", Georgia, serif; font-size: 17px; color: #3a3530; white-space: nowrap; }';
    document.head.appendChild(s);
  }
  function ensureDom(){
    ensureStyles();
    var cur = currentFile();
    var sidebar = document.getElementById('nav-sidebar');
    if (!document.getElementById('hamburger-menu')) {
      var wrap = document.createElement('div');
      wrap.id = 'nav-root';
      wrap.innerHTML =
        '<button aria-label="open menu" id="hamburger-menu" type="button"><span></span><span></span><span></span></button>' +
        '<div id="nav-overlay"></div>' +
        '<aside aria-hidden="true" id="nav-sidebar"></aside>';
      document.body.insertBefore(wrap, document.body.firstChild);
      sidebar = document.getElementById('nav-sidebar');
    }
    if (!sidebar) return;
    var wasOpen = sidebar.classList.contains('open');
    sidebar.innerHTML = sidebarInner(cur);
    if (wasOpen) sidebar.classList.add('open');
    // Clicking the page link inside summary should navigate, not only toggle.
    sidebar.querySelectorAll('details.nav-parent > summary a').forEach(function(a){
      a.addEventListener('click', function(e){
        // Allow toggle via caret area; link itself navigates.
        e.stopPropagation();
      });
    });
  }

  function rebuildNav(){
    var sidebar = document.getElementById('nav-sidebar');
    if (!sidebar) return;
    var wasOpen = sidebar.classList.contains('open');
    ensureDom();
    if (wasOpen) {
      sidebar.classList.add('open');
      sidebar.setAttribute('aria-hidden', 'false');
    }
    sidebar.dataset.dragWired = '';
    wireDrag(sidebar);
    sidebar.dataset.dragWired = '1';
    var cur = currentFile();
    document.querySelectorAll('#nav-sidebar nav a').forEach(function(a){
      a.classList.toggle('current', fileOf(a.getAttribute('href')) === cur);
    });
  }

  function wireDrag(sidebar){
    if (sidebar.dataset.dragWired === '1') return;
    var ghost = null;
    var dragging = null;
    var started = false;
    var moved = false;
    var startX = 0;
    var startY = 0;
    var activePointer = null;
    function clearMarks(){
      sidebar.querySelectorAll('.is-drop, .is-insert, .is-nest-target').forEach(function(el){
        el.classList.remove('is-drop', 'is-insert', 'is-nest-target');
      });
    }
    function bucketAt(x, y){
      var el = document.elementFromPoint(x, y);
      return el && el.closest ? el.closest('#nav-sidebar .nav-bucket') : null;
    }
    function linkAt(x, y, exclude){
      var el = document.elementFromPoint(x, y);
      var a = el && el.closest ? el.closest('#nav-sidebar nav a') : null;
      var skip = exclude || dragging;
      return a && a !== skip ? a : null;
    }
    function isDescendantHref(parentHref, maybeChildHref, srcEl){
      var items = resolvedLinks();
      var by = {};
      items.forEach(function(it){ by[it.href] = it; });
      var p = maybeChildHref;
      var guard = 0;
      while (p && guard++ < 20) {
        if (p === parentHref) return true;
        p = by[p] ? by[p].parent : null;
      }
      // Also: if dragging a parent, can't nest into its current child.
      p = parentHref;
      guard = 0;
      while (p && guard++ < 20) {
        var item = by[p];
        if (!item) break;
        if (item.parent === maybeChildHref) return true;
        // walk up from parentHref — check if maybeChild is ancestor of dragging
        break;
      }
      // If nest target is inside dragging's open branch in DOM:
      var srcNode = srcEl || dragging;
      if (srcNode) {
        var branch = srcNode.closest('details.nav-parent');
        var targetA = sidebar.querySelector('a[data-nav-href="'+maybeChildHref+'"], a[href="'+maybeChildHref+'"]');
        if (branch && targetA && branch.contains(targetA) && targetA !== srcNode) return true;
      }
      return false;
    }
    function nestTargetAt(x, y, srcEl){
      var src = srcEl || dragging;
      var a = linkAt(x, y, src);
      if (!a || !src) return null;
      var srcHref = src.getAttribute('href');
      var dstHref = a.getAttribute('href');
      if (!srcHref || !dstHref || srcHref === dstHref) return null;
      if (isDescendantHref(srcHref, dstHref, src)) return null;
      return a;
    }
    function endDrag(x, y){
      document.removeEventListener('pointermove', onMove, true);
      document.removeEventListener('pointerup', onUp, true);
      document.removeEventListener('pointercancel', onUp, true);
      if (dragging && activePointer != null) {
        try { dragging.releasePointerCapture(activePointer); } catch (err) {}
      }
      activePointer = null;
      if (ghost && ghost.parentNode) ghost.parentNode.removeChild(ghost);
      ghost = null;
      var src = dragging;
      if (!src) {
        dragging = null;
        return;
      }
      src.classList.remove('is-dragging');
      if (!started) {
        dragging = null;
        return;
      }
      // Resolve nest/bucket WHILE src is still known — nestTargetAt needs the
      // dragged link so highlight-on-move and commit-on-drop stay in sync.
      var nest = nestTargetAt(x, y, src);
      var bucket = bucketAt(x, y);
      clearMarks();
      dragging = null;
      if (nest) {
        // Reparent: nest src under nest target.
        var layout = loadLayout();
        var by = {};
        resolvedLinks().forEach(function(it){ by[it.href] = { href: it.href, group: it.group, parent: it.parent || null }; });
        layout.forEach(function(s){
          if (!s || !s.href || !by[s.href]) return;
          if (s.group) by[s.href].group = s.group;
          if ('parent' in s) by[s.href].parent = s.parent || null;
        });
        var srcHref = src.getAttribute('href');
        var dstHref = nest.getAttribute('href');
        if (by[srcHref] && by[dstHref]) {
          by[srcHref].parent = dstHref;
          by[srcHref].group = by[dstHref].group;
          var out = Object.keys(by).map(function(h){ return by[h]; });
          try { localStorage.setItem(STORE, JSON.stringify(out)); } catch (e) {}
          rebuildNav();
        }
        return;
      }
      if (!bucket) return;
      var nav = bucket.querySelector(':scope > nav');
      if (!nav) return;
      // Drop into bucket as a top-level page (unnest) / reorder among top-level.
      var srcHref = src.getAttribute('href');
      var layout2 = resolvedLinks().map(function(it){
        return { href: it.href, group: it.group, parent: it.parent || null };
      });
      var before = linkAt(x, y, src);
      // Compute new order of top-level in this bucket only; keep nested parents.
      layout2.forEach(function(it){
        if (it.href === srcHref) {
          it.group = bucket.getAttribute('data-group');
          it.parent = null;
        }
      });
      // Reorder: move src among top-level entries of this group.
      var tops = layout2.filter(function(it){ return it.group === bucket.getAttribute('data-group') && !it.parent && it.href !== srcHref; });
      var srcItem = layout2.filter(function(it){ return it.href === srcHref; })[0];
      var others = layout2.filter(function(it){ return it.href !== srcHref; });
      var insertAt = others.length;
      if (before) {
        var bh = before.getAttribute('href');
        // If before is nested, use its topmost ancestor in this group.
        var map = {};
        layout2.forEach(function(it){ map[it.href] = it; });
        var walk = bh;
        while (map[walk] && map[walk].parent) walk = map[walk].parent;
        var idx = tops.findIndex(function(it){ return it.href === walk; });
        if (idx >= 0) {
          tops.splice(idx, 0, srcItem);
        } else {
          tops.push(srcItem);
        }
      } else {
        tops.push(srcItem);
      }
      var nested = others.filter(function(it){ return it.parent; });
      var restGroups = others.filter(function(it){ return it.group !== bucket.getAttribute('data-group') || (!it.parent && it.href !== srcHref); });
      // restGroups already excludes src; tops has new top order for this group.
      var restOtherGroup = others.filter(function(it){ return it.group !== bucket.getAttribute('data-group'); });
      var nestedHere = others.filter(function(it){ return it.group === bucket.getAttribute('data-group') && it.parent; });
      var out2 = restOtherGroup.concat(tops).concat(nestedHere);
      // Deduplicate
      var seen = {};
      out2 = out2.filter(function(it){
        if (!it || seen[it.href]) return false;
        seen[it.href] = 1;
        return true;
      });
      // Ensure every link still present
      layout2.forEach(function(it){
        if (!seen[it.href]) out2.push(it);
      });
      try { localStorage.setItem(STORE, JSON.stringify(out2)); } catch (e) {}
      var details = bucket.closest('details');
      if (details) details.open = true;
      rebuildNav();
    }
    function onMove(e){
      if (!dragging) return;
      if (activePointer != null && e.pointerId !== activePointer) return;
      var dx = e.clientX - startX;
      var dy = e.clientY - startY;
      if (!started && (dx * dx + dy * dy) < 36) return;
      if (!started) {
        started = true;
        moved = true;
        dragging.classList.add('is-dragging');
        ghost = document.createElement('div');
        ghost.className = 'nav-drag-ghost';
        ghost.textContent = dragging.textContent;
        document.body.appendChild(ghost);
      }
      e.preventDefault();
      ghost.style.left = (e.clientX + 10) + 'px';
      ghost.style.top = (e.clientY + 10) + 'px';
      clearMarks();
      var nest = nestTargetAt(e.clientX, e.clientY);
      if (nest) {
        nest.classList.add('is-nest-target');
        var pd = nest.closest('details.nav-parent');
        if (pd) pd.classList.add('is-nest-target');
        return;
      }
      var bucket = bucketAt(e.clientX, e.clientY);
      if (bucket) {
        bucket.classList.add('is-drop');
        if (bucket.tagName === 'DETAILS') bucket.open = true;
      }
      var before = linkAt(e.clientX, e.clientY);
      if (before) before.classList.add('is-insert');
    }
    function onUp(e){
      if (activePointer != null && e.pointerId !== activePointer) return;
      endDrag(e.clientX, e.clientY);
    }
    sidebar.addEventListener('pointerdown', function(e){
      if (e.button !== 0) return;
      // ⌘/Ctrl+click archives — don't start a drag.
      if (e.metaKey || e.ctrlKey) return;
      // Don't start drag from the caret/summary chrome — only from links.
      var a = e.target.closest('#nav-sidebar nav a');
      if (!a) return;
      dragging = a;
      started = false;
      moved = false;
      startX = e.clientX;
      startY = e.clientY;
      activePointer = e.pointerId;
      try { a.setPointerCapture(e.pointerId); } catch (err) {}
      document.addEventListener('pointermove', onMove, true);
      document.addEventListener('pointerup', onUp, true);
      document.addEventListener('pointercancel', onUp, true);
    });
    sidebar.addEventListener('click', function(e){
      var a = e.target.closest('#nav-sidebar nav a');
      if (!a) return;
      if (e.metaKey || e.ctrlKey) {
        e.preventDefault();
        e.stopPropagation();
        if (e.stopImmediatePropagation) e.stopImmediatePropagation();
        var href = a.getAttribute('href') || a.getAttribute('data-nav-href');
        if (archiveNavPage(href, (a.textContent || '').replace(/\s+/g, ' ').trim())) {
          rebuildNav();
        }
        return;
      }
      if (!moved) return;
      e.preventDefault();
      e.stopPropagation();
      moved = false;
    }, true);
  }

  function setup(){
    ensureDom();
    var btn = document.getElementById('hamburger-menu');
    var sidebar = document.getElementById('nav-sidebar');
    var overlay = document.getElementById('nav-overlay');
    var closeBtn = document.getElementById('nav-close');
    if (!btn || !sidebar || !overlay) return;
    function open(){
      sidebar.classList.add('open');
      overlay.classList.add('open');
      sidebar.setAttribute('aria-hidden', 'false');
    }
    function close(){
      sidebar.classList.remove('open');
      overlay.classList.remove('open');
      sidebar.setAttribute('aria-hidden', 'true');
    }
    if (!btn.dataset.wired) {
      btn.dataset.wired = '1';
      btn.addEventListener('click', function(e){
        e.preventDefault();
        e.stopPropagation();
        open();
      }, true);
      overlay.addEventListener('click', close);
      document.addEventListener('keydown', function(e){
        if (e.key === 'Escape' && sidebar.classList.contains('open')) close();
      });
    }
    if (closeBtn && !closeBtn.dataset.wired) {
      closeBtn.dataset.wired = '1';
      closeBtn.addEventListener('click', function(e){
        e.preventDefault();
        e.stopPropagation();
        close();
      }, true);
    }
    var cur = currentFile();
    document.querySelectorAll('#nav-sidebar nav a').forEach(function(a){
      a.classList.toggle('current', fileOf(a.getAttribute('href')) === cur);
    });
    if (!sidebar.dataset.dragWired) {
      wireDrag(sidebar);
      sidebar.dataset.dragWired = '1';
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setup);
  else setup();
})();
