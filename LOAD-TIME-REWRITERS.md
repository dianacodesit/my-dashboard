# Load-time rewriters / restylers inventory

**File this describes:** `/Users/diana/my-dashboard/everything.html`  
**Written:** 8 Sep 2026  
**Ask:** list every auto-flip / restyle — not only section titles.

Diana never asked the board to rewrite itself when a day stops being today. Cursor agents added that. This file is the map.

---

## How to read this

A **rewriter** is any JS that, on page load / day expand / chrome sync, walks the live board or `localStorage` and **changes** wording, photos, type, or layout without Diana clicking something.

**Trigger keys**

| When | What fires |
|---|---|
| Script parse (every refresh) | IIFEs at the bottom of `everything.html` — they run as the file loads |
| Day expand (click a collapsed day) | `window.__bootOverviewDay(block)` from the day-header click (~24580, ~24682) |
| `boot(onlyBlk)` (~61716) | The overview hydration pipeline — **not** auto-run on reload (comment at 61875). Still runs when a day is opened |
| Adding a section | `addTile` → used to call `titledForBlock` (now a pass-through) |
| Hydrating stored adds | `applyStoredEdits` → `normalizeAddedSection` + `titledForBlock` |

**Who** = Cursor agents writing into `everything.html`. Not a Diana rule. Where a Cursor **rule** later banned the behavior, that is noted.

**Status this morning**

- Title **helpers** (`titledForBlock`, `displaySectionTitle`, `ensureISectionTitle`, `toIAmSectionTitle`, `normalizeAddedSection`, `renameShortSectionTitles`) were gutted to pass-throughs in this chat. They still **exist** and are still **called**.
- The load IIFEs that walk titles (`migrateSectionToPrefix`, `migrationSectionIPrefixV1`, `scrubDoubleISectionTitles`) are **still in the file** and still run `forceAll()` every refresh. They currently no-op on live titles only because the helpers return the same string. They can still rewrite `localStorage` on first run if the MKEY is missing.
- Photo / layout / name-flip walkers below were **not** deleted.

`pastTenseDay` / `toPastSectionTitle` / `regularPastVerb` / `migrationSectionPastTenseV1` are **gone** from the file. The rule `vision-collage-no-overlap.mdc` forbids putting them back.

---

## 1. The tense / prefix engine (the thing that wrecked history)

This is one machine. Agents stacked eras on top of it.

### 1a. `SECTION_PAST` + `collapseStackedPast` + `presentLemma`  
**Where:** ~48300  
**Does:** Dictionary of present → past (`succeed` → `succeeded`, `earn` → `earned`, …). `collapseStackedPast` was added after titles became `earnededededed`. `presentLemma` maps a past word back to the present lemma.  
**Triggers:** Any caller of `matchPlainSection` / `bareSectionTitle` paths. Alias matching in `sectionAliasSet` still uses `SECTION_PAST`.  
**Why it was added:** A previous agent in [title rewrite chat](013c462b-74f2-4ca6-a405-e393b7e45986) implemented Sep 5 past tense as **automatic for every day ≥ 2026-09-05**, not as baked words on Sep 5. Diana asked for those words **on Sep 5**. She did not ask for midnight auto-flip.  
**What it changed:** `I will succeed` → `I succeeded` (then `I succeededed` …) on any day the function thought was “past.”  
**Who:** Cursor agent. **Not** a Diana rule. Later banned in `vision-collage-no-overlap.mdc`.

### 1b. `plainLabelDay` + `SECTION_PLAIN` + `matchPlainSection`  
**Where:** ~48343–48421  
**Does:** If the day’s date is ≥ `2026-09-06` (`PLAIN_SECTION_ERA`), map a section to an **I am…** label + photo (training, grad student, worshipping, networking, winning, earning, …). Sep 7+ special-cases: academia → `I am pursuing my Ph.D`, fighting → `I am giving 'em hell`.  
**Triggers:** Still called from `migrationPlainSectionLabelsSep6V1`, `sectionPresets`, `addTile` / photo paths, `existingSectionNames`.  
**Why:** Agents encoded Sep 6 present-tense wording as a **date rule** that rewrites tiles, instead of baking the words on those days.  
**What it changed:** `I will train` / `train` / `body` → `I am training` + gym photo; Pepperdine/succeed → academia / grad-student photo; itaq-allah → deen / worshipping; etc. Also **swaps focus slugs** (body → fitness, pepperdine → academia).  
**Who:** Cursor agent. Diana asked for the **Sep 6/7 words**. She did not ask for a load-time remapper.

