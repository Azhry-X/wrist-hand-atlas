#!/usr/bin/env python3
"""Build the Wrist & Hand Test Atlas (index.html at the repo root) from atlas/data/tests.yaml.

    python atlas/build_atlas.py

Every card is rendered as static HTML (deep-linkable as #card-id). Calculators are
described in the YAML (kinds: formula, scale, lsi) and run by a small generic JS engine,
so adding a calculator never needs new code.
"""
import json, html, pathlib, datetime, sys, re
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'atlas'))
from config import ATLAS_BASE_URL  # noqa: E402

PAGE_NAMES = {1: 'Triage & red flags', 2: 'Differential & prognosis', 3: 'Objective exam', 4: 'Special tests & PROMs',
              5: 'Post-surgical & fracture', 6: 'Orthoses, injections & EPAs', 7: 'Manual therapy', 8: 'Exercise & return to activity', 9: 'Flowsheet'}
PAGE_COLORS = {1: '#f87171', 2: '#60a5fa', 3: '#60a5fa', 4: '#60a5fa', 5: '#c084fc', 6: '#fb923c', 7: '#2dd4bf', 8: '#4ade80', 9: '#94a3b8'}
EV = {'H': ('High', 'ev-h'), 'M': ('Moderate', 'ev-m'), 'L': ('Low', 'ev-l'), 'E': ('Expert opinion', 'ev-e')}
e = html.escape


def yt_id(url):
    if not url:
        return None
    if 'watch?v=' in url:
        return url.split('watch?v=')[1].split('&')[0]
    if 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    return None


def dossier_pages():
    """Dossier pages that link to each card (scanned from src/pages/pN.html), so the page badges and
    page filters always match the PDF. A card that no page links to falls back to its YAML 'page'."""
    used = {}
    for n in range(1, 10):
        f = ROOT / 'src' / 'pages' / f'p{n}.html'
        if f.exists():
            for cid in re.findall(r'data-atlas="([^"]+)"', f.read_text(encoding='utf-8')):
                used.setdefault(cid, set()).add(n)
    return used


def render_card(c):
    cid = c['id']
    page = c['page']
    pages = c['_pages']
    color = PAGE_COLORS.get(page, '#94a3b8')
    vid = yt_id(c.get('video_url'))
    calc = c.get('calculator')
    plist = ', '.join(map(str, pages))
    ptag = 'P' + '·'.join(map(str, pages))
    ptitle = ('Dossier pages ' if len(pages) > 1 else 'Dossier page ') + plist
    badges = [f'<span class="b b-page" style="--pc:{color}" title="{ptitle}">{ptag}</span>',
              f'<span class="b b-type b-{e(c["type"])}">{e(c["type"].upper())}</span>']
    if vid:
        badges.append('<span class="b b-vid" title="Video">&#9654; VIDEO</span>')
    if calc:
        badges.append('<span class="b b-calc" title="Calculator">CALC</span>')
    if c.get('review_status', 'draft') != 'approved':
        badges.append('<span class="b b-draft">DRAFT</span>')
    search = ' '.join([c['title'], c.get('summary', ''), ' '.join(c.get('steps', []) or []), c.get('positive', '') or '', cid]).lower()
    body = []
    if c.get('summary'):
        body.append(f'<p class="summary">{e(c["summary"])}</p>')
    if vid:
        body.append(f'''<div class="video" data-vid="{e(vid)}">
          <button class="yt" type="button" aria-label="Play video: {e(c.get('video_title') or c['title'])}" style="background-image:url('https://i.ytimg.com/vi/{e(vid)}/hqdefault.jpg')"><span class="play" aria-hidden="true"></span></button>
          <div class="vcap">{e(c.get('video_title') or '')} &middot; <a href="https://www.youtube.com/watch?v={e(vid)}" target="_blank" rel="noopener">Open on YouTube</a></div>
        </div>''')
    if c.get('steps'):
        lis = ''.join(f'<li>{e(s)}</li>' for s in c['steps'])
        label = 'How to perform' if c['type'] == 'test' else 'Key points'
        body.append(f'<h4>{label}</h4><ol class="steps">{lis}</ol>')
    if c.get('positive'):
        body.append(f'<div class="box pos"><h4>Positive / result</h4><p>{e(c["positive"])}</p></div>')
    if c.get('interpretation'):
        body.append(f'<div class="box interp"><h4>Interpretation</h4><p>{e(c["interpretation"])}</p></div>')
    if c.get('metrics') or c.get('evidence'):
        ev = c.get('evidence')
        evh = f'<span class="ev {EV[ev][1]}">Evidence: {EV[ev][0]}</span>' if ev in EV else ''
        mt = f'<p>{e(c["metrics"])}</p>' if c.get('metrics') else ''
        body.append(f'<div class="box acc"><h4>Accuracy &amp; evidence {evh}</h4>{mt}</div>')
    if c.get('cautions'):
        body.append(f'<div class="box warn"><h4>Cautions</h4><p>{e(c["cautions"])}</p></div>')
    if calc:
        body.append(f'<div class="calc" data-calc="{e(json.dumps(calc, ensure_ascii=False))}"><h4>Calculator</h4><div class="calc-body"></div></div>')
    if c.get('sources'):
        lis = []
        for s in c['sources']:
            tag = ' <span class="ft">free full text</span>' if s.get('free_full_text') else ''
            if s.get('url'):
                lis.append(f'<li><a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["text"])}</a>{tag}</li>')
            else:
                lis.append(f'<li>{e(s["text"])}</li>')
        body.append(f'<h4>Sources</h4><ul class="src">{"".join(lis)}</ul>')
    where = (f'Dossier page {pages[0]} &middot; {e(PAGE_NAMES.get(pages[0], ""))}' if len(pages) == 1 else
             'Dossier ' + ' &middot; '.join(f'p{p} {e(PAGE_NAMES.get(p, ""))}' for p in pages))
    body.append(f'<div class="cfoot"><span>{where}</span>'
                f'<button class="copy" type="button" data-id="{e(cid)}">Copy link</button></div>')
    return f'''<article class="card" id="{e(cid)}" data-page="{' '.join(map(str, pages))}" data-type="{e(c['type'])}" data-vid="{1 if vid else 0}" data-calc="{1 if calc else 0}" data-search="{e(search)}" style="--pc:{color}">
  <button class="head" type="button" aria-expanded="false" aria-controls="{e(cid)}-body">
    <span class="badges">{''.join(badges)}</span>
    <span class="title">{e(c['title'])}</span>
    <span class="chev" aria-hidden="true"></span>
  </button>
  <div class="body" id="{e(cid)}-body" hidden>
    {''.join(body)}
  </div>
</article>'''


