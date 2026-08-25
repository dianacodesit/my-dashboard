#!/usr/bin/env python3
"""Generate standalone HTML pages for the hamburger menu."""
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parent
FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Newsreader:ital,opsz,wght@6..72,300;6..72,400;1,400"
    "&family=DM+Mono:wght@300;400"
    "&family=Italiana"
    "&family=Reenie+Beanie"
    "&family=Cinzel:wght@500;700"
    "&family=Playfair+Display:ital,wght@0,400;0,700;1,400"
    "&family=Bodoni+Moda:opsz,wght@6..96,400;6..96,700"
    "&family=Instrument+Serif:ital@0;1"
    "&display=swap"
)

SHELL_CSS = r"""
  :root { --cream:#F5F0E8; --paper:#FAF6EE; --ink:#2a2520; --muted:#6f5f54; --accent:#8a9e85; }
  * { box-sizing:border-box; margin:0; padding:0; }
  html, body { min-height:100%; }
  body { font-family:'Newsreader', Georgia, serif; color:var(--ink); background:#1a1822; overflow-x:hidden; }
  .page-bg {
    position:fixed; inset:0; z-index:0;
    background:
      linear-gradient(165deg, rgba(26,24,34,0.55) 0%, rgba(38,32,48,0.42) 45%, rgba(22,20,28,0.62) 100%),
      url('manus-storage/deen-moodboard-bg_807e7166.jpg') center/cover no-repeat;
    filter: saturate(0.9) brightness(0.7);
  }
  .page-shell { position:relative; z-index:1; min-height:100vh; padding:72px 24px 48px; display:flex; justify-content:center; }
  .panel {
    width:min(860px,100%);
    background:rgba(250,246,238,0.94);
    border:1px solid rgba(196,168,130,0.35);
    border-radius:18px;
    box-shadow:0 24px 60px rgba(0,0,0,0.28);
    overflow:hidden;
  }
  .panel-header { padding:28px 32px 16px; border-bottom:1px solid rgba(196,168,130,0.22); }
  .eyebrow { font-family:'DM Mono',monospace; font-size:10px; letter-spacing:0.22em; text-transform:uppercase; color:var(--muted); margin-bottom:8px; }
  h1 { font-family:'Italiana',serif; font-size:clamp(30px,5vw,42px); font-weight:400; letter-spacing:0.03em; }
  .sub { margin-top:8px; font-family:'DM Mono',monospace; font-size:10px; letter-spacing:0.12em; color:var(--accent); }
  .panel-body { padding:20px 28px 28px; }
  .add-row { display:flex; gap:8px; margin-bottom:16px; }
  .add-row input, textarea.note {
    flex:1; padding:10px 12px; border:1px solid rgba(110,100,86,0.28); border-radius:10px;
    background:#fffaf2; font-family:'Newsreader',serif; font-size:16px; color:var(--ink); outline:none;
  }
  .add-row button, .ghost {
    padding:8px 14px; border:none; border-radius:10px; background:rgba(110,100,86,0.18);
    font-family:'DM Mono',monospace; font-size:11px; letter-spacing:0.08em; cursor:pointer; color:#41373a;
  }
  .item { display:flex; align-items:flex-start; gap:10px; padding:10px 0; border-bottom:1px solid rgba(196,168,130,0.18); }
  .item input[type=checkbox] { margin-top:6px; }
  .item .t { flex:1; font-size:17px; line-height:1.4; }
  .item.done .t { opacity:0.45; text-decoration:line-through; }
  .item .x { background:none; border:none; color:#a8706a; cursor:pointer; font-size:16px; }
  .status { font-family:'DM Mono',monospace; font-size:9px; letter-spacing:0.14em; text-transform:uppercase; color:var(--muted); margin-top:12px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(160px,1fr)); gap:12px; }
  .swatch { border-radius:12px; min-height:88px; padding:12px; color:#fff; text-shadow:0 1px 4px rgba(0,0,0,0.35); font-family:'DM Mono',monospace; font-size:11px; }
  .sample { padding:16px; border:1px solid rgba(196,168,130,0.22); border-radius:12px; background:#fffaf2; margin-bottom:10px; }
  .flow-demo { display:flex; flex-direction:column; align-items:center; gap:6px; padding:18px 0; }
  .pill { padding:8px 16px; border-radius:999px; background:rgba(245,240,233,0.9); border:1px solid rgba(110,100,86,0.25); }
"""

