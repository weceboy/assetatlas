from __future__ import annotations
import json, sqlite3
from pathlib import Path
from .models import AssetMetadata

class AssetStore:
    def __init__(self,path="data/assetatlas.db"):
        Path(path).parent.mkdir(parents=True,exist_ok=True);self.db=sqlite3.connect(path,check_same_thread=False);self.db.row_factory=sqlite3.Row;self.init()
    def init(self):
        self.db.executescript('''CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY, filename TEXT, category TEXT, subcategory TEXT, tags TEXT, style TEXT, orientation TEXT, width INTEGER, height INTEGER, alpha INTEGER, source TEXT, model TEXT, prompt TEXT, created_at TEXT, version INTEGER, scenes TEXT, quality_status TEXT, variant_of TEXT, bbox TEXT, atlas_id TEXT, embedding TEXT); CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(category);''');self.db.commit()
    def upsert(self,a:AssetMetadata):
        self.db.execute('''INSERT OR REPLACE INTO assets VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (a.id,a.filename,a.category,a.subcategory,json.dumps(a.tags),a.style,a.orientation,a.width,a.height,int(a.alpha),a.source,a.model,a.prompt,a.created_at,a.version,json.dumps(a.scenes),a.quality_status,a.variant_of,json.dumps(a.bbox),a.atlas_id,json.dumps(a.embedding)));self.db.commit()
    def all(self): return [self._row(r) for r in self.db.execute('SELECT * FROM assets ORDER BY created_at DESC')]
    def search(self,q="",category=None,tag=None,scene=None):
        rows=self.all();q=q.lower().strip();out=[]
        for a in rows:
            hay=' '.join([a.filename,a.category,a.subcategory or '',*a.tags]).lower()
            if q and q not in hay:continue
            if category and a.category!=category:continue
            if tag and tag not in a.tags:continue
            if scene and scene not in a.scenes:continue
            out.append(a)
        return out
    def _row(self,r):
        d=dict(r);d['tags']=json.loads(d['tags']);d['scenes']=json.loads(d['scenes']);d['bbox']=json.loads(d['bbox']) if d['bbox'] else None;d['embedding']=json.loads(d['embedding']) if d['embedding'] else None;d['alpha']=bool(d['alpha']);return AssetMetadata(**d)
