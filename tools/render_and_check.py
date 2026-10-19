#!/usr/bin/env python3
"""Render master_wrist_hand_dossier.html to PDF with Chromium and verify it.

Hard failures (exit 1):
  * page count != 9
  * any content overflowing its page, page body, card, box or table cell (DOM geometry, print media)
  * any element poking outside its card or page
  * overlapping words in the PDF text layer
  * bundled font not used / Type 3 font present
  * a REQUIRED string missing from the PDF text
Writes preview/page-N.png for visual review.
"""
import sys, json, shutil, subprocess, pathlib, asyncio, re

for _s in (sys.stdout, sys.stderr):  # Windows consoles: never crash on ▸ ≥ ° in messages
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT = pathlib.Path(__file__).resolve().parents[1]
HTML = ROOT / 'master_wrist_hand_dossier.html'
PDF = ROOT / 'master_wrist_hand_dossier.pdf'
PREV = ROOT / 'preview'

DOM_CHECK_JS = r"""
() => {
  const out = [];
  const snip = el => (el.innerText || el.className || el.tagName).toString().replace(/\s+/g,' ').slice(0,90);
  const pages = [...document.querySelectorAll('.clinical-page')];
  pages.forEach((pg, i) => {
    const P = i + 1, pr = pg.getBoundingClientRect();
    if (pg.scrollHeight > pg.clientHeight + 1) out.push(`p${P}: PAGE overflow by ${(pg.scrollHeight-pg.clientHeight).toFixed(1)}px`);
    const body = pg.querySelector('.pg-body');
    if (body && body.scrollHeight > body.clientHeight + 1) out.push(`p${P}: BODY overflow by ${(body.scrollHeight-body.clientHeight).toFixed(1)}px`);
    pg.querySelectorAll('.card, .box, .mini, .crit, .note, .dots, td, th, .router-col').forEach(el => {
      if (el.scrollHeight > el.clientHeight + 1.5) out.push(`p${P}: V-overflow ${(el.scrollHeight-el.clientHeight).toFixed(1)}px in ${el.tagName}.${el.className} :: ${snip(el)}`);
      if (el.scrollWidth > el.clientWidth + 1.5) out.push(`p${P}: H-overflow ${(el.scrollWidth-el.clientWidth).toFixed(1)}px in ${el.tagName}.${el.className} :: ${snip(el)}`);
    });
    pg.querySelectorAll('.card').forEach(card => {
      const cr = card.getBoundingClientRect();
      card.querySelectorAll('*').forEach(el => {
        if (el.closest('svg') && el.tagName.toLowerCase() !== 'svg') return;
        const r = el.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) return;
        if (r.right > cr.right + 0.6 || r.left < cr.left - 0.6 || r.bottom > cr.bottom + 0.6)
          out.push(`p${P}: OUTSIDE CARD (${(r.right-cr.right).toFixed(1)},${(r.bottom-cr.bottom).toFixed(1)}) ${el.tagName}.${el.className} :: ${snip(el)}`);
      });
    });
    pg.querySelectorAll('*').forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) return;
      if (r.right > pr.right + 0.5 || r.bottom > pr.bottom + 0.5) out.push(`p${P}: OUTSIDE PAGE ${el.tagName}.${el.className} :: ${snip(el)}`);
    });
  });
  return out;
}
"""


async def render():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 794, 'height': 1123})
        await pg.emulate_media(media='print')
        await pg.goto(HTML.as_uri(), wait_until='load')
        await pg.evaluate('document.fonts.ready')
        font_ok = await pg.evaluate('document.fonts.check(\'700 12px "Source Sans 3"\') && document.fonts.check(\'400 12px "Source Sans 3"\')')
        issues = await pg.evaluate(DOM_CHECK_JS)
        # dedupe nested repeats
        seen, dom = set(), []
        for s in issues:
            if s not in seen:
                seen.add(s); dom.append(s)
        await pg.pdf(path=str(PDF), prefer_css_page_size=True, print_background=True)
        await b.close()
        return font_ok, dom