### 1c. `toIAmSectionTitle` / `ensureISectionTitle` / `displaySectionTitle` / `titledForBlock`  
**Where:** ~48424–48444  
**Does now:** Pass-through (trim only).  
**Did before:**  
- `ensureISectionTitle` — force `I will ` + bare name  
- `toIAmSectionTitle` — force `I am ` + gerund  
- `displaySectionTitle` — canonicalize (pepperdine → succeed, body → train, …) then wrap in `I will`  
- `titledForBlock` — pick `I am` vs `I will` vs freeze-on-past-days by date  

**Triggers:** `addTile` (~54514), `applyStoredEdits` (~54103), `sectionPresets` (~47903), plus the IIFEs in §2.  
**Why:** Same prefix eras: first **to…**, then **I will…**, then **I am…**, then **past tense by date**.  
**Who:** Cursor agents across multiple sessions. Diana asked for wording **on specific days**, not a formatter that rewrites the whole file on load.

### 1d. `normalizeAddedSection`  
**Where:** ~48263  
**Does now:** Only fills missing `focus` from title.  
**Did before:** On every hydrate of `btm_overview_edits_v1.addedSections`, rewrite stored titles to `I will train`, `I will succeed`, `I am earning`, etc.  
**Triggers:** `purgeConflictingAdds`, `applyStoredEdits` when a day is booted.  
**Who:** Cursor agent.

---

## 2. Load IIFEs that still walk titles (every refresh)

These run as soon as the script is parsed. **Not** gated on “only today.”

### 2a. `migrateSectionToPrefix`  
**Where:** ~58779  
**MKEY:** `migration-section-to-prefix-v1`  
**Does:** `forceAll()` every load: every `.vision-tile-title` → `titledForBlock` / `displaySectionTitle`. First run also rewrites **all** `localStorage` HTML + `btm_overview_edits_v1` to prefix titles (`to train` historically; later helpers turned that into `I will` / `I am`).  
**Triggers:** Every page load (`forceAll()` is **before** the MKEY return).  
**Why:** Agent comment in file: *Prefix every section title with “to …”*.  
**What it changed:** Short names (`train`, `glow up`) → `to train` / later `I will train` / later `I am training` depending on helper version. Wrote into shells + edits so refresh kept the new words.  
**Who:** Cursor agent. Diana did not ask for a global “to…” rewriter.

### 2b. `migrationSectionIPrefixV1`  
**Where:** ~58830  
**MKEY:** `migration-section-achieve-to-succeed-v1`  
**Does:** `forceAll()` every load. Extra hard maps: surrender → `I will surrender to Allah ﷻ`; pepperdine/enroll/succeed → `I will succeed`; master → `I will master`; achieve → `I will achieve`; she pursues → `I will pursue`. First run rewrites `localStorage` + archived-section titles.  
**Triggers:** Every page load.  
**Why:** After “to…”, agents flipped the prefix to **I will**. Also renamed Pepperdine → succeed.  
**What it changed:** Any matching title on **any** live day-block. Archived titles too.  
**Who:** Cursor agent.

### 2c. `scrubDoubleISectionTitles`  
**Where:** ~59174  
**MKEY:** `migration-strip-double-i-v1`  
**Does:** `forceAll` is stubbed. First run (if MKEY missing) still rewrites every stored `vision-tile-title` / `data-carve` through `displaySectionTitle`.  
**Why:** After prefix stacking, titles became `I I will…` / `to I will…`. Agent added a cleaner that **is itself a rewriter**.  
**Who:** Cursor agent. Later the same agent turned this IIFE into `migrationSectionPastTenseV1` (deleted). This shell came back.

### 2d. `migrationPlainSectionLabelsSep6V1`  
**Where:** ~59051  
**MKEY:** `migration-iam-section-labels-sep6-v2`  
**Does:** `forceAll` is defined but **not** called (comment: do not force I am… on load). Still on first run: rewrite `btm_overview_edits_v1` + `btm_day_shells_v1` for days ≥ Sep 6 via `matchPlainSection` (titles **and** focus slugs **and** photos). Also writes `btm_zone_photos_v1`. Always runs `restoreLiveSubsections()` (re-seeds fitness / surrender / academia / healthy / centered subsections on live days).  
**Why:** Encode Sep 6 “I am…” as a migration instead of baking HTML.  
**What it changed:** Stored HTML for Sep 6+; zone photo cache; subsections reappear after delete if “ensure*” thinks they belong.  
**Who:** Cursor agent.

