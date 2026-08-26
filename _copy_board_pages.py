#!/usr/bin/env python3
"""Copy Everything day-card chrome (from Aug 25) onto Agenda, and copy
grid cards onto Dimensions. Does not modify everything.html."""
from __future__ import annotations

import json
import re
from collections import OrderedDict
from datetime import date, timedelta
from html import escape
from pathlib import Path

ROOT = Path("/Users/diana/dashboard")
EVERYTHING = ROOT / "everything.html"
AGENDA_PRAYER = ROOT / "agenda.html"
START = date(2026, 8, 25)
TODAY = date(2026, 8, 25)
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]  # date.weekday()
SKIP_HDR = re.compile(r"^'|escattr|escAttr|\+safe\+|oldname|newname|\+dn\+|'\s*\+", re.I)

FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Newsreader:ital,opsz,wght@6..72,300;6..72,400;1,400"
    "&family=DM+Mono:wght@300;400"
    "&family=Italiana"
    "&family=Cinzel:wght@500;600"
    "&family=Playfair+Display:ital,wght@0,400;0,700;1,400"
    "&family=Jost:wght@400;500"
    "&family=Reenie+Beanie"
    "&display=swap"
)


def find_matching_div(html: str, start: int) -> str | None:
    i = start
    n = len(html)
    depth = 0
    while i < n:
        lt = html.find("<", i)
        if lt < 0:
            return None
        if html.startswith("<!--", lt):
            end = html.find("-->", lt)
            i = end + 3 if end >= 0 else lt + 1
            continue
        if html.startswith("</div", lt) or html.startswith("</DIV", lt):
            depth -= 1
            gt = html.find(">", lt)
            if gt < 0:
                return None
            i = gt + 1
            if depth == 0:
                return html[start:i]
            continue
        if html.startswith("<div", lt) or html.startswith("<DIV", lt):
            ch = html[lt + 4] if lt + 4 < n else ""
            if ch in " \t\n\r/>":
                depth += 1
        gt = html.find(">", lt)
        if gt < 0:
            return None
        i = gt + 1
    return None


def extract_styles(html: str) -> str:
    chunks = []
    for m in re.finditer(r"<style\b([^>]*)>(.*?)</style>", html, flags=re.I | re.S):
        attrs = m.group(1) or ""
        body = m.group(2)
        sid = ""
        idm = re.search(r'id=["\']([^"\']+)["\']', attrs)
        if idm:
            sid = f"/* from #{idm.group(1)} */\n"
        chunks.append(sid + body)
    extra = """
/* copied-page shell */
.copied-page header { text-align:center; margin-bottom:36px; }
.copied-page header .eyebrow { font-family:'DM Mono',monospace; font-size:10px; letter-spacing:0.25em; color:var(--dusty); text-transform:uppercase; margin-bottom:8px; }
.copied-page header h1 { font-size:clamp(36px,8vw,64px); font-weight:400; font-style:italic; color:#1c140e; line-height:1.1; }
.copied-page .page-note { font-family:'DM Mono',monospace; font-size:9px; letter-spacing:0.16em; text-transform:uppercase; color:var(--sage); margin-top:10px; }
html body.copied-page #hamburger-menu span { background:#1c140e !important; box-shadow:0 1px 3px rgba(20,12,6,0.45); }
.dimensions-host { margin:0 !important; }
.dimensions-host .sec-grid {
  width:100%;
  display:flex !important;
  flex-wrap:wrap !important;
  gap:10px !important;
  height:auto !important;
  position:relative !important;
}
.dimensions-host .sec-card {
  position:relative !important;
  top:auto !important;
  left:auto !important;
  right:auto !important;
}
"""
    return "\n\n".join(chunks) + extra


def card_hdr(block: str) -> str:
    m = re.search(r'data-newhdr="([^"]*)"', block)
    if m:
        return m.group(1).strip()
    m = re.search(r'alt="([^"]*)"', block)
    return (m.group(1) if m else "").strip()


def is_junk_hdr(name: str) -> bool:
    if not name:
        return True
    if SKIP_HDR.search(name):
        return True
    if name.startswith("+") or "'" in name or '"' in name:
        return True
    return False


