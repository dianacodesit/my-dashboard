(function(){
  if (window.__navSharedWired) return;
  window.__navSharedWired = 1;

  var STORE = 'nav_page_layout_v1';
  var LINKS = [
    { href: 'index.html', label: 'home', group: 'top' },
    { href: 'today.html', label: 'today', group: 'wip' },
    { href: 'tasks-obsidian-v1127.html', label: 'taskboard', group: 'wip' },
    { href: 'identity.html', label: 'identity', group: 'wip' },
    { href: 'goals.html', label: 'goals', group: 'wip' },
    { href: 'projects.html', label: 'projects', group: 'wip' },
    { href: 'lifestyle.html', label: 'lifestyle', group: 'wip' },
    { href: 'planner.html', label: 'timelines', group: 'main' },
    { href: 'accomplishments.html', label: 'accomplishments', group: 'main' },
    { href: 'striving.html', label: 'striving', group: 'main' },
    { href: 'deen.html', label: 'deen', group: 'main' },
    { href: 'duaa.html', label: "Dua'a", group: 'main' },
    { href: 'dimensions.html', label: 'dimensions', group: 'main' },
    { href: 'grids.html', label: 'grids', group: 'main' },
    { href: 'everything.html', label: 'everything', group: 'main' },
    { href: 'dashboard.html', label: 'dashboard', group: 'main' },
    { href: 'brain-dump.html', label: 'brain dump', group: 'main' },
    { href: 'adhd.html', label: 'ADHD / neurodiversity', group: 'main' },
    { href: 'research-proposals.html', label: 'research proposals', group: 'main' },
    { href: 'curriculum-vitae.html', label: 'Curriculum Vitae', group: 'main' },
    { href: 'business-ideas.html', label: 'business ideas', group: 'main' },
    { href: 'power-opportunities.html', label: 'power opportunities', group: 'main' },
    { href: 'quantum-consciousness.html', label: 'quantum consciousness', group: 'main' },
    { href: 'priming.html', label: 'priming & prompting', group: 'main' },
    { href: 'abundance.html', label: 'abundance economics', group: 'main' },
    { href: 'parallel-timelines.html', label: 'parallel timelines', group: 'main' },
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
  function saveLayout(){
    var out = [];
    document.querySelectorAll('#nav-sidebar .nav-bucket').forEach(function(bucket){
      var group = bucket.getAttribute('data-group');
      bucket.querySelectorAll(':scope > nav a').forEach(function(a){
        out.push({ href: a.getAttribute('href'), group: group });
      });
    });
    try { localStorage.setItem(STORE, JSON.stringify(out)); } catch (e) {}
  }
  function resolvedLinks(){
    var byHref = {};
    LINKS.forEach(function(x){
      byHref[x.href] = { href: x.href, label: x.label, group: x.group };
    });
    var saved = loadLayout();
    var seen = {};
    var ordered = [];
    saved.forEach(function(s){
      if (!s || !byHref[s.href] || seen[s.href]) return;
      if (s.group) byHref[s.href].group = s.group;
      ordered.push(byHref[s.href]);
      seen[s.href] = 1;
    });
    LINKS.forEach(function(x){
      if (!seen[x.href]) ordered.push(byHref[x.href]);
    });
    return ordered;
  }
  function aTag(item, cur){
    var cls = fileOf(item.href) === cur ? ' class="current"' : '';
    return '<a href="'+item.href+'"'+cls+' draggable="false">'+item.label+'</a>';
  }
  function linksFor(group, items, cur){
    return items.filter(function(x){ return x.group === group; })
      .map(function(x){ return aTag(x, cur); }).join('');
  }
  function sidebarInner(cur){
    var items = resolvedLinks();
    var html = '<button aria-label="close menu" id="nav-close" type="button">×</button>';
    GROUPS.forEach(function(g){
      var nav = '<nav>' + linksFor(g.id, items, cur) + '</nav>';
      if (g.details) {
        var inGroup = items.some(function(x){
          return x.group === g.id && fileOf(x.href) === cur;
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
      '#nav-sidebar nav a.is-dragging { opacity: 0.35; }' +
      '#nav-sidebar nav a.is-insert { box-shadow: inset 0 2px 0 #8a9e85; }' +
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
  }

  function wireDrag(sidebar){
    var ghost = null;
    var dragging = null;
    var started = false;
    var moved = false;
    var startX = 0;
    var startY = 0;
    function clearMarks(){
      sidebar.querySelectorAll('.is-drop, .is-insert').forEach(function(el){
        el.classList.remove('is-drop', 'is-insert');
      });
    }
    function bucketAt(x, y){
      var el = document.elementFromPoint(x, y);
      return el && el.closest ? el.closest('#nav-sidebar .nav-bucket') : null;
    }
    function linkAt(x, y){
      var el = document.elementFromPoint(x, y);
      var a = el && el.closest ? el.closest('#nav-sidebar nav a') : null;
      return a && a !== dragging ? a : null;
    }
    function endDrag(x, y){
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp);
      document.removeEventListener('pointercancel', onUp);
      if (ghost && ghost.parentNode) ghost.parentNode.removeChild(ghost);
      ghost = null;
      var src = dragging;
      dragging = null;
      if (!src) return;
      src.classList.remove('is-dragging');
      if (!started) return;
      var bucket = bucketAt(x, y);
      var before = linkAt(x, y);
      clearMarks();
      if (!bucket) return;
      var nav = bucket.querySelector(':scope > nav');
      if (!nav) return;
      if (before && before.parentNode === nav) nav.insertBefore(src, before);
      else nav.appendChild(src);
      var details = bucket.closest('details');
      if (details) details.open = true;
      saveLayout();
    }
    function onMove(e){
      if (!dragging) return;
      var dx = e.clientX - startX;
      var dy = e.clientY - startY;
      if (!started && (dx * dx + dy * dy) < 64) return;
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
      var bucket = bucketAt(e.clientX, e.clientY);
      if (bucket) {
        bucket.classList.add('is-drop');
        if (bucket.tagName === 'DETAILS') bucket.open = true;
      }
      var before = linkAt(e.clientX, e.clientY);
      if (before) before.classList.add('is-insert');
    }
    function onUp(e){
      endDrag(e.clientX, e.clientY);
    }
    sidebar.addEventListener('pointerdown', function(e){
      if (e.button !== 0) return;
      var a = e.target.closest('#nav-sidebar nav a');
      if (!a) return;
      dragging = a;
      started = false;
      moved = false;
      startX = e.clientX;
      startY = e.clientY;
      document.addEventListener('pointermove', onMove);
      document.addEventListener('pointerup', onUp);
      document.addEventListener('pointercancel', onUp);
    });
    sidebar.addEventListener('click', function(e){
      if (!moved) return;
      var a = e.target.closest('#nav-sidebar nav a');
      if (!a) return;
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
      sidebar.dataset.dragWired = '1';
      wireDrag(sidebar);
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setup);
  else setup();
})();
