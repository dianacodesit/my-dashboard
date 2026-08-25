(function(){
  if (window.__navSharedWired) return;
  window.__navSharedWired = 1;

  var LINKS = [
    { href: 'today.html', label: 'today', group: 'top' },
    { href: 'tasks-obsidian-v1127.html', label: 'taskboard', group: 'main' },
    { href: 'identity.html', label: 'identity', group: 'main' },
    { href: 'goals.html', label: 'goals', group: 'main' },
    { href: 'projects.html', label: 'projects', group: 'main' },
    { href: 'agenda.html', label: 'agenda', group: 'main' },
    { href: 'everything.html', label: 'everything', group: 'main' },
    { href: 'dashboard.html', label: 'dashboard', group: 'main' },
    { href: 'brain-dump.html', label: 'brain dump', group: 'main' },
    { href: 'palettes.html', label: 'color palettes', group: 'design' },
    { href: 'colors.html', label: 'individual colors', group: 'design' },
    { href: 'fonts.html', label: 'editorial fonts', group: 'design' },
    { href: 'flow-fonts.html', label: 'cursive flow fonts', group: 'design' },
    { href: 'deadline-fonts.html', label: 'deadline pill fonts', group: 'design' },
    { href: 'flow-styles.html', label: 'flow chart designs', group: 'design' },
    { href: 'arrows.html', label: 'arrow formations', group: 'design' },
    { href: 'transitions.html', label: 'transition styles', group: 'design' }
  ];

  function fileOf(href){
    return String(href || '').split('/').pop();
  }
  function currentFile(){
    var path = (window.location.pathname || '').split('/').pop();
    return path || 'dashboard.html';
  }
  function aTag(item, cur){
    var cls = fileOf(item.href) === cur ? ' class="current"' : '';
    return '<a href="'+item.href+'"'+cls+'>'+item.label+'</a>';
  }

  function ensureDom(){
    if (document.getElementById('hamburger-menu')) return;
    var cur = currentFile();
    var top = LINKS.filter(function(x){ return x.group === 'top'; }).map(function(x){ return aTag(x, cur); }).join('');
    var main = LINKS.filter(function(x){ return x.group === 'main'; }).map(function(x){ return aTag(x, cur); }).join('');
    var design = LINKS.filter(function(x){ return x.group === 'design'; }).map(function(x){ return aTag(x, cur); }).join('');
    var html =
      '<button aria-label="open menu" id="hamburger-menu" type="button"><span></span><span></span><span></span></button>' +
      '<div id="nav-overlay"></div>' +
      '<aside aria-hidden="true" id="nav-sidebar">' +
      '<button aria-label="close menu" id="nav-close" type="button">×</button>' +
      '<h2>pages</h2>' +
      '<nav>' + top + '</nav>' +
      '<div class="nav-section">main</div>' +
      '<nav>' + main + '</nav>' +
      '<details class="nav-group">' +
      '<summary class="nav-section">design previews</summary>' +
      '<nav>' + design + '</nav>' +
      '</details>' +
      '</aside>';
    var wrap = document.createElement('div');
    wrap.id = 'nav-root';
    wrap.innerHTML = html;
    document.body.insertBefore(wrap, document.body.firstChild);
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
      btn.addEventListener('click', open);
      if (closeBtn) closeBtn.addEventListener('click', close);
      overlay.addEventListener('click', close);
      document.addEventListener('keydown', function(e){
        if (e.key === 'Escape' && sidebar.classList.contains('open')) close();
      });
    }
    var cur = currentFile();
    document.querySelectorAll('#nav-sidebar nav a').forEach(function(a){
      a.classList.toggle('current', fileOf(a.getAttribute('href')) === cur);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setup);
  else setup();
})();
