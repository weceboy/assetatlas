# AssetAtlas MVP

AssetAtlas turns a scene plan into reusable motion-graphics assets with a scene → requirements → deduplication → atlas → extraction → PNG → library workflow.

## Implemented MVP

- Text, JSON and CSV scene parsing.
- Structured asset requirements with category, priority, reusable flag, tags and scene references.
- Requirement normalization/deduplication across scenes.
- Existing-library matching before generation.
- Atlas planning with deterministic grid packing, padding and configurable resolution.
- Prompt generation isolated behind a provider boundary.
- Swappable image generation providers: deterministic `MockImageProvider`, file adapter, and optional OpenAI adapter.
- Atlas cropper using explicit atlas geometry.
- Baseline background matting producing RGBA PNGs without requiring an external segmentation API.
- SQLite metadata store.
- Tag/category/scene search and a minimal visual browser.
- Asset IDs, prompts, atlas references, source, status, bounding boxes, scene references and variants in the data model.
- Regression tests for parsing, deduplication and atlas geometry.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn assetatlas.main:app --reload
```

Open `http://127.0.0.1:8000`.

The default MVP uses a deterministic mock generator so the complete pipeline is runnable without API credentials. To connect a real model, implement `ImageGenerationProvider` or use the optional provider adapters in `assetatlas.providers`.

## API

`POST /api/analyze`

```json
{"text":"Scene 04\nLocation: Warehouse\nRequired elements:\n- dense smoke\n- sparks","filename":"scene.txt"}
```

`POST /api/process` runs the complete MVP pipeline and returns generated/reused assets plus the atlas plan.

`GET /api/assets?q=smoke&scene=SC04` searches the library.

## Architecture

```text
SceneInputParser
      ↓
RequirementEngine
      ↓
AssetMatcher / Deduplication
      ↓
AssetSpec + PromptGenerator
      ↓
ImageGenerationProvider
      ↓
AtlasPacker
      ↓
Crop / Matting
      ↓
PNG + AssetMetadata
      ↓
SQLite AssetStore
      ↓
Search / Library UI
```

## Important extension points

The MVP deliberately does **not** pretend that generic background-removal is equivalent to production matting for smoke, glow, hair or additive light. `MattingEngine` is therefore a replaceable boundary. A production implementation should add model-backed segmentation/matting, edge decontamination and alpha validation.

Likewise, the current matcher is deterministic tag/lexical matching. A production semantic layer can add CLIP/Sentence-Transformers embeddings while retaining the same `AssetStore` contract.

Planned next steps: PDF/DOCX ingestion, LLM-backed requirement extraction, semantic embeddings, free-form bin packing, model-specific atlas constraints, production matting, review UI, version graphs, and After Effects/Blender/Resolve export adapters.
