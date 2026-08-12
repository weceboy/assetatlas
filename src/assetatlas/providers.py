from __future__ import annotations
from pathlib import Path
from typing import Protocol
from .models import AtlasPlan

class ImageGenerationProvider(Protocol):
    name: str
    def generate_atlas(self,prompt: str,plan: AtlasPlan,output: Path) -> Path: ...

class FileImageProvider:
    """Adapter for externally generated atlas files; useful for Midjourney, ComfyUI, etc."""
    name="file"
    def __init__(self,source: str): self.source=Path(source)
    def generate_atlas(self,prompt,plan,output):
        if not self.source.exists(): raise FileNotFoundError(self.source)
        output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(self.source.read_bytes());return output

class OpenAIImageProvider:
    """Optional provider. The API key is supplied by the host application, never persisted in metadata."""
    name="openai"
    def __init__(self,client,model="gpt-image-1"): self.client=client;self.model=model
    def generate_atlas(self,prompt,plan,output):
        from base64 import b64decode
        result=self.client.images.generate(model=self.model,prompt=prompt,size="1024x1024")
        data=result.data[0].b64_json
        output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(b64decode(data));return output