### 2e. `restorePastDayBakedTitles`  
**Where:** ~58910  
**Does:** For each past day in a hardcoded `BAKED` map (Aug 26–Sep 6), set each tile’s title back to the baked string. Also rewrites `heroHtml` / `html` in edits and `btm_day_shells_v1`.  
**Triggers:** Once at parse (`restorePastDayBakedTitles()`), and again at the end of every `boot()` (~61852).  
**Why:** Undo after agents rewrote history. Added **after** Diana complained.  
**What it changes:** Titles (and stored HTML) on past days to the map. Does **not** invent tense from the clock — it writes known words.  
**Who:** Cursor agent, as an antidote. Still a load-time title writer.

### 2f. `fixPursuingUxPhotoAndIamCap`  
**Where:** ~59329  
**Does:** Every load + DOMContentLoaded: (1) capitalize any title that starts with `i am` → `I am`; (2) if the tile is “pursuing”, force `zone-she-pursues.jpg`. Also scrubs UX/Figma photo URLs from storage.  
**Triggers:** Every refresh.  
**Why:** Agent fix for lowercase “i am” and a wrong UX-design photo on pursuing.  
**Who:** Cursor agent.

---

## 3. Style / layout restylers (not titles)

### 3a. `stampTitleEra` / `stampAllTitleEras`  
**Where:** ~59008  
**Does:** Sets `data-title-era="foil"` on days ≥ Sep 6, `"pre-foil"` on Aug 26–Sep 5. CSS (~69928+) then switches centered gold Playfair vs white Newsreader bottom-left.  
**Triggers:** Parse + every `boot()`.  
**Why:** After agents pushed Sep 6 foil onto earlier days. Added to **lock** eras.  
**What it changes:** Type style (font, position, gold vs white). Not the words.  
**Who:** Cursor agent. The **rule** (Diana, after the mess) is in `vision-collage-no-overlap.mdc`: foil starts Sep 6; do not push it backward.

### 3b. `scrubMosaicLeakFromPastDays`  
**Where:** ~59027  
**Does:** If a day `< 2026-09-07` has `dash-mosaic-era`, strip that class, strip mosaic tile positioning (left/top/width/height).  
**Triggers:** Every parse.  
**Why:** Agents applied Sep 7 room packing to earlier days.  
**What it changes:** Layout classes + inline position/size.  
**Who:** Cursor agent antidote. Rule: do not restyle past days into Sep 7 rooms.

### 3c. `syncOverviewEraChrome`  
**Where:** ~18501  
**Does:** Adds `overview-era-day`; if iso ≥ Sep 1 adds `collage-flush`; adds `depth-four-era` + `card-style-deboss-chip` from Aug 26; may add/remove the “Pursuits” header word.  
**Triggers:** Chrome sync on overview-era days (expand / boot / chrome).  
**Why:** Era chrome (flush mosaic Sep 1–6, depth pills, card style).  
**What it changes:** Layout classes, header copy.  
**Who:** Cursor agents implementing era looks Diana asked for **on those dates**. Dangerous if it runs on the wrong day.

### 3d. `packDashMosaic`  
**Where:** ~47431  
**Does:** For days ≥ Sep 7, adds `dash-mosaic-era` / `vision-hero-dashmosaic` and absolutely positions tiles as rooms. For days `< Sep 7`, **removes** mosaic class and returns.  
**Triggers:** Pack / resize / add-remove on Sep 7+ (and any pack call that hits a past day).  
**Why:** Sep 7 “dashboard rooms” Diana asked for.  
**What it changes:** Layout of the live collage.  
**Who:** Cursor agent from her Sep 7 packing instructions. Rule: do not apply to Aug 26–Sep 6.

### 3e. New-day clone chrome (~25229)  
**Does:** When cloning a day shell, if iso ≥ Sep 1 add `collage-flush`; if iso ≥ Sep 7 add `dash-mosaic-era`.  
**Triggers:** Creating a new day.  
**Why:** New days inherit the current era.  
**Who:** Cursor agent.

