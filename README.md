# mta-effectcraft-automation

Headless replacement for the After Effects step in
[`mta-instantly-campaiign`](https://github.com/wasabi-atm/mta-instantly-campaiign): the bespoke
5-second **email 3 sneak-peek GIF** per company, built and rendered with no display, so it runs in a
Claude Code cloud session instead of on a Mac with After Effects open.

| Before (AE, Mac only) | Now (headless, Linux or Mac) |
|---|---|
| `osascript … DoScriptFile` into a running After Effects 2026 | [EffectCraft](https://github.com/storytold/effectcraft) `effectcraft-cli` (pure-Rust AE clone with the same ExtendScript object model), or its MCP server |
| Cinema 4D renderer for real extrusion (`MTA.ernst`, `MTA.extrude3d`) | Blender 5.2 as the `bpy` module, Cycles on the CPU, via `sneakpeek/blender/mta3d.py` or the headless Blender MCP (`blender_mcp/server.py`) |
| `run.sh` + `.ae-lock` + Lossless `.mov` | `sneakpeek run <scene>` (3D passes, build, render PNG frames, GIF, contact sheet) |
| `gifmake.py`, `sheet.py`, `brand_extract.py` | the same tools, ported to read PNG frame folders |

`sneakpeek/jsx/lib_mta.jsx` is the AE helper library unchanged: 32 of its 33 helpers run as-is in
EffectCraft (`extrude3d` needs the Cinema 4D renderer, which EffectCraft lacks; use a Blender pass).

## Setup

```bash
scripts/setup.sh            # builds .tools/bin/effectcraft-cli (pinned commit), .venv with bpy
bin/sneakpeek doctor
```

## Use

```bash
bin/sneakpeek run scenes/<company>      # 3d -> build -> render -> gif
bin/sneakpeek host scenes/<company> --prefix eu1015 --csv media/sneakpeek-urls.csv
```

MCP servers for interactive work are in `.mcp.json`: `effectcraft` (headless) and `blender`
(headless `bpy`).

Status: work in progress. See the open pull request for what is done and what is next.