def extract_unique_cards(html: str) -> OrderedDict[str, str]:
    found: OrderedDict[str, str] = OrderedDict()
    for m in re.finditer(r"<div\b[^>]*\bsec-card\b[^>]*>", html, flags=re.I):
        block = find_matching_div(html, m.start())
        if not block:
            continue
        hdr = card_hdr(block)
        if is_junk_hdr(hdr):
            continue
        key = hdr.lower()
        if key in {"vibes2", "glow-up", "shopped"}:
            continue
        has_img = bool(re.search(r"<img\b", block, flags=re.I))
        prev = found.get(key)
        if prev is None:
            found[key] = block
            continue
        prev_img = bool(re.search(r"<img\b", prev, flags=re.I))
        if has_img and not prev_img:
            found[key] = block
        elif has_img == prev_img:
            found[key] = block  # later copy wins
    cleaned: OrderedDict[str, str] = OrderedDict()
    for key, block in found.items():
        if "j22-item" not in block and " is-empty" not in block[:180]:
            block = re.sub(r"(\bsec-card\b)", r"\1 is-empty", block, count=1)
        block = re.sub(r'\sstyle="--ff-x:[^"]*"', "", block, count=1)
        cleaned[key] = block
    return cleaned


def day_label(d: date) -> str:
    return f"{MONTHS[d.month - 1]} {d.day} · {WEEKDAYS[d.weekday()]}"


def day_block_html(d: date, is_today: bool) -> str:
    today_cls = " today-block" if is_today else ""
    return f"""<div class="day-block fmt22{today_cls}" data-date="{d.isoformat()}">
<div class="day-dot"></div>
<div class="day-card">
<div class="day-card-header"><span class="day-date">{escape(day_label(d))}</span></div>
<div class="today-view-toggle">
<button class="tv-pill active" data-view="pursuits">pursuits</button>
<button class="tv-pill" data-view="flow">flow</button>
</div>
<div class="day-tasks">
<div class="tv-panel tv-pursuits active">
<div class="flow-chart-card"><div class="sec-grid freeform"></div></div>
</div>
<div class="tv-panel tv-flow" style="display:none">
<div class="flow-chart-card"><p class="flow-title">flow</p></div>
</div>
</div>
</div>
</div>"""


def days_html() -> str:
    blocks = []
    d = START
    end = TODAY if TODAY >= START else START
    while d <= end:
        blocks.append(day_block_html(d, d == TODAY))
        d += timedelta(days=1)
    return "\n".join(blocks)


