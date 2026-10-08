import os
import sys
import ctypes
from ctypes import wintypes
import winreg
import re

def get_process_path_by_name(name="hammerplusplus.exe"):
    kernel32 = ctypes.windll.kernel32
    TH32CS_SNAPPROCESS = 0x00000002
    
    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ('dwSize', wintypes.DWORD),
            ('cntUsage', wintypes.DWORD),
            ('th32ProcessID', wintypes.DWORD),
            ('th32DefaultHeapID', ctypes.POINTER(wintypes.ULONG)),
            ('th32ModuleID', wintypes.DWORD),
            ('cntThreads', wintypes.DWORD),
            ('th32ParentProcessID', wintypes.DWORD),
            ('pcPriClassBase', wintypes.LONG),
            ('dwFlags', wintypes.DWORD),
            ('szExeFile', ctypes.c_char * 260)
        ]
        
    hSnap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    pe = PROCESSENTRY32()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
    
    pid = None
    if kernel32.Process32First(hSnap, ctypes.byref(pe)):
        while True:
            exe = pe.szExeFile.decode('latin1', errors='ignore').lower()
            if name.lower() in exe:
                pid = pe.th32ProcessID
                break
            if not kernel32.Process32Next(hSnap, ctypes.byref(pe)):
                break
    kernel32.CloseHandle(hSnap)
    
    if not pid:
        return None
        
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    hProc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not hProc:
        return None
        
    buf = ctypes.create_unicode_buffer(1024)
    size = wintypes.DWORD(1024)
    res = kernel32.QueryFullProcessImageNameW(hProc, 0, buf, ctypes.byref(size))
    kernel32.CloseHandle(hProc)
    
    if res:
        return buf.value
    return None

def get_steam_libraries():
    libraries = []
    steam_path = None
    for root_key in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(root_key, r"Software\Valve\Steam") as key:
                val, _ = winreg.QueryValueEx(key, "SteamPath")
                steam_path = val.replace("/", "\\")
                break
        except OSError:
            pass
            
    if steam_path and os.path.exists(steam_path):
        libraries.append(steam_path)
        vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf):
            try:
                with open(vdf, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                matches = re.findall(r'"path"\s+"([^"]+)"', content)
                for m in matches:
                    p = m.replace("\\\\", "\\")
                    if os.path.exists(p) and p not in libraries:
                        libraries.append(p)
            except Exception:
                pass
                
    common_roots = [r"C:\Program Files (x86)\Steam", r"C:\Steam", r"D:\Steam", r"D:\SteamLibrary", r"E:\SteamLibrary", r"F:\SteamLibrary"]
    for cr in common_roots:
        if os.path.exists(cr) and cr not in libraries:
            libraries.append(cr)
            
    return libraries

def resolve_gmod_root():
    cfg_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if os.path.exists(cfg_file):
        try:
            import json
            with open(cfg_file, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            if "gmod_root" in cfg and os.path.exists(cfg["gmod_root"]):
                return cfg["gmod_root"]
        except Exception:
            pass
            
    running_hammer = get_process_path_by_name("hammerplusplus.exe")
    if running_hammer:
        bin_dir = os.path.dirname(running_hammer)
        candidate = os.path.abspath(os.path.join(bin_dir, "..", ".."))
        if os.path.exists(os.path.join(candidate, "garrysmod")):
            return candidate
        candidate2 = os.path.abspath(os.path.join(bin_dir, ".."))
        if os.path.exists(os.path.join(candidate2, "garrysmod")):
            return candidate2

    libs = get_steam_libraries()
    for lib in libs:
        candidate = os.path.join(lib, "steamapps", "common", "GarrysMod")
        if os.path.exists(candidate) and os.path.exists(os.path.join(candidate, "garrysmod")):
            return candidate
            
    for drive in ["C", "D", "E", "F", "G"]:
        for base in [f"{drive}:\\Games\\GarrysMod", f"{drive}:\\GarrysMod", f"{drive}:\\SteamLibrary\\steamapps\\common\\GarrysMod"]:
            if os.path.exists(base) and os.path.exists(os.path.join(base, "garrysmod")):
                return base
                
    return r"C:\Program Files (x86)\Steam\steamapps\common\GarrysMod"