def pdf_fonts(reader):
    """Walk page and form-XObject resources (pure Python, no poppler needed).
    Returns (font names without subset prefix, has_type3, names of fonts that are not embedded)."""
    names, type3, not_embedded, seen = set(), False, set(), set()

    def embedded(f):
        fd = f.get('/FontDescriptor')
        if fd is None and f.get('/DescendantFonts'):
            fd = f['/DescendantFonts'][0].get_object().get('/FontDescriptor')
        if fd is None:
            return f.get('/Subtype') == '/Type3'
        fd = fd.get_object()
        return any(k in fd for k in ('/FontFile', '/FontFile2', '/FontFile3'))

    def walk(res):
        nonlocal type3
        if res is None:
            return
        res = res.get_object()
        fonts = res.get('/Font')
        for f in (fonts.get_object().values() if fonts else []):
            f = f.get_object()
            if f.get('/Subtype') == '/Type3':
                type3 = True
            name = re.sub(r'^[A-Z]{6}\+', '', str(f.get('/BaseFont', '/Type3')).lstrip('/'))
            names.add(name)
            if not embedded(f):
                not_embedded.add(name)
        xo = res.get('/XObject')
        for x in (xo.get_object().values() if xo else []):
            key = getattr(x, 'idnum', None) or id(x)
            if key in seen:
                continue
            seen.add(key)
            x = x.get_object()
            if x.get('/Subtype') == '/Form':
                walk(x.get('/Resources'))

    for p in reader.pages:
        walk(p.get('/Resources'))
    return names, type3, not_embedded