PAGE_JS = r"""
(function(){
  var START = '2026-08-25';
  var MONTHS = ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'];
  var WD = ['sun','mon','tue','wed','thu','fri','sat'];
  function pad(n){ return String(n).padStart(2,'0'); }
  function todayStr(){
    var t = new Date();
    return t.getFullYear() + '-' + pad(t.getMonth()+1) + '-' + pad(t.getDate());
  }
  function labelFor(iso){
    var p = iso.split('-').map(Number);
    var t = new Date(p[0], p[1]-1, p[2]);
    return MONTHS[t.getMonth()] + ' ' + t.getDate() + ' · ' + WD[t.getDay()];
  }
  function isoAdd(iso, days){
    var p = iso.split('-').map(Number);
    var t = new Date(p[0], p[1]-1, p[2] + days);
    return t.getFullYear() + '-' + pad(t.getMonth()+1) + '-' + pad(t.getDate());
  }
  function dayTemplate(iso, isToday){
    var wrap = document.createElement('div');
    wrap.innerHTML = '<div class="day-block fmt22'+(isToday?' today-block':'')+'" data-date="'+iso+'"><div class="day-dot"></div><div class="day-card"><div class="day-card-header"><span class="day-date"></span></div><div class="today-view-toggle"><button class="tv-pill active" data-view="pursuits">pursuits</button><button class="tv-pill" data-view="flow">flow</button></div><div class="day-tasks"><div class="tv-panel tv-pursuits active"><div class="flow-chart-card"><div class="sec-grid freeform"></div></div></div><div class="tv-panel tv-flow" style="display:none"><div class="flow-chart-card"><p class="flow-title">flow</p></div></div></div></div></div>';
    var blk = wrap.firstElementChild;
    blk.querySelector('.day-date').textContent = labelFor(iso);
    return blk;
  }
  function rail(){
    return document.querySelector('#agendaBody > .timeline') || document.querySelector('.timeline');
  }
  function ensureRange(){
    var r = rail();
    if(!r) return;
    var iso = START;
    var last = todayStr();
    if(last < START) last = START;
    while(iso <= last){
      if(!document.querySelector('.day-block[data-date="'+iso+'"]')){
        var blk = dayTemplate(iso, iso === last);
        var days = Array.from(r.querySelectorAll(':scope > .day-block.fmt22[data-date]'));
        var placed = false;
        for(var i=0;i<days.length;i++){
          var d = days[i].getAttribute('data-date') || '';
          if(d > iso){
            r.insertBefore(blk, days[i]);
            placed = true;
            break;
          }
        }
        if(!placed) r.appendChild(blk);
      }
      var existing = document.querySelector('.day-block[data-date="'+iso+'"]');
      if(existing){
        existing.classList.toggle('today-block', iso === last);
        existing.classList.remove('past');
        if(iso < last) existing.classList.add('past');
      }
      iso = isoAdd(iso, 1);
    }
  }
  function wireDots(){
    document.querySelectorAll('.day-dot').forEach(function(dot){
      if(dot.dataset.wired) return;
      dot.dataset.wired = '1';
      dot.addEventListener('click', function(e){
        e.stopPropagation();
        var block = dot.closest('.day-block');
        if(!block) return;
        block.classList.toggle('collapsed');
        try{
          var key = 'agenda-collapsed-days';
          var set = new Set(JSON.parse(localStorage.getItem(key) || '[]'));
          var dateStr = block.getAttribute('data-date') || '';
          if(block.classList.contains('collapsed')) set.add(dateStr);
          else set.delete(dateStr);
          localStorage.setItem(key, JSON.stringify(Array.from(set)));
        }catch(err){}
      });
    });
    try{
      var collapsed = JSON.parse(localStorage.getItem('agenda-collapsed-days') || '[]');
      collapsed.forEach(function(d){
        var b = document.querySelector('.day-block[data-date="'+d+'"]');
        if(b && !b.classList.contains('today-block')) b.classList.add('collapsed');
      });
    }catch(err){}
  }
  document.addEventListener('click', function(e){
    var pill = e.target.closest('.tv-pill');
    if(!pill) return;
    var block = pill.closest('.day-block');
    if(!block) return;
    var view = pill.getAttribute('data-view');
    if(!view || view === 'agenda') return;
    e.preventDefault();
    block.querySelectorAll('.tv-pill').forEach(function(p){
      p.classList.toggle('active', p.getAttribute('data-view') === view);
    });
    block.querySelectorAll('.tv-panel').forEach(function(panel){
      var show = panel.classList.contains('tv-' + view);
      panel.style.display = show ? '' : 'none';
      panel.classList.toggle('active', show);
    });
  });

  var IMG = {
    'dr betty':'manus-storage/pursuit-elevate-betty.jpg?v=1',
    'elevate':'manus-storage/pursuit-elevate-betty.jpg?v=1',
    'leverage':'manus-storage/pursuit-leverage-v4.jpg?v=key',
    'workflow':'manus-storage/pursuit-workflow-v6_6f889c15.jpg',
    'postal':'manus-storage/pursuit-postal_v1_53e3e315.jpg',
    'frequency':'manus-storage/pursuit-momentum-v5_f7c3e8ce.jpg',
    'momentum':'manus-storage/pursuit-momentum-v13.jpg?v=work',
    'vibes':'manus-storage/pursuit-vibes_e645a2da.jpg',
    'ux design':'manus-storage/pursuit-ux-design-v12_f2f2c818.jpg',
    'persons':'manus-storage/pursuit-persons_be56f167.jpg',
    'text mom':'manus-storage/pursuit-persons_be56f167.jpg',
    'capital blueprint':'manus-storage/pursuit-money_57ff14e0.jpg',
    'glow up':'manus-storage/mock-glow-up-skin-v3.jpg?v=cheek',
    'body':'manus-storage/zone-body.jpg?v=abs',
    'curated lifestyle':'manus-storage/pursuit-curated-lifestyle.jpg?v=2',
    'shopped':'manus-storage/pursuit-lifestyle_577937e8.jpg',
    'returns':'manus-storage/pursuit-returns-v2.jpg',
    'pickups':'manus-storage/pursuit-pickups.jpg',
    'social media':'manus-storage/pursuit-social-media-v7_c5f03b96.jpg',
    'quantum':'manus-storage/zone-quantum-v15.jpg?v=observe',
    'adderall / adhd meds':'manus-storage/pursuit-pharmacy-new_8ec4cd7a.jpg',
    'adderall':'manus-storage/pursuit-pharmacy-new_8ec4cd7a.jpg',
    'litigation wins':'manus-storage/pursuit-legal_b70d3da7.jpg',
    'power':'manus-storage/mock-power.jpg',
    'lifestyle':'manus-storage/pursuit-lifestyle_577937e8.jpg',
    'traveler':'manus-storage/pursuit-travel.jpg',
    'document translation into arabic':'manus-storage/pursuit-arabic-translation.jpg'
  };
  var THEMES = {
    'persons':'blush','text mom':'blush','capital blueprint':'amber','body':'blush','glow up':'blush',
    'shopped':'warm','returns':'warm','pickups':'warm','curated lifestyle':'warm','social media':'sage',
    'vibes':'lavender','adderall':'lavender','litigation wins':'sage','momentum':'coral','frequency':'coral',
    'ux design':'warm','workflow':'sage','postal':'warm','power':'amber','leverage':'warm','quantum':'lavender',
    'traveler':'warm','elevate':'coral'
  };
  var KEYWORDS = [
    [/translat|arabic/, 'manus-storage/pursuit-arabic-translation.jpg'],
    [/\bbody\b/, 'manus-storage/zone-body.jpg?v=abs'],
    [/person|\bmom\b|text/, 'manus-storage/pursuit-persons_be56f167.jpg'],
    [/money|capital|fund/, 'manus-storage/pursuit-money_57ff14e0.jpg'],
    [/glow|skin|beauty/, 'manus-storage/mock-glow-up-skin-v3.jpg?v=cheek'],
    [/ux|design/, 'manus-storage/pursuit-ux-design-v12_f2f2c818.jpg'],
    [/leverage/, 'manus-storage/pursuit-leverage-v4.jpg?v=key'],
    [/work|flow/, 'manus-storage/pursuit-workflow-v6_6f889c15.jpg'],
    [/momentum/, 'manus-storage/pursuit-momentum-v13.jpg?v=work'],
    [/frequency/, 'manus-storage/pursuit-momentum-v5_f7c3e8ce.jpg'],
    [/vibe/, 'manus-storage/pursuit-vibes_e645a2da.jpg'],
    [/return/, 'manus-storage/pursuit-returns-v2.jpg'],
    [/pickup/, 'manus-storage/pursuit-pickups.jpg'],
    [/postal|mail/, 'manus-storage/pursuit-postal_v1_53e3e315.jpg'],
    [/pharmacy|adderall|meds/, 'manus-storage/pursuit-pharmacy-new_8ec4cd7a.jpg'],
    [/legal|litigat/, 'manus-storage/pursuit-legal_b70d3da7.jpg'],
    [/social/, 'manus-storage/pursuit-social-media-v7_c5f03b96.jpg'],
    [/travel/, 'manus-storage/pursuit-travel.jpg'],
    [/power/, 'manus-storage/mock-power.jpg'],
    [/shop|lifestyle|curat/, 'manus-storage/pursuit-curated-lifestyle.jpg?v=2']
  ];
  function resolveImg(name){
    var n = (name||'').trim().toLowerCase();
    if(IMG[n]) return IMG[n];
    for(var i=0;i<KEYWORDS.length;i++){ if(KEYWORDS[i][0].test(n)) return KEYWORDS[i][1]; }
    return 'manus-storage/pursuit-lifestyle_577937e8.jpg';
  }
  function resolveTheme(name){
    var n = (name||'').trim().toLowerCase();
    if(THEMES[n]) return THEMES[n];
    if(/power|money|capital/.test(n)) return 'amber';
    if(/person|glow|beauty|skin|mom|body/.test(n)) return 'blush';
    if(/legal|social|work/.test(n)) return 'sage';
    if(/vibe|med|adderall/.test(n)) return 'lavender';
    if(/moment|frequency|elevate/.test(n)) return 'coral';
    return 'warm';
  }
  window.__secImgFor = resolveImg;
  window.__secThemeFor = resolveTheme;
  var CARD_NAMES = window.__COPIED_CARD_NAMES || [];
  var SECTION_NAMES = ['GLOW UP','LIFESTYLE','FINANCES','POWER','AMBITION','QUANTUM'];
  var ZONE_LC = { 'glow up':1,'lifestyle':1,'finances':1,'power':1,'ambition':1,'quantum':1 };

  function makeCard(name){
    name = (name||'').trim();
    var theme = resolveTheme(name);
    var src = resolveImg(name);
    var sec = document.createElement('div');
    sec.className = 'j22-section card sec-card is-empty';
    sec.setAttribute('data-theme', theme);
    sec.innerHTML = '<div class="card-visual theme-'+theme+'"><img alt="" src=""><p class="j22-group" contenteditable="true" spellcheck="false"></p></div><div class="card-body"><div class="j22-section-items"></div></div><button type="button" class="card-add-task" aria-label="add task">+</button>';
    var img = sec.querySelector('img');
    img.alt = name; img.src = src;
    var g = sec.querySelector('.j22-group');
    g.setAttribute('data-newhdr', name);
    g.textContent = name;
    return sec;
  }
  function closePicker(){
    document.querySelectorAll('.sec-picker').forEach(function(el){ el.remove(); });
  }
  function openPicker(anchor, grid, kind){
    closePicker();
    var box = document.createElement('div');
    box.className = 'sec-picker';
    var lab = document.createElement('p');
    lab.className = 'sec-picker-label';
    lab.textContent = kind === 'section' ? 'add a section' : 'add a card';
    box.appendChild(lab);
    var names = kind === 'section' ? SECTION_NAMES : CARD_NAMES.filter(function(n){ return !ZONE_LC[n.toLowerCase()]; });
    var list = document.createElement('div');
    list.className = 'sec-picker-list';
    names.forEach(function(name){
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'sec-picker-opt';
      b.textContent = name;
      b.addEventListener('click', function(ev){
        ev.preventDefault(); ev.stopPropagation();
        closePicker();
        if(kind === 'card') grid.appendChild(makeCard(name));
        else grid.appendChild(makeCard(name));
        savePage();
      });
      list.appendChild(b);
    });
    box.appendChild(list);
    var row = document.createElement('div');
    row.className = 'sec-picker-new';
    var inp = document.createElement('input');
    inp.className = 'plus-name-input';
    inp.placeholder = kind === 'section' ? 'or type a section' : 'or type a name';
    var go = document.createElement('button');
    go.type = 'button';
    go.textContent = 'add';
    function submit(){
      var v = (inp.value||'').trim();
      if(!v) return;
      closePicker();
      grid.appendChild(makeCard(v));
      savePage();
    }
    go.addEventListener('click', submit);
    inp.addEventListener('keydown', function(e){ if(e.key==='Enter') submit(); });
    row.appendChild(inp); row.appendChild(go);
    box.appendChild(row);
    if(anchor && anchor.parentNode) anchor.parentNode.insertBefore(box, anchor.nextSibling);
    inp.focus();
  }
  function ensureBtns(){
    document.querySelectorAll('.day-block.fmt22').forEach(function(blk){
      if(blk.classList.contains('dimensions-host')) return;
      var grid = blk.querySelector('.tv-pursuits .sec-grid') || blk.querySelector('.sec-grid');
      if(!grid) return;
      if(blk.querySelector('.add-board-row')) return;
      var row = document.createElement('div');
      row.className = 'add-board-row';
      function mk(cls, text, kind){
        var b = document.createElement('button');
        b.className = cls; b.type = 'button'; b.textContent = text;
        b.addEventListener('click', function(e){
          e.stopPropagation(); e.preventDefault();
          openPicker(row, grid, kind);
        });
        return b;
      }
      row.appendChild(mk('add-grid','+ section','section'));
      row.appendChild(mk('add-card-btn','+ card','card'));
      var toggle = blk.querySelector('.today-view-toggle');
      if(toggle && toggle.parentNode) toggle.insertAdjacentElement('afterend', row);
      else if(grid.parentNode) grid.parentNode.insertBefore(row, grid);
    });
  }
  var SAVE_KEY = document.body.getAttribute('data-save-key') || 'agenda_page_v1';
  function savePage(){
    if(SAVE_KEY === 'agenda_page_v1'){
      var days = {};
      document.querySelectorAll('.day-block.fmt22[data-date]').forEach(function(blk){
        var g = blk.querySelector('.sec-grid');
        days[blk.getAttribute('data-date')] = g ? g.innerHTML : '';
      });
      try{ localStorage.setItem(SAVE_KEY, JSON.stringify(days)); }catch(e){}
    } else {
      var grid = document.getElementById('dimGrid');
      if(!grid) return;
      try{ localStorage.setItem(SAVE_KEY, grid.innerHTML); }catch(e){}
    }
  }
  function restorePage(){
    try{
      if(SAVE_KEY === 'agenda_page_v1'){
        var days = JSON.parse(localStorage.getItem(SAVE_KEY) || '{}');
        Object.keys(days).forEach(function(iso){
          var blk = document.querySelector('.day-block[data-date="'+iso+'"]');
          var g = blk && blk.querySelector('.sec-grid');
          if(g && days[iso]) g.innerHTML = days[iso];
        });
      } else {
        var html = localStorage.getItem(SAVE_KEY);
        var grid = document.getElementById('dimGrid');
        if(html && grid) grid.innerHTML = html;
      }
    }catch(e){}
  }
  document.addEventListener('click', function(e){
    if(e.target.closest('.sec-picker, .add-grid, .add-card-btn, .add-board-row')) return;
    closePicker();
  });
  document.addEventListener('click', function(e){
    var add = e.target.closest('.card-add-task');
    if(!add) return;
    var card = add.closest('.sec-card');
    if(!card) return;
    var box = card.querySelector('.j22-section-items');
    if(!box) return;
    var lab = document.createElement('label');
    lab.className = 'j22-item';
    lab.innerHTML = '<input class="agenda-check" type="checkbox"><span class="j22-t" contenteditable="true" spellcheck="false">new task</span>';
    box.appendChild(lab);
    card.classList.remove('is-empty');
    card.classList.add('has-tasks');
    var t = lab.querySelector('.j22-t');
    if(t){ t.focus(); }
    savePage();
  });
  document.addEventListener('input', savePage);
  document.addEventListener('change', savePage);

  function normalizeCards(root){
    (root||document).querySelectorAll('.sec-card').forEach(function(card){
      var vis = card.querySelector('.card-visual');
      var group = card.querySelector('.j22-group');
      if(vis && group && group.parentElement !== vis) vis.appendChild(group);
      var img = vis && vis.querySelector('img');
      var name = group ? (group.getAttribute('data-newhdr')||group.textContent||'').trim() : '';
      if(img && name && !img.getAttribute('src')) img.src = resolveImg(name);
      if(name){
        var theme = resolveTheme(name);
        card.setAttribute('data-theme', theme);
        if(vis) vis.className = 'card-visual theme-' + theme;
      }
    });
  }
  function boot(){
    if(document.body.classList.contains('agenda-copy-page')){
      ensureRange();
    }
    restorePage();
    normalizeCards();
    ensureBtns();
    wireDots();
    var dimAdd = document.getElementById('dimAddCard');
    if(dimAdd){
      dimAdd.addEventListener('click', function(e){
        e.preventDefault();
        var grid = document.getElementById('dimGrid');
        openPicker(dimAdd, grid, 'card');
      });
    }
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
"""


