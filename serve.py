#!/usr/bin/env python3
"""Dashboard static server with durable GitHub bake.

POST /bake  JSON {"data": {localStorageKey: value, ...}}
  - Rewrites the /*baked-data*/ seed script in everything.html
  - Writes localStorage_dump.json
  - Commits and pushes to origin

Also accepts the dashboard's existing /save and /move-cards POSTs
as no-op 200s so the UI does not spam console errors.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DASHBOARD = ROOT / "everything.html"
BRAIN = ROOT / "brain-dump.html"
DUMP = ROOT / "localStorage_dump.json"
PORT = int(os.environ.get("PORT", "8080"))
GIT_LOCK = threading.Lock()
PHOTO_LOCK = threading.Lock()
PHOTO_MAP = ROOT / "manus-storage" / "card-photos.json"
STORAGE = ROOT / "manus-storage"
KNOWN_CARD_PHOTOS = {
    "induction": "manus-storage/card-induction.jpg",
    "cleanse": "manus-storage/card-cleanse.jpg",
    "application": "manus-storage/card-application.jpg",
    "scholarship application": "manus-storage/card-application.jpg",
    "scholarship re-application": "manus-storage/card-application.jpg",
    "scholarship reapplication": "manus-storage/card-application.jpg",
    "tuition": "manus-storage/card-tuition.jpg",
    "tuition money": "manus-storage/card-tuition.jpg",
    "committee check-in": "manus-storage/pepperdine-committee-checkin.jpg",
    "gsa": "manus-storage/handshake-pepperdine-gsa.jpg",
    "pepperdine gsa": "manus-storage/handshake-pepperdine-gsa.jpg",
    "graduate student association": "manus-storage/handshake-pepperdine-gsa.jpg",
    "pepperdine graduate student association": "manus-storage/handshake-pepperdine-gsa.jpg",
    "top applicant": "manus-storage/handshake-pepperdine-gsa.jpg",
    "pepperdine gsa · top applicant": "manus-storage/handshake-pepperdine-gsa.jpg",
    "graduate student association · top applicant": "manus-storage/handshake-pepperdine-gsa.jpg",
    "pepperdine graduate student association · top applicant": "manus-storage/handshake-pepperdine-gsa.jpg",
    "psi chi": "manus-storage/card-psi-chi.jpg",
    "ps chi": "manus-storage/card-psi-chi.jpg",
    "handshake": "manus-storage/card-handshake.jpg",
    "sabr": "manus-storage/card-sabr.jpg",
    "shukr": "manus-storage/card-shukr.jpg",
    # Pepperdine section / zone only — not tuition/application cards
    "pepperdine": "manus-storage/pursuit-pepperdine.jpg",
    "grad school": "manus-storage/pursuit-pepperdine.jpg",
    "grad": "manus-storage/pursuit-pepperdine.jpg",
}
PHOTO_SKIP = re.compile(
    r"\b(person|people|portrait|face|faces|woman|women|man|men|girl|boy|child|selfie|crowd|model|couple)\b",
    re.I,
)

BAKE_START = "<script>/*baked-data*/(function(){try{var D="
BAKE_END = ';for(var k in D){if(localStorage.getItem(k)===null){localStorage.setItem(k,D[k]);}}}catch(e){}})();</script>'
BRAIN_START = '<script id="brain-dump-data" type="application/json">'
BRAIN_END = "</script><!--/brain-dump-data-->"

ALLOWED_SECTIONS = {
    "body",
    "life",
    "shopping",
    "finances",
    "leverage",
    "ambition",
    "presence",
    "inbox",
    "later",
    "cancelled",
    "deferred",
    "review",
}


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def bake_to_github(data: dict) -> dict:
    if not isinstance(data, dict) or not data:
        raise ValueError("expected non-empty data object")

    # localStorage values are always strings
    clean = {str(k): ("" if v is None else str(v)) for k, v in data.items()}

    html = DASHBOARD.read_text(encoding="utf-8")
    start = html.find(BAKE_START)
    if start < 0:
        raise RuntimeError("baked-data script not found in everything.html")
    obj_start = start + len(BAKE_START)
    end = html.find(BAKE_END, obj_start)
    if end < 0:
        raise RuntimeError("baked-data script end marker not found")

    payload = json.dumps(clean, ensure_ascii=False, separators=(",", ":"))
    new_html = html[:obj_start] + payload + html[end:]
    DASHBOARD.write_text(new_html, encoding="utf-8")
    DUMP.write_text(json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with GIT_LOCK:
        status = _git("status", "--porcelain")
        if status.returncode != 0:
            raise RuntimeError(status.stderr.strip() or "git status failed")
        if not status.stdout.strip():
            return {"ok": True, "committed": False, "message": "already up to date"}

        add = _git("add", "everything.html", "localStorage_dump.json")
        if add.returncode != 0:
            raise RuntimeError(add.stderr.strip() or "git add failed")

        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        msg = f"Bake browser dashboard state ({stamp})."
        commit = _git(
            "commit",
            "-m",
            msg,
            "-m",
            "Persist phone/browser localStorage into everything.html and localStorage_dump.json for durable GitHub sync.",
        )
        if commit.returncode != 0:
            raise RuntimeError(commit.stderr.strip() or commit.stdout.strip() or "git commit failed")

        branch = _git("rev-parse", "--abbrev-ref", "HEAD")
        branch_name = (branch.stdout or "main").strip()
        push = _git("push", "-u", "origin", branch_name)
        if push.returncode != 0:
            raise RuntimeError(push.stderr.strip() or push.stdout.strip() or "git push failed")

        sha = _git("rev-parse", "--short", "HEAD")
        return {
            "ok": True,
            "committed": True,
            "branch": branch_name,
            "sha": (sha.stdout or "").strip(),
            "keys": len(clean),
        }


def _day_block_bounds(html: str, date: str) -> tuple[int, int, int]:
    """Return (marker_i, block_start, block_end) for a dated day-block.

    Must match the real <div class="day-block" data-date="..."> — not CSS/JS
    mentions of the same date string (prototype.html quotes Aug 30 in selectors).
    """
    date = str(date or "").strip()
    marker = f'data-date="{date}"'
    block_re = re.compile(
        r'<div\b(?=[^>]*\bclass="[^"]*\bday-block\b)(?=[^>]*\bdata-date="'
        + re.escape(date)
        + r'")[^>]*>',
        re.IGNORECASE,
    )
    m = block_re.search(html)
    if not m:
        raise ValueError(f"day block {date} not found")
    block_start = m.start()
    marker_i = html.find(marker, block_start)
    if marker_i < 0 or marker_i > m.end():
        marker_i = block_start
    # Next dated day-block (or doha/archive) ends this one.
    nxt = re.search(r'\n<div class="day-block[^"]*"\s+data-date="', html[m.end() :])
    block_end = (m.end() + nxt.start()) if nxt else len(html)
    return marker_i, block_start, block_end


TILE_RE = re.compile(
    r'<article\b[^>]*\bclass="[^"]*\bvision-tile\b[^"]*"[^>]*>.*?</article>',
    re.IGNORECASE | re.DOTALL,
)


def _tile_key(chunk: str) -> str:
    fm = re.search(r'data-focus="([^"]+)"', chunk, re.I)
    tm = re.search(r'<h3 class="vision-tile-title"[^>]*>([^<]+)</h3>', chunk, re.I)
    key = (fm.group(1) if fm else "") or (tm.group(1) if tm else "")
    return re.sub(r"\s+", " ", key).strip().lower()


def _tile_aliases(key: str) -> set[str]:
    k = re.sub(r"\s+", " ", str(key or "")).strip().lower()
    out = {k, k.replace(" ", "-")}
    pairs = (
        ("gym", "body"),
        ("finances", "abundance"),
        ("lifestyle", "curated lifestyle"),
        ("curated-lifestyle", "curated lifestyle"),
        ("ambition", "executive"),
        ("grad school", "pepperdine"),
        ("grad", "pepperdine"),
        ("god conscious", "god-conscious"),
        ("villain", "villains"),
        ("fight-back", "fight back"),
        ("inner-fire", "inner fire"),
        ("glow-up", "glow up"),
    )
    for a, b in pairs:
        if k in (a, b, a.replace(" ", "-"), b.replace(" ", "-")):
            out.update((a, b, a.replace(" ", "-"), b.replace(" ", "-")))
    return {x for x in out if x}


def _tiles_from_inner(inner: str) -> list[tuple[str, str]]:
    return [(_tile_key(m.group(0)), m.group(0)) for m in TILE_RE.finditer(inner or "")]


def merge_hero_inner(existing_inner: str, new_inner: str, removed=None) -> str:
    """Keep tiles the incoming HTML forgot, unless they were explicitly removed."""
    removed_set: set[str] = set()
    if isinstance(removed, (list, tuple)):
        for item in removed:
            removed_set |= _tile_aliases(str(item))
    new_tiles = _tiles_from_inner(new_inner)
    if not new_tiles:
        return existing_inner if str(existing_inner or "").strip() else str(new_inner or "")
    have: set[str] = set()
    for key, _chunk in new_tiles:
        have |= _tile_aliases(key)
    merged = list(new_tiles)
    for key, chunk in _tiles_from_inner(existing_inner):
        aliases = _tile_aliases(key)
        if aliases & removed_set or aliases & have:
            continue
        merged.append((key, chunk))
        have |= aliases
    out = "\n".join(chunk for _key, chunk in merged)
    if out and not out.endswith("\n"):
        out += "\n"
    return out


def _vision_hero_span(html: str, date: str) -> tuple[int, int]:
    """Return (start_inner, end_inner) for the real .vision-hero in a dated day-block."""
    date = str(date or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError(f"invalid overview date: {date}")
    marker_i, block_start, block_end = _day_block_bounds(html, date)
    tag_re = re.compile(
        r'<div\b[^>]*\bclass="[^"]*\bvision-hero\b[^"]*"[^>]*>',
        re.IGNORECASE,
    )
    m = tag_re.search(html, block_start, block_end)
    if not m:
        raise ValueError(f"vision-hero div for {date} not found inside day block")
    open_end = m.end() - 1
    if html[open_end] != ">":
        raise ValueError(f"vision-hero tag for {date} is malformed")
    pos = open_end + 1
    depth = 1
    start_inner = pos
    end_inner = -1
    while pos < block_end:
        next_open = html.find("<div", pos)
        next_close = html.find("</div>", pos)
        if next_close < 0 or next_close >= block_end:
            raise ValueError(f"unclosed vision-hero for {date}")
        if next_open >= 0 and next_open < next_close and next_open < block_end:
            depth += 1
            pos = next_open + 4
            continue
        depth -= 1
        if depth == 0:
            end_inner = next_close
            break
        pos = next_close + 6
    if end_inner < 0:
        raise ValueError(f"could not parse vision-hero for {date}")
    return start_inner, end_inner


def replace_vision_hero_inner(html: str, date: str, new_inner: str) -> str:
    """Replace children of the real .vision-hero div inside a dated day-block.

    CRITICAL: never match the bare substring "vision-hero" (it appears inside JS
    strings in June 22 migrations). Matching those used to splice collage HTML
    into the middle of a .replace(/.../) and swallow every later day.
    """
    date = str(date or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError(f"invalid overview date: {date}")

    start_inner, end_inner = _vision_hero_span(html, date)

    inner = str(new_inner or "")
    if inner and not inner.endswith("\n"):
        inner += "\n"
    new_html = html[:start_inner] + inner + html[end_inner:]

    # Integrity: never allow the known mid-regex splice corruption, and never
    # delete later day markers that existed before the write.
    if '.replace(/<h3 class="vision-tile-title">\n<article' in new_html:
        raise ValueError("refusing save: would corrupt power-purpose JS splice")
    for later in ("2026-06-23", "2026-08-28", "2026-08-29", "2026-08-30"):
        marker_later = f'data-date="{later}"'
        if marker_later in html and marker_later not in new_html:
            raise ValueError(f"refusing save: would delete day block {later}")
    return new_html


OVERVIEW_FILES = (DASHBOARD, ROOT / "prototype.html")


def save_overview_hero(date: str, hero_html: str, removed_sections=None) -> dict:
    """Write vision-collage hero HTML into everything.html and prototype.html."""
    written: list[str] = []
    warnings: list[str] = []
    for path in OVERVIEW_FILES:
        if not path.exists():
            continue
        try:
            html = path.read_text(encoding="utf-8")
            start_inner, end_inner = _vision_hero_span(html, date)
            merged = merge_hero_inner(html[start_inner:end_inner], hero_html, removed_sections)
            new_html = replace_vision_hero_inner(html, date, merged)
            if new_html != html:
                path.write_text(new_html, encoding="utf-8")
            written.append(path.name)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{path.name}: {exc}")
    if not written:
        raise ValueError(warnings[0] if warnings else "no overview file written")

    with GIT_LOCK:
        status = _git("status", "--porcelain")
        if status.returncode != 0:
            return {
                "ok": True,
                "committed": False,
                "pushed": False,
                "date": date,
                "files": written,
                "warning": status.stderr.strip() or "git status failed",
            }
        if not status.stdout.strip():
            return {
                "ok": True,
                "committed": False,
                "pushed": False,
                "date": date,
                "files": written,
                "message": "already up to date",
            }

        add = _git("add", *[name for name in ("everything.html", "prototype.html") if name in written])
        if add.returncode != 0:
            return {
                "ok": True,
                "committed": False,
                "pushed": False,
                "date": date,
                "files": written,
                "warning": add.stderr.strip() or "git add failed",
            }

        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        msg = f"Save overview collage for {date} ({stamp})."
        commit = _git("commit", "-m", msg)
        if commit.returncode != 0:
            return {
                "ok": True,
                "committed": False,
                "pushed": False,
                "date": date,
                "warning": commit.stderr.strip() or commit.stdout.strip() or "git commit failed",
            }

        branch = _git("rev-parse", "--abbrev-ref", "HEAD")
        branch_name = (branch.stdout or "main").strip()
        push = _git("push", "-u", "origin", branch_name)
        if push.returncode != 0:
            sha = _git("rev-parse", "--short", "HEAD")
            return {
                "ok": True,
                "committed": True,
                "pushed": False,
                "date": date,
                "branch": branch_name,
                "sha": (sha.stdout or "").strip(),
                "warning": push.stderr.strip() or push.stdout.strip() or "git push failed",
            }

        sha = _git("rev-parse", "--short", "HEAD")
        return {
            "ok": True,
            "committed": True,
            "pushed": True,
            "date": date,
            "branch": branch_name,
            "sha": (sha.stdout or "").strip(),
        }


def save_brain_dump(entries) -> dict:
    """Write brain-dump entries into brain-dump.html. Does not git commit."""
    if not isinstance(entries, list):
        raise ValueError("expected entries array")

    clean = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        section = str(item.get("section") or "inbox").strip().lower()
        if section not in ALLOWED_SECTIONS:
            section = "inbox"
        clean.append(
            {
                "id": str(item.get("id") or "")[:80],
                "text": text[:4000],
                "section": section,
                "at": str(item.get("at") or "")[:80],
            }
        )

    html = BRAIN.read_text(encoding="utf-8")
    start = html.find(BRAIN_START)
    if start < 0:
        raise RuntimeError("brain-dump-data marker missing")
    obj_start = start + len(BRAIN_START)
    end = html.find(BRAIN_END, obj_start)
    if end < 0:
        raise RuntimeError("brain-dump-data end marker missing")

    payload = json.dumps(clean, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c")
    tmp = BRAIN.with_name("brain-dump.html.tmp")
    tmp.write_text(html[:obj_start] + payload + html[end:], encoding="utf-8")
    tmp.replace(BRAIN)
    return {"ok": True, "count": len(clean)}


def _photo_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")[:48]
    return slug or "card"


def _load_photo_map() -> dict:
    try:
        raw = json.loads(PHOTO_MAP.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _save_photo_map(data: dict) -> None:
    STORAGE.mkdir(parents=True, exist_ok=True)
    PHOTO_MAP.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _http_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": "diana-dashboard/1.0 (photo-for)"})
    with urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "diana-dashboard/1.0 (photo-for)"})
    with urlopen(req, timeout=18) as resp:
        return resp.read()


def _photo_bytes_usable(data: bytes | None) -> bool:
    """Reject empty, tiny, or near-black JPEGs that read as blank thumbnails."""
    if not data or len(data) < 20000:
        return False
    try:
        from io import BytesIO
        from PIL import Image

        im = Image.open(BytesIO(data)).convert("RGB")
        w, h = im.size
        if w < 64 or h < 64:
            return False
        # Sample ~4k pixels for mean luminance
        step = max(1, (w * h) // 4000)
        pixels = list(im.getdata())[::step]
        if not pixels:
            return False
        avg = sum(sum(c) for c in pixels) / (len(pixels) * 3.0)
        dark = sum(1 for c in pixels if (sum(c) / 3.0) < 18) / float(len(pixels))
        if avg < 22 or dark > 0.92:
            return False
        return True
    except Exception:
        # Without PIL, still require a reasonably sized blob
        return len(data) >= 40000


def _photo_path_usable(path: Path) -> bool:
    try:
        if not path.exists() or not path.is_file():
            return False
        return _photo_bytes_usable(path.read_bytes())
    except Exception:
        return False


def _archive_bad_photo(path: Path) -> None:
    try:
        if not path.exists():
            return
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        archived = path.with_name(f"{path.stem}-bad-{stamp}{path.suffix}")
        path.replace(archived)
    except Exception:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass


def _fetch_still_life(name: str) -> bytes | None:
    query = f"{name} still life object"
    try:
        ov = _http_json(
            "https://api.openverse.org/v1/images/?"
            + urlencode({"q": query, "page_size": "8", "license_type": "commercial"})
        )
        for hit in ov.get("results") or []:
            title = str(hit.get("title") or "")
            tags = " ".join(
                t.get("name", "") if isinstance(t, dict) else str(t)
                for t in (hit.get("tags") or [])
            )
            if PHOTO_SKIP.search(title) or PHOTO_SKIP.search(tags):
                continue
            url = hit.get("url") or hit.get("thumbnail")
            if url:
                data = _http_bytes(str(url))
                if _photo_bytes_usable(data):
                    return data
    except Exception:
        pass
    try:
        wm = _http_json(
            "https://commons.wikimedia.org/w/api.php?"
            + urlencode(
                {
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": query,
                    "gsrnamespace": "6",
                    "gsrlimit": "8",
                    "prop": "imageinfo",
                    "iiprop": "url",
                    "iiurlwidth": "900",
                    "format": "json",
                }
            )
        )
        pages = ((wm.get("query") or {}).get("pages") or {})
        for page in pages.values():
            title = str(page.get("title") or "")
            if PHOTO_SKIP.search(title):
                continue
            info = (page.get("imageinfo") or [{}])[0]
            url = info.get("thumburl") or info.get("url")
            if url:
                data = _http_bytes(str(url))
                if _photo_bytes_usable(data):
                    return data
    except Exception:
        pass
    return None


def photo_for_name(name: str) -> dict:
    key = " ".join(str(name or "").replace("\u2011", "-").split()).strip().lower()
    if not key:
        return {"ok": False, "error": "empty"}
    with PHOTO_LOCK:
        stored = _load_photo_map()
        cached = stored.get(key) or KNOWN_CARD_PHOTOS.get(key)
        if cached:
            path = ROOT / str(cached).split("?", 1)[0]
            if path.exists() and _photo_path_usable(path):
                stored[key] = cached
                _save_photo_map(stored)
                return {"ok": True, "src": cached, "cached": True}
            # Stale map pointing at a missing or blank/black file — drop it
            if path.exists() and not _photo_path_usable(path):
                # Don't delete known/preset assets in KNOWN_CARD_PHOTOS unless
                # they failed usability (e.g. prior bad auto-fetch overwrite).
                if key not in KNOWN_CARD_PHOTOS or str(cached).split("?", 1)[0] == f"manus-storage/card-{_photo_slug(key)}.jpg":
                    if key not in KNOWN_CARD_PHOTOS:
                        _archive_bad_photo(path)
            stored.pop(key, None)
        dest = STORAGE / f"card-{_photo_slug(key)}.jpg"
        if dest.exists():
            if _photo_path_usable(dest):
                src = f"manus-storage/{dest.name}"
                stored[key] = src
                _save_photo_map(stored)
                return {"ok": True, "src": src, "cached": True}
            _archive_bad_photo(dest)
        blob = _fetch_still_life(key)
        if not blob:
            # Fall back to a known good preset if we have one on disk
            known = KNOWN_CARD_PHOTOS.get(key)
            if known:
                kpath = ROOT / str(known).split("?", 1)[0]
                if _photo_path_usable(kpath):
                    stored[key] = known
                    _save_photo_map(stored)
                    return {"ok": True, "src": known, "cached": True}
            return {"ok": False, "error": "no photo"}
        dest.write_bytes(blob)
        src = f"manus-storage/{dest.name}"
        stored[key] = src
        _save_photo_map(stored)
        return {"ok": True, "src": src, "cached": False}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _json(self, code: int, body: dict):
        raw = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/photo-for":
            name = unquote((parse_qs(parsed.query).get("name") or [""])[0])
            try:
                return self._json(200, photo_for_name(name))
            except Exception as e:  # noqa: BLE001
                return self._json(500, {"ok": False, "error": str(e)})
        return super().do_GET()

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/photo-for":
                body = self._read_json()
                name = body.get("name") if isinstance(body, dict) else ""
                return self._json(200, photo_for_name(str(name or "")))
            if path == "/bake":
                body = self._read_json()
                data = body.get("data") if isinstance(body, dict) else None
                result = bake_to_github(data)
                return self._json(200, result)
            if path in ("/brain-dump", "/brain-dump-save"):
                body = self._read_json()
                entries = body.get("entries") if isinstance(body, dict) else None
                result = save_brain_dump(entries)
                return self._json(200, result)
            if path == "/save-overview":
                body = self._read_json()
                date = body.get("date") if isinstance(body, dict) else None
                hero_html = body.get("html") if isinstance(body, dict) else None
                removed = body.get("removedSections") if isinstance(body, dict) else None
                result = save_overview_hero(str(date or ""), str(hero_html or ""), removed)
                return self._json(200, result)
            if path in ("/save", "/move-cards"):
                # Acknowledge UI autosave hooks; durable path is /bake.
                length = int(self.headers.get("Content-Length") or "0")
                if length:
                    self.rfile.read(length)
                return self._json(200, {"ok": True, "ignored": True})
            return self._json(404, {"ok": False, "error": "not found"})
        except Exception as e:  # noqa: BLE001
            return self._json(500, {"ok": False, "error": str(e)})

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    # Avoid serving parent paths; stay in ROOT.
    os.chdir(ROOT)
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"dashboard server on http://127.0.0.1:{PORT}/", flush=True)
    print("POST /bake to persist localStorage into GitHub", flush=True)
    print("POST /brain-dump to write thoughts into brain-dump.html", flush=True)
    print("POST /save-overview to write vision collage into everything.html + prototype.html", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