LIST_JS = r"""
(function(){
  var KEY = window.PAGE_STORE_KEY;
  var listEl = document.getElementById('list');
  var input = document.getElementById('new-item');
  var status = document.getElementById('status');
  function load(){ try { return JSON.parse(localStorage.getItem(KEY)||'[]'); } catch(e){ return []; } }
  function save(items){
    try { localStorage.setItem(KEY, JSON.stringify(items)); status.textContent='saved locally'; }
    catch(e){ status.textContent='save failed'; }
  }
  function render(){
    var items = load();
    listEl.innerHTML = '';
    items.forEach(function(it, i){
      var row = document.createElement('div');
      row.className = 'item' + (it.done ? ' done' : '');
      row.innerHTML = '<input type="checkbox"'+(it.done?' checked':'')+'><div class="t" contenteditable="true" spellcheck="false"></div><button class="x" type="button">×</button>';
      row.querySelector('.t').textContent = it.t || '';
      row.querySelector('input').addEventListener('change', function(){
        var all = load(); all[i].done = this.checked; save(all); render();
      });
      row.querySelector('.t').addEventListener('blur', function(){
        var all = load(); all[i].t = this.textContent.trim(); save(all);
      });
      row.querySelector('.x').addEventListener('click', function(){
        var all = load(); all.splice(i,1); save(all); render();
      });
      listEl.appendChild(row);
    });
  }
  function add(){
    var t = (input.value||'').trim(); if(!t) return;
    var all = load(); all.push({t:t, done:false}); save(all); input.value=''; render();
  }
  document.getElementById('add-btn').addEventListener('click', add);
  input.addEventListener('keydown', function(e){ if(e.key==='Enter'){ e.preventDefault(); add(); } });
  render();
})();
"""

def page(title, eyebrow, heading, sub, body, extra_js=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title} · diana's board</title>
<link href="{FONTS}" rel="stylesheet"/>
<link rel="stylesheet" href="nav-shared.css"/>
<style>{SHELL_CSS}</style>
</head>
<body>
<div class="page-bg" aria-hidden="true"></div>
<main class="page-shell">
  <article class="panel">
    <header class="panel-header">
      <p class="eyebrow">{eyebrow}</p>
      <h1>{heading}</h1>
      <p class="sub">{sub}</p>
    </header>
    <div class="panel-body">
{body}
    </div>
  </article>
