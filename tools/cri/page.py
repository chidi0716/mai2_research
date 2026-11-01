"""用 extract.py 輸出的 cues.json 產生單檔試聽頁: python -I page.py <輸出目錄>
產生 <輸出目錄>/index.html, 音檔沿用 audio/*.mp3。直接用瀏覽器開即可(不需伺服器)。"""
import sys, json, html
out = sys.argv[1]
cues = json.load(open(out + '/cues.json', encoding='utf-8'))['cues']
data = json.dumps(cues, ensure_ascii=False).replace('</', '<\\/')
page = '''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>音效試聽</title><style>
:root{--bg:#f6f6f8;--fg:#1d1d22;--card:#fff;--line:#ddd;--acc:#2b6de8}
@media (prefers-color-scheme:dark){:root{--bg:#16161a;--fg:#e8e8ee;--card:#222228;--line:#333;--acc:#6b9bff}}
body{margin:0;background:var(--bg);color:var(--fg);font:14px system-ui,sans-serif;padding:12px 16px 90px}
input{width:100%;box-sizing:border-box;padding:8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
.row{display:flex;gap:8px;align-items:center;padding:6px 8px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.id{width:3.5em;opacity:.6}.nm{flex:1;min-width:10em;word-break:break-all}
button{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:5px;padding:3px 9px;cursor:pointer}
button.on{background:var(--acc);color:#fff}.none{opacity:.45}
#bar{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:8px 16px;display:flex;gap:10px;align-items:center}
#seek{flex:1}</style>
<input id="q" placeholder="搜尋名稱或編號"><div id="list"></div>
<div id="bar"><button id="pp">▶</button><span id="now">未播放</span><input id="seek" type="range" min="0" max="1000" value="0"><span id="t">0:00</span></div>
<script>
const C=__DATA__,a=new Audio(),L=document.getElementById('list');let cur=null,queue=[];
const f=s=>Math.floor(s/60)+':'+String(Math.floor(s%60)).padStart(2,'0');
function play(c,files,btn){queue=files.slice();cur&&cur.classList.remove('on');cur=btn;btn.classList.add('on');
 document.getElementById('now').textContent=c.id+' '+c.name;next()}
function next(){if(!queue.length){cur&&cur.classList.remove('on');return}a.src='audio/'+queue.shift();a.play()}
a.onended=next;a.ontimeupdate=()=>{if(a.duration){seek.value=a.currentTime/a.duration*1000;t.textContent=f(a.currentTime)+' / '+f(a.duration)}};
a.onplay=()=>pp.textContent='❚❚';a.onpause=()=>pp.textContent='▶';
seek.oninput=()=>{if(a.duration)a.currentTime=seek.value/1000*a.duration};
pp.onclick=()=>a.paused?a.play():a.pause();
function render(){const k=q.value.trim().toLowerCase();L.innerHTML='';
 for(const c of C){if(k&&!(c.name.toLowerCase().includes(k)||String(c.id)==k))continue;
  const r=document.createElement('div');r.className='row'+(c.files.length?'':' none');
  r.innerHTML='<span class="id">'+c.id+'</span><span class="nm"></span>';r.querySelector('.nm').textContent=c.name+(c.len?' ('+c.len.toFixed(2)+'s)':'');
  c.files.forEach((fn,i)=>{const b=document.createElement('button');b.textContent=c.files.length>1?'#'+(i+1):'▶';b.onclick=()=>play(c,[fn],b);r.append(b)});
  if(c.files.length>1){const b=document.createElement('button');b.textContent='全部';b.onclick=()=>play(c,c.files,b);r.append(b)}
  if(!c.files.length)r.append('（無聲音）');L.append(r)}}
q.oninput=render;render();
document.onkeydown=e=>{if(e.target===q)return;if(e.code==='Space'){e.preventDefault();pp.click()}if(e.key==='Escape'){a.pause();a.currentTime=0}};
</script></html>'''.replace('__DATA__', data)
open(out + '/index.html', 'w', encoding='utf-8').write(page)
print('wrote', out + '/index.html', len(cues), 'cues')
