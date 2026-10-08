import os
import math

class VMFEngine:
    def __init__(self, skyname="sky_day01_01"):
        self.skyname = skyname
        self.next_id = 1
        self.solids = []
        self.entities = []
        self.active_camera = {"position": "[-128 -128 128]", "look": "[0 0 64]"}
        
    def _alloc_id(self):
        cur = self.next_id
        self.next_id += 1
        return cur

    def create_solid_box(self, min_pt, max_pt, material="DEV/DEV_MEASUREGENERIC01B", 
                         mat_top=None, mat_bottom=None, mat_sides=None):
        x0, y0, z0 = min_pt
        x1, y1, z1 = max_pt
        
        if x0 > x1: x0, x1 = x1, x0
        if y0 > y1: y0, y1 = y1, y0
        if z0 > z1: z0, z1 = z1, z0
        
        solid_id = self._alloc_id()
        
        m_top = mat_top or material
        m_bottom = mat_bottom or material
        m_side = mat_sides or material
        
        sides = [
            {
                "id": self._alloc_id(),
                "plane": f"({x0} {y1} {z1}) ({x1} {y1} {z1}) ({x1} {y0} {z1})",
                "material": m_top,
                "uaxis": "[1 0 0 0] 0.25",
                "vaxis": "[0 -1 0 0] 0.25"
            },
            {
                "id": self._alloc_id(),
                "plane": f"({x0} {y0} {z0}) ({x1} {y0} {z0}) ({x1} {y1} {z0})",
                "material": m_bottom,
                "uaxis": "[1 0 0 0] 0.25",
                "vaxis": "[0 -1 0 0] 0.25"
            },
            {
                "id": self._alloc_id(),
                "plane": f"({x0} {y1} {z1}) ({x0} {y1} {z0}) ({x1} {y1} {z0})",
                "material": m_side,
                "uaxis": "[1 0 0 0] 0.25",
                "vaxis": "[0 0 -1 0] 0.25"
            },
            {
                "id": self._alloc_id(),
                "plane": f"({x1} {y0} {z0}) ({x0} {y0} {z0}) ({x0} {y0} {z1})",
                "material": m_side,
                "uaxis": "[1 0 0 0] 0.25",
                "vaxis": "[0 0 -1 0] 0.25"
            },
            {
                "id": self._alloc_id(),
                "plane": f"({x1} {y1} {z1}) ({x1} {y1} {z0}) ({x1} {y0} {z0})",
                "material": m_side,
                "uaxis": "[0 1 0 0] 0.25",
                "vaxis": "[0 0 -1 0] 0.25"
            },
            {
                "id": self._alloc_id(),
                "plane": f"({x0} {y0} {z1}) ({x0} {y0} {z0}) ({x0} {y1} {z0})",
                "material": m_side,
                "uaxis": "[0 1 0 0] 0.25",
                "vaxis": "[0 0 -1 0] 0.25"
            }
        ]
        
        return {"id": solid_id, "sides": sides}

    def add_world_brush(self, min_pt, max_pt, material="DEV/DEV_MEASUREGENERIC01B", 
                        mat_top=None, mat_bottom=None, mat_sides=None):
        solid = self.create_solid_box(min_pt, max_pt, material, mat_top, mat_bottom, mat_sides)
        self.solids.append(solid)
        return solid

    def create_room(self, origin, width, length, height, wall_thickness=16,
                    mat_floor="DEV/DEV_MEASUREGENERIC01B",
                    mat_wall="DEV/DEV_MEASUREWALL01A",
                    mat_ceiling="DEV/DEV_MEASUREGENERIC01B"):
        ox, oy, oz = origin
        hw = width / 2
        hl = length / 2
        t = wall_thickness
        
        self.add_world_brush(
            (ox - hw - t, oy - hl - t, oz - t),
            (ox + hw + t, oy + hl + t, oz),
            mat_top=mat_floor, mat_sides=mat_wall, mat_bottom=mat_wall
        )
        
        self.add_world_brush(
            (ox - hw - t, oy - hl - t, oz + height),
            (ox + hw + t, oy + hl + t, oz + height + t),
            mat_bottom=mat_ceiling, mat_sides=mat_wall, mat_top=mat_wall
        )
        
        self.add_world_brush(
            (ox - hw - t, oy - hl, oz),
            (ox - hw, oy + hl, oz + height),
            material=mat_wall
        )
        
        self.add_world_brush(
            (ox + hw, oy - hl, oz),
            (ox + hw + t, oy + hl, oz + height),
            material=mat_wall
        )
        
        self.add_world_brush(
            (ox - hw - t, oy - hl - t, oz),
            (ox + hw + t, oy - hl, oz + height),
            material=mat_wall
        )
        
        self.add_world_brush(
            (ox - hw - t, oy + hl, oz),
            (ox + hw + t, oy + hl + t, oz + height),
            material=mat_wall
        )
        
        return {
            "bounds_inner": ((ox - hw, oy - hl, oz), (ox + hw, oy + hl, oz + height)),
            "floor_z": oz,
            "center": (ox, oy, oz + height / 2)
        }

    def add_player_spawn(self, origin, angles="0 0 0"):
        ent_id = self._alloc_id()
        ent = {
            "id": ent_id,
            "classname": "info_player_start",
            "origin": f"{origin[0]} {origin[1]} {origin[2]}",
            "angles": angles
        }
        self.entities.append(ent)
        return ent

    def add_light(self, origin, color="255 255 255 200", brightness=None):
        if brightness is not None and len(color.split()) == 3:
            color = f"{color} {brightness}"
        ent_id = self._alloc_id()
        ent = {
            "id": ent_id,
            "classname": "light",
            "origin": f"{origin[0]} {origin[1]} {origin[2]}",
            "_light": color,
            "_distance": "0",
            "_zero_percent_distance": "0"
        }
        self.entities.append(ent)
        return ent

    def add_light_environment(self, origin, angles="0 45 0", pitch="-45",
                              color="255 255 255 200", ambient="128 160 192 100"):
        ent_id = self._alloc_id()
        ent = {
            "id": ent_id,
            "classname": "light_environment",
            "origin": f"{origin[0]} {origin[1]} {origin[2]}",
            "angles": angles,
            "pitch": str(pitch),
            "_light": color,
            "_ambient": ambient,
            "SunSpreadAngle": "0"
        }
        self.entities.append(ent)
        return ent

    def add_prop(self, classname, model, origin, angles="0 0 0", skin=0, targetname=""):
        ent_id = self._alloc_id()
        ent = {
            "id": ent_id,
            "classname": classname,
            "model": model,
            "origin": f"{origin[0]} {origin[1]} {origin[2]}",
            "angles": angles,
            "skin": str(skin),
            "disableshadows": "0",
            "fademindist": "-1",
            "fademaxdist": "0"
        }
        if targetname:
            ent["targetname"] = targetname
        self.entities.append(ent)
        return ent

    def add_trigger(self, min_pt, max_pt, classname="trigger_multiple", targetname="", 
                    outputs=None):
        ent_id = self._alloc_id()
        solid = self.create_solid_box(min_pt, max_pt, material="TOOLS/TOOLSTRIGGER")
        ent = {
            "id": ent_id,
            "classname": classname,
            "spawnflags": "1",
            "wait": "1",
            "solids": [solid]
        }
        if targetname:
            ent["targetname"] = targetname
        if outputs:
            ent["connections"] = outputs
        self.entities.append(ent)
        return ent

    def to_vmf_string(self):
        lines = []
        lines.append('versioninfo\n{\n\t"editorversion" "400"\n\t"editorbuild" "8872"\n\t"mapversion" "1"\n\t"formatversion" "100"\n\t"prefab" "0"\n}')
        lines.append('visgroups\n{\n}')
        lines.append('viewsettings\n{\n\t"bShowLogicGrid" "0"\n\t"bShowGrid" "1"\n\t"bShow3DGrid" "0"\n\t"gridspacing" "64"\n\t"bShowPrickles" "0"\n}')
        
        lines.append('world\n{')
        lines.append(f'\t"id" "1"\n\t"mapversion" "1"\n\t"classname" "worldspawn"\n\t"detailmaterial" "detail/detailsprites"\n\t"detailvbsp" "detail.vbsp"\n\t"maxpropscreenwidth" "-1"\n\t"skyname" "{self.skyname}"')
        
        for s in self.solids:
            lines.append('\tsolid\n\t{')
            lines.append(f'\t\t"id" "{s["id"]}"')
            for side in s["sides"]:
                lines.append('\t\tside\n\t\t{')
                lines.append(f'\t\t\t"id" "{side["id"]}"')
                lines.append(f'\t\t\t"plane" "{side["plane"]}"')
                lines.append(f'\t\t\t"material" "{side["material"]}"')
                lines.append(f'\t\t\t"uaxis" "{side["uaxis"]}"')
                lines.append(f'\t\t\t"vaxis" "{side["vaxis"]}"')
                lines.append('\t\t\t"rotation" "0"\n\t\t\t"lightmapscale" "16"\n\t\t\t"smoothing_groups" "0"')
                lines.append('\t\t}')
            lines.append('\t}')
        lines.append('}')
        
        for e in self.entities:
            lines.append('entity\n{')
            for k, v in e.items():
                if k in ("solids", "connections"):
                    continue
                lines.append(f'\t"{k}" "{v}"')
            if "connections" in e:
                lines.append('\tconnections\n\t{')
                for conn in e["connections"]:
                    lines.append(f'\t\t"{conn[0]}" "{conn[1]},{conn[2]},{conn[3]},{conn[4]},{conn[5]}"')
                lines.append('\t}')
            if "solids" in e:
                for s in e["solids"]:
                    lines.append('\tsolid\n\t{')
                    lines.append(f'\t\t"id" "{s["id"]}"')
                    for side in s["sides"]:
                        lines.append('\t\tside\n\t\t{')
                        lines.append(f'\t\t\t"id" "{side["id"]}"')
                        lines.append(f'\t\t\t"plane" "{side["plane"]}"')
                        lines.append(f'\t\t\t"material" "{side["material"]}"')
                        lines.append(f'\t\t\t"uaxis" "{side["uaxis"]}"')
                        lines.append(f'\t\t\t"vaxis" "{side["vaxis"]}"')
                        lines.append('\t\t\t"rotation" "0"\n\t\t\t"lightmapscale" "16"\n\t\t\t"smoothing_groups" "0"')
                        lines.append('\t\t}')
                    lines.append('\t}')
            lines.append('}')
            
        lines.append(f'cameras\n{{\n\t"activecamera" "-1"\n\tcamera\n\t{{\n\t\t"position" "{self.active_camera["position"]}"\n\t\t"look" "{self.active_camera["look"]}"\n\t}}\n}}')
        lines.append('cordons\n{\n\t"active" "0"\n}')
        return '\n'.join(lines)

    def save(self, filepath):
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_vmf_string())
        return filepath