</main>
<script src="nav-shared.js"></script>
{extra_js}
</body>
</html>
"""

def list_page(filename, title, eyebrow, heading, sub, store_key):
    body = """      <div class="add-row">
        <input id="new-item" type="text" placeholder="add an item" autocomplete="off"/>
        <button id="add-btn" type="button">add</button>
      </div>
      <div id="list"></div>
      <p class="status" id="status">saved locally</p>"""
    js = f"<script>window.PAGE_STORE_KEY={store_key!r};</script>\n<script>{LIST_JS}</script>"
    (ROOT / filename).write_text(page(title, eyebrow, heading, sub, body, js), encoding="utf-8")

list_page("identity.html", "identity", "who you are", "Identity", "values · roles · how you move", "page_identity_v1")
list_page("goals.html", "goals", "direction", "Goals", "what you are building toward", "page_goals_v1")
list_page("projects.html", "projects", "in motion", "Projects", "active work, one line each", "page_projects_v1")
list_page("agenda.html", "agenda", "this stretch", "Agenda", "events, blocks, and appointments", "page_agenda_v1")
list_page("tasks-obsidian-v1127.html", "taskboard", "capture", "Taskboard", "standalone list — dashboard stays on dashboard.html", "page_taskboard_v1")

(ROOT / "palettes.html").write_text(page(
    "palettes", "design preview", "Color palettes", "the board's working set",
    """
      <div class="grid">
        <div class="swatch" style="background:#F5F0E8;color:#2a2520;text-shadow:none">cream #F5F0E8</div>
        <div class="swatch" style="background:#FAF6EE;color:#2a2520;text-shadow:none">paper #FAF6EE</div>
        <div class="swatch" style="background:#2a2520">ink #2a2520</div>
        <div class="swatch" style="background:#8a9e85">sage #8a9e85</div>
        <div class="swatch" style="background:#c4a882">warm #c4a882</div>
        <div class="swatch" style="background:#bf8f93">blush #bf8f93</div>
        <div class="swatch" style="background:#9b8ec4">lavender #9b8ec4</div>
        <div class="swatch" style="background:#5a8a4a">today green #5a8a4a</div>
      </div>
    """
), encoding="utf-8")

(ROOT / "colors.html").write_text(page(
    "colors", "design preview", "Individual colors", "one chip at a time",
    """
      <div class="grid">
        <div class="swatch" style="background:#1c140e">espresso</div>
        <div class="swatch" style="background:#3d2a18">bronze</div>
        <div class="swatch" style="background:#6f5f54">dusty</div>
        <div class="swatch" style="background:#C19BA5">rose</div>
        <div class="swatch" style="background:#A6B69E">mist sage</div>
        <div class="swatch" style="background:#4A9EFF">today blue</div>
      </div>
    """
), encoding="utf-8")

(ROOT / "fonts.html").write_text(page(
    "fonts", "design preview", "Editorial fonts", "headers and body on the board",
    """
      <div class="sample" style="font-family:'Italiana',serif;font-size:36px">Italiana — page titles</div>
      <div class="sample" style="font-family:'Cinzel',serif;letter-spacing:0.12em">CINZEL — DATE RAIL</div>
      <div class="sample" style="font-family:'Newsreader',serif;font-size:22px">Newsreader — body copy and cards</div>
      <div class="sample" style="font-family:'Playfair Display',serif;font-size:22px">Playfair Display — editorial punch</div>
      <div class="sample" style="font-family:'Bodoni Moda',serif;font-size:22px">Bodoni Moda — fashion editorial</div>
      <div class="sample" style="font-family:'Instrument Serif',serif;font-size:22px">Instrument Serif — modern minimal</div>
      <div class="sample" style="font-family:'DM Mono',monospace;font-size:12px;letter-spacing:0.14em">DM MONO — LABELS</div>
    """
), encoding="utf-8")

(ROOT / "flow-fonts.html").write_text(page(
    "flow fonts", "design preview", "Cursive flow fonts", "handwriting on cards",
    """
      <div class="sample" style="font-family:'Reenie Beanie',cursive;font-size:34px">text Dr Betty</div>
      <div class="sample" style="font-family:'Reenie Beanie',cursive;font-size:34px">document translation into arabic</div>
      <div class="sample" style="font-family:'Instrument Serif',serif;font-style:italic;font-size:26px">Instrument Serif italic as a quieter option</div>
    """
), encoding="utf-8")

(ROOT / "deadline-fonts.html").write_text(page(
    "deadline fonts", "design preview", "Deadline pill fonts", "compact time labels",
    """
      <div class="sample"><span class="pill" style="font-family:'DM Mono',monospace;font-size:11px;letter-spacing:0.14em">8:30 AM PT</span></div>
      <div class="sample"><span class="pill" style="font-family:'Cinzel',serif;font-size:12px">AUG 24 · MON</span></div>
      <div class="sample"><span class="pill" style="font-family:'Newsreader',serif;font-style:italic">due tonight</span></div>
    """
), encoding="utf-8")

(ROOT / "flow-styles.html").write_text(page(
    "flow styles", "design preview", "Flow chart designs", "vertical sequence",
    """
      <div class="flow-demo">
        <div class="pill">morning adhkar</div>
        <div>↓</div>
        <div class="pill">deep work block</div>
        <div>↓</div>
        <div class="pill">claude session</div>
      </div>
    """
), encoding="utf-8")

(ROOT / "arrows.html").write_text(page(
    "arrows", "design preview", "Arrow formations", "connectors used on the board",
    """
      <div class="flow-demo">
        <svg width="14" height="26"><line x1="7" y1="2" x2="7" y2="22" stroke="#C19BA5" stroke-width="1.4"/><polygon points="4,20 10,20 7,24" fill="#C19BA5"/></svg>
        <svg width="80" height="32"><path d="M10 4 Q50 4 50 28" stroke="#A6B69E" stroke-width="1.4" fill="none" stroke-linecap="round"/><polygon points="47,26 53,26 50,30" fill="#A6B69E"/></svg>
        <svg width="80" height="36"><path d="M8 4 C30 4 20 32 70 32" stroke="#c4a882" stroke-width="1.4" fill="none"/><polygon points="67,29 73,29 70,34" fill="#c4a882"/></svg>
      </div>
    """
), encoding="utf-8")

(ROOT / "transitions.html").write_text(page(
    "transitions", "design preview", "Transition styles", "how the board moves",
    """
      <div class="sample">sidebar: left 0.3s ease</div>
      <div class="sample">day cards: collapse instantly, no fade on the date rail</div>
      <div class="sample">zone drag: left/top 0.16s ease, none while dragging</div>
    """
), encoding="utf-8")

src_today = Path("/Users/diana/Documents/GitHub/task-dashboard/client/public/today.html")
if src_today.exists():
    html = src_today.read_text(encoding="utf-8")
    html = html.replace(
        "url('/manus-storage/room-bg_35822b41.jpg')",
        "url('manus-storage/deen-moodboard-bg_807e7166.jpg')",
    )
    if "nav-shared.js" not in html:
        html = html.replace(
            "</head>",
            '<link rel="stylesheet" href="nav-shared.css"/>\n</head>',
            1,
        )
        html = html.replace(
            "</body>",
            '<script src="nav-shared.js"></script>\n</body>',
            1,
        )
    (ROOT / "today.html").write_text(html, encoding="utf-8")
    print("wrote today.html from repo")
else:
    print("today.html source missing")

print("pages ready")
for p in sorted(ROOT.glob("*.html")):
    print(p.name)