def pdf_checks():
    import pdfplumber
    from pypdf import PdfReader
    fails, info = [], []
    r = PdfReader(str(PDF))
    n = len(r.pages)
    info.append(f'pages: {n}')
    if n != 9:
        fails.append(f'page count {n} != 9')
    ext, internal, small = [], 0, []
    for i, pgobj in enumerate(r.pages, 1):
        for a in pgobj.get('/Annots') or []:
            a = a.get_object()
            if a.get('/Subtype') != '/Link':
                continue
            x0, y0, x1, y1 = [float(v) for v in a['/Rect']]
            A = a.get('/A')
            if A is not None and A.get('/URI'):
                ext.append((i, str(A['/URI'])))
            else:
                internal += 1
                w_mm, h_mm = (x1 - x0) / 72 * 25.4, (y1 - y0) / 72 * 25.4
                if min(w_mm, h_mm) < 4.0:
                    small.append((i, round(w_mm, 1), round(h_mm, 1)))
    info.append(f'internal links: {internal}  external links: {len(ext)}  (unique external: {len(set(u for _, u in ext))})')
    if small:
        fails.append(f'internal link targets smaller than 4 mm: {small[:6]}')
    # fonts
    fams, type3, not_emb = pdf_fonts(r)
    if type3:
        fails.append('Type 3 font present (emoji/glyph fallback)')
    if not any(f.startswith('SourceSans3') for f in fams):
        fails.append('bundled Source Sans 3 not embedded')
    if not_emb:
        fails.append('fonts not embedded: ' + ', '.join(sorted(not_emb)))
    others = sorted(f for f in fams if not f.startswith('SourceSans3'))
    if others:
        fails.append('glyph fallback to a non-bundled font (a character is missing from Source Sans 3): ' + ', '.join(others))
    info.append('embedded fonts: ' + ', '.join(sorted(fams)))
    # overlapping glyphs on the text layer — checked per character, so a collision on the same line
    # (which word extraction would silently merge into one "word") is caught as well as line-on-line
    text_all = []
    with pdfplumber.open(str(PDF)) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text_all.append(page.extract_text() or '')
            chars = sorted((c for c in page.dedupe_chars().chars if c['text'].strip()),
                           key=lambda c: (c['top'], c['x0']))
            hits = []
            for k, a in enumerate(chars):
                for b in chars[k + 1:]:
                    if b['top'] >= a['bottom']:
                        break
                    ix = min(a['x1'], b['x1']) - max(a['x0'], b['x0'])
                    iy = min(a['bottom'], b['bottom']) - max(a['top'], b['top'])
                    if ix > 1.0 and iy > 1.5:
                        hits.append(a)
                        break
            reported = []
            for a in hits:
                if any(abs(a['top'] - t) < 3 and abs(a['x0'] - x) < 40 for t, x in reported):
                    continue
                reported.append((a['top'], a['x0']))
                ctx = ''.join(c['text'] for c in sorted(
                    (c for c in chars if abs(c['top'] - a['top']) < 2.5 and abs(c['x0'] - a['x0']) < 45),
                    key=lambda c: c['x0']))
                fails.append(f'p{i}: overlapping text at x={a["x0"] / 72 * 25.4:.0f} mm, y={a["top"] / 72 * 25.4:.0f} mm :: "{ctx}"')
    # leaked markup / placeholders in the printed text (e.g. a broken "&lambda;" printing as "lambda;")
    for i, t in enumerate(text_all, 1):
        for m in re.finditer(r'&[a-zA-Z]{2,8};|\b(?:lambda|ndash|mdash|nbsp|middot|rarr|larr|uarr|darr|times|asymp|plusmn|deg|amp|quot)\b;'
                             r'|\b(?:undefined|NaN|TODO|FIXME|XXX|lorem)\b|\{\{|\}\}', t):
            fails.append(f'p{i}: leaked markup/placeholder "{m.group(0)}" :: "{t[max(0, m.start() - 30):m.end() + 30].strip()}"')
    req = ROOT / 'tools' / 'required_strings.txt'
    if req.exists():
        blob = re.sub(r'\s+', ' ', ' '.join(text_all))
        missing = []
        for line in req.read_text(encoding='utf-8').splitlines():
            s = line.strip()
            if s and not s.startswith('#') and re.sub(r'\s+', ' ', s).lower() not in blob.lower():
                missing.append(s)
        info.append(f'required strings: {sum(1 for l in req.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")) - len(missing)} present, {len(missing)} missing')
        fails += [f'missing required string: {m}' for m in missing]
    (ROOT / 'build').mkdir(exist_ok=True)
    (ROOT / 'build' / 'external_links.json').write_text(json.dumps(sorted(set(u for _, u in ext)), indent=1), encoding='utf-8')
    return fails, info


def previews():
    """PNG previews for visual review: poppler's pdftoppm if installed, else pypdfium2 (+ pillow), else skipped."""
    PREV.mkdir(exist_ok=True)
    for f in PREV.glob('page-*.png'):
        f.unlink()
    exe = shutil.which('pdftoppm')
    if exe:
        subprocess.run([exe, '-r', '110', '-png', str(PDF), str(PREV / 'page')], check=True)
        return 'previews: preview/page-N.png (pdftoppm)'
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(PDF))
        for i in range(len(doc)):
            doc[i].render(scale=110 / 72).to_pil().save(PREV / f'page-{i + 1}.png')
        return 'previews: preview/page-N.png (pypdfium2)'
    except ImportError:
        return 'previews: skipped (optional: pip install pypdfium2 pillow)'


if __name__ == '__main__':
    font_ok, dom = asyncio.run(render())
    fails, info = pdf_checks()
    info.append(previews())
    if not font_ok:
        fails.insert(0, 'Source Sans 3 did not load')
    fails = dom + fails
    print('\n'.join(info))
    if fails:
        print(f'\nFAIL ({len(fails)} issues)')
        for f in fails[:80]:
            print('  -', f)
        sys.exit(1)
    print('\nALL CHECKS PASSED')
