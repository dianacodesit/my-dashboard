(function(){
  var body = document.body;
  var KEY = body.getAttribute('data-store') || 'page_capture_v1';
  var emptyText = body.getAttribute('data-empty') || 'nothing kept yet';
  var listEl = document.getElementById('list');
  var input = document.getElementById('new-item');
  var status = document.getElementById('status');
  var addBtn = document.getElementById('add-btn');
  if (!listEl || !input) return;

  function load(){
    try { return JSON.parse(localStorage.getItem(KEY) || '[]'); }
    catch (e) { return []; }
  }
  function save(items){
    try {
      localStorage.setItem(KEY, JSON.stringify(items));
      if (status) status.textContent = 'saved here';
    } catch (e) {
      if (status) status.textContent = 'save failed';
    }
  }
  function render(){
    var items = load();
    listEl.innerHTML = '';
    if (!items.length) {
      var empty = document.createElement('p');
      empty.className = 'empty';
      empty.textContent = emptyText;
      listEl.appendChild(empty);
      return;
    }
    items.forEach(function(it, i){
      var row = document.createElement('div');
      row.className = 'item';
      row.innerHTML = '<span class="mark">✦</span><div class="t" contenteditable="true" spellcheck="false"></div><button class="x" type="button" aria-label="remove">×</button>';
      row.querySelector('.t').textContent = it.t || '';
      row.querySelector('.t').addEventListener('blur', function(){
        var all = load();
        if (!all[i]) return;
        all[i].t = this.textContent.trim();
        save(all);
      });
      row.querySelector('.x').addEventListener('click', function(){
        var all = load();
        all.splice(i, 1);
        save(all);
        render();
      });
      listEl.appendChild(row);
    });
  }
  function add(){
    var t = (input.value || '').trim();
    if (!t) return;
    var all = load();
    all.unshift({ t: t });
    save(all);
    input.value = '';
    render();
  }
  if (addBtn) addBtn.addEventListener('click', add);
  input.addEventListener('keydown', function(e){
    if (e.key === 'Enter') { e.preventDefault(); add(); }
  });
  render();
})();
