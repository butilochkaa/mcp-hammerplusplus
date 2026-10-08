import os
import struct
import io
import re
from PIL import Image, ImageDraw
from paths import resolve_gmod_root

class AssetBrowser:
    def __init__(self, gmod_root=None):
        self.gmod_root = gmod_root or resolve_gmod_root()
        self.garrysmod_dir = os.path.join(self.gmod_root, "garrysmod")
        self.vpk_entries = {}
        self.loose_models = []
        self.loose_materials = []
        self._indexed = False
        
    def index_assets(self):
        if self._indexed:
            return
            
        vpks = []
        if os.path.exists(self.garrysmod_dir):
            for f in os.listdir(self.garrysmod_dir):
                if f.endswith("_dir.vpk"):
                    vpks.append(os.path.join(self.garrysmod_dir, f))
                    
        addons_dir = os.path.join(self.garrysmod_dir, "addons")
        if os.path.exists(addons_dir):
            for root, dirs, files in os.walk(addons_dir):
                for f in files:
                    if f.endswith(".vpk"):
                        vpks.append(os.path.join(root, f))
                        
        for vpk in vpks:
            try:
                entries = self._parse_vpk(vpk)
                for e in entries:
                    norm = e["path"].lower().replace("\\", "/")
                    if norm not in self.vpk_entries:
                        self.vpk_entries[norm] = (vpk, e)
            except Exception:
                pass
                
        for sub, target_list in [("models", self.loose_models), ("materials", self.loose_materials)]:
            p = os.path.join(self.garrysmod_dir, sub)
            if os.path.exists(p):
                for root, dirs, files in os.walk(p):
                    for f in files:
                        rel = os.path.relpath(os.path.join(root, f), self.garrysmod_dir).replace("\\", "/")
                        target_list.append(rel)
                        
        self._indexed = True

    def _parse_vpk(self, vpk_path):
        entries = []
        with open(vpk_path, 'rb') as f:
            sig, ver, tree_sz = struct.unpack('<III', f.read(12))
            if sig != 0x55aa1234:
                return []
            if ver == 2:
                f.seek(16, 1)
                
            tree_bytes = f.read(tree_sz)
            header_data_offset = f.tell()
            idx = 0
            
            def read_str():
                nonlocal idx
                end = tree_bytes.find(b'\x00', idx)
                if end == -1: return ""
                s = tree_bytes[idx:end].decode('latin1', errors='ignore')
                idx = end + 1
                return s

            while True:
                ext = read_str()
                if not ext: break
                while True:
                    folder = read_str()
                    if not folder: break
                    while True:
                        name = read_str()
                        if not name: break
                        crc, preload_bytes, arch_idx, offset, length, term = struct.unpack('<IHHIIH', tree_bytes[idx:idx+18])
                        idx += 18
                        preload_data = b""
                        if preload_bytes > 0:
                            preload_data = tree_bytes[idx:idx+preload_bytes]
                            idx += preload_bytes
                        full_path = f"{folder}/{name}.{ext}" if folder != " " else f"{name}.{ext}"
                        entries.append({
                            "path": full_path,
                            "ext": ext,
                            "archive": arch_idx,
                            "offset": offset,
                            "length": length,
                            "preload_data": preload_data,
                            "vpk_path": vpk_path,
                            "header_data_offset": header_data_offset
                        })
        return entries

    def read_file(self, rel_path):
        self.index_assets()
        norm = rel_path.lower().replace("\\", "/")
        
        disk_path = os.path.join(self.garrysmod_dir, rel_path)
        if os.path.exists(disk_path):
            with open(disk_path, 'rb') as f:
                return f.read()
                
        if norm in self.vpk_entries:
            vpk_path, entry = self.vpk_entries[norm]
            data = entry.get("preload_data", b"")
            length = entry["length"]
            if length > 0:
                arch_idx = entry["archive"]
                offset = entry["offset"]
                if arch_idx == 0x7FFF:
                    with open(vpk_path, 'rb') as f:
                        f.seek(entry["header_data_offset"] + offset)
                        data += f.read(length)
                else:
                    base = vpk_path
                    if base.endswith('_dir.vpk'):
                        base = base[:-8]
                    arch_path = f"{base}_{arch_idx:03d}.vpk"
                    if os.path.exists(arch_path):
                        with open(arch_path, 'rb') as f:
                            f.seek(offset)
                            data += f.read(length)
            return data
            
        return None

    def search_models(self, query="", limit=50):
        self.index_assets()
        q = query.lower()
        results = []
        
        for k in self.vpk_entries:
            if k.endswith(".mdl") and (not q or q in k):
                results.append(k)
                if len(results) >= limit:
                    break
                    
        if len(results) < limit:
            for m in self.loose_models:
                if m.endswith(".mdl") and (not q or q in m.lower()) and m.lower() not in results:
                    results.append(m)
                    if len(results) >= limit:
                        break
        return results

    def get_model_info(self, model_path):
        data = self.read_file(model_path)
        if not data or len(data) < 148:
            return {"error": f"Model file not found: {model_path}"}
            
        idst, ver, checksum = struct.unpack('<III', data[:12])
        if idst != 0x54534449:
            return {"error": "Invalid MDL signature"}
            
        name = data[12:76].split(b'\x00')[0].decode('latin1', errors='ignore')
        bb_min = struct.unpack('<fff', data[104:116])
        bb_max = struct.unpack('<fff', data[116:128])
        flags = struct.unpack('<I', data[144:148])[0]
        
        size = [bb_max[i] - bb_min[i] for i in range(3)]
        
        tex_names = []
        cd_names = []
        skin_count = 1
        if len(data) >= 232:
            tex_count, tex_offset = struct.unpack('<II', data[204:212])
            cd_count, cd_offset = struct.unpack('<II', data[212:220])
            skin_count, skin_fam, _ = struct.unpack('<III', data[220:232])
            
            for i in range(min(tex_count, 32)):
                pos = tex_offset + i * 64
                if pos + 4 <= len(data):
                    rel = struct.unpack('<i', data[pos:pos+4])[0]
                    t_pos = pos + rel
                    if t_pos < len(data):
                        t_name = data[t_pos:].split(b'\x00')[0].decode('latin1', errors='ignore')
                        tex_names.append(t_name)
                        
            for i in range(min(cd_count, 16)):
                pos = cd_offset + i * 4
                if pos + 4 <= len(data):
                    rel = struct.unpack('<i', data[pos:pos+4])[0]
                    if rel < len(data):
                        s = data[rel:].split(b'\x00')[0].decode('latin1', errors='ignore')
                        cd_names.append(s)

        return {
            "path": model_path,
            "version": ver,
            "bounds_min": [round(x, 1) for x in bb_min],
            "bounds_max": [round(x, 1) for x in bb_max],
            "size": [round(abs(x), 1) for x in size],
            "textures": tex_names,
            "texture_dirs": cd_names,
            "skins": skin_count
        }

    def decode_dxt1(self, data, width, height):
        img = Image.new('RGBA', (width, height))
        pixels = img.load()
        offset = 0
        for by in range(0, height, 4):
            for bx in range(0, width, 4):
                if offset + 8 > len(data): break
                c0, c1, lookup = struct.unpack('<HHI', data[offset:offset+8])
                offset += 8
                
                r0 = ((c0 >> 11) & 0x1F) * 255 // 31
                g0 = ((c0 >> 5) & 0x3F) * 255 // 63
                b0 = (c0 & 0x1F) * 255 // 31
                
                r1 = ((c1 >> 11) & 0x1F) * 255 // 31
                g1 = ((c1 >> 5) & 0x3F) * 255 // 63
                b1 = (c1 & 0x1F) * 255 // 31
                
                colors = [
                    (r0, g0, b0, 255),
                    (r1, g1, b1, 255),
                    ((2*r0 + r1)//3, (2*g0 + g1)//3, (2*b0 + b1)//3, 255) if c0 > c1 else ((r0 + r1)//2, (g0 + g1)//2, (b0 + b1)//2, 255),
                    ((r0 + 2*r1)//3, (g0 + 2*g1)//3, (b0 + 2*b1)//3, 255) if c0 > c1 else (0, 0, 0, 0)
                ]
                for py in range(4):
                    for px in range(4):
                        if bx + px < width and by + py < height:
                            shift = (py * 4 + px) * 2
                            pixels[bx + px, by + py] = colors[(lookup >> shift) & 0x03]
        return img

    def preview_material(self, mat_path):
        self.index_assets()
        norm = mat_path.lower().replace("\\", "/")
        if not norm.startswith("materials/"):
            norm = "materials/" + norm
        if not norm.endswith(".vmt") and not norm.endswith(".vtf"):
            norm += ".vmt"
            
        vtf_path = norm
        if norm.endswith(".vmt"):
            vmt_data = self.read_file(norm)
            if not vmt_data:
                raise FileNotFoundError(f"Material not found: {mat_path}")
            text = vmt_data.decode('utf-8', errors='ignore')
            m = re.search(r'\$basetexture["\s]+([^"\r\n\t]+)', text, re.IGNORECASE)
            if m:
                tex_name = m.group(1).strip().replace("\\", "/")
                vtf_path = f"materials/{tex_name}.vtf"
            else:
                vtf_path = norm[:-4] + ".vtf"
                
        vtf_data = self.read_file(vtf_path)
        if not vtf_data or len(vtf_data) < 64:
            raise FileNotFoundError(f"VTF texture not found: {vtf_path}")
            
        hdr_sz, w, h = struct.unpack('<IHH', vtf_data[12:20])
        fmt = struct.unpack('<I', vtf_data[52:56])[0]
        low_fmt, low_w, low_h = struct.unpack('<IBB', vtf_data[57:63])
        
        if low_w > 0 and low_h > 0 and low_fmt == 13:
            thumb_sz = max(1, low_w // 4) * max(1, low_h // 4) * 8
            thumb_data = vtf_data[hdr_sz:hdr_sz + thumb_sz]
            img = self.decode_dxt1(thumb_data, low_w, low_h)
            return img.resize((256, 256), Image.Resampling.NEAREST)
            
        placeholder = Image.new('RGB', (256, 256), color=(60, 60, 60))
        draw = ImageDraw.Draw(placeholder)
        draw.text((10, 10), f"VTF: {w}x{h}\nFormat: {fmt}\n{os.path.basename(vtf_path)}", fill=(220, 220, 220))
        return placeholder

    def preview_model(self, model_path):
        info = self.get_model_info(model_path)
        if "error" in info:
            raise RuntimeError(info["error"])
            
        w, h = 512, 384
        img = Image.new('RGB', (w, h), color=(30, 32, 36))
        draw = ImageDraw.Draw(img)
        
        draw.rectangle([(0, 0), (w, 36)], fill=(20, 22, 25))
        draw.text((12, 10), f"MODEL: {os.path.basename(model_path)}", fill=(255, 200, 80))
        
        sz = info["size"]
        b_min = info["bounds_min"]
        b_max = info["bounds_max"]
        
        specs = [
            f"Dimensions (WxLxH): {sz[0]} x {sz[1]} x {sz[2]} units",
            f"Bounds Min: {b_min}",
            f"Bounds Max: {b_max}",
            f"Skins: {info['skins']}",
            f"Textures: {', '.join(info['textures'][:3]) or 'none'}"
        ]
        
        for i, s in enumerate(specs):
            draw.text((16, 50 + i * 20), s, fill=(200, 205, 215))
            
        center_x, center_y = 160, 260
        scale = min(120 / max(sz[0], 1), 120 / max(sz[1], 1), 120 / max(sz[2], 1), 1.5)
        
        dx = sz[0] * scale * 0.7
        dy = sz[1] * scale * 0.4
        dz = sz[2] * scale * 0.8
        
        p0 = (center_x - dx, center_y + dy/2)
        p1 = (center_x, center_y + dy)
        p2 = (center_x + dx, center_y + dy/2)
        p3 = (center_x, center_y)
        
        t0 = (p0[0], p0[1] - dz)
        t1 = (p1[0], p1[1] - dz)
        t2 = (p2[0], p2[1] - dz)
        t3 = (p3[0], p3[1] - dz)
        
        wire_color = (0, 220, 255)
        draw.polygon([t0, t1, t2, t3], outline=wire_color, fill=(40, 60, 80))
        draw.polygon([p0, p1, t1, t0], outline=wire_color, fill=(35, 50, 65))
        draw.polygon([p1, p2, t2, t1], outline=wire_color, fill=(30, 45, 58))
        
        if info["textures"]:
            t_name = info["textures"][0]
            cd = info["texture_dirs"][0] if info["texture_dirs"] else "models/"
            mat_candidates = [
                f"materials/{cd}{t_name}.vtf",
                f"materials/models/{t_name}.vtf",
                f"materials/{t_name}.vtf"
            ]
            for cand in mat_candidates:
                try:
                    tex_img = self.preview_material(cand)
                    tex_img = tex_img.resize((160, 160))
                    img.paste(tex_img, (330, 190))
                    draw.rectangle([(329, 189), (491, 351)], outline=(100, 100, 110))
                    draw.text((330, 170), f"Texture: {t_name}", fill=(180, 180, 180))
                    break
                except Exception:
                    pass
                    
        return img
