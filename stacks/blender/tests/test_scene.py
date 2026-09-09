from pathlib import Path


def test_scene_source_has_edit_seam_and_node_materials():
    scene = Path(__file__).parents[1] / "scene.py"
    content = scene.read_text()
    assert "BRIEF" in content
    assert "result.use_nodes = True" in content
