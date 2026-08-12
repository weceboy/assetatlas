from assetatlas.pipeline import SceneInputParser, RequirementEngine, AtlasPacker

def test_scene_to_requirements_and_dedupe():
    text='''Scene 04\nLocation: Warehouse\nMood: Dark\nRequired elements:\n- dense background smoke\n- sparks\nScene 07\nRequired elements:\n- background fog\n- sparks'''
    scenes=SceneInputParser().parse(text)
    reqs=RequirementEngine().extract(scenes)
    assert len(scenes)==2
    assert any(r.type.value=='fx' for r in reqs)
    assert any('sparks' in r.tags for r in reqs)

def test_atlas_is_deterministic_grid_shape():
    from assetatlas.models import AssetSpec, AssetType
    specs=[AssetSpec(name='smoke',type=AssetType.fx,canonical_name='smoke',prompt='x',atlas_group='fx_smoke',quantity=1,generation_count=4)]
    plan=AtlasPacker().plan(specs,1024,1024,16)
    assert len(plan.cells)==4
    assert all(c.x>=16 and c.y>=16 for c in plan.cells)