---

## 4. Photo remappers that run on load (not only titles)

These **restyle** the board: they overwrite `--tile-photo` on existing tiles.

### 4a. Every-load photo walkers (parse + again inside `boot`)

| Name | ~line | What it forces | Why / who |
|---|---|---|---|
| `__rewriteConceptSectionPhotos` / `applyAll` | 57760 | MAP of concept names → zone photos (soul, darkness, earn, networking, …). Skips `__isFileDay`. | Keep approved photos. Cursor. Also re-applied in `boot` ~61824 |
| `__rewritePoliticsPhotosNow` | 57857 | Politics tile → `zone-politics.jpg?v=chess5`. Also **re-packs every day**. | Ban corridor photo. Cursor + later rule |
| `__rewriteAudacityPhotosNow` | 57911 | Audacity → finger silhouette `v=finger1` | Diana-supplied photo; agents keep forcing it |
| `__rewriteDarknessPhotosNow` | 57802 | Darkness → **nophoto** (strip banned people/candle) | Diana rejected those photos (`rejected-section-photos-banned`) |
| `__rewriteAttentionPhotosNow` | (same family) | Attention → approved spotlight | Same pattern |
| `__rewriteRepetitionsPhotosNow` | | Repeat tile → cubes | Same |
| `__rewriteSoulPhotosNow` | | Soul → wilted rose, never candle | Diana rejected candle |
| `__rewriteAbundancePhotosNow` / Tree | | Abundance wheat **banned** → nophoto / tree | Diana rejected wheat |

**Trigger:** IIFE `applyAll()` / `rewrite*Now()` on parse, **and** `boot()` calls them again (~61823–61831).  
**What they change:** Photos on **matching tiles on every day they can see** (except file-frozen days). Some also rewrite `localStorage`.

### 4b. `hardwiredSectionPhoto` + `ensureOverviewEditChrome`  
**Where:** photo map ~51771; chrome ~53759  
**Does:** On chrome-sync, for each tile, if `hardwiredSectionPhoto` returns a URL and it differs from current, **set `--tile-photo`**. Comment says it does not rewrite titles.  
**Triggers:** `ensureOverviewEditChrome` on day expand / boot (file days too ~61725).  
**What it changes:** Photos. Can fight a photo Diana just set if the map disagrees.  
**Who:** Cursor agent, grown as photos were assigned.

### 4c. Parse IIFEs that force a photo every refresh (no MKEY, or MKEY after apply)

| Name | ~line | Change |
|---|---|---|
| `forceFinanciallyAbundantNophoto` | 59229 | Financially abundant → nophoto; scrub tree URL near that name |
| `forceGradStudentPhotoSep7` | 59254 | Grad-student / academia → plaza photo |
| `forceNetworkingPhotoSep7` | 59281 | Networking → `zone-networking.jpg` |
| `scrubPepperdineSchoolLineSep7` | 59309 | Any caruso-line / graziadio asset → `csol12` plaza |
| `remapIamSectionPhotosSep7V1` | 59369 | Live (non-file) tiles: look up `__secImgFor(title)` and set photo |
| `migrationIWillMasterV1` | 69113 | **Every load** `apply()`: master tiles → diploma photo + **rewrite title** to `I will master`; achieve → nophoto + **rewrite title** to `I will achieve`. Also `__addTile` on Sep 3–4 if missing |
| `migrationExecuteChessAestheticV1` | 59744 | First run: execute photo + **title** via `titledForBlock('I will execute')` |
| `migrationSurrenderYourselfV1` | 59904 | First run: surrender tiles → **title** via `titledForBlock('I will surrender…')` |
| `migrateInversionsYogaPhoto` | 49876 | `forceAll()` every load: inversions subsection photo → yoga (not rings) |

### 4d. One-shot photo / nophoto migrations (MKEY, first run only)

These exist to enforce **Diana-rejected** photos (wheat, faces, diploma-as-section, romance rings, rain-as-feel, mountains-as-persevere, door/race as seize, paint as curate). They rewrite DOM + storage **once**, then set a key.