CSS = r"""
:root{--bg:#0b1220;--panel:#111a2e;--panel2:#16213a;--line:#24324f;--ink:#e6edf7;--mut:#94a3b8;--acc:#60a5fa;--good:#34d399;--warn:#fbbf24;--bad:#f87171;}
*{box-sizing:border-box} html{scroll-padding-top:150px}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 "Source Sans 3",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;-webkit-text-size-adjust:100%}
@font-face{font-family:"Source Sans 3";src:url("fonts/SourceSans3-Regular.ttf") format("truetype");font-weight:400;font-display:swap}
@font-face{font-family:"Source Sans 3";src:url("fonts/SourceSans3-Semibold.ttf") format("truetype");font-weight:600;font-display:swap}
@font-face{font-family:"Source Sans 3";src:url("fonts/SourceSans3-Bold.ttf") format("truetype");font-weight:700;font-display:swap}
a{color:#93c5fd}
.banner{background:#7c2d12;color:#ffedd5;text-align:center;font-weight:700;font-size:13px;padding:6px 16px}
.banner.ok{background:#14532d;color:#dcfce7}
header{position:sticky;top:0;z-index:20;background:rgba(11,18,32,.96);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:12px 16px 10px}
.hwrap{max-width:900px;margin:0 auto}
.trow{display:flex;align-items:center;justify-content:space-between;gap:12px}
h1{margin:0;font-size:21px;line-height:1.15;background:linear-gradient(90deg,#93c5fd,#c4b5fd);-webkit-background-clip:text;background-clip:text;color:transparent}
.count{font-size:12px;color:#bfdbfe;border:1px solid #1e3a8a;background:#0f1b3a;border-radius:999px;padding:3px 10px;white-space:nowrap}
.search{margin-top:10px;width:100%;padding:11px 14px;border-radius:12px;border:1px solid var(--line);background:var(--panel);color:var(--ink);font-size:16px}
.filters{display:flex;gap:6px;overflow-x:auto;padding:8px 0 2px;scrollbar-width:none}
.filters::-webkit-scrollbar{display:none}
.chip{flex:0 0 auto;border:1px solid var(--line);background:var(--panel);color:var(--mut);border-radius:999px;padding:5px 11px;font-size:13px;font-weight:600;cursor:pointer}
.chip.on{background:#1d4ed8;border-color:#1d4ed8;color:#fff}
main{max-width:900px;margin:0 auto;padding:12px 16px 40px}
.card{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--pc);border-radius:14px;margin:10px 0;overflow:hidden}
.card.hl{box-shadow:0 0 0 2px var(--pc)}
.head{all:unset;box-sizing:border-box;display:flex;align-items:center;gap:10px;width:100%;padding:12px 14px;cursor:pointer}
.head:focus-visible{outline:2px solid var(--acc);outline-offset:-2px}
.badges{display:flex;flex-direction:column;gap:3px;flex:0 0 auto}
.b{font-size:10.5px;font-weight:800;letter-spacing:.04em;border-radius:5px;padding:1px 6px;text-align:center;border:1px solid}
.b-page{color:#fff;background:color-mix(in srgb,var(--pc) 35%,transparent);border-color:var(--pc)}
.b-type{color:#86efac;border-color:#166534;background:#052e16}
.b-test{color:#93c5fd;border-color:#1e40af;background:#0b1f4d}
.b-vid{color:#fecaca;border-color:#7f1d1d;background:#2a0b0b}
.b-calc{color:#a7f3d0;border-color:#065f46;background:#022c22}
.b-draft{color:#fde68a;border-color:#92400e;background:#2a1a05}
.title{flex:1 1 auto;font-weight:700;font-size:16px;line-height:1.25}
.chev{width:10px;height:10px;border-right:2px solid var(--mut);border-bottom:2px solid var(--mut);transform:rotate(45deg);transition:transform .15s;margin-right:4px}
.card.open .chev{transform:rotate(-135deg)}
.body{padding:2px 16px 14px}
.summary{color:#cbd5e1;margin:0 0 8px}
h4{margin:12px 0 6px;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:#a5b4fc}
.steps{margin:0;padding-left:20px} .steps li{margin:3px 0}
.box{border-radius:10px;padding:8px 12px;margin:10px 0;border:1px solid var(--line);background:var(--panel2)}
.box h4{margin-top:2px} .box p{margin:0}
.box.pos{border-color:#1e40af} .box.interp{border-color:#334155} .box.acc{border-color:#065f46} .box.warn{border-color:#7f1d1d;background:#1f0d0d}
.ev{font-size:11px;font-weight:800;border-radius:5px;padding:1px 7px;margin-left:6px;letter-spacing:.02em;text-transform:none}
.ev-h{background:#064e3b;color:#a7f3d0} .ev-m{background:#78350f;color:#fde68a} .ev-l{background:#7f1d1d;color:#fecaca} .ev-e{background:#312e81;color:#c7d2fe}
.video{margin:8px 0 4px}
.yt{all:unset;cursor:pointer;display:block;width:100%;aspect-ratio:16/9;border-radius:10px;background-size:cover;background-position:center;position:relative;background-color:#000}
.yt .play{position:absolute;left:50%;top:50%;width:68px;height:48px;transform:translate(-50%,-50%);background:#dc2626;border-radius:12px}
.yt .play::after{content:"";position:absolute;left:27px;top:14px;border-left:18px solid #fff;border-top:10px solid transparent;border-bottom:10px solid transparent}
.video iframe{width:100%;aspect-ratio:16/9;border:0;border-radius:10px}
.vcap{font-size:12.5px;color:var(--mut);margin-top:4px}
.src{margin:0;padding-left:18px;font-size:13.5px} .src li{margin:3px 0}
.ft{font-size:11px;font-weight:700;color:#a7f3d0;border:1px solid #065f46;border-radius:4px;padding:0 5px;margin-left:4px;white-space:nowrap}
.cfoot{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:12px;padding-top:8px;border-top:1px dashed var(--line);font-size:12.5px;color:var(--mut)}
.copy{all:unset;cursor:pointer;white-space:nowrap;flex:0 0 auto;font-size:12.5px;font-weight:700;color:#93c5fd;border:1px solid #1e3a8a;border-radius:8px;padding:3px 10px}
.calc{border:1px solid #065f46;background:#06261d;border-radius:12px;padding:6px 12px 12px;margin:12px 0}
.calc h4{color:#6ee7b7}
.ch{font-size:12px;font-weight:800;color:#6ee7b7;text-transform:uppercase;letter-spacing:.05em;margin:10px 0 2px}
.fi{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.06)}
.fi label{flex:1 1 auto}
.fi.st{flex-wrap:wrap}
.fi.st label{flex:1 1 14em;line-height:1.35}
.fi.st select{width:100%;max-width:26em}
.cnote{font-size:12.5px;color:var(--mut);margin:2px 0 6px;line-height:1.4}
.fi input[type=checkbox]{width:22px;height:22px;accent-color:#10b981;flex:0 0 auto}
.fi input[type=number],.fi select{width:9.5em;max-width:55%;padding:7px 9px;border-radius:8px;border:1px solid var(--line);background:#0b1220;color:var(--ink);font-size:16px}
.res{margin-top:10px;border-radius:10px;padding:10px 12px;font-weight:700;background:#0b1220;border:1px solid var(--line)}
.res .val{font-size:22px;display:block;color:#fff}
.res.good{border-color:#059669;color:#a7f3d0} .res.warn{border-color:#d97706;color:#fde68a} .res.bad{border-color:#dc2626;color:#fecaca}
.lsi{width:100%;border-collapse:collapse;font-size:14px;table-layout:fixed}
.lsi th:first-child{width:36%} .lsi th:last-child{width:16%}
.lsi th,.lsi td{padding:5px 4px;border-bottom:1px solid rgba(255,255,255,.07);text-align:left}
.lsi input{width:100%;padding:6px 7px;border-radius:7px;border:1px solid var(--line);background:#0b1220;color:var(--ink);font-size:16px}
.pass{color:#34d399;font-weight:800} .fail{color:#f87171;font-weight:800}
.reset{all:unset;cursor:pointer;font-size:12.5px;color:var(--mut);margin-top:8px;display:inline-block;text-decoration:underline}
.empty{color:var(--mut);text-align:center;padding:30px 0}
footer{max-width:900px;margin:0 auto;padding:10px 16px 40px;color:var(--mut);font-size:13px;border-top:1px solid var(--line)}
@media (max-width:520px){h1{font-size:18px}.title{font-size:15px}.badges{flex-direction:row;flex-wrap:wrap;max-width:110px}}
"""

