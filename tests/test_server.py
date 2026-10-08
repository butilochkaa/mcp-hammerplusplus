import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import mcp, create_map, add_room, add_brush_box, add_player_spawn, add_light, add_prop

class TestTools(unittest.TestCase):
    def test_tools_registered(self):
        tool_names = [t.name for t in mcp._tool_manager.list_tools()]
        self.assertIn("get_viewport_screenshot", tool_names)
        self.assertIn("get_editor_status", tool_names)
        self.assertIn("create_map", tool_names)
        self.assertIn("add_room", tool_names)
        self.assertEqual(len(tool_names), 16)

    def test_tool_annotations(self):
        for tool in mcp._tool_manager.list_tools():
            self.assertIsNotNone(tool.annotations, f"Tool {tool.name} missing annotations")
            self.assertIsInstance(tool.annotations.readOnlyHint, bool)
            self.assertIsInstance(tool.annotations.destructiveHint, bool)
            self.assertIsInstance(tool.annotations.idempotentHint, bool)
            self.assertIsInstance(tool.annotations.openWorldHint, bool)

    def test_map_and_room_tools(self):
        res_map = create_map("test_unit_map")
        self.assertTrue(res_map["success"])
        res_room = add_room("test_unit_map", 0, 0, 0, 256, 256, 128)
        self.assertTrue(res_room["success"])
        res_box = add_brush_box("test_unit_map", -10, -10, 0, 10, 10, 20)
        self.assertTrue(res_box["success"])
        res_spawn = add_player_spawn("test_unit_map", 0, 0, 16)
        self.assertTrue(res_spawn["success"])
        res_light = add_light("test_unit_map", 0, 0, 100)
        self.assertTrue(res_light["success"])

if __name__ == "__main__":
    unittest.main()
