from __future__ import annotations
import json, uuid
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from .models import AssetSpec, AssetMetadata
from .pipeline import SceneInputParser, RequirementEngine, AssetMatcher, PromptGenerator, AtlasPacker, MattingEngine, MockImageProvider, crop_atlas
from .store import AssetStore

ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/"data"; ASSETS=DATA/"assets"; ATLAS=DATA/"atlases"
for p in (ASSETS,ATLAS): p.mkdir(parents=True,exist_ok=True)
store=AssetStore(str(DATA/"assetatlas.db")); parser=SceneInputParser(); engine=RequirementEngine(); prompts=PromptGenerator(); packer=AtlasPacker(); matte=MattingEngine(); provider=MockImageProvider()
app=FastAPI(title="AssetAtlas",version="0.1.0")

@app.get("/",response_class=HTMLResponse)
def index():
    return '''<!doctype html><html><head><meta charset=utf-8><title>AssetAtlas</title><style>body{font:15px system-ui;max-width:1100px;margin:40px auto;padding:0 20px}textarea{width:100%;height:180px}button{padding:9px 14px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px}.card{border:1px solid #ddd;padding:10px}.card img{width:100%;background:#eee}</style></head><body><h1>AssetAtlas</h1><p>Scene → requirements → dedupe → atlas → PNG → library.</p><textarea id=t placeholder="Scene 04\nLocation: Warehouse\nMood: Dark / cinematic\nRequired elements:\n- dense background smoke\n- sparks\n- overhead light rays"></textarea><br><button onclick=run()>Analyze & Process</button> <input id=q placeholder="Search assets" oninput=search()><h2>Library</h2><div id=out class=grid></div><script>async function run(){let r=await fetch('/api/process',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({text:t.value,filename:'scene.txt'})});let j=await r.json();alert(JSON.stringify(j,null,2));search()}async function search(){let j=await (await fetch('/api/assets?q='+encodeURIComponent(q.value))).json();out.innerHTML=j.map(a=>`<div class=card><img src="/files/assets/${a.filename}"><b>${a.filename}</b><br>${a.tags.join(', ')}</div>`).join('')}</script></body></html>'''

@app.post("/api/analyze")
def analyze(payload:dict):
    scenes=parser.parse(payload.get("text",json.dumps(payload.get("scenes",[]))),payload.get("filename","scene.json")); reqs=engine.extract(scenes)
    return {"scenes":[s.model_dump() for s in scenes],"requirements":[r.model_dump() for r in reqs]}

@app.post("/api/process")
def process(payload:dict):
    scenes=parser.parse(payload.get("text",""),payload.get("filename","scene.txt")); reqs=engine.extract(scenes); existing=store.all(); specs=[]; reused=[]
    for r in reqs:
        match=AssetMatcher(existing).match(r)
        if match and r.reusable: reused.append({"requirement":r.name,"asset_id":match.id,"filename":match.filename}); continue
        spec=AssetSpec(**r.model_dump(),canonical_name=r.name,prompt="",atlas_group=f"{r.type.value}_{r.tags[0] if r.tags else 'misc'}",generation_count=max(1,r.quantity)); spec.prompt=prompts.generate(spec); specs.append(spec)
    if not specs:return {"scenes":len(scenes),"generated":0,"reused":reused,"assets":[]}
    plan=packer.plan(specs); atlas_path=ATLAS/f"{plan.atlas_id}.png"; provider.generate_atlas('\n'.join(s.prompt for s in specs),plan,atlas_path); atlas=Image.open(atlas_path); cropped=crop_atlas(atlas,plan,ASSETS,matte); created=[]
    for i,(fn,path,img) in enumerate(cropped):
        cell=plan.cells[i]; spec=next(s for s in specs if s.canonical_name==cell.asset_name); aid="asset_"+uuid.uuid4().hex[:12]
        meta=AssetMetadata(id=aid,filename=fn,category=spec.type.value,subcategory=spec.tags[0] if spec.tags else None,tags=sorted(set(spec.tags+[spec.canonical_name])),width=img.width,height=img.height,alpha=True,prompt=spec.prompt,scenes=spec.scenes,atlas_id=plan.atlas_id,source="ai_generated",quality_status="PROCESSED",bbox={"x":cell.x,"y":cell.y,"width":cell.width,"height":cell.height}); store.upsert(meta); created.append(meta.model_dump())
    return {"scenes":len(scenes),"generated":len(created),"reused":reused,"atlas":plan.model_dump(),"assets":created}

@app.get("/api/assets")
def assets(q:str=Query(""),category:str|None=None,tag:str|None=None,scene:str|None=None): return [a.model_dump() for a in store.search(q,category,tag,scene)]

app.mount('/files/assets',StaticFiles(directory=ASSETS),name='assets'); app.mount('/files/atlases',StaticFiles(directory=ATLAS),name='atlases')