JS = r"""
(function(){
  const cards=[...document.querySelectorAll('.card')];
  const q=document.getElementById('q'); const chips=[...document.querySelectorAll('.chip')];
  let filter='all';
  function openCard(card, scroll){
    if(!card) return;
    const head=card.querySelector('.head'), body=card.querySelector('.body');
    card.classList.add('open'); head.setAttribute('aria-expanded','true'); body.hidden=false;
    initCalc(card); if(scroll){ card.scrollIntoView({behavior:'smooth',block:'start'}); card.classList.add('hl'); setTimeout(()=>card.classList.remove('hl'),1800); }
  }
  function toggle(card){
    const head=card.querySelector('.head'), body=card.querySelector('.body');
    const open=!card.classList.contains('open');
    card.classList.toggle('open',open); head.setAttribute('aria-expanded',String(open)); body.hidden=!open;
    if(open){ initCalc(card); history.replaceState(null,'','#'+card.id); }
  }
  cards.forEach(c=>c.querySelector('.head').addEventListener('click',()=>toggle(c)));
  function apply(){
    const term=(q.value||'').trim().toLowerCase(); let n=0;
    cards.forEach(c=>{
      let ok=true;
      if(filter==='test') ok=c.dataset.type==='test';
      else if(filter==='info') ok=c.dataset.type!=='test';
      else if(filter==='video') ok=c.dataset.vid==='1';
      else if(filter==='calc') ok=c.dataset.calc==='1';
      else if(filter.startsWith('p')) ok=c.dataset.page.split(' ').includes(filter.slice(1));
      if(ok && term) ok=c.dataset.search.includes(term);
      c.style.display=ok?'':'none'; if(ok) n++;
    });
    document.getElementById('empty').style.display=n?'none':'';
    document.getElementById('shown').textContent=n;
  }
  q.addEventListener('input',apply);
  chips.forEach(ch=>ch.addEventListener('click',()=>{chips.forEach(x=>x.classList.remove('on')); ch.classList.add('on'); filter=ch.dataset.f; apply();}));
  document.querySelectorAll('.copy').forEach(b=>b.addEventListener('click',ev=>{
    ev.stopPropagation(); const url=location.origin+location.pathname+'#'+b.dataset.id;
    (navigator.clipboard?navigator.clipboard.writeText(url):Promise.reject()).then(()=>{b.textContent='Copied';setTimeout(()=>b.textContent='Copy link',1500)}).catch(()=>{prompt('Copy this link',url)});
  }));
  document.querySelectorAll('.video').forEach(v=>{
    v.querySelector('.yt').addEventListener('click',()=>{
      const f=document.createElement('iframe');
      f.src='https://www.youtube-nocookie.com/embed/'+v.dataset.vid+'?autoplay=1&rel=0&playsinline=1';
      f.allow='autoplay; encrypted-media; picture-in-picture; fullscreen'; f.allowFullscreen=true; f.title='Video';
      v.querySelector('.yt').replaceWith(f);
    });
  });
  // ---------------- calculator engine ----------------
  function fmt(x,d){ if(typeof x!=='number'||!isFinite(x)) return '—'; return (d==null?x:Number(x.toFixed(d))).toString(); }
  function tmpl(text,scope){ return text.replace(/\{([^}|]+)(?:\|(\d+))?\}/g,(m,ex,d)=>{ try{ const f=new Function(...Object.keys(scope),'return ('+ex+');'); return fmt(f(...Object.values(scope)), d==null?null:+d);}catch(e){return '—';} }); }
  function initCalc(card){
    const box=card.querySelector('.calc'); if(!box||box.dataset.ready) return; box.dataset.ready='1';
    const spec=JSON.parse(box.dataset.calc); const host=box.querySelector('.calc-body');
    if(spec.kind==='formula') formula(spec,host); else if(spec.kind==='scale') scale(spec,host); else if(spec.kind==='lsi') lsi(spec,host);
  }
  function el(tag,attrs,html){ const n=document.createElement(tag); Object.assign(n,attrs||{}); if(html!=null) n.innerHTML=html; return n; }
  function formula(spec,host){
    const keys=[];
    spec.inputs.forEach((inp,i)=>{
      if(inp.heading){ host.appendChild(el('div',{className:'ch'},inp.heading)); return; }
      const id=host.closest('.card').id+'-'+inp.key; keys.push(inp);
      const row=el('div',{className:'fi'});
      if(inp.type==='check'){ const cb=el('input',{type:'checkbox',id}); const lb=el('label',{htmlFor:id},inp.label); row.append(cb,lb); }
      else if(inp.type==='number'){ const lb=el('label',{htmlFor:id},inp.label); const nb=el('input',{type:'number',id,inputMode:'decimal',step:'any'}); row.append(lb,nb); }
      else if(inp.type==='select'){ const lb=el('label',{htmlFor:id},inp.label); const s=el('select',{id}); inp.options.forEach(o=>s.appendChild(el('option',{value:o[0]},o[1]))); row.append(lb,s); }
      host.appendChild(row);
    });
    const res=el('div',{className:'res'}); host.appendChild(res);
    const reset=el('button',{className:'reset',type:'button'},'Reset'); host.appendChild(reset);
    function calc(){
      const scope={};
      keys.forEach(inp=>{ const n=document.getElementById(host.closest('.card').id+'-'+inp.key);
        scope[inp.key]= inp.type==='check' ? (n.checked?1:0) : (n.value===''?NaN:parseFloat(n.value)); });
      let v; try{ v=new Function(...Object.keys(scope),'return ('+spec.expr+');')(...Object.values(scope)); }catch(e){ v=NaN; }
      scope.v=v;
      let html='';
      if(spec.value_label) html+='<span class="val">'+(isFinite(v)?fmt(v,spec.decimals):'—')+'</span><span>'+spec.value_label+'</span>';
      let tone='';
      const usesNumber=keys.some(k=>k.type==='number');
      if(!(usesNumber && !isFinite(v))){
        for(const o of (spec.outputs||[])){
          let ok=false; try{ ok=!!new Function(...Object.keys(scope),'return ('+o.when+');')(...Object.values(scope)); }catch(e){}
          if(ok){ html+=(html?'<br>':'')+tmpl(o.text,scope); tone=o.tone||''; break; }
        }
      } else if(!spec.value_label){ html='Enter the values above'; }
      res.className='res '+tone; res.innerHTML=html||'Enter the values above';
    }
    host.addEventListener('input',calc); host.addEventListener('change',calc);
    reset.addEventListener('click',()=>{ host.querySelectorAll('input').forEach(i=>{ if(i.type==='checkbox') i.checked=false; else i.value=''; }); host.querySelectorAll('select').forEach(s=>s.selectedIndex=0); calc(); });
    calc();
  }
  function scale(spec,host){
    const step=spec.step||1; const sels=[];
    if(spec.note) host.appendChild(el('div',{className:'cnote'},spec.note));
    function addRange(s,lo,hi,st,desc,labels){
      const vals=[]; for(let x=lo;x<=hi+1e-9;x+=st) vals.push(Math.round(x*100)/100);
      if(desc) vals.reverse();
      vals.forEach(x=>s.appendChild(el('option',{value:x},(labels&&labels[x]!=null)?labels[x]:String(x))));
    }
    for(let i=1;i<=spec.items;i++){
      const id=host.closest('.card').id+'-i'+i;
      const lab=(spec.item_labels&&spec.item_labels[i-1])?(i+'. '+spec.item_labels[i-1]):((spec.item_label||'Item')+' '+i);
      const row=el('div',{className:'fi st'});
      const s=el('select',{id}); s.appendChild(el('option',{value:''},'— select —'));
      const io=spec.item_options&&spec.item_options[i-1];
      if(Array.isArray(io)&&io.length&&io[0]&&io[0].group){
        io.forEach(g=>{ const og=el('optgroup',{label:g.group}); g.options.forEach(o=>og.appendChild(el('option',{value:o[0]},o[1]))); s.appendChild(og); });
      } else if(Array.isArray(io)){
        io.forEach(o=>s.appendChild(el('option',{value:o[0]},o[1])));
      } else if(io&&io.range10){
        addRange(s,0,10,1,false,{0:'0 · '+io.range10,10:'10 · none / no problem'});
      } else addRange(s,spec.min,spec.max,step,spec.order==='desc',spec.option_labels);
      row.append(el('label',{htmlFor:id},lab), s); host.appendChild(row); sels.push(s);
    }
    const res=el('div',{className:'res'}); host.appendChild(res);
    const reset=el('button',{className:'reset',type:'button'},'Reset'); host.appendChild(reset);
    function calc(){
      const vals=sels.map(s=>s.value===''?null:+s.value).filter(v=>v!==null);
      if(!vals.length){ res.className='res'; res.innerHTML='Answer each item to see the score'; return; }
      const sum=vals.reduce((a,b)=>a+b,0); const v=spec.aggregate==='mean'?sum/vals.length:sum;
      const done=vals.length===spec.items;
      res.className='res '+(done?'good':'warn'); res.innerHTML='<span class="val">'+fmt(v,spec.decimals)+'</span><span>'+spec.value_label+' &middot; '+vals.length+'/'+spec.items+' items answered'+(done?'':' (incomplete)')+'</span>';
    }
    host.addEventListener('change',calc); reset.addEventListener('click',()=>{sels.forEach(s=>s.value=''); calc();}); calc();
  }
  function lsi(spec,host){
    const t=el('table',{className:'lsi'}); t.innerHTML='<tr><th>Test</th><th>Involved</th><th>Uninvolved</th><th>LSI</th></tr>';
    const rows=spec.rows.map((r,i)=>{ const tr=el('tr'); tr.innerHTML='<td>'+r.label+'</td><td><input type="number" inputmode="decimal" step="any"></td><td><input type="number" inputmode="decimal" step="any"></td><td class="o">—</td>'; t.appendChild(tr); return [tr,r]; });
    host.appendChild(t); const res=el('div',{className:'res'}); host.appendChild(res);
    function calc(){
      let done=0, pass=0;
      rows.forEach(([tr,r])=>{ const [a,b]=[...tr.querySelectorAll('input')].map(x=>parseFloat(x.value)); const o=tr.querySelector('.o');
        if(isFinite(a)&&isFinite(b)&&a>0&&b>0){ const v=r.mode==='time'? b/a*100 : a/b*100; const ok=v>=spec.threshold; done++; if(ok) pass++;
          o.innerHTML='<span class="'+(ok?'pass':'fail')+'">'+v.toFixed(0)+'%</span>'; } else o.textContent='—'; });
      res.className='res '+(done? (pass===done?'good':'bad') : ''); res.innerHTML= done? pass+' / '+done+' tests at LSI ≥ '+spec.threshold+'%' : 'Enter involved and uninvolved values (timed tests: seconds)';
    }
    host.addEventListener('input',calc); calc();
  }
  function fromHash(){ const id=decodeURIComponent(location.hash.slice(1)); if(!id) return; const c=document.getElementById(id); if(c&&c.classList.contains('card')){ c.style.display=''; openCard(c,true);} }
  window.addEventListener('hashchange',fromHash); fromHash(); apply();
})();
"""


