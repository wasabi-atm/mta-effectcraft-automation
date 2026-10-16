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

`sneakpeek/jsx/lib_mta.jsx` is the AE helper library with one change (SF Pro names mapped to Inter
Display): 32 of its 33 helpers run as-is in EffectCraft. `extrude3d` needs the Cinema 4D renderer,
which EffectCraft lacks, so real extrusion is a Blender pass. Details in
[docs/migration-from-after-effects.md](docs/migration-from-after-effects.md).

Worked example: [`scenes/apple/`](scenes/apple/brief.md), a chip hero in Blender (brushed lid,
gradient softbox, die floorplan, traces lit outward in Apple's system palette) composited in
EffectCraft with an Apple-style end card.

## Setup

```bash
scripts/setup.sh            # builds .tools/bin/effectcraft-cli (pinned commit), .venv with bpy
bin/sneakpeek doctor
```

## Use

```bash
bin/sneakpeek new scenes/<company>      # scaffold brief.md, scene.jsx, 3d/hero.py
bin/sneakpeek brand concepts.csv scenes/_brand    # logo, CTA, colours from their site (Playwright)
bin/sneakpeek run scenes/<company>      # 3d -> build -> render -> gif + contact sheet
bin/sneakpeek host scenes/<company> --prefix eu1015 --domain acme.com --csv media/sneakpeek-urls.csv
```

Claude sessions: start with the `/sneakpeek` skill (`.claude/skills/sneakpeek/SKILL.md`).

Tests: `.venv/bin/python -m unittest discover -s tests -v` (EffectCraft and Blender tests skip when
the tools are not installed).

MCP servers for interactive work are in `.mcp.json`: `effectcraft` (headless) and `blender`
(headless `bpy`).

