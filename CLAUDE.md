# mta-effectcraft-automation

Headless motion graphics for Motion The Agency's Instantly campaigns: the bespoke 5-second
**email 3 sneak-peek GIF** per company (`SneakPeekUrl`). It replaces the After Effects + osascript
toolkit that lived in `mta-instantly-campaiign/campaigns/<run>/media/sneakpeek/ae/`, so the step runs
in a cloud session with no display.

**Start every sneak-peek task with the project skill `/sneakpeek`** (`.claude/skills/sneakpeek/SKILL.md`).

## Tools

| Tool | What | How Claude drives it |
|---|---|---|
| EffectCraft (`.tools/bin/effectcraft-cli`) | 2D compositing, type, shapes, effects, render | `bin/sneakpeek build/render`, or the `effectcraft` MCP server (`.mcp.json`) |
| Blender 5.2 (`bpy` in `.venv`) | real 3D: extruded type and logos, products, lit and DOF | `scenes/<co>/3d/*.py` via `bin/sneakpeek 3d`, or the `blender` MCP server (`blender_mcp/server.py`) |
| `sneakpeek/jsx/lib_mta.jsx` | the AE helper library (`MTA.*`), runs unchanged in EffectCraft | `$.evalFile`d by the runner before `scene.jsx` |
| `sneakpeek/blender/mta3d.py` | Blender helpers (`M.*`): text3d, svg3d, mat, key, cam, rig3, render_sequence | imported as `M` in 3D passes |
| `bin/sneakpeek` | `doctor`, `new`, `brand`, `3d`, `build`, `render`, `gif`, `run`, `host` | Bash |

First run in a new container: `scripts/setup.sh` (builds EffectCraft at the pinned commit, about
11 minutes on 4 cores; installs `bpy`, `fonts-inter`), then `bin/sneakpeek doctor`.

## Layout

| Path | What |
|---|---|
| `scenes/<company>/` | one scene: `brief.md`, `brand/`, `scene.jsx`, `3d/*.py`, `out/` (gitignored renders) |
| `scenes/apple/` | worked demo: Blender chip hero + EffectCraft composite |
| `templates/scene/` | what `sneakpeek new` copies |
| `examples/ae-originals/` | two After Effects scenes from the 15 Oct run, for reference when porting |
| `docs/migration-from-after-effects.md` | what changed, what EffectCraft lacks, and the workarounds |

## Hard rules

- **Never host a GIF the user hasn't approved**, and never write a `SneakPeekUrl` that does not answer 200.
- **Every word on screen is the company's own** (their H1, their CTA, their claims with a source in
  `brief.md`). Illustrative numbers are listed in `brief.md` as illustrative.
- **No logos redrawn from memory.** Use the logo `sneakpeek brand` pulled from their site.
- GIF: 640x360, 20 fps, 5 s, at most 2.2 MB (`gifmake.py` ladders down to fit).
- Bespoke per company, never a template with the name swapped (user, 12 Oct).
- No em dashes in on-screen copy. Secrets live in `.env` (gitignored): check a key is set, never print it.