def main():
    cards = yaml.safe_load((ROOT / 'atlas' / 'data' / 'tests.yaml').read_text(encoding='utf-8'))
    used = dossier_pages()
    for c in cards:
        c['_pages'] = sorted(used.get(c['id']) or {c['page']})
    cards.sort(key=lambda c: (c['page'], 0 if c['type'] == 'test' else 1, c['title'].lower()))
    n = len(cards)
    nv = sum(1 for c in cards if c.get('video_url'))
    nc = sum(1 for c in cards if c.get('calculator'))
    pages = sorted(set().union(*(c['_pages'] for c in cards)))
    chips = ['<button class="chip on" data-f="all" type="button">All</button>',
             '<button class="chip" data-f="test" type="button">Tests</button>',
             '<button class="chip" data-f="info" type="button">Info</button>',
             f'<button class="chip" data-f="video" type="button">&#9654; Video ({nv})</button>',
             f'<button class="chip" data-f="calc" type="button">Calculators ({nc})</button>']
    chips += [f'<button class="chip" data-f="p{p}" type="button">P{p} {html.escape(PAGE_NAMES[p])}</button>' for p in pages]
    built = datetime.date.today().isoformat()
    ndraft = sum(1 for c in cards if c.get('review_status', 'draft') != 'approved')
    banner = ('<div class="banner">Clinical education reference &mdash; ' +
              (f'{ndraft} card{"s" if ndraft != 1 else ""} still under clinical review' if ndraft else 'clinically reviewed') +
              '. Not a substitute for clinical judgement.</div>')
    if not ndraft:
        banner = banner.replace('class="banner"', 'class="banner ok"')
    doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Wrist &amp; Hand — Test Atlas</title>