Includes (non-exhaustive):  
`migrationSoulNoPeopleV1`, `migrationSoulDarknessNophotoV1`, `migrationToLoveNoRomanceNophotoV1`, `migrationToFeelNoHumansNophotoV1`, `migrationToPersevereNoHumansNophotoV1`, `migrationFeelNoRainV1`, `migrationPersevereNoMountainsV1`, `migrationAchieveLicenseToBackgroundsNophotoV1`, `migrationRecoupVillaToBackgroundsNophotoV1`, `migrationSeizeOpportunitiesPhotoV2/V3/V4`, `migrationCurateSelectPhotoV1`, `migrationTrainGymV1`, `migrationIWillEarnV1`, `migrationIWillWinV11`, …

**Who for the bans:** Diana, via complaints. Encoded in `rejected-section-photos-banned.mdc`.  
**Who for the migration code:** Cursor agents. Same *class* of load rewriter; different *reason*.

---

## 5. `boot()` rename / seed pipeline (day expand)

`boot(onlyBlk)` (~61716) runs when a day is opened (`__bootOverviewDay`). Comment at 61875: **do not run on reload** because it restyles and flashes.

On each eligible day it can still:

| Call | ~line | Flips |
|---|---|---|
| `migratePepperdineSection` | 53653 | Titles: grad school / pepperdine → `achieve`; gym → `body`; lifestyle → `curated lifestyle`; power \| purpose → `power`. Photos: plaza, power lightning, purpose compass. Dedupes pepperdine tiles |
| `renameExecutiveToAmbition` | 57387 | executive → ambition (title + focus) |
| `renameBodyToTonedBody` | 57430 | Can set title to `train` |
| `renameFutureSelfToFuture` | 57106 | `future self` → title `future` |
| `renameShortSectionTitles` | 57157 | **Dead** (`return false`) but still **called twice** (~61787, ~61817) |
| `ensureAudacityZoomHeader` | 57161 | Fight-family titles → `fight`; photo → finger; kicker → `audacity`; drops duplicate fight tiles |
| `renameToFearAllah` | 57046 | Merges surrender tiles; does **not** flip I will ↔ I surrendered (comment) |
| `demotePepperdineCardSections` | 56992 | Turns fake Pepperdine *sections* into cards |
| `fixScholarshipReApplicationLabel` | 56879 | Card/task label “scholarship re-application” → “scholarship” |
| `seedRequestedFoci` | 57223 | **Adds** sections on Aug 30 / Sep 1 / Sep 2 if missing (detach, travel, execute, …) |
| `seedAug30*` / `seedSep01*` / `seedSep02*` | 61769+ | Re-seed boards, cards, audacity, soul, enroll-move cards |
| `ensureFitnessSubsections` / Glow / Surrender / Academia / Healthy / Centered | 61791+ | Re-add subsections if the ensure fn thinks they belong |
| `stripFreshDayAutoSections` / `scrubUninvitedAutoSections` | 61802 | **Removes** sections agents auto-added on empty days |
| `copyCardsIntoTasksDays` | 61820 | Copies cards onto tasks-depth days |
| `syncHeroLayoutClass` | 61836 | Re-packs collage (layout restyle) |
| `persistDay` | 61839 | Writes the mutated HTML back into storage |

**Why:** Years of “fix this name / seed this day” agent work, left on a hose that runs whenever a day opens.  
**Who:** Mix. Some names Diana asked to change once (executive → ambition). The **pipeline that re-applies them forever** is Cursor.

---

## 6. Early one-shot title/photo IIFEs (top of file, MKEY)

Run once per browser if the key is missing. Still **code that flips**.

Examples (~16371–17500):  
`btm_power_purpose_split_v1` (split “power \| purpose”, rewrite titles + photos), `btm_remember_to_fight_v1`, `btm_finances_to_abundance_v1` (`finances` → `abundance`), polaroid unstack `btm_unstack_polaroids_v2`–`v5` (repositions cards).

**Who:** Cursor agents from Aug collage work.

---

## 7. Card / chrome restyle (not section titles)

| Name | What |
|---|---|
| `migrationStripCardHeadlinesV2` (~51553) | Removes card headline chrome |
| Late `boot`/`strip` (~69565) | Every load + MutationObserver: delete `.vision-card-headline`; blank “success begets…” spans |
| `migrationDefaultOverviewDepthSectionsV1` / `…TasksV2` | Flip default depth (sections vs tasks) in storage |
| `migrationSep6TasksVisibleV1` | Force tasks visible on Sep 6 |
| Quote CSS (~293) | Hides `.vision-tile-quote` until zoom — restyles when quotes show |

