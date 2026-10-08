import os
import sys
import json
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import mcp

OUT_DIR = r"C:\Users\chuvak\.gemini\antigravity\mcp\hammerplusplus"
os.makedirs(OUT_DIR, exist_ok=True)

async def dump_schemas():
    tools = await mcp.list_tools()
    for t in tools:
        fname = f"{t.name}.json"
        fpath = os.path.join(OUT_DIR, fname)
        ann = t.annotations.model_dump() if t.annotations else {}
        schema = {
            "name": t.name,
            "description": t.description or "",
            "parameters": t.inputSchema or {"type": "object", "properties": {}},
            "annotations": ann
        }
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
    instructions = """# Hammer++ MCP Server Instructions

Use these tools to interact directly with Hammer++ and Garry's Mod / Source Engine mapping.

## Workflow Best Practices
1. Viewport: Call `get_viewport_screenshot` to inspect the 3D scene or 2D orthographic grids.
2. Asset Browser:
   - `search_models` to locate props (.mdl)
   - `preview_model` to see dimensions and textures before placing
   - `search_materials` and `preview_material` to inspect VTF textures
3. Map Construction:
   - Use `add_room` to build sealed, leak-proof rooms
   - Use `add_brush_box` for custom walls, platforms, and detailing
   - Use `add_prop` with `snap_to_floor=True` to cleanly position models on the floor
   - Use `add_light` to illuminate rooms
4. Compilation & Leak Detection:
   - Run `compile_map` with `fast=True`
   - If leaked, inspect the returned `leak_details` containing the exact coordinates from the .lin file
   - Run `launch_game` to test the map inside Garry's Mod
"""
    with open(os.path.join(OUT_DIR, "instructions.md"), 'w', encoding='utf-8') as f:
        f.write(instructions)

if __name__ == "__main__":
    asyncio.run(dump_schemas())
