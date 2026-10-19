# Wrist & Hand — Master Clinical Dossier & Companion Test Atlas

**Live Atlas:** https://azhry-x.github.io/wrist-hand-atlas/  
**Dossier PDF:** [`master_wrist_hand_dossier.pdf`](./master_wrist_hand_dossier.pdf) — 9 pages, A4 portrait, built for Apple Pencil in Notability / GoodNotes.

Sister projects:
- [Knee Complex dossier + atlas](https://github.com/Azhry-X/knee-atlas) — same design system, same page architecture.
- [Ankle & Foot dossier + atlas](https://github.com/Azhry-X/ankle-atlas) — same design system, same page architecture.
- [Lumbar Spine dossier + atlas](https://github.com/Azhry-X/lumbar-atlas) — same design system, same page architecture.
- [Shoulder Complex dossier + atlas](https://github.com/Azhry-X/shoulder-atlas) — same design system, same page architecture.
- [Cervical Spine dossier + atlas](https://github.com/Azhry-X/cervical-atlas) — same design system, same page architecture.
- [Elbow dossier + atlas](https://github.com/Azhry-X/elbow-atlas) — same design system, same page architecture.

## What is in the dossier
| Page | Content | Accent |
|---|---|---|
| 1 | Triage & red flags (suspected scaphoid fracture — Carpenter, Mallee 2014, Parvizi, Mallee 2020 rule, Bäcker, Mallee 2015 Cochrane imaging; acute CTS after DRF — Leow; CRPS Budapest criteria — Harden; pyogenic flexor tenosynovitis / Kanavel signs — Pang, compartment syndrome, septic arthritis, high-pressure injection, fight bite), pathway router, subjective, body chart | red |
| 2 | Differential diagnosis matrix (CTS, de Quervain, thumb CMC OA, trigger finger, TFCC / ulnar-sided pain, DRUJ instability, scapholunate instability, scaphoid fracture / non-union, DRF, CRPS, hand OA), Atroshi CTS prevalence, Padua natural history, Goubau WHAT, Merritt grind, Tay fovea sign & Chang outcomes, Prosser persistent wrist pain, Mahdavi PRWE screen | blue |
| 3 | Objective examination: wrist, forearm, thumb & finger ROM write-in table (LaStayo goniometry ICCs), grip & pinch write-in (Wang Jamar norms range; Mutalib device non-interchangeability), sensory & neuro screen (median / ulnar / radial territory, 2-point discrimination, monofilament, APB / interossei, Froment, Wartenberg, Allen test, ULNT1 median), oedema write-in (volumetry / figure-of-eight) | blue |
| 4 | Special tests & PROMs: CTS tests (MacDermid, D'Arcy, Wainner CPR, JOSPT CPG diagnosis quote, CTS-6), de Quervain (WHAT, Finkelstein, Eichhoff), thumb CMC grind, TFCC / DRUJ / carpal instability tests (fovea sign, TFCC compression, ulnar grinding, DRUJ test, Watson scaphoid shift, lunotriquetral ballottement, midcarpal test), PROM dashboard (PRWE, QuickDASH / DASH, BCTQ + NPRS, MHQ, AUSCAN, PSFS) | blue |
| 5 | Post-surgical & fracture: surgeon-directed restrictions, DRF (WRIST — Chung, DRAFFT — Costa 2014 / 2019, rehab — Handoll, Kay, Laohaprasitiporn, Gutiérrez-Espinoza), CTS surgery & rehab (Gerritsen, Jarvik, Peters 2016), scaphoid waist (SWIFFT — Dias), flexor tendon repair (Starr), thumb CMC surgery (Wajon), trigger finger release vs injection (Sato, Zyluk), CRPS prevention (Zollinger, Evaniew), wound / neuro / cast-complaint re-check, operative log | purple |
| 6 | Orthoses, injections & electrophysical agents: CTS steroid injection (Marshall, Atroshi 2013, Hofer), CTS splinting (Page 2012, Karjalainen 2023), therapeutic ultrasound (Page 2013), JOSPT CTS CPG orthosis / physical-agent / ergonomics quotes, ergonomic equipment (O'Connor), de Quervain injection ± spica (Ippolito), thumb CMC OA splints & combined care (Buhler, Deveza), trigger finger injection (Peters-Veluthamaningal), CRPS GMI / mirror therapy (Moseley, Méndez-Rebolledo), orthosis / parameter log | orange |
| 7 | Manual therapy: CTS exercise & mobilisation (Page 2012), neural mobilisation (Basson), manual therapy vs surgery (Fernández-de-las-Peñas), JOSPT CTS CPG manual therapy quotes, thumb CMC OA manual therapy (Villafañe, Magni), hand oedema mobilisation (Miller), safety & informed consent | teal |
| 8 | Exercise & return to activity: hand OA exercise (Østerås), rheumatoid hand SARAH (Lamb), DRF recovery (MacDermid 2003), CRPS-I exposure in vivo (den Hollander), return to work (Neutel, Bai), JOSPT CTS CPG outcome-measure quotes, tendon / nerve gliding & proprioception progression, 12-week loading log | green |
| 9 | 12-visit flowsheet, discharge milestones (PRWE, QuickDASH / DASH, BCTQ, NPRS vs verified MCIDs by population), discharge summary | slate |

Every statistic carries an evidence marker: **H** high · **M** moderate · **L** low · **E** expert opinion.
Underlined test names open the matching Atlas card; **▸** marks cards with a verified video.

## Repository layout
```
index.html                       Atlas (GitHub Pages entry point) — generated
master_wrist_hand_dossier.html   Dossier (generated, self-contained CSS)
master_wrist_hand_dossier.pdf    Dossier PDF (generated)
src/pages/p1.html … p9.html      Dossier page bodies  ← edit content here
src/dossier.css                  Design system
atlas/data/tests.yaml            Atlas cards: steps, criteria, accuracy, evidence, videos, calculators  ← single source of truth
atlas/build_atlas.py             Builds index.html from tests.yaml (page badges/filters = every dossier page that links the card)
atlas/config.py                  Atlas base URL
tools/build_dossier.py           Assembles HTML → PDF → runs every check
tools/render_and_check.py        Page count, overflow, overlap, fonts, required safety strings, previews
tools/check_links.py             Verifies every PDF link, Atlas anchor, card source (DOIs via the DOI registry) and video
tools/required_strings.txt       Safety-critical text that must never disappear
fonts/                           Source Sans 3 (OFL)
```

## Rebuild after an edit
One-time setup (Python 3.10+ and Node.js):
```bash
pip install -r requirements.txt
python -m playwright install chromium
npm install
```
Windows, one command (stops at the first failure):
```powershell
powershell -ExecutionPolicy Bypass -File build.ps1            # Atlas + PDF + all checks + link audit
powershell -ExecutionPolicy Bypass -File build.ps1 -SkipLinks # same, without the network link audit
```
Or step by step on any OS:
```bash
python atlas/build_atlas.py                # Atlas
python tools/build_dossier.py              # Dossier PDF + all checks (exit 1 on any problem)
python tools/check_links.py                # links (add --live after the site is published)
```
The dossier build fails on: page count ≠ 9, content overflowing a page / card / cell, overlapping glyphs,
a character missing from Source Sans 3 (font fallback), malformed tables, leaked markup, internal link targets
under 4 mm, or a missing safety string from `tools/required_strings.txt`.
Page previews are written to `preview/` when poppler (`pdftoppm`) or `pip install pypdfium2 pillow` is available.
Authoring shortcuts in `src/pages/*.html` (expanded at build time):
`<a class="test-link" data-atlas="phalens-test">Phalen's test</a>` · `<a class="info-icon" data-atlas="jospt-2019-cts-cpg"></a>` ·
`<a class="calc-badge" data-atlas="prwe">Calc</a>` · `<a class="guide-badge" href="https://…">JOSPT CPG</a>`.
An unknown `data-atlas` id stops the build.

## Status
Draft cards under clinical review with open-access citations and video demonstrations.
