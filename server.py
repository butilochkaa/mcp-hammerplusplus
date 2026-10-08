import os
import sys
import io
import json
from mcp.server.fastmcp import FastMCP, Image
from mcp.types import ToolAnnotations
from PIL import Image as PILImage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from paths import resolve_gmod_root
from hammer_bridge import find_hammer_window, capture_viewport, focus_hammer, send_hotkey
from asset_browser import AssetBrowser
from vmf_engine import VMFEngine
from compiler import MapCompiler

GMOD_ROOT = resolve_gmod_root()
MAPS_DIR = os.path.join(GMOD_ROOT, "garrysmod", "maps")

mcp = FastMCP("hammerplusplus")
browser = AssetBrowser(GMOD_ROOT)
compiler = MapCompiler(GMOD_ROOT)

active_maps = {}

RO_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
)

MUT_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False
)

IDEMP_MUT_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False
)

GAME_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True
)

def get_or_create_map(map_name, skyname="sky_day01_01"):
    if not map_name.endswith('.vmf'):
        map_name += '.vmf'
    if map_name not in active_maps:
        engine = VMFEngine(skyname=skyname)
        active_maps[map_name] = engine
    return active_maps[map_name]

def save_and_reload(map_name):
    if not map_name.endswith('.vmf'):
        map_name += '.vmf'
    engine = active_maps.get(map_name)
    if not engine:
        return None
    full_path = os.path.join(MAPS_DIR, map_name)
    engine.save(full_path)
    try:
        send_hotkey('ctrl+r')
    except Exception:
        pass
    return full_path

@mcp.tool(annotations=RO_ANNOTATIONS)
def get_viewport_screenshot(view_type: str = "full", max_size: int = 1280) -> Image:
    """
    Capture a screenshot of Hammer++ to see the current map view, geometry, and layout.
    """
    img = capture_viewport(view_type=view_type, max_size=max_size)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Image(data=buf.getvalue(), format="png")

@mcp.tool(annotations=RO_ANNOTATIONS)
def get_editor_status() -> dict:
    """
    Check if Hammer++ is running, get window handle, title, dimensions, and active map.
    """
    win = find_hammer_window()
    if not win:
        return {"running": False, "message": "Hammer++ is not running."}
    return {
        "running": True,
        "hwnd": win["hwnd"],
        "title": win["title"],
        "window_size": f"{win['width']}x{win['height']}",
        "class": win["class"]
    }

@mcp.tool(annotations=MUT_ANNOTATIONS)
def send_hammer_command(action: str) -> dict:
    """
    Send hotkeys or commands to the running Hammer++ editor (save, reload, compile, focus).
    """
    if action == "focus":
        ok = focus_hammer()
        return {"success": ok, "action": "focus"}
    elif action == "save":
        ok = send_hotkey("ctrl+s")
        return {"success": ok, "action": "save"}
    elif action == "reload":
        ok = send_hotkey("ctrl+r")
        return {"success": ok, "action": "reload"}
    elif action == "compile":
        ok = send_hotkey("f9")
        return {"success": ok, "action": "compile"}
    else:
        return {"success": False, "error": f"Unknown action: {action}"}

@mcp.tool(annotations=RO_ANNOTATIONS)
def search_models(query: str = "", limit: int = 30) -> list:
    """
    Search 3D models (.mdl) in Garry's Mod VPKs and addon directories.
    """
    return browser.search_models(query=query, limit=limit)

@mcp.tool(annotations=RO_ANNOTATIONS)
def get_model_info(model_path: str) -> dict:
    """
    Inspect detailed properties of a Source model (.mdl).
    """
    return browser.get_model_info(model_path)

@mcp.tool(annotations=RO_ANNOTATIONS)
def preview_model(model_path: str) -> Image:
    """
    Generate an isometric 3D schematic preview of the model with bounding box dimensions.
    """
    img = browser.preview_model(model_path)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Image(data=buf.getvalue(), format="png")

@mcp.tool(annotations=RO_ANNOTATIONS)
def search_materials(query: str = "", limit: int = 30) -> list:
    """
    Search materials (.vmt) in Garry's Mod VPKs and addon directories.
    """
    browser.index_assets()
    q = query.lower()
    results = []
    for k in browser.vpk_entries:
        if k.endswith(".vmt") and (not q or q in k):
            results.append(k)
            if len(results) >= limit:
                break
    return results

@mcp.tool(annotations=RO_ANNOTATIONS)
def preview_material(material_path: str) -> Image:
    """
    Decode and preview a Source material / VTF texture as a PNG image.
    """
    img = browser.preview_material(material_path)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Image(data=buf.getvalue(), format="png")

@mcp.tool(annotations=IDEMP_MUT_ANNOTATIONS)
def create_map(map_name: str, skyname: str = "sky_day01_01") -> dict:
    """
    Create a new map workspace.
    """
    if not map_name.endswith('.vmf'):
        map_name += '.vmf'
    engine = VMFEngine(skyname=skyname)
    active_maps[map_name] = engine
    full_path = os.path.join(MAPS_DIR, map_name)
    engine.save(full_path)
    return {
        "success": True,
        "map_name": map_name,
        "vmf_path": full_path,
        "skyname": skyname
    }

