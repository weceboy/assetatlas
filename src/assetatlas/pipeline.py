from __future__ import annotations
import csv, io, json, math, re
from pathlib import Path
from typing import Protocol
import numpy as np
from PIL import Image
from .models import *

class SceneInputParser:
    def parse(self, data: str, filename: str = "scene.txt") -> list[Scene]:
        ext = Path(filename).suffix.lower()
        if ext == ".json":
            obj = json.loads(data); rows = obj if isinstance(obj, list) else obj.get("scenes", [obj])
            return [self._scene(x, i) for i, x in enumerate(rows, 1)]
        if ext == ".csv":
            return [self._scene(x, i) for i, x in enumerate(csv.DictReader(io.StringIO(data)), 1)]
        return self._text(data)
    def _scene(self, x, i):
        e=x.get("required_elements", x.get("required elements", []))
        if isinstance(e,str): e=[z.strip(" -*") for z in re.split(r"\n|;|,",e) if z.strip()]
        return Scene(scene_id=str(x.get("scene_id",x.get("id",f"SC{i:02d}"))),location=x.get("location"),mood=x.get("mood"),action=x.get("action"),required_elements=e,raw=x)
    def _text(self,text):
        blocks=re.split(r"(?im)(?=^\s*(?:scene|szene)\s*\d+\b)",text); out=[]
        for i,b in enumerate([x for x in blocks if x.strip()],1):
            m=re.search(r"(?im)^\s*(?:scene|szene)\s*([\w-]+)",b); sid=f"SC{i:02d}" if not m else f"SC{m.group(1)}"
            def field(names):
                q=re.search(rf"(?im)^\s*(?:{names})\s*:\s*(.+)$",b); return q.group(1).strip() if q else None
            q=re.search(r"(?ims)(?:required elements|benötigte\s+elemente)\s*:\s*(.*?)(?=^\w[\w ]*:\s*|\Z)",b)
            elems=[re.sub(r"^\s*[-*]\s*","",z).strip() for z in q.group(1).splitlines() if z.strip()] if q else []
            out.append(Scene(scene_id=sid,location=field("Location|Ort"),mood=field("Mood|Stimmung"),action=field("Action|Aktion"),required_elements=elems,raw={"text":b}))
        return out

class RequirementEngine:
    KEYWORDS={"smoke":("fx","smoke"),"fog":("fx","fog"),"dust":("particle","dust"),"spark":("particle","sparks"),"light ray":("light","light_ray"),"glow":("light","glow"),"warning sign":("prop","warning_sign"),"logo":("ui","logo"),"character":("character","character"),"background":("background","background"),"texture":("texture","texture"),"shadow":("fx","shadow")}
    def extract(self,scenes):
        out=[]
        for s in scenes:
            for raw in s.required_elements:
                low=raw.lower(); typ,sub=self._classify(low); name=re.sub(r"[^a-z0-9]+","_",low).strip("_")[:60] or "asset"
                priority=Priority.high if any(x in low for x in ("hero","main","primary")) else Priority.medium
                tags=sorted(set([sub,typ.value,*re.findall(r"[a-z0-9]+",low)]))
                out.append(AssetRequirement(name=name,type=typ,priority=priority,reusable=not any(x in low for x in ("unique","one-off")),tags=tags,scenes=[s.scene_id]))
        return self._dedupe(out)
    def _classify(self,t):
        for k,v in self.KEYWORDS.items():
            if k in t:return AssetType(v[0]),v[1]
        return AssetType.unknown,"misc"
    def _dedupe(self,rs):
        g={}
        for r in rs:
            key=re.sub(r"[^a-z0-9]+","_",re.sub(r"(dense|soft|background|atmospheric)","",r.name.lower())).strip("_")
            if key in g:g[key].scenes=sorted(set(g[key].scenes+r.scenes));g[key].tags=sorted(set(g[key].tags+r.tags))
            else:g[key]=r.model_copy(deep=True)
        return list(g.values())

class AssetMatcher:
    def __init__(self,existing):self.existing=existing
    def match(self,req):
        q=set(req.tags+[req.name]); best=None; score=0
        for a in self.existing:
            s=len(q&set(a.tags+[a.filename,a.subcategory or ""]))
            if s>score:best,score=a,s
        return best if score>=2 else None

class PromptGenerator:
    def generate(self,spec):
        n=max(1,spec.quantity); subject=spec.canonical_name.replace("_"," ")
        return f"Generate {n} isolated cinematic {subject} elements, visually distinct, generous spacing, no overlap, no text, no labels, alpha-friendly edges."

class AtlasPacker:
    def plan(self,specs,width=2048,height=2048,padding=32):
        n=sum(max(1,s.generation_count) for s in specs); cols=max(1,math.ceil(math.sqrt(n))); rows=math.ceil(n/cols)
        cw=(width-(cols+1)*padding)//cols;ch=(height-(rows+1)*padding)//rows;cells=[];i=0
        for s in specs:
            for _ in range(max(1,s.generation_count)):
                r,c=divmod(i,cols);cells.append(AtlasCell(asset_name=s.canonical_name,x=padding+c*(cw+padding),y=padding+r*(ch+padding),width=cw,height=ch));i+=1
        return AtlasPlan(atlas_id=f"atlas_{len(specs)}_{width}x{height}",width=width,height=height,padding=padding,cells=cells)

class MattingEngine:
    def alpha_from_background(self,image,threshold=18):
        rgba=image.convert("RGBA"); a=np.array(rgba);rgb=a[:,:,:3].astype(np.int16)
        corners=np.concatenate([rgb[0:8,0:8].reshape(-1,3),rgb[0:8,-8:].reshape(-1,3),rgb[-8:,0:8].reshape(-1,3),rgb[-8:,-8:].reshape(-1,3)])
        bg=np.median(corners,axis=0);dist=np.linalg.norm(rgb-bg,axis=2);a[:,:,3]=np.clip((dist-threshold)*255/max(1,threshold*2),0,255).astype(np.uint8)
        return Image.fromarray(a,"RGBA")

class MockImageProvider:
    def generate_atlas(self,prompt,plan,output):
        im=Image.new("RGBA",(plan.width,plan.height),(245,245,245,255));from PIL import ImageDraw;d=ImageDraw.Draw(im)
        for i,c in enumerate(plan.cells):d.rounded_rectangle((c.x,c.y,c.x+c.width,c.y+c.height),radius=20,fill=(30+20*(i%8),50+10*(i%10),80+15*(i%7),255));d.text((c.x+20,c.y+20),c.asset_name,fill=(255,255,255,255))
        output.parent.mkdir(parents=True,exist_ok=True);im.save(output,"PNG");return output

def crop_atlas(atlas,plan,out_dir,matte):
    out_dir.mkdir(parents=True,exist_ok=True);results=[]
    for i,c in enumerate(plan.cells,1):
        crop=matte.alpha_from_background(atlas.crop((c.x,c.y,c.x+c.width,c.y+c.height)));fn=f"{re.sub(r'[^a-z0-9]+','_',c.asset_name.lower()).strip('_')}_{i:03d}.png";path=out_dir/fn;crop.save(path,"PNG");results.append((fn,path,crop))
    return results
