# AssetAtlas Manual Web MVP

Open `index.html` in a modern browser. No backend or build step is required.

## Workflow

1. Paste a scene plan.
2. Generate the Scene Breakdown prompt and run it in an online LLM.
3. Paste the returned JSON into Scene JSON and validate/store it.
4. Use the Prompt Chain to generate normalization, library matching, atlas planning and generation prompts.
5. Generate the atlas manually with an online image model.
6. Import the atlas PNG and the matching atlas JSON.
7. Extract all cells locally as transparent PNG files.
8. Assets are stored in IndexedDB and searchable in the local library.

The app intentionally treats online AI tools as manual providers. The data contracts can later be connected to APIs without changing the local asset model.
