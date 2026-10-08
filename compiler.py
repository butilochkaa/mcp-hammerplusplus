import os
import subprocess
from paths import resolve_gmod_root

class MapCompiler:
    def __init__(self, gmod_root=None):
        self.gmod_root = gmod_root or resolve_gmod_root()
        self.bin_dir = os.path.join(self.gmod_root, "bin", "win64")
        if not os.path.exists(self.bin_dir):
            self.bin_dir = os.path.join(self.gmod_root, "bin")
            
        self.garrysmod_dir = os.path.join(self.gmod_root, "garrysmod")
        self.maps_dir = os.path.join(self.garrysmod_dir, "maps")
        
        self.vbsp = os.path.join(self.bin_dir, "vbsp.exe")
        self.vvis = os.path.join(self.bin_dir, "vvis.exe")
        self.vrad = os.path.join(self.bin_dir, "vrad.exe")
        self.gmod = os.path.join(self.gmod_root, "gmod.exe")
        if not os.path.exists(self.gmod):
            self.gmod = os.path.join(self.gmod_root, "hl2.exe")

    def parse_lin_file(self, lin_path):
        if not os.path.exists(lin_path):
            return None
        points = []
        with open(lin_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 3:
                    try:
                        points.append([float(parts[0]), float(parts[1]), float(parts[2])])
                    except ValueError:
                        pass
        return points

    def compile(self, vmf_path, fast=True, run_vis=True, run_rad=True):
        if not os.path.isabs(vmf_path):
            vmf_path = os.path.join(self.maps_dir, vmf_path)
        if not vmf_path.endswith('.vmf'):
            vmf_path += '.vmf'
            
        if not os.path.exists(vmf_path):
            return {"success": False, "error": f"VMF file not found: {vmf_path}"}

        map_base = os.path.splitext(vmf_path)[0]
        map_name = os.path.basename(map_base)
        bsp_path = f"{map_base}.bsp"
        lin_path = f"{map_base}.lin"

        if os.path.exists(lin_path):
            try: os.remove(lin_path)
            except OSError: pass

        stages = []
        
        vbsp_cmd = [self.vbsp, "-game", self.garrysmod_dir, vmf_path]
        res_vbsp = subprocess.run(vbsp_cmd, capture_output=True, text=True)
        vbsp_ok = (res_vbsp.returncode == 0)
        
        leaked = False
        leak_info = None
        if "**** LEAKED ****" in res_vbsp.stdout or "leaked!" in res_vbsp.stdout or os.path.exists(lin_path):
            leaked = True
            pts = self.parse_lin_file(lin_path)
            leak_info = {
                "leaked": True,
                "lin_file": lin_path,
                "trail_points": pts[:10] if pts else [],
                "origin_point": pts[0] if pts else None
            }

        stages.append({
            "stage": "VBSP",
            "success": vbsp_ok and not leaked,
            "output": res_vbsp.stdout[-1500:] if res_vbsp.stdout else res_vbsp.stderr[-500:]
        })

        if not vbsp_ok or leaked:
            return {
                "success": False,
                "map": map_name,
                "bsp": bsp_path,
                "leaked": leaked,
                "leak_details": leak_info,
                "stages": stages
            }

        if run_vis:
            vvis_cmd = [self.vvis]
            if fast:
                vvis_cmd.append("-fast")
            vvis_cmd.extend(["-game", self.garrysmod_dir, bsp_path])
            res_vvis = subprocess.run(vvis_cmd, capture_output=True, text=True)
            stages.append({
                "stage": "VVIS",
                "success": (res_vvis.returncode == 0),
                "output": res_vvis.stdout[-1000:]
            })

        if run_rad:
            vrad_cmd = [self.vrad]
            if fast:
                vrad_cmd.append("-fast")
            vrad_cmd.extend(["-game", self.garrysmod_dir, bsp_path])
            res_vrad = subprocess.run(vrad_cmd, capture_output=True, text=True)
            stages.append({
                "stage": "VRAD",
                "success": (res_vrad.returncode == 0),
                "output": res_vrad.stdout[-1000:]
            })

        all_ok = all(s["success"] for s in stages)
        return {
            "success": all_ok,
            "map": map_name,
            "bsp_path": bsp_path,
            "bsp_size_bytes": os.path.getsize(bsp_path) if os.path.exists(bsp_path) else 0,
            "stages": stages
        }

    def launch_game(self, map_name):
        if map_name.endswith('.vmf') or map_name.endswith('.bsp'):
            map_name = os.path.splitext(os.path.basename(map_name))[0]
        cmd = [self.gmod, "-novid", "-windowed", "+map", map_name]
        p = subprocess.Popen(cmd, cwd=self.gmod_root)
        return {"launched": True, "pid": p.pid, "map": map_name}
