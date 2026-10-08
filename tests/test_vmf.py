import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vmf_engine import VMFEngine
from paths import resolve_gmod_root

class TestVMFEngine(unittest.TestCase):
    def test_create_solid_box(self):
        engine = VMFEngine()
        solid = engine.create_solid_box((-64, -64, 0), (64, 64, 128))
        self.assertEqual(len(solid["sides"]), 6)
        self.assertIn("DEV/DEV_MEASUREGENERIC01B", solid["sides"][0]["material"])

    def test_create_room(self):
        engine = VMFEngine()
        room = engine.create_room((0, 0, 0), 256, 256, 128)
        self.assertEqual(room["floor_z"], 0)
        self.assertEqual(len(engine.solids), 6)

    def test_add_entities(self):
        engine = VMFEngine()
        p = engine.add_player_spawn((0, 0, 16))
        l = engine.add_light((0, 0, 100))
        pr = engine.add_prop("prop_physics", "models/props_junk/wood_crate001a.mdl", (10, 10, 0))
        self.assertEqual(len(engine.entities), 3)

    def test_vmf_export(self):
        engine = VMFEngine()
        engine.create_room((0, 0, 0), 128, 128, 64)
        vmf = engine.to_vmf_string()
        self.assertIn("versioninfo", vmf)
        self.assertIn("worldspawn", vmf)

class TestPaths(unittest.TestCase):
    def test_resolve_root(self):
        root = resolve_gmod_root()
        self.assertTrue(isinstance(root, str))
        self.assertTrue(len(root) > 0)

if __name__ == "__main__":
    unittest.main()