def page_shell(title: str, body_class: str, save_key: str, inner: str, card_names: list[str]) -> str:
    names_js = json.dumps(card_names, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{escape(title)} · diana's board</title>
<link href="{FONTS}" rel="stylesheet"/>
<link rel="stylesheet" href="nav-shared.css"/>
<link rel="stylesheet" href="board-copy.css"/>
</head>
<body class="copied-page {body_class}" data-save-key="{escape(save_key)}">
<img id="page-bg-img" src="manus-storage/_339ab459.jpg" style="position:fixed;top:0;left:0;width:100%;height:100%;object-fit:cover;z-index:0;pointer-events:none;" alt=""/>
<div id="page-bg-wrapper" style="padding:48px 24px 80px; margin:0; min-height:100vh; box-sizing:border-box; position:relative; z-index:1;">
{inner}
</div>
<script src="nav-shared.js"></script>
<script>window.__COPIED_CARD_NAMES = {names_js};</script>
<script>{PAGE_JS}</script>
</body>
</html>
"""


def write_deen():
    dest = ROOT / "deen.html"
    src = AGENDA_PRAYER.read_text(encoding="utf-8")
    if "prayer-cards-container" not in src:
        if dest.exists() and "prayer-cards-container" in dest.read_text(encoding="utf-8"):
            return
        raise SystemExit("agenda.html is not the prayer page; cannot copy deen")
    src = src.replace("agenda · diana's board", "deen · diana's board", 1)
    src = src.replace(
        '<div class="prayer-header-title">agenda</div>',
        '<div class="prayer-header-title">deen</div>',
        1,
    )
    dest.write_text(src, encoding="utf-8")


def main():
    html = EVERYTHING.read_text(encoding="utf-8", errors="replace")
    css = extract_styles(html)
    (ROOT / "board-copy.css").write_text(css, encoding="utf-8")
    cards = extract_unique_cards(html)
    # Prefer human titles: if shopped card's visible text is curated lifestyle, keep both keys
    names = []
    for key, block in cards.items():
        hdr = card_hdr(block) or key
        names.append(hdr)
    names = list(dict.fromkeys(names))

    write_deen()

    agenda_inner = f"""  <header>
    <p class="eyebrow">from aug 25</p>
    <h1>agenda</h1>
    <p class="page-note">day cards from august 25</p>
  </header>
  <div class="schedule-section">
    <div class="agenda-body" id="agendaBody">
      <div class="timeline">
{days_html()}
      </div>
    </div>
  </div>"""
    (ROOT / "agenda.html").write_text(
        page_shell("agenda", "agenda-copy-page", "agenda_page_v1", agenda_inner, names),
        encoding="utf-8",
    )

    grid = "\n".join(cards.values())
    dim_inner = f"""  <header>
    <p class="eyebrow">pursuit cards</p>
    <h1>dimensions</h1>
    <p class="page-note">the pursuit grid</p>
  </header>
  <div class="add-board-row" style="margin-bottom:18px;">
    <button type="button" class="add-card-btn" id="dimAddCard">+ card</button>
  </div>
  <div class="day-block fmt22 dimensions-host">
    <div class="sec-grid freeform" id="dimGrid">
{grid}
    </div>
  </div>"""
    (ROOT / "dimensions.html").write_text(
        page_shell("dimensions", "dimensions-copy-page", "dimensions_cards_v1", dim_inner, names),
        encoding="utf-8",
    )

    print("wrote board-copy.css", (ROOT / "board-copy.css").stat().st_size)
    print("cards", len(cards), names)
    print("agenda.html", (ROOT / "agenda.html").stat().st_size)
    print("dimensions.html", (ROOT / "dimensions.html").stat().st_size)
    print("deen.html", (ROOT / "deen.html").stat().st_size)


if __name__ == "__main__":
    main()