<meta name="description" content="Companion Test Atlas for the Wrist &amp; Hand Master Dossier: how to perform each test, positive criteria, accuracy, evidence level, verified videos and calculators.">
<meta name="theme-color" content="#0b1220">
<style>{CSS}</style>
</head>
<body>
{banner}
<header><div class="hwrap">
  <div class="trow"><h1>Wrist &amp; Hand &mdash; Test Atlas</h1><span class="count"><span id="shown">{n}</span> / {n} cards</span></div>
  <input id="q" class="search" type="search" placeholder="Search tests, criteria, conditions…" autocomplete="off" aria-label="Search the atlas">
  <div class="filters" role="toolbar" aria-label="Filters">{''.join(chips)}</div>
</div></header>
<main>
{''.join(render_card(c) for c in cards)}
<p id="empty" class="empty" style="display:none">No cards match. Clear the search or choose another filter.</p>
</main>
<footer>
  Companion to the <b>Wrist &amp; Hand Master Clinical Assessment &amp; Rehabilitation Dossier</b> (9-page A4). Tap a test name in the PDF to open its card here.
  Videos: Physiotutors &amp; verified clinical channels (YouTube), verified by title. Evidence levels: High &middot; Moderate &middot; Low &middot; Expert opinion.
  Sister atlases: <a href="https://azhry-x.github.io/knee-atlas/">Knee Complex Test Atlas</a> &middot; <a href="https://azhry-x.github.io/ankle-atlas/">Ankle &amp; Foot Test Atlas</a> &middot; <a href="https://azhry-x.github.io/lumbar-atlas/">Lumbar Spine Test Atlas</a> &middot; <a href="https://azhry-x.github.io/shoulder-atlas/">Shoulder Complex Test Atlas</a> &middot; <a href="https://azhry-x.github.io/cervical-atlas/">Cervical Spine Test Atlas</a> &middot; <a href="https://azhry-x.github.io/elbow-atlas/">Elbow Test Atlas</a>. Built {built}.
</footer>
<script>{JS}</script>
</body>
</html>
'''
    (ROOT / 'index.html').write_text(doc, encoding='utf-8')
    print(f'index.html: {n} cards, {nv} videos, {nc} calculators -> {ROOT / "index.html"}')


if __name__ == '__main__':
    main()