---

## 8. What Diana actually asked for vs what agents built

| Diana asked | Agent built |
|---|---|
| Sep 5 titles in **past tense** (those words, that day) | `pastTenseDay`: any day ≥ Sep 5 auto-conjugates on load (deleted; **do not restore**) |
| Sep 6+ **I am…** wording | `plainLabelDay` / `SECTION_PLAIN` remapper for all days ≥ Sep 6 |
| Era looks: Aug gapped collage; Sep 1–6 flush; Sep 6 foil; Sep 7 rooms | JS that **stamps classes by date** and sometimes leaked backward |
| Rejected photos stay gone (wheat, candle, faces, diploma-as-tile, …) | Dozens of photo IIFEs that rewrite `--tile-photo` on load |
| Don’t rewrite history | `restorePastDayBakedTitles` + `stampTitleEra` (undo code, still writers) |

No Cursor **rule** ever said “flip titles at midnight.” The rule now says the opposite (`vision-collage-no-overlap.mdc`).

---

## 9. Call graph (short)

```
page load
  ├─ migrateSectionToPrefix.forceAll()          // titles, every refresh
  ├─ migrationSectionIPrefixV1.forceAll()       // titles, every refresh
  ├─ restorePastDayBakedTitles()                // titles, past days
  ├─ stampAllTitleEras()                        // type style
  ├─ scrubMosaicLeakFromPastDays()              // layout
  ├─ migrationPlainSectionLabelsSep6V1          // storage + subsections
  ├─ scrubDoubleISectionTitles                  // storage if no MKEY
  ├─ fixPursuingUxPhotoAndIamCap.apply()        // titles + photo
  ├─ force*Photo / rewrite*PhotosNow            // photos
  └─ migrationIWillMasterV1.apply()             // photos + titles

click to expand a day
  └─ __bootOverviewDay(blk)
        ├─ migratePepperdineSection             // titles + photos
        ├─ rename* / ensureAudacityZoomHeader   // titles + photos
        ├─ seed* / ensure*Subsections           // add tiles
        ├─ ensureOverviewEditChrome
        │     └─ hardwiredSectionPhoto          // photos
        ├─ __rewrite*PhotosNow                  // photos again
        ├─ stampAllTitleEras / restorePastDayBakedTitles
        └─ persistDay                           // save the mutations
```

---

## 10. Still-callable helpers (gutted, not deleted)

These are **still in the file** and **still invoked**. Bodies are pass-through as of this morning’s edit:

- `titledForBlock`
- `displaySectionTitle`
- `ensureISectionTitle` / `ensureToSectionTitle`
- `toIAmSectionTitle`
- `normalizeAddedSection`
- `renameShortSectionTitles`

`SECTION_PAST`, `plainLabelDay`, `matchPlainSection`, `SECTION_PLAIN` are **not** gutted.

---

## 11. File / line index (everything.html)

| Symbol | Approx. line |
|---|---|
| `SECTION_PAST` / `plainLabelDay` / `SECTION_PLAIN` | 48300 |
| Title helpers (gutted) | 48263, 48424–48444 |
| `hardwiredSectionPhoto` | 51771 |
| `migratePepperdineSection` | 53653 |
| `ensureOverviewEditChrome` | 53759 |
| `applyStoredEdits` + `titledForBlock` | 54103 |
| `addTile` + `titledForBlock` | ~54514 |
| `__rewriteConceptSectionPhotos` | 57760 |
| `__rewriteDarknessPhotosNow` | 57802 |
| `__rewritePoliticsPhotosNow` | 57857 |
| `__rewriteAudacityPhotosNow` | 57911 |
| `migrateSectionToPrefix` | 58779 |
| `migrationSectionIPrefixV1` | 58830 |
| `restorePastDayBakedTitles` | 58910 |
| `stampTitleEra` | 59008 |
| `scrubMosaicLeakFromPastDays` | 59027 |
| `migrationPlainSectionLabelsSep6V1` | 59051 |
| `scrubDoubleISectionTitles` | 59174 |
| `fixPursuingUxPhotoAndIamCap` | 59329 |
| `boot` / `__bootOverviewDay` | 61716 / 61874 |
| `migrationIWillMasterV1` | 69113 |
| Foil / pre-foil CSS | 301, 317, 69928+ |
| Day-expand boot hook | 24580, 24682 |
