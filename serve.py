#!/usr/bin/env python3
"""Dashboard static server with durable GitHub bake.

POST /bake  JSON {"data": {localStorageKey: value, ...}}
  - Writes baked-data.json (idle-seeded by boot-seed.js; not inlined in HTML)
  - Writes localStorage_dump.json
  - Commits and pushes to origin

Also accepts the dashboard's existing /save and /move-cards POSTs
as no-op 200s so the UI does not spam console errors.
"""

from __future__ import annotations

import gzip
import json
import os
import re
import subprocess
import threading
from io import BytesIO
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
SAVE_OVERVIEW_LOCK = threading.Lock()
PHOTO_LOCK = threading.Lock()
PHOTO_MAP = ROOT / "manus-storage" / "card-photos.json"
STORAGE = ROOT / "manus-storage"
KNOWN_CARD_PHOTOS = {
    "induction": "manus-storage/card-induction.jpg",
    "cleanse": "manus-storage/card-cleanse.jpg",
    "application": "manus-storage/card-application.jpg",
    "scholarship": "manus-storage/card-application.jpg",
    "scholarship application": "manus-storage/card-application.jpg",
    "scholarship re-application": "manus-storage/card-application.jpg",
    "scholarship reapplication": "manus-storage/card-application.jpg",
    "tuition": "manus-storage/card-tuition.jpg",
    "tuition payment": "manus-storage/card-tuition.jpg",
    "fall 2026 enrollment": "manus-storage/card-fall-2026-enrollment.jpg",
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
    "refunds": "manus-storage/card-refunds.jpg",
    "enhancv": "manus-storage/card-enhancv.jpg",
    "certified letters": "manus-storage/card-certified-letters.jpg",
    "amazon qr return codes": "manus-storage/card-amazon-qr-return-codes.jpg",
    "amazon return qr codes": "manus-storage/card-amazon-qr-return-codes.jpg",
    "neighbor payment": "manus-storage/card-neighbor-payment.jpg",
    "re: manus restoration issue": "manus-storage/card-re-manus-restoration-issue.jpg",
    # Pepperdine section / zone only — not tuition/application cards
    "calisthenics": "manus-storage/card-calisthenics.jpg",
    "inversions": "manus-storage/card-inversions-yoga.jpg?v=yoga1",
    "pepperdine": "manus-storage/zone-achieve-csol.jpg?v=csol2",
    "enroll": "manus-storage/zone-achieve-csol.jpg?v=csol2",
    "achieve": "manus-storage/zone-achieve-csol.jpg?v=csol2",
    "I will achieve": "manus-storage/zone-achieve-csol.jpg?v=csol2",
    "I will succeed": "manus-storage/zone-achieve-csol.jpg?v=csol2",
    "i will succeed": "manus-storage/zone-achieve-csol.jpg?v=csol2",
    "succeed": "manus-storage/zone-achieve-csol.jpg?v=csol2",
    "to succeed": "manus-storage/zone-achieve-csol.jpg?v=csol2",
    "i will achieve": "manus-storage/zone-achieve-csol.jpg?v=csol2",
    "grad school": "manus-storage/zone-achieve-csol.jpg?v=csol2",
    "grad": "manus-storage/zone-achieve-csol.jpg?v=csol2",
    "soul": "",
    # sorrow is NOT soul — distinct focus; no approved photo (was soul-rose duplicate)
    "sorrow": "",
    "attention": "manus-storage/zone-attention.jpg?v=beam1",
    "anticipate": "manus-storage/zone-attention.jpg?v=beam1",
    "inner fire": "manus-storage/zone-inner-fire.jpg?v=spark1",
    "inner-fire": "manus-storage/zone-inner-fire.jpg?v=spark1",
    "ignite": "manus-storage/zone-inner-fire.jpg?v=spark1",
    "glow up": "manus-storage/zone-glow-up.jpg?v=glow6",
    "luscious hair": "manus-storage/card-luscious-hair-lux.jpg?v=lux1",
    "glass skin": "manus-storage/card-glass-skin-cheek.jpg?v=cheek1",
    "facial tone": "manus-storage/card-facial-tone-sculpt.jpg?v=sculpt1",
    "facial structure": "manus-storage/card-facial-tone-sculpt.jpg?v=sculpt1",
    "aligned teeth": "manus-storage/card-aligned-teeth.jpg?v=glow4",
    "glow-up": "manus-storage/zone-glow-up.jpg?v=glow6",
    "glow": "manus-storage/zone-glow-up.jpg?v=glow6",
    "she pursues": "manus-storage/zone-she-pursues.jpg?v=pursue1",
    "she-pursues": "manus-storage/zone-she-pursues.jpg?v=pursue1",
    "pursue": "manus-storage/zone-she-pursues.jpg?v=pursue1",
    "I will pursue": "manus-storage/zone-she-pursues.jpg?v=pursue1",
    "i will pursue": "manus-storage/zone-she-pursues.jpg?v=pursue1",
    "I pursue": "manus-storage/zone-she-pursues.jpg?v=pursue1",
    "i pursue": "manus-storage/zone-she-pursues.jpg?v=pursue1",
    "to glow up": "manus-storage/zone-glow-up.jpg?v=glow6",
    "i glow up": "manus-storage/zone-glow-up.jpg?v=glow6",
    "I glow up": "manus-storage/zone-glow-up.jpg?v=glow6",
    "I will glow up": "manus-storage/zone-glow-up.jpg?v=glow6",
    "i will glow up": "manus-storage/zone-glow-up.jpg?v=glow6",
    "darkness": "",
    "audacity": "manus-storage/zone-audacity.jpg?v=finger1",
    "fight": "manus-storage/zone-audacity.jpg?v=finger1",
    "remember who you are": "manus-storage/zone-audacity.jpg?v=finger1",
    "politics": "manus-storage/zone-politics.jpg?v=chess5",
    "repetitions": "manus-storage/zone-repetitions.jpg?v=cubes1",
    "repeat 10,000 times": "manus-storage/zone-repetitions.jpg?v=cubes1",
    "repeat 10000 times": "manus-storage/zone-repetitions.jpg?v=cubes1",
    "repeat-10000-times": "manus-storage/zone-repetitions.jpg?v=cubes1",
    "wins": "manus-storage/zone-wins.jpg?v=game2",
    "win": "manus-storage/zone-wins.jpg?v=game2",
    "I will win": "manus-storage/zone-wins.jpg?v=game2",
    "i will win": "manus-storage/zone-wins.jpg?v=game2",
    "I win": "manus-storage/zone-wins.jpg?v=game2",
    # abundance — approved money-tree (wheat/plenty2 forever banned)
    "abundance": "manus-storage/zone-abundance-tree.jpg?v=tree1",
    "abundant": "manus-storage/zone-abundance-tree.jpg?v=tree1",
    "receive": "manus-storage/zone-abundance-tree.jpg?v=tree1",
    "ask": "manus-storage/zone-abundance-tree.jpg?v=tree1",
    "finances": "manus-storage/zone-abundance-tree.jpg?v=tree1",
    "become": "manus-storage/zone-envision.jpg?v=swap1",
    "future": "manus-storage/zone-envision.jpg?v=swap1",
    "align": "manus-storage/zone-alignment.jpg?v=align1",
    "workflow": "manus-storage/zone-plan.jpg?v=swap1",
    "to workflow": "manus-storage/zone-plan.jpg?v=swap1",
    "i workflow": "manus-storage/zone-plan.jpg?v=swap1",
    "I workflow": "manus-storage/zone-plan.jpg?v=swap1",
    "I will workflow": "manus-storage/zone-plan.jpg?v=swap1",
    "start": "manus-storage/zone-plan.jpg?v=swap1",
    "to start": "manus-storage/zone-plan.jpg?v=swap1",
    "i start": "manus-storage/zone-plan.jpg?v=swap1",
    "I start": "manus-storage/zone-plan.jpg?v=swap1",
    "I will start": "manus-storage/zone-plan.jpg?v=swap1",
    "to-start": "manus-storage/zone-plan.jpg?v=swap1",
    "navigate": "manus-storage/zone-plan.jpg?v=swap1",
    "to navigate": "manus-storage/zone-plan.jpg?v=swap1",
    "i navigate": "manus-storage/zone-plan.jpg?v=swap1",
    "I navigate": "manus-storage/zone-plan.jpg?v=swap1",
    "I will navigate": "manus-storage/zone-plan.jpg?v=swap1",
    "to-navigate": "manus-storage/zone-plan.jpg?v=swap1",
    "alignment": "manus-storage/zone-alignment.jpg?v=align1",
    "train": "manus-storage/zone-athletic.jpg?v=color2",
    "i train": "manus-storage/zone-athletic.jpg?v=color2",
    "I train": "manus-storage/zone-athletic.jpg?v=color2",
    "I will train": "manus-storage/zone-athletic.jpg?v=color2",
    "i will train": "manus-storage/zone-athletic.jpg?v=color2",
    "fitness training": "manus-storage/zone-athletic.jpg?v=color2",
    "surrender to allah": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "surrender myself": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "i surrender myself": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "I surrender myself": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "I will surrender myself": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "surrender myself": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "i surrender myself": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "I surrender myself": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "I surrender myself to Allah \ufdfb": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "I will surrender myself to Allah \ufdfb": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "I will surrender to Allah \ufdfb": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "I will surrender": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "surrender to Allah \ufdfb": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "i surrender myself to allah": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "surrender myself to Allah \ufdfb": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "surrender-to-allah": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "surrender to allah \ufdfb": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "itaqallah": "manus-storage/zone-god-conscious.jpg?v=remembrance1",
    "detach": "manus-storage/zone-detach-silhouette-woman.jpg?v=woman1",
    "start over": "manus-storage/zone-start-over-positano.jpg?v=travel1",
    "start-over": "manus-storage/zone-start-over-positano.jpg?v=travel1",
    "create again": "manus-storage/zone-start-over-positano.jpg?v=travel1",
    "create-again": "manus-storage/zone-start-over-positano.jpg?v=travel1",
    "travel": "manus-storage/zone-start-over-positano.jpg?v=travel1",
    "to travel": "manus-storage/zone-start-over-positano.jpg?v=travel1",
    "i travel": "manus-storage/zone-start-over-positano.jpg?v=travel1",
    "I travel": "manus-storage/zone-start-over-positano.jpg?v=travel1",
    "I will travel": "manus-storage/zone-start-over-positano.jpg?v=travel1",
    "to-travel": "manus-storage/zone-start-over-positano.jpg?v=travel1",
    "tune into": "",
    "tune-into": "",
    "self-actualize": "",
    "self actualize": "",
    "claim": "",
    "sabotage": "manus-storage/zone-sabotage.jpg?v=1",
    "say thank you in advance": "manus-storage/zone-say-thank-you-in-advance.jpg?v=advance1",
    "say-thank-you-in-advance": "manus-storage/zone-say-thank-you-in-advance.jpg?v=advance1",
    "execute": "manus-storage/zone-execute-focus.jpg?v=chess1",
    "to seize opportunities": "manus-storage/zone-seize-opportunities.jpg?v=seize4",
    "i seize opportunities": "manus-storage/zone-seize-opportunities.jpg?v=seize4",
    "I seize opportunities": "manus-storage/zone-seize-opportunities.jpg?v=seize4",
    "I will seize opportunities": "manus-storage/zone-seize-opportunities.jpg?v=seize4",
    "seize opportunities": "manus-storage/zone-seize-opportunities.jpg?v=seize4",
    "seize-opportunities": "manus-storage/zone-seize-opportunities.jpg?v=seize4",
    "seize": "manus-storage/zone-seize-opportunities.jpg?v=seize4",
    "scholarship application": "manus-storage/zone-scholarship-application.jpg?v=app1",
    "to litigate": "manus-storage/zone-to-litigate.jpg?v=court1",
    "i litigate": "manus-storage/zone-to-litigate.jpg?v=court1",
    "I litigate": "manus-storage/zone-to-litigate.jpg?v=court1",
    "I will litigate": "manus-storage/zone-to-litigate.jpg?v=court1",
    "litigate": "manus-storage/zone-to-litigate.jpg?v=court1",
    "to-litigate": "manus-storage/zone-to-litigate.jpg?v=court1",
    "to recoup": "manus-storage/zone-to-recoup.jpg?v=villa1",
    "i recoup": "manus-storage/zone-to-recoup.jpg?v=villa1",
    "I recoup": "manus-storage/zone-to-recoup.jpg?v=villa1",
    "I will recoup": "manus-storage/zone-to-recoup.jpg?v=villa1",
    "I recoup every dollar": "manus-storage/zone-to-recoup.jpg?v=villa1",
    "I will recoup every dollar": "manus-storage/zone-to-recoup.jpg?v=villa1",
    "i recoup every dollar": "manus-storage/zone-to-recoup.jpg?v=villa1",
    "recoup": "manus-storage/zone-to-recoup.jpg?v=villa1",
    "to-recoup": "manus-storage/zone-to-recoup.jpg?v=villa1",
    "to scholarship application": "manus-storage/zone-scholarship-application.jpg?v=app1",
    "i scholarship application": "manus-storage/zone-scholarship-application.jpg?v=app1",
    "I scholarship application": "manus-storage/zone-scholarship-application.jpg?v=app1",
    "I will scholarship application": "manus-storage/zone-scholarship-application.jpg?v=app1",
    "scholarship-application": "manus-storage/zone-scholarship-application.jpg?v=app1",
    "to-scholarship-application": "manus-storage/zone-scholarship-application.jpg?v=app1",
    "curate": "manus-storage/zone-to-curate-select.jpg?v=select1",
    "to curate": "manus-storage/zone-to-curate-select.jpg?v=select1",
    "i curate": "manus-storage/zone-to-curate-select.jpg?v=select1",
    "I curate": "manus-storage/zone-to-curate-select.jpg?v=select1",
    "I will curate": "manus-storage/zone-to-curate-select.jpg?v=select1",
    "to-curate": "manus-storage/zone-to-curate-select.jpg?v=select1",
    "to love": "manus-storage/zone-to-love-souls.jpg?v=souls3",
    "i love": "manus-storage/zone-to-love-souls.jpg?v=souls3",
    "I love": "manus-storage/zone-to-love-souls.jpg?v=souls3",
    "I will love": "manus-storage/zone-to-love-souls.jpg?v=souls3",
    "to persevere": "manus-storage/zone-to-persevere-continue.jpg?v=go1",
    "i persevere": "manus-storage/zone-to-persevere-continue.jpg?v=go1",
    "I persevere": "manus-storage/zone-to-persevere-continue.jpg?v=go1",
    "I will persevere": "manus-storage/zone-to-persevere-continue.jpg?v=go1",
    "to feel": "",
    "i feel": "",
    "I feel": "",
    "I will feel": "",
    "to-feel": "",
    "tofeel": "",
    "feel": "",
    "to channel": "manus-storage/zone-to-channel-souls.jpg?v=souls1",
    "i channel": "manus-storage/zone-to-channel-souls.jpg?v=souls1",
    "I channel": "manus-storage/zone-to-channel-souls.jpg?v=souls1",
    "I will channel": "manus-storage/zone-to-channel-souls.jpg?v=souls1",
    "to-channel": "manus-storage/zone-to-channel-souls.jpg?v=souls1",
    "tochannel": "manus-storage/zone-to-channel-souls.jpg?v=souls1",
    "channel": "manus-storage/zone-to-channel-souls.jpg?v=souls1",
    "to-persevere": "manus-storage/zone-to-persevere-continue.jpg?v=go1",
    "topersevere": "manus-storage/zone-to-persevere-continue.jpg?v=go1",
    "persevere": "manus-storage/zone-to-persevere-continue.jpg?v=go1",
    "to-love": "manus-storage/zone-to-love-souls.jpg?v=souls3",
    "tolove": "manus-storage/zone-to-love-souls.jpg?v=souls3",
}
# Forever-banned section photo URL substrings (candle / people / rejected conceptuals).
# Never return these from /photo-for for soul, sorrow, darkness, abundance, attention.
# soul ≠ sorrow — never alias them.
REJECTED_SECTION_PHOTOS = (
    "zone-to-feel-rain",
    "zone-to-feel-heart",
    "zone-to-love-rings",
    "zone-to-love-aurora",
    "zone-tune-into-field",
    "zone-self-actualize-maslow",
    "zone-to-persevere-peaks",
    "zone-to-persevere-resolve",
    "zone-soul-flame",
    "zone-soul-heal",
    "zone-soul-chair",
    "zone-soul-depth",
    "zone-soul-dua",
    "zone-soul-heart",
    "zone-soul-glance-heart",
    "zone-soul-mosque",
    "zone-soul-presence",
    "zone-soul-still-water",
    "zone-soul-candle",
    "zone-tune-into-radio",
    "zone-soul-person-window",
    "zone-soul.jpg?v=nopeople",
    "zone-soul.jpg?v=heal",
    "zone-soul.jpg?v=flame",
    "zone-soul.jpg?v=inner",
    "zone-soul.jpg?v=presence",
    "zone-soul.jpg?v=soul2",
    "zone-soul.jpg",
    "zone-sorrow.jpg?v=nopeople",
    "zone-sorrow.jpg?v=candle",
    "zone-sorrow.jpg?v=sorrow1",
    "zone-sorrow.jpg?v=heal",
    # entire zone-sorrow.jpg was a copy of soul rose — never treat as sorrow photo
    "zone-sorrow.jpg",
    "zone-darkness-aware",
    "zone-darkness-inner",
    "zone-darkness-night-street",
    "zone-darkness-person-storm",
    "zone-darkness-storm-study",
    "zone-darkness-candle",
    "zone-darkness-battle",
    "zone-darkness-night-void",
    "zone-darkness-ink-abyss",
    "zone-darkness-room",
    "zone-darkness.jpg?v=nopeople",
    "zone-darkness.jpg?v=inner",
    "zone-darkness.jpg?v=aware",
    "zone-darkness.jpg?v=storm",
    "zone-darkness.jpg?v=void1",
    "zone-darkness.jpg",
    "person-storm",
    "person-window",
    "heal3",
    "inner3",
    "/archive/zone-soul-",
    "/archive/zone-darkness-",
    "candle-archive",
    "candle-flame",
    "candle-aware",
    # abundance — ALL wheat fields / harvest / plenty2 forever banned
    "zone-abundance.jpg",
    "zone-finances-v2",
    "plenty2",
    "plenty1",
    "abundance-wheat",
    "abundance-wheat-sunset",
    "wheat-sunset",
    "zone-abundance-harvest",
    "zone-abundance-overflow",
    "abundance-bg.jpg",
    "abundance-grapes",
    "abundance-poppies",
    # prosperity gold bars (abundance-bg-wealth / prosperity-bg-gold-bars) is NOT banned — not wheat
    # prosperity page photo deleted (was prosperity-bg-money-magnet.jpg) — leave empty
    # legacy fight-back coral tile — audacity uses finger photo only
    "zone-fight-back",
    # detach / start over — rope + old leaf + dawn road forever banned
    "zone-detach.jpg",
    "zone-detach-leaf",
    "zone-detach-rope",
    "zone-detach-silhouette.jpg",
    "zone-to-love-aurora",
    "zone-start-over.jpg",
    "zone-start-over-road",
    "zone-start-over-openroad",
    # self-actualize — rejected AI cairn + mountain summit (not Maslow hierarchy)
    "zone-self-actualize-summit",
    "zone-self-actualize.jpg",
    # to channel — abstract single-core field (no shared souls) forever banned
    "zone-to-channel.jpg?v=field1",
    "zone-to-channel-luminous",
    "zone-to-channel-irrigation",
    "zone-to-channel.jpg?v=canal",
    "zone-seize-opportunities.jpg?v=seize1",
    "zone-seize-opportunities.jpg?v=seize3",
    "zone-seize-opportunities-door-banned",
    "zone-seize-opportunities-racing-banned",
    "/archive/zone-seize-opportunities-door",
    "/archive/zone-seize-opportunities-racing",
    # to curate — paintbrushes / wet paint / studio painting forever banned
    "zone-curate-create",
    "zone-curate-create.jpg?v=create1",
    "/archive/zone-curate-create-paint",
)
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

    # Keep the 1.8MB seed off the HTML critical path (boot-seed.js fetches this idle).
    payload = json.dumps(clean, ensure_ascii=False, separators=(",", ":"))
    (ROOT / "baked-data.json").write_text(payload, encoding="utf-8")
    DUMP.write_text(json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with GIT_LOCK:
        status = _git("status", "--porcelain")
        if status.returncode != 0:
            raise RuntimeError(status.stderr.strip() or "git status failed")
        if not status.stdout.strip():
            return {"ok": True, "committed": False, "message": "already up to date"}

        add = _git("add", "baked-data.json", "localStorage_dump.json")
        if add.returncode != 0:
            raise RuntimeError(add.stderr.strip() or "git add failed")

        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        msg = f"Bake browser dashboard state ({stamp})."
        commit = _git(
            "commit",
            "-m",
            msg,
            "-m",
            "Persist phone/browser localStorage into baked-data.json and localStorage_dump.json for durable GitHub sync.",
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


def _day_label(date: str) -> str:
    dt = datetime.strptime(date, "%Y-%m-%d")
    mon = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"][dt.month - 1]
    dow = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][dt.weekday()]
    return f"{mon} {dt.day} · {dow}"


def _overview_day_shell(date: str) -> str:
    label = _day_label(date)
    return (
        f'<div class="day-block fmt22 vision-collage-day overview-era-day card-style-deboss-chip make-flow-day collage-flush depth-four-era" data-date="{date}">\n'
        f'<div class="day-dot"></div>\n'
        f'<div class="day-card">\n'
        f'<div class="day-card-header"><span class="day-date">{label}</span></div>\n'
        f'<div class="today-view-toggle">\n'
        f'<button class="tv-pill active" data-view="pursuits">overview</button>\n'
        f'<button class="tv-pill" data-view="impulses">impulses</button>\n'
        f'<button class="tv-pill" data-view="flow">flow</button>\n'
        f'<button class="tv-pill" data-view="nodes">nodes</button>\n'
        f'</div>\n'
        f'<div class="day-tasks">\n'
        f'<div class="tv-panel tv-pursuits active">\n'
        f'<div class="vision-board" aria-label="vision collage">\n'
        f'<button type="button" class="vision-zoom-out" hidden>all of today</button>\n'
        f'<p class="vision-hint">the day, wide — click a focus to go in</p>\n'
        f'<div class="vision-hero">\n'
        f'</div>\n'
        f'</div></div></div></div></div>\n'
    )


def _next_day_block_index(html: str, date: str) -> int:
    """Insert point: first later dated day-block, else doha/archive."""
    best = -1
    for m in re.finditer(r'\n<div class="day-block[^"]*"\s+data-date="([^"]+)"', html):
        other = m.group(1)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", other) and other > date:
            return m.start()
        if other in ("doha", "archive") and best < 0:
            best = m.start()
    return best


def ensure_overview_day_block(html: str, date: str) -> str:
    """Add a vision-collage day shell so /save-overview can bake a missing date."""
    try:
        _day_block_bounds(html, date)
        return html
    except ValueError:
        pass
    insert_at = _next_day_block_index(html, date)
    shell = _overview_day_shell(date)
    if insert_at < 0:
        return html + "\n" + shell
    return html[:insert_at] + "\n" + shell + html[insert_at:]


def ensure_day_on_disk(date: str, page: str = "") -> dict:
    """Persist a missing vision-collage day shell into the page HTML."""
    date = str(date or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError(f"invalid day date: {date}")
    paths = [p for p in _overview_paths_for_page(page) if p.exists()]
    if not paths:
        raise ValueError("overview file not found")
    written: list[str] = []
    created = False
    with SAVE_OVERVIEW_LOCK:
        for path in paths:
            html = path.read_text(encoding="utf-8")
            new_html = ensure_overview_day_block(html, date)
            if new_html != html:
                if "<!DOCTYPE" not in new_html[:80]:
                    raise ValueError(f"refusing save: {path.name} lost its document shell")
                path.write_text(new_html, encoding="utf-8")
                created = True
            written.append(path.name)
    return {"ok": True, "date": date, "files": written, "created": created}


TILE_RE = re.compile(
    r'<article\b[^>]*\bclass="[^"]*\bvision-tile\b[^"]*"[^>]*>.*?</article>',
    re.IGNORECASE | re.DOTALL,
)


def _tile_key(chunk: str) -> str:
    fm = re.search(r'data-focus="([^"]+)"', chunk, re.I)
    tm = re.search(r'<h3 class="vision-tile-title"[^>]*>([^<]+)</h3>', chunk, re.I)
    key = (fm.group(1) if fm else "") or (tm.group(1) if tm else "")
    return re.sub(r"\s+", " ", key).strip().lower()


_SECTION_PREFIX_RE = re.compile(r"^(to|i will|i)[\s-]+")


def _bare_section(key: str) -> str:
    s = re.sub(r"\s+", " ", str(key or "")).strip().lower()
    while _SECTION_PREFIX_RE.match(s):
        s = _SECTION_PREFIX_RE.sub("", s, count=1)
    return s


def _tile_aliases(key: str) -> set[str]:
    k = re.sub(r"\s+", " ", str(key or "")).strip().lower()
    bare = _bare_section(k)
    out = {k, k.replace(" ", "-"), bare, bare.replace(" ", "-")}
    if bare:
        out.update({
            f"to {bare}",
            f"i {bare}",
            f"i will {bare}",
            f"to-{bare.replace(' ', '-')}",
            f"i-{bare.replace(' ', '-')}",
            f"i-will-{bare.replace(' ', '-')}",
        })
    pairs = (
        ("gym", "body"),
        ("toned body", "body"),
        ("toned-body", "body"),
        ("athletic", "body"),
        ("fitness training", "body"),
        ("fitness-training", "body"),
        ("train", "body"),
        ("finances", "abundance"),
        ("abundant", "abundance"),
        ("receive", "abundance"),
        ("ask", "abundance"),
        ("win", "wins"),
        ("become", "future"),
        ("align", "alignment"),
        ("lifestyle", "curated lifestyle"),
        ("curated-lifestyle", "curated lifestyle"),
        ("ambition", "executive"),
        ("grad school", "pepperdine"),
        ("grad", "pepperdine"),
        ("enroll", "pepperdine"),
        ("achieve", "pepperdine"),
        ("god conscious", "god-conscious"),
        ("villain", "villains"),
        ("fight-back", "audacity"),
        ("fight back", "audacity"),
        ("remember who you are", "audacity"),
        ("fight", "audacity"),
        ("inner-fire", "inner fire"),
        ("ignite", "inner fire"),
        ("glow-up", "glow up"),
        ("art | science", "art-science"),
        ("art/science", "art-science"),
        ("self esteem", "self-esteem"),
        ("selfesteem", "self-esteem"),
        ("god conscious", "itaq-allah"),
        ("god-conscious", "itaq-allah"),
        ("awliya allah", "itaq-allah"),
        ("awliya-allah", "itaq-allah"),
        ("awliya allah swt", "itaq-allah"),
        ("awliya-allah-swt", "itaq-allah"),
        ("awliyah allah swt", "itaq-allah"),
        ("fear allah", "itaq-allah"),
        ("fear-allah", "itaq-allah"),
        ("fear allah \ufdfb", "itaq-allah"),
        ("itaqallah", "itaq-allah"),
        ("itaqAllah", "itaq-allah"),
    )
    for a, b in pairs:
        names = (a, b, a.replace(" ", "-"), b.replace(" ", "-"))
        if k in names or bare in names:
            out.update(names)
    return {x for x in out if x}


def _tiles_from_inner(inner: str) -> list[tuple[str, str]]:
    return [(_tile_key(m.group(0)), m.group(0)) for m in TILE_RE.finditer(inner or "")]


_SWALLOW_RE = re.compile(
    r'(<h4 class="vision-subsection-title">[^<]*</h4></article>)(\s*)(<article class="vision-tile")',
    re.I,
)


def unswallow_hero_inner(inner: str) -> str:
    """Close fitness tiles that swallowed later .vision-tile siblings."""
    text = str(inner or "")
    prev = None
    while prev != text:
        prev = text
        text = _SWALLOW_RE.sub(r"\1</div></article>\2\3", text)
    return text


# Titles Diana archived that a restore/merge must never put back on Aug 30.
AUG30_ARCHIVED_EXTRAS = {
    "pursuits", "power", "purpose", "phd", "ph.d", "ph-d", "focus",
    "strengths", "plan", "envision", "fight back", "fight-back", "remember who you are", "fight",
    "villains", "potential", "ambition",
}


def _drop_key_set(items) -> set[str]:
    out: set[str] = set()
    if not items:
        return out
    for item in items:
        out |= _tile_aliases(str(item))
    return out


def merge_hero_inner(existing_inner: str, new_inner: str, removed=None, drop_keys=None) -> str:
    """Keep tiles the incoming HTML forgot, unless they were explicitly removed."""
    existing_inner = unswallow_hero_inner(existing_inner)
    new_inner = unswallow_hero_inner(new_inner)
    removed_set: set[str] = _drop_key_set(removed)
    drop_set: set[str] = _drop_key_set(drop_keys)
    ban = removed_set | drop_set
    new_tiles = [
        (key, chunk) for key, chunk in _tiles_from_inner(new_inner)
        if not (_tile_aliases(key) & ban)
    ]
    if not new_tiles:
        return existing_inner if str(existing_inner or "").strip() else str(new_inner or "")
    have: set[str] = set()
    for key, _chunk in new_tiles:
        have |= _tile_aliases(key)
    merged = list(new_tiles)
    for key, chunk in _tiles_from_inner(existing_inner):
        aliases = _tile_aliases(key)
        if aliases & ban or aliases & have:
            continue
        merged.append((key, chunk))
        have |= aliases
    out = "\n".join(chunk for _key, chunk in merged)
    if out and not out.endswith("\n"):
        out += "\n"
    return unswallow_hero_inner(out)


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
            break
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
        # Swallowed / unclosed hero: bake up to the next day-block, then close.
        end_inner = block_end
        while end_inner > start_inner and html[end_inner - 1] in " \t\r\n":
            end_inner -= 1
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
    # If the hero never closed, the span runs to the next day-block — close
    # vision-hero + board/panel/tasks/card/block so later days stay siblings.
    tail = html[end_inner:end_inner + 6]
    if tail != "</div>":
        inner += "</div>\n</div></div></div></div></div>\n"
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


def save_overview_hero(date: str, hero_html: str, removed_sections=None, archived_sections=None) -> dict:
    """Autosave used to rewrite everything.html + prototype.html on every tab load.
    That file-write reloads every open page. Disk persist is SAVE TO GITHUB /bake."""
    return {
        "ok": True,
        "skipped": True,
        "committed": False,
        "pushed": False,
        "date": str(date or "").strip(),
        "files": [],
        "warnings": [],
    }
    date = str(date or "").strip()
    drop_keys = None
    if date == "2026-08-30":
        drop_keys = sorted(AUG30_ARCHIVED_EXTRAS | _drop_key_set(archived_sections))
    # History days: never honor ordinary removed lists from a live tab.
    # Aug 30 archived extras are banned from merge so a restorer cannot resurrect them.
    if date and date < "2026-09-01":
        removed_sections = list(drop_keys) if drop_keys else None
    hero_html = unswallow_hero_inner(hero_html)
    written: list[str] = []
    warnings: list[str] = []
    with SAVE_OVERVIEW_LOCK:
      for path in OVERVIEW_FILES:
        if not path.exists():
            continue
        try:
            html = ensure_overview_day_block(path.read_text(encoding="utf-8"), date)
            start_inner, end_inner = _vision_hero_span(html, date)
            merged = merge_hero_inner(html[start_inner:end_inner], hero_html, removed_sections, drop_keys)
            new_html = replace_vision_hero_inner(html, date, merged)
            if "<!DOCTYPE" not in new_html[:80]:
                raise ValueError(f"refusing save: {path.name} lost its document shell")
            if len(html) > 500_000 and len(new_html) < 500_000:
                raise ValueError(
                    f"refusing save: {path.name} would shrink from {len(html)} to {len(new_html)}"
                )
            if new_html != html:
                path.write_text(new_html, encoding="utf-8")
            written.append(path.name)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{path.name}: {exc}")
    if not written:
        raise ValueError(warnings[0] if warnings else "no overview file written")
    # Disk only. GitHub is the SAVE TO GITHUB /bake button — do not commit/push here.
    return {
        "ok": True,
        "committed": False,
        "pushed": False,
        "date": date,
        "files": written,
        "warnings": warnings,
    }


def _xml_escape(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _article_span(block: str, start: int) -> tuple[int, int]:
    i = start
    depth = 0
    while i < len(block):
        nxt_open = block.find("<article", i)
        nxt_close = block.find("</article>", i)
        if nxt_close < 0:
            raise ValueError("unclosed article")
        if nxt_open >= 0 and nxt_open < nxt_close:
            depth += 1
            i = nxt_open + 8
        else:
            depth -= 1
            end = nxt_close + len("</article>")
            if depth == 0:
                return start, end
            i = end
    raise ValueError("unclosed article")


def _insert_before_matching_div_close(html: str, open_idx: int, insert: str) -> str:
    tag_end = html.find(">", open_idx) + 1
    depth = 1
    i = tag_end
    while i < len(html) and depth:
        nxt_open = html.find("<div", i)
        nxt_close = html.find("</div>", i)
        if nxt_close < 0:
            raise ValueError("unclosed details")
        if nxt_open >= 0 and nxt_open < nxt_close:
            depth += 1
            i = nxt_open + 4
        else:
            depth -= 1
            if depth == 0:
                return html[:nxt_close] + insert + html[nxt_close:]
            i = nxt_close + 6
    raise ValueError("unclosed details")


def _tile_span_for_focus(block: str, focus: str) -> tuple[int, int] | None:
    return _tile_span_for_section(block, focus, "")


def _tile_span_for_section(block: str, focus: str, title: str = "") -> tuple[int, int] | None:
    aliases = _tile_aliases(focus) | _tile_aliases(title)
    if not aliases:
        return None
    for m in re.finditer(r"<article\b(?=[^>]*\bvision-tile\b)[^>]*>", block, re.I):
        try:
            start, end = _article_span(block, m.start())
        except ValueError:
            continue
        chunk = block[start:end]
        fm = re.search(r'data-focus="([^"]+)"', m.group(0), re.I)
        tm = re.search(r'<h3 class="vision-tile-title"[^>]*>([^<]+)</h3>', chunk, re.I)
        tile_focus = (fm.group(1) if fm else "").strip().lower()
        tile_title = re.sub(r"\s+", " ", (tm.group(1) if tm else "")).strip().lower()
        keys = _tile_aliases(tile_focus) | _tile_aliases(tile_title)
        if keys & aliases:
            return start, end
    return None


def save_vision_check(date: str, focus: str, title: str) -> dict:
    """Insert one user-added vision-check into the day's tile in both HTML files."""
    date = str(date or "").strip()
    focus = str(focus or "").strip()
    title = re.sub(r"\s+", " ", str(title or "")).strip()
    if not date or not title:
        raise ValueError("date and title required")
    safe = _xml_escape(title)
    label = (
        f'<label class="vision-check" style="--px: 48%; --py: 28%;">'
        f'<input class="agenda-check" type="checkbox"><span>{safe}</span></label>'
    )
    written: list[str] = []
    warnings: list[str] = []
    with SAVE_OVERVIEW_LOCK:
        for path in OVERVIEW_FILES:
            if not path.exists():
                continue
            try:
                html = path.read_text(encoding="utf-8")
                _, start, end = _day_block_bounds(html, date)
                block = html[start:end]
                span = _tile_span_for_focus(block, focus)
                if not span:
                    raise ValueError(f"section {focus or title} not found on {date}")
                art_s, art_e = span
                art = block[art_s:art_e]
                if re.search(
                    r'<span>\s*' + re.escape(safe) + r"\s*</span>",
                    art,
                    re.I,
                ):
                    written.append(path.name)
                    continue
                det = re.search(r'<div class="vision-tile-details">', art)
                if det:
                    new_art = _insert_before_matching_div_close(art, det.start(), label)
                else:
                    new_art = (
                        art[: -len("</article>")]
                        + '<div class="vision-tile-details">'
                        + label
                        + "</div></article>"
                    )
                new_block = block[:art_s] + new_art + block[art_e:]
                new_html = html[:start] + new_block + html[end:]
                if "<!DOCTYPE" not in new_html[:80]:
                    raise ValueError(f"refusing save: {path.name} lost its document shell")
                if new_html != html:
                    path.write_text(new_html, encoding="utf-8")
                written.append(path.name)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{path.name}: {exc}")
    if not written:
        raise ValueError(warnings[0] if warnings else "task not baked")
    return {
        "ok": True,
        "date": date,
        "title": title,
        "focus": focus,
        "files": written,
        "warnings": warnings,
    }


_VISION_CHECK_RE = re.compile(
    r'<label class="vision-check"[^>]*>.*?</label>',
    re.I | re.S,
)


def _check_label_title(chunk: str) -> str:
    sm = re.search(r"<span[^>]*>(.*?)</span>", chunk or "", re.I | re.S)
    raw = sm.group(1) if sm else ""
    raw = re.sub(r"<[^>]+>", "", raw)
    return re.sub(r"\s+", " ", raw).strip()


def _mutate_vision_check(date: str, focus: str, title: str, rewriter, page: str = "") -> dict:
    date = str(date or "").strip()
    focus = str(focus or "").strip()
    title = re.sub(r"\s+", " ", str(title or "")).strip()
    if not date or not title:
        raise ValueError("date and title required")
    written: list[str] = []
    warnings: list[str] = []
    paths = _overview_paths_for_page(page) if page else OVERVIEW_FILES
    with SAVE_OVERVIEW_LOCK:
        for path in paths:
            if not path.exists():
                continue
            try:
                html = path.read_text(encoding="utf-8")
                _, start, end = _day_block_bounds(html, date)
                block = html[start:end]
                span = _tile_span_for_focus(block, focus)
                if not span:
                    raise ValueError(f"section {focus or title} not found on {date}")
                art_s, art_e = span
                art = block[art_s:art_e]
                new_art = rewriter(art, title)
                if new_art == art:
                    written.append(path.name)
                    continue
                new_block = block[:art_s] + new_art + block[art_e:]
                new_html = html[:start] + new_block + html[end:]
                if "<!DOCTYPE" not in new_html[:80]:
                    raise ValueError(f"refusing save: {path.name} lost its document shell")
                if new_html != html:
                    path.write_text(new_html, encoding="utf-8")
                written.append(path.name)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{path.name}: {exc}")
    if not written:
        raise ValueError(warnings[0] if warnings else "task not baked")
    return {
        "ok": True,
        "date": date,
        "title": title,
        "focus": focus,
        "files": written,
        "warnings": warnings,
    }


def remove_vision_check(date: str, focus: str, title: str, page: str = "") -> dict:
    want = re.sub(r"\s+", " ", str(title or "")).strip().lower()

    def rewriter(art: str, _title: str) -> str:
        def drop(m):
            return "" if _check_label_title(m.group(0)).lower() == want else m.group(0)
        return _VISION_CHECK_RE.sub(drop, art)

    return _mutate_vision_check(date, focus, title, rewriter, page)


def rename_vision_check(date: str, focus: str, old: str, new: str, page: str = "") -> dict:
    old_s = re.sub(r"\s+", " ", str(old or "")).strip()
    new_s = re.sub(r"\s+", " ", str(new or "")).strip()
    if not new_s:
        return remove_vision_check(date, focus, old_s, page)
    want = old_s.lower()

    def rewriter(art: str, _title: str) -> str:
        def swap(m):
            chunk = m.group(0)
            if _check_label_title(chunk).lower() != want:
                return chunk
            return re.sub(
                r"(<span[^>]*>)(.*?)(</span>)",
                lambda sm: sm.group(1) + _xml_escape(new_s) + sm.group(3),
                chunk,
                count=1,
                flags=re.I | re.S,
            )
        return _VISION_CHECK_RE.sub(swap, art)

    result = _mutate_vision_check(date, focus, old_s, rewriter, page)
    result["title"] = new_s
    result["old"] = old_s
    return result


def save_vision_check_order(date: str, focus: str, titles, page: str = "") -> dict:
    """Reorder vision-check labels inside a day's section tile."""
    date = str(date or "").strip()
    focus = str(focus or "").strip()
    want = []
    seen = set()
    for raw in titles or []:
        t = re.sub(r"\s+", " ", str(raw or "")).strip()
        k = t.lower()
        if t and k not in seen:
            want.append(t)
            seen.add(k)
    if not date or not want:
        raise ValueError("date and titles required")
    paths = OVERVIEW_FILES
    written: list[str] = []
    warnings: list[str] = []
    with SAVE_OVERVIEW_LOCK:
        for path in paths:
            if not path.exists():
                continue
            try:
                html = path.read_text(encoding="utf-8")
                _, start, end = _day_block_bounds(html, date)
                block = html[start:end]
                span = _tile_span_for_focus(block, focus)
                if not span:
                    raise ValueError(f"section {focus} not found on {date}")
                art_s, art_e = span
                art = block[art_s:art_e]
                checks = _VISION_CHECK_RE.findall(art)
                if not checks:
                    written.append(path.name)
                    continue

                def check_key(chunk: str) -> str:
                    m = re.search(r"<span[^>]*>([^<]*)</span>", chunk, re.I)
                    return re.sub(r"\s+", " ", (m.group(1) if m else "")).strip().lower()

                by_key: dict[str, str] = {}
                for chunk in checks:
                    k = check_key(chunk)
                    if k and k not in by_key:
                        by_key[k] = chunk
                ordered = []
                used = set()
                for title in want:
                    k = title.lower()
                    if k in by_key and k not in used:
                        ordered.append(by_key[k])
                        used.add(k)
                for chunk in checks:
                    k = check_key(chunk)
                    if k not in used:
                        ordered.append(chunk)
                        used.add(k)
                art_no = _VISION_CHECK_RE.sub("", art)
                det = re.search(r'<div class="vision-tile-details">', art_no)
                if not det:
                    written.append(path.name)
                    continue
                insert_at = det.end()
                new_art = art_no[:insert_at] + "".join(ordered) + art_no[insert_at:]
                new_block = block[:art_s] + new_art + block[art_e:]
                new_html = html[:start] + new_block + html[end:]
                if "<!DOCTYPE" not in new_html[:80]:
                    raise ValueError(f"refusing save: {path.name} lost its document shell")
                if new_html != html:
                    path.write_text(new_html, encoding="utf-8")
                written.append(path.name)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{path.name}: {exc}")
    if not written:
        raise ValueError(warnings[0] if warnings else "task order not baked")
    return {
        "ok": True,
        "date": date,
        "focus": focus,
        "titles": want,
        "files": written,
        "warnings": warnings,
    }


def _overview_paths_for_page(page: str) -> list[Path]:
    p = str(page or "").strip().lower()
    if p in ("prototype", "prototypes", "prototype.html", "prototypes-page"):
        return [ROOT / "prototype.html"]
    return [DASHBOARD]


def _safe_section_photo(photo: str) -> str:
    photo = str(photo or "").strip()
    if not photo:
        return ""
    wrapped = re.match(r"""(?i)url\(\s*['"]?([^'")]+)['"]?\s*\)""", photo)
    if wrapped:
        photo = wrapped.group(1).strip()
    if photo.lower() in ("none", "nophoto"):
        return ""
    photo = photo.split("#", 1)[0]
    photo = re.sub(r"^https?://(?:127\.0\.0\.1|localhost)(?::\d+)?/", "", photo, flags=re.I)
    photo = photo.lstrip("/")
    if photo.startswith("./"):
        photo = photo[2:]
    if not photo.startswith("manus-storage/"):
        return ""
    if ".." in photo or any(c in photo for c in "<>\"'\\ \n\r"):
        return ""
    if not re.fullmatch(r"manus-storage/[A-Za-z0-9._/?=-]+", photo):
        return ""
    return photo


def _bare_section_name(s: str) -> str:
    t = re.sub(r"\s+", " ", str(s or "")).strip().lower()
    t = re.sub(r"^to\s+", "", t)
    t = re.sub(r"^i will\s+", "", t)
    return t.replace("-", " ")


def _is_fitness_subsection_name(title: str, focus: str = "") -> bool:
    return _bare_section_name(title) in {"calisthenics", "inversions"} or _bare_section_name(focus) in {"calisthenics", "inversions"}


def _normalize_section_recs(body: dict) -> list[dict]:
    raw: list = []
    sections = body.get("sections") if isinstance(body, dict) else None
    if isinstance(sections, list):
        raw.extend(item for item in sections if isinstance(item, dict))
    elif isinstance(body, dict) and (body.get("title") or body.get("focus")):
        raw.append(body)
    out: list[dict] = []
    seen: set[str] = set()
    for rec in raw:
        title = re.sub(r"\s+", " ", str(rec.get("title") or "")).strip()[:80]
        focus_src = str(rec.get("focus") or title)
        focus = re.sub(r"[^a-z0-9.-]+", "-", focus_src.lower()).strip("-")[:48]
        if not title or not focus:
            continue
        if _is_fitness_subsection_name(title, focus):
            continue
        key = f"{focus}\n{title.lower()}"
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "focus": focus,
            "title": title,
            "photo": _safe_section_photo(str(rec.get("photo") or "")),
        })
    return out


def _hero_has_section(inner: str, focus: str, title: str) -> bool:
    if _tile_span_for_focus(inner, focus):
        return True
    want = re.sub(r"\s+", " ", str(title or "")).strip().lower()
    if not want:
        return False
    for m in re.finditer(r'<h3 class="vision-tile-title"[^>]*>([^<]*)</h3>', inner, re.I):
        got = re.sub(r"\s+", " ", m.group(1)).strip().lower()
        if got == want or got in _tile_aliases(focus) or want in _tile_aliases(got):
            return True
    return False


def _vision_tile_html(focus: str, title: str, photo: str) -> str:
    extra = ""
    aliases = _tile_aliases(focus) | _tile_aliases(title)
    if aliases & {
        "body", "gym", "train", "toned body", "toned-body",
        "athletic", "fitness training", "fitness-training",
    }:
        extra += " vision-tile-body vision-tile-tall"
    if not photo:
        extra += " vision-tile-nophoto"
        style = "--tile-photo: none;"
    else:
        style = f"--tile-photo: url('{photo}');"
    safe_title = _xml_escape(title)
    carve = safe_title.replace('"', "&quot;")
    focus_attr = _xml_escape(focus)
    return (
        f'<article class="vision-tile{extra}" data-focus="{focus_attr}" '
        f'style="{style}">'
        f'<div class="vision-tile-photo"></div>'
        f'<h3 class="vision-tile-title" data-carve="{carve}">{safe_title}</h3>'
        f'<div class="vision-tile-details"></div></article>\n'
    )


def save_vision_sections(date: str, recs: list, page: str) -> dict:
    """Insert user-added vision tiles into one day's collage. One file, one write."""
    date = str(date or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError(f"invalid overview date: {date}")
    if not recs:
        raise ValueError("section title required")
    paths = [p for p in _overview_paths_for_page(page) if p.exists()]
    if not paths:
        raise ValueError("overview file not found")
    written: list[str] = []
    warnings: list[str] = []
    added: list[str] = []
    with SAVE_OVERVIEW_LOCK:
        for path in paths:
            try:
                html = path.read_text(encoding="utf-8")
                start_inner, end_inner = _vision_hero_span(html, date)
                inner = html[start_inner:end_inner]
                chunks: list[str] = []
                for rec in recs:
                    focus = rec["focus"]
                    title = rec["title"]
                    aliases = _tile_aliases(focus) | _tile_aliases(title)
                    if date == "2026-08-30" and aliases & AUG30_ARCHIVED_EXTRAS:
                        continue
                    probe = inner + "".join(chunks)
                    if _hero_has_section(probe, focus, title):
                        continue
                    chunks.append(_vision_tile_html(focus, title, rec.get("photo") or ""))
                    added.append(title)
                if not chunks:
                    written.append(path.name)
                    continue
                insert = "".join(chunks)
                if not inner.endswith("\n"):
                    insert = "\n" + insert
                if html[end_inner:end_inner + 6] == "</div>":
                    new_html = html[:end_inner] + insert + html[end_inner:]
                else:
                    new_inner = inner + ("" if inner.endswith("\n") else "\n") + "".join(chunks)
                    new_html = replace_vision_hero_inner(html, date, new_inner)
                if "<!DOCTYPE" not in new_html[:80]:
                    raise ValueError(f"refusing save: {path.name} lost its document shell")
                if len(html) > 500_000 and len(new_html) < 500_000:
                    raise ValueError(
                        f"refusing save: {path.name} would shrink from {len(html)} to {len(new_html)}"
                    )
                if '.replace(/<h3 class="vision-tile-title">\n<article' in new_html:
                    raise ValueError("refusing save: would corrupt power-purpose JS splice")
                for later in (
                    "2026-06-23", "2026-08-28", "2026-08-29",
                    "2026-08-30", "2026-09-01", "2026-09-02", "2026-09-03",
                ):
                    marker = f'data-date="{later}"'
                    if marker in html and marker not in new_html:
                        raise ValueError(f"refusing save: would delete day block {later}")
                if new_html != html:
                    path.write_text(new_html, encoding="utf-8")
                written.append(path.name)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{path.name}: {exc}")
    if not written:
        raise ValueError(warnings[0] if warnings else "section not baked")
    return {
        "ok": True,
        "date": date,
        "page": "prototype" if paths[0].name == "prototype.html" else "everything",
        "added": added,
        "files": written,
        "warnings": warnings,
    }


def remove_vision_sections(date: str, recs: list, page: str) -> dict:
    """Cut specific vision tiles out of one day's collage. One file, one write."""
    date = str(date or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError(f"invalid overview date: {date}")
    if not recs:
        raise ValueError("section required")
    paths = [p for p in _overview_paths_for_page(page) if p.exists()]
    if not paths:
        raise ValueError("overview file not found")
    written: list[str] = []
    warnings: list[str] = []
    removed: list[str] = []
    with SAVE_OVERVIEW_LOCK:
        for path in paths:
            try:
                html = path.read_text(encoding="utf-8")
                start_inner, end_inner = _vision_hero_span(html, date)
                inner = html[start_inner:end_inner]
                cut = 0
                for rec in recs:
                    span = _tile_span_for_section(inner, rec.get("focus") or "", rec.get("title") or "")
                    if not span:
                        continue
                    s, e = span
                    while e < len(inner) and inner[e] in " \t\r\n":
                        e += 1
                    inner = inner[:s] + inner[e:]
                    cut += 1
                    removed.append(rec.get("title") or rec.get("focus") or "")
                if not cut:
                    written.append(path.name)
                    continue
                new_html = html[:start_inner] + inner + html[end_inner:]
                if "<!DOCTYPE" not in new_html[:80]:
                    raise ValueError(f"refusing save: {path.name} lost its document shell")
                if len(html) > 500_000 and len(new_html) < 500_000:
                    raise ValueError(
                        f"refusing save: {path.name} would shrink from {len(html)} to {len(new_html)}"
                    )
                if '.replace(/<h3 class="vision-tile-title">\n<article' in new_html:
                    raise ValueError("refusing save: would corrupt power-purpose JS splice")
                for later in (
                    "2026-06-23", "2026-08-28", "2026-08-29",
                    "2026-08-30", "2026-09-01", "2026-09-02", "2026-09-03",
                ):
                    marker = f'data-date="{later}"'
                    if marker in html and marker not in new_html:
                        raise ValueError(f"refusing save: would delete day block {later}")
                if new_html != html:
                    path.write_text(new_html, encoding="utf-8")
                written.append(path.name)
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{path.name}: {exc}")
    if not written:
        raise ValueError(warnings[0] if warnings else "section not removed")
    return {
        "ok": True,
        "date": date,
        "page": "prototype" if paths[0].name == "prototype.html" else "everything",
        "removed": removed,
        "files": written,
        "warnings": warnings,
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


def _section_photo_rejected(src: str) -> bool:
    s = str(src or "").lower()
    return any(token in s for token in REJECTED_SECTION_PHOTOS)


CONCEPTUAL_SECTION_KEYS = frozenset({
    "soul", "sorrow", "darkness", "abundance", "abundant", "receive", "ask", "attention", "anticipate", "finances",
    "tune into", "tune-into", "self-actualize", "self actualize", "claim",
})


def _approved_section_photo(key: str) -> str | None:
    if key not in CONCEPTUAL_SECTION_KEYS:
        return None
    # Empty string means intentionally cleared (no approved photo yet).
    if key not in KNOWN_CARD_PHOTOS:
        return None
    return str(KNOWN_CARD_PHOTOS.get(key) or "")


def photo_for_name(name: str) -> dict:
    key = " ".join(str(name or "").replace("\u2011", "-").split()).strip().lower()
    if not key:
        return {"ok": False, "error": "empty"}
    with PHOTO_LOCK:
        approved = _approved_section_photo(key)
        stored = _load_photo_map()
        # Conceptual sections always use the approved zone URL — never card-* auto-fetch.
        # Skip blackness usability (darkness void is intentionally near-black).
        if key in CONCEPTUAL_SECTION_KEYS:
            cached_c = stored.get(key)
            if cached_c and _section_photo_rejected(str(cached_c)):
                stored.pop(key, None)
                _save_photo_map(stored)
                cached_c = None
            if approved:
                kpath = ROOT / str(approved).split("?", 1)[0]
                if kpath.exists() and kpath.is_file() and kpath.stat().st_size >= 20000:
                    stored[key] = approved
                    _save_photo_map(stored)
                    return {"ok": True, "src": approved, "cached": True}
            # Intentionally cleared — do not auto-fetch a replacement.
            return {"ok": False, "error": "no photo", "cleared": True}
        if approved:
            kpath = ROOT / str(approved).split("?", 1)[0]
            if kpath.exists() and kpath.is_file() and kpath.stat().st_size >= 20000:
                stored[key] = approved
                _save_photo_map(stored)
                return {"ok": True, "src": approved, "cached": True}
        cached = stored.get(key) or KNOWN_CARD_PHOTOS.get(key)
        if cached and _section_photo_rejected(str(cached)):
            stored.pop(key, None)
            cached = approved or KNOWN_CARD_PHOTOS.get(key)
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
                if kpath.exists() and kpath.is_file() and kpath.stat().st_size >= 20000:
                    stored[key] = known
                    _save_photo_map(stored)
                    return {"ok": True, "src": known, "cached": True}
            return {"ok": False, "error": "no photo"}
        dest.write_bytes(blob)
        src = f"manus-storage/{dest.name}"
        stored[key] = src
        _save_photo_map(stored)
        return {"ok": True, "src": src, "cached": False}


_GZIP_CACHE: dict[str, tuple[tuple[str, float, int], bytes]] = {}
_GZIP_LOCK = threading.Lock()


def _gzip_file(path: str) -> bytes | None:
    try:
        st = os.stat(path)
    except OSError:
        return None
    key = (path, st.st_mtime, st.st_size)
    with _GZIP_LOCK:
        hit = _GZIP_CACHE.get(path)
        if hit and hit[0] == key:
            return hit[1]
        compressed = gzip.compress(Path(path).read_bytes(), compresslevel=5)
        _GZIP_CACHE[path] = (key, compressed)
        return compressed


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
            if path == "/save-task":
                body = self._read_json()
                result = save_vision_check(
                    str((body or {}).get("date") or ""),
                    str((body or {}).get("focus") or ""),
                    str((body or {}).get("title") or ""),
                )
                return self._json(200, result)
            if path == "/remove-task":
                body = self._read_json()
                result = remove_vision_check(
                    str((body or {}).get("date") or ""),
                    str((body or {}).get("focus") or ""),
                    str((body or {}).get("title") or ""),
                    str((body or {}).get("page") or ""),
                )
                return self._json(200, result)
            if path == "/rename-task":
                body = self._read_json()
                result = rename_vision_check(
                    str((body or {}).get("date") or ""),
                    str((body or {}).get("focus") or ""),
                    str((body or {}).get("old") or (body or {}).get("from") or ""),
                    str((body or {}).get("title") or (body or {}).get("new") or ""),
                    str((body or {}).get("page") or ""),
                )
                return self._json(200, result)
            if path == "/save-task-order":
                body = self._read_json()
                result = save_vision_check_order(
                    str((body or {}).get("date") or ""),
                    str((body or {}).get("focus") or ""),
                    (body or {}).get("titles") or [],
                    str((body or {}).get("page") or ""),
                )
                return self._json(200, result)
            if path == "/save-section":
                body = self._read_json()
                recs = _normalize_section_recs(body if isinstance(body, dict) else {})
                result = save_vision_sections(
                    str((body or {}).get("date") or ""),
                    recs,
                    str((body or {}).get("page") or ""),
                )
                return self._json(200, result)
            if path == "/remove-section":
                body = self._read_json()
                recs = _normalize_section_recs(body if isinstance(body, dict) else {})
                result = remove_vision_sections(
                    str((body or {}).get("date") or ""),
                    recs,
                    str((body or {}).get("page") or ""),
                )
                return self._json(200, result)
            if path == "/ensure-day":
                body = self._read_json()
                result = ensure_day_on_disk(
                    str((body or {}).get("date") or ""),
                    str((body or {}).get("page") or ""),
                )
                return self._json(200, result)
            if path == "/save-overview":
                body = self._read_json()
                date = body.get("date") if isinstance(body, dict) else None
                hero_html = body.get("html") if isinstance(body, dict) else None
                removed = body.get("removedSections") if isinstance(body, dict) else None
                archived = body.get("archivedSections") if isinstance(body, dict) else None
                result = save_overview_hero(str(date or ""), str(hero_html or ""), removed, archived)
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
        if not getattr(self, "_cache_set", False):
            path = urlparse(self.path).path.lower()
            ext = Path(path).suffix
            if ext in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".woff2", ".woff", ".ico"}:
                self.send_header("Cache-Control", "public, max-age=604800")
            else:
                self.send_header("Cache-Control", "no-store")
            self._cache_set = True
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path) or not os.path.isfile(path):
            return super().send_head()
        ext = Path(path).suffix.lower()
        accept = self.headers.get("Accept-Encoding", "")
        if ext in {".html", ".js", ".css", ".json", ".svg", ".txt"} and "gzip" in accept:
            compressed = _gzip_file(path)
            if compressed is None:
                self.send_error(404, "File not found")
                return None
            self.send_response(200)
            self.send_header("Content-type", self.guess_type(path))
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(compressed)))
            self.send_header("Vary", "Accept-Encoding")
            self.end_headers()
            return BytesIO(compressed)
        return super().send_head()

    def log_message(self, fmt, *args):
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    # Avoid serving parent paths; stay in ROOT.
    os.chdir(ROOT)
    for name in ("everything.html", "prototype.html"):
        _gzip_file(str(ROOT / name))
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"dashboard server on http://127.0.0.1:{PORT}/", flush=True)
    print("POST /bake to persist localStorage into GitHub", flush=True)
    print("POST /brain-dump to write thoughts into brain-dump.html", flush=True)
    print("POST /save-overview is a no-op; POST /save-section, /remove-section, /save-task and /save-task-order bake into HTML", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
