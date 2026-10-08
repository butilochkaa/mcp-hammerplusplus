import os
import sys
import json
import shutil
import subprocess

CONFIG_PATH = os.path.expandvars(r"%USERPROFILE%\.gemini\config\mcp_config.json")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_PY = os.path.join(PROJECT_DIR, "server.py")
DUMP_SCHEMAS_PY = os.path.join(PROJECT_DIR, "dump_schemas.py")

def find_uv():
    uv_candidates = [
        os.path.expandvars(r"%USERPROFILE%\.local\bin\uv.exe"),
        shutil.which("uv"),
        shutil.which("uv.exe")
    ]
    for c in uv_candidates:
        if c and os.path.exists(c):
            return c
    return None

def install_mcp():
    uv_exe = find_uv()
    
    config = {"mcpServers": {}}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            pass
            
    if "mcpServers" not in config:
        config["mcpServers"] = {}
        
    if uv_exe:
        server_entry = {
            "command": uv_exe,
            "args": [
                "run",
                "--with",
                "mcp<2",
                "--with",
                "pillow",
                "python",
                SERVER_PY
            ]
        }
        cmd = [uv_exe, "run", "--with", "mcp<2", "--with", "pillow", "python", DUMP_SCHEMAS_PY]
        subprocess.run(cmd, check=False)
    else:
        venv_dir = os.path.join(PROJECT_DIR, ".venv")
        venv_py = os.path.join(venv_dir, "Scripts", "python.exe")
        if not os.path.exists(venv_py):
            subprocess.run([sys.executable, "-m", "venv", venv_dir], check=False)
        pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
        subprocess.run([pip_exe, "install", "mcp<2", "pillow"], check=False)
        
        server_entry = {
            "command": venv_py,
            "args": [SERVER_PY]
        }
        subprocess.run([venv_py, DUMP_SCHEMAS_PY], check=False)

    config["mcpServers"]["hammerplusplus"] = server_entry
    
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        
    print("Hammer++ MCP successfully installed.")

if __name__ == "__main__":
    install_mcp()
