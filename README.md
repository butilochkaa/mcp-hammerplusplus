# mcp-hammerplusplus

[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-blue)](https://modelcontextprotocol.io)
[![Source Engine](https://img.shields.io/badge/Source%20Engine-Hammer%2B%2B-orange)](https://ficool2.github.io/HammerPlusPlus-Website/)

Model Context Protocol (MCP) server for **Hammer++** (Source Engine / Garry's Mod). Enables AI agents to inspect viewports, browse models & materials, build sealed geometry, place entities with floor-snapping, and compile maps with leak diagnostics.

---

## features / возможности

### english
- **real-time viewport vision**: grab live hammer++ 3d camera & 2d grid views
- **asset browser**: search & preview models (`.mdl`) and materials (`.vtf` / `.vmt`)
- **leak-proof vmf generator**: procedural sealed rooms and solids without void leaks
- **smart entity placement**: automatic floor-snapping for props and lights
- **compile pipeline**: run `vbsp`, `vvis`, `vrad` with automatic `.lin` leak trail parsing

### русский
- просмотр вьюпорта hammer++ в реальном времени (3d камера / 2d сетки)
- поиск и предпросмотр моделей (`.mdl`) и текстур (`.vtf` / `.vmt`)
- создание и редактирование карт (`.vmf`) без ликов
- расстановка пропов с автоматическим снепом к полу
- компиляция (`vbsp`, `vvis`, `vrad`) и поиск утечек в космос

---

## installation / установка

run `install.bat` or:
```bash
python install.py
```

---

star this repo if you like it ⭐
понравилось? закинь звёздочку ⭐
