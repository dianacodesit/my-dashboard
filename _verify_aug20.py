#!/usr/bin/env python3
"""Browser verification for Aug 20/22/23 dashboard fixes."""
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/dashboard.html"
results = []

def ok(name, cond, detail=""):
    results.append((bool(cond), name, detail))
    print(("PASS" if cond else "FAIL"), name, detail)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="chrome")
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)

    info = page.evaluate("""() => {
      const a20 = document.querySelector('.day-block[data-date="2026-08-20"]');
      const a22 = document.querySelector('.day-block[data-date="2026-08-22"]');
      const a23 = document.querySelector('.day-block[data-date="2026-08-23"]');
      const a24 = document.querySelector('.day-block[data-date="2026-08-24"]');
      const rail = [...document.querySelectorAll('.rail-date')].map(el => el.getAttribute('data-rail-date'));
      const card = a20 && a20.querySelector('.day-card');
      const zones = a20 ? [...a20.querySelectorAll('.pursuit-zone')].map(z => ({
        id: z.getAttribute('data-zone'),
        w: getComputedStyle(z).width,
        h: getComputedStyle(z).height,
        hasResize: !!z.querySelector('.zone-resize'),
        photo: z.style.getPropertyValue('--zone-photo')
      })) : [];
      const oneoffs = a20 ? a20.querySelectorAll('.canvas-oneoff, .zone-oneoff.canvas-oneoff').length : -1;
      const pills = a20 ? [...a20.querySelectorAll('.tv-pill')].map(p => p.textContent.trim()) : [];
      return {
        a20Class: a20 ? a20.className : null,
        a20Collapsed: a20 ? a20.classList.contains('collapsed') : null,
        a22Class: a22 ? a22.className : null,
        a23Class: a23 ? a23.className : null,
        a23Collapsed: a23 ? a23.classList.contains('collapsed') : null,
        a24Class: a24 ? a24.className : null,
        rail,
        cardW: card ? getComputedStyle(card).width : null,
        zones,
        oneoffs,
        pills,
        todayBlocks: [...document.querySelectorAll('.today-block')].map(b => b.getAttribute('data-date'))
      };
    }""")

    ok("Aug 20 exists", info["a20Class"] is not None, info["a20Class"])
    ok("Aug 20 not today-block", info["a20Class"] and "today-block" not in info["a20Class"], info["a20Class"])
    ok("Aug 20 is zone-board-day", info["a20Class"] and "zone-board-day" in info["a20Class"], info["a20Class"])
    ok("Aug 20 not auto-collapsed", info["a20Collapsed"] is False, str(info["a20Collapsed"]))
    ok("Aug 23 keeps zone-board-day", info["a23Class"] and "zone-board-day" in (info["a23Class"] or ""), info["a23Class"])
    ok("Aug 23 not auto-collapsed", info.get("a23Collapsed") is False, str(info.get("a23Collapsed")))
    ok("Aug 22 is not a cloned zone canvas", info["a22Class"] and "zone-board-day" not in (info["a22Class"] or ""), info["a22Class"])
    ok("Real today is Aug 24", "2026-08-24" in (info["todayBlocks"] or []) and "2026-08-20" not in (info["todayBlocks"] or []), str(info["todayBlocks"]))
    ok("Rail has Aug 20", "2026-08-20" in info["rail"], str(info["rail"][-8:]))
    ok("Rail has Aug 22", "2026-08-22" in info["rail"], "")
    ok("Rail has Aug 23", "2026-08-23" in info["rail"], "")
    ok("Aug 20 card is wide", info["cardW"] and float(info["cardW"].replace("px","")) > 800, info["cardW"])
    ok("Aug 20 has section zones", len(info["zones"]) >= 4, str(len(info["zones"])))
    ok("Zones have resize handles", all(z["hasResize"] for z in info["zones"]), str(info["zones"]))
    ok("No canvas oneoffs on Aug 20", info["oneoffs"] == 0, str(info["oneoffs"]))
    ok("Pursuits/flow/agenda pills kept", set(info["pills"]) >= {"pursuits","flow","agenda"}, str(info["pills"]))

    # Scroll Aug 20 into view
    page.evaluate("""() => {
      const b = document.querySelector('.day-block[data-date="2026-08-20"]');
      if (b) { b.classList.remove('collapsed'); b.scrollIntoView({block:'center'}); }
    }""")
    page.wait_for_timeout(600)

    # Resize handle geometry
    handle = page.locator('.day-block[data-date="2026-08-20"] .pursuit-zone[data-zone="finances"] .zone-resize')
    ok("Resize handle in DOM", handle.count() > 0)
    box = handle.bounding_box()
    ok("Resize handle visible/hittable", box and box["width"] >= 20 and box["height"] >= 20, str(box))

    finances = page.locator('.day-block[data-date="2026-08-20"] .pursuit-zone[data-zone="finances"]')
    before = page.evaluate("""() => {
      const z = document.querySelector('.day-block[data-date="2026-08-20"] .pursuit-zone[data-zone="finances"]');
      return {w: z.style.getPropertyValue('--zone-w'), h: z.style.getPropertyValue('--zone-h'),
              cw: getComputedStyle(z).width, ch: getComputedStyle(z).height};
    }""")
    if box:
        cx = box["x"] + box["width"]/2
        cy = box["y"] + box["height"]/2
        hit = page.evaluate("""({x,y}) => {
          const el = document.elementFromPoint(x,y);
          return el && {cls: el.className, tag: el.tagName, zone: !!(el.closest && el.closest('.zone-resize'))};
        }""", {"x": cx, "y": cy})
        print("HIT", hit)
        page.mouse.move(cx, cy)
        page.mouse.down()
        page.mouse.move(cx + 90, cy + 70, steps=12)
        page.mouse.up()
        page.wait_for_timeout(400)
    after = page.evaluate("""() => {
      const z = document.querySelector('.day-block[data-date="2026-08-20"] .pursuit-zone[data-zone="finances"]');
      return {w: z.style.getPropertyValue('--zone-w'), h: z.style.getPropertyValue('--zone-h'),
              cw: getComputedStyle(z).width, ch: getComputedStyle(z).height};
    }""")
    def px(s):
        try: return float(str(s).replace("px",""))
        except: return 0
    grew = px(after["w"]) > px(before["w"]) + 20 or px(after["cw"]) > px(before["cw"]) + 20
    ok("Drag resize updates --zone-w/--zone-h", grew, f"{before} -> {after}")

    # Click section PHOTO (not header) to zoom
    page.evaluate("""() => {
      const z = document.querySelector('.day-block[data-date="2026-08-20"] .pursuit-zone[data-zone="presence"]');
      if (z) z.scrollIntoView({block:'center'});
    }""")
    page.wait_for_timeout(300)
    zbox = page.locator('.day-block[data-date="2026-08-20"] .pursuit-zone[data-zone="presence"]').bounding_box()
    if zbox:
        # click in the photo body, below the 44px header
        page.mouse.click(zbox["x"] + zbox["width"]/2, zbox["y"] + min(zbox["height"]-20, 90))
        page.wait_for_timeout(500)
    zoom = page.evaluate("""() => {
      const grid = document.querySelector('.day-block[data-date="2026-08-20"] .sec-grid');
      const z = document.querySelector('.day-block[data-date="2026-08-20"] .pursuit-zone[data-zone="presence"]');
      if (!grid || !z) return null;
      const cs = getComputedStyle(z);
      const before = getComputedStyle(z, '::before');
      const head = z.querySelector('.pursuit-zone-head');
      const zg = z.querySelector('.pursuit-zone-grid');
      return {
        zoomed: grid.classList.contains('zone-zoomed'),
        isZoomed: z.classList.contains('is-zoomed'),
        w: cs.width, h: cs.height,
        size: before.backgroundSize,
        opacity: before.opacity,
        headDisplay: head ? getComputedStyle(head).display : null,
        gridDisplay: zg ? getComputedStyle(zg).display : null,
        leftoverTitle: head && getComputedStyle(head).display !== 'none' && getComputedStyle(head).visibility !== 'hidden'
      };
    }""")
    ok("Photo click zooms section", zoom and zoom["zoomed"] and zoom["isZoomed"], str(zoom))
    ok("Zoomed photo uses contain", zoom and "contain" in str(zoom.get("size","")), str(zoom and zoom.get("size")))
    ok("Zoomed photo opacity 1", zoom and str(zoom.get("opacity")) in ("1", "1.0"), str(zoom and zoom.get("opacity")))
    ok("No leftover title/sidebar on zoom", zoom and zoom.get("headDisplay")=="none" and zoom.get("gridDisplay")=="none", str(zoom))

    # Zoom out via all sections or second photo click
    zoomed_out = page.evaluate("""() => {
      const host = document.querySelector('.day-block[data-date="2026-08-20"] .pursuit-zoom-host');
      const btn = host && host.querySelector('.zone-zoom-out');
      if (btn) {
        btn.hidden = false;
        btn.removeAttribute('hidden');
        btn.click();
      } else {
        const z = document.querySelector('.day-block[data-date="2026-08-20"] .pursuit-zone.is-zoomed');
        if (z) z.click();
      }
      const grid = document.querySelector('.day-block[data-date="2026-08-20"] .sec-grid');
      return {out: grid && !grid.classList.contains('zone-zoomed'), btn: !!(btn), btnDisplay: btn ? getComputedStyle(btn).display : null};
    }""")
    ok("Zoom out works", zoomed_out and zoomed_out["out"], str(zoomed_out))

    # Header click collapses
    page.evaluate("""() => {
      const z = document.querySelector('.day-block[data-date="2026-08-20"] .pursuit-zone[data-zone="body"]');
      if (z) { z.classList.remove('zone-collapsed'); z.scrollIntoView({block:'center'}); }
    }""")
    page.wait_for_timeout(300)
    hbox = page.locator('.day-block[data-date="2026-08-20"] .pursuit-zone[data-zone="body"] .pursuit-zone-title').bounding_box()
    if hbox:
        page.mouse.click(hbox["x"] + hbox["width"]/2, hbox["y"] + hbox["height"]/2)
        page.wait_for_timeout(400)
    collapsed = page.evaluate("""() => {
      const z = document.querySelector('.day-block[data-date="2026-08-20"] .pursuit-zone[data-zone="body"]');
      return {on: z.classList.contains('zone-collapsed'), h: getComputedStyle(z).height};
    }""")
    ok("Header click collapses section", collapsed and collapsed["on"], str(collapsed))
    page.evaluate("""() => {
      const t = document.querySelector('.day-block[data-date="2026-08-20"] .pursuit-zone[data-zone="body"] .pursuit-zone-title');
      if (t) { t.scrollIntoView({block:'center'}); t.click(); }
    }""")
    page.wait_for_timeout(400)
    expanded = page.evaluate("""() => {
      const z = document.querySelector('.day-block[data-date="2026-08-20"] .pursuit-zone[data-zone="body"]');
      return {on: z.classList.contains('zone-collapsed'), h: getComputedStyle(z).height};
    }""")
    ok("Header click expands again", expanded and not expanded["on"], str(expanded))

    browser.close()

fails = [r for r in results if not r[0]]
print("\n==== SUMMARY ====")
print(f"{len(results)-len(fails)}/{len(results)} passed")
for f in fails:
    print("FAIL:", f[1], f[2])
raise SystemExit(1 if fails else 0)