@mcp.tool(annotations=MUT_ANNOTATIONS)
def add_room(map_name: str, 
             center_x: float = 0.0, center_y: float = 0.0, floor_z: float = 0.0,
             width: float = 512.0, length: float = 512.0, height: float = 256.0,
             wall_thickness: float = 16.0,
             floor_material: str = "DEV/DEV_MEASUREGENERIC01B",
             wall_material: str = "DEV/DEV_MEASUREWALL01A",
             ceiling_material: str = "DEV/DEV_MEASUREGENERIC01B") -> dict:
    """
    Build a sealed, leak-proof room with floor, ceiling, and 4 exterior walls.
    """
    engine = get_or_create_map(map_name)
    room = engine.create_room(
        (center_x, center_y, floor_z),
        width=width, length=length, height=height,
        wall_thickness=wall_thickness,
        mat_floor=floor_material,
        mat_wall=wall_material,
        mat_ceiling=ceiling_material
    )
    vmf_path = save_and_reload(map_name)
    return {
        "success": True,
        "room_center": room["center"],
        "bounds_inner": room["bounds_inner"],
        "floor_z": room["floor_z"],
        "vmf_path": vmf_path
    }

@mcp.tool(annotations=MUT_ANNOTATIONS)
def add_brush_box(map_name: str,
                  min_x: float, min_y: float, min_z: float,
                  max_x: float, max_y: float, max_z: float,
                  material: str = "DEV/DEV_MEASUREGENERIC01B") -> dict:
    """
    Add a solid brush box to the map.
    """
    engine = get_or_create_map(map_name)
    solid = engine.add_world_brush((min_x, min_y, min_z), (max_x, max_y, max_z), material=material)
    vmf_path = save_and_reload(map_name)
    return {
        "success": True,
        "solid_id": solid["id"],
        "bounds": [(min_x, min_y, min_z), (max_x, max_y, max_z)],
        "material": material,
        "vmf_path": vmf_path
    }

@mcp.tool(annotations=MUT_ANNOTATIONS)
def add_player_spawn(map_name: str, x: float = 0.0, y: float = 0.0, z: float = 16.0, angles: str = "0 0 0") -> dict:
    """
    Place an info_player_start entity in the map.
    """
    engine = get_or_create_map(map_name)
    ent = engine.add_player_spawn((x, y, z), angles=angles)
    vmf_path = save_and_reload(map_name)
    return {"success": True, "id": ent["id"], "origin": (x, y, z), "angles": angles, "vmf_path": vmf_path}

@mcp.tool(annotations=MUT_ANNOTATIONS)
def add_light(map_name: str, x: float, y: float, z: float, color: str = "255 255 255 200") -> dict:
    """
    Add a point light source to illuminate the scene.
    """
    engine = get_or_create_map(map_name)
    ent = engine.add_light((x, y, z), color=color)
    vmf_path = save_and_reload(map_name)
    return {"success": True, "id": ent["id"], "origin": (x, y, z), "color": color, "vmf_path": vmf_path}

@mcp.tool(annotations=MUT_ANNOTATIONS)
def add_prop(map_name: str, model: str, x: float, y: float, z: float,
             prop_type: str = "prop_physics", angles: str = "0 0 0",
             snap_to_floor: bool = True, skin: int = 0) -> dict:
    """
    Place a model entity with automatic floor snap.
    """
    engine = get_or_create_map(map_name)
    final_z = z
    if snap_to_floor:
        info = browser.get_model_info(model)
        if "bounds_min" in info:
            b_min_z = info["bounds_min"][2]
            final_z = z - b_min_z
            
    ent = engine.add_prop(prop_type, model, (x, y, final_z), angles=angles, skin=skin)
    vmf_path = save_and_reload(map_name)
    return {
        "success": True,
        "id": ent["id"],
        "classname": prop_type,
        "model": model,
        "origin": (x, y, final_z),
        "angles": angles,
        "vmf_path": vmf_path
    }

@mcp.tool(annotations=IDEMP_MUT_ANNOTATIONS)
def compile_map(map_name: str, fast: bool = True, run_vis: bool = True, run_rad: bool = True) -> dict:
    """
    Compile the map with VBSP, VVIS, and VRAD.
    """
    if not map_name.endswith('.vmf'):
        map_name += '.vmf'
    vmf_path = os.path.join(MAPS_DIR, map_name)
    return compiler.compile(vmf_path, fast=fast, run_vis=run_vis, run_rad=run_rad)

@mcp.tool(annotations=GAME_ANNOTATIONS)
def launch_game(map_name: str) -> dict:
    """
    Launch Garry's Mod with the compiled map (+map <map_name>).
    """
    return compiler.launch_game(map_name)

if __name__ == "__main__":
    mcp.run()
