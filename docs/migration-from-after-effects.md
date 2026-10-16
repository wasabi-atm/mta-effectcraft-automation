# From the After Effects toolkit to EffectCraft + Blender

The 12-15 Oct sneak peeks were built in After Effects 2026 on a Mac: `run.sh <scene>` wrote a runner
`.jsx`, took a shared `.ae-lock`, sent it to the open app with `osascript ... DoScriptFile`, rendered
a Lossless `.mov`, then `gifmake.py` and `sheet.py` ran on the `.mov`. Nothing about that can run in
a cloud session: no macOS, no After Effects, no display.

## What maps to what

| After Effects toolkit | Here | Notes |
|---|---|---|
| `osascript` + `DoScriptFile` + `.ae-lock` | `effectcraft-cli run prefs.set ... script.run ...` (`sneakpeek build`) | headless; one process per scene, so no lock |
| AE MCP bridge (checks only, no render) | `effectcraft` MCP server: `run_script`, `render_frame`, `get_layer`, `add_effect`... | it renders, too |
| `lib_mta.jsx` | the same file | font map changed (below); everything else unchanged |
| `scenes/<co>.jsx` with absolute `/Users/wira/...` paths | `scenes/<co>/scene.jsx` with `MTA.BRAND`, `MTA.OUT3D`, `MTA.ROOT` | the runner sets them |
| `comp SP_<name>` | `MTA.newComp(MTA.COMP, bg)` | `MTA.COMP` is `SP_<slug>` |
| `MTA.ernst` + `MTA.extrude3d` (Cinema 4D renderer) | a Blender pass (`3d/*.py`, `mta3d.text3d` / `svg3d`), imported with `MTA.sequence` | EffectCraft has Classic 3D and Advanced 3D, no Cinema 4D renderer and no extrusion group |
| `tools/dot_globe.py` etc. (PIL PNG sequences) | still work: write them to `out/3d/<name>/f_0001.png` and import with `MTA.sequence` | or do them as Blender passes |
| `MTA.render(comp, ".mov")` Lossless | `sneakpeek render` -> PNG frames | `MTA.render` itself also works in EffectCraft (ProRes) |
| `gifmake.py in.mov out.gif` | `gifmake.py frames/ out.gif` | same temporal hold and palette ladder; also takes a video |
| `sheet.py` | `sheet.py frames/ sheet.png` | same 14 timestamps |
| `brand_extract.py` | the same file (`sneakpeek brand`) | needs Playwright + network access to the site |
| `upload_imagekit.sh` (styleframe-concept-automation) | `sneakpeek host` | same `outreach/sneakpeek-gif/<prefix>-sp-<domain>.gif?v=<sha1[:12]>` URLs |

## What `lib_mta.jsx` does in EffectCraft (probed 16 Oct, v0.10.0 at 08627d4)

32 of 33 helpers run unchanged: newComp, solid, ramp, glowBlob, rect, ellipse, path + trim, text,
sourceRectAtTime, k (eases), pop, fade, extrude (fake), shadow, glow, button, camRig + attach,
whipBlur, motionBlurAll, typeOn, counter, colorKeys, tint, kids, reveal, ring, sweep, band, arc,
rig3, render (render queue, Lossless template), plus `setTrackMatte`.

| Difference | Effect | Fix |
|---|---|---|
| `MTA.extrude3d` throws (no `ADBE Extrsn Options Group`) | no real extruded type in EffectCraft | Blender pass |
| `comp.renderer = "ADBE Ernst"` is ignored (stays Classic 3D) | | Blender pass |
| SF Pro font names fall back to Inter **Regular** | every weight flattens silently | `MTA.F` now maps to Inter Display (`fonts-inter`) |
| Scripts can't read files outside their folder by default | `$.evalFile(lib)` and brand images fail | the runner enables "Allow Scripts to Write Files" in a private config dir |
| CC Light Sweep has no visible effect on white type | | gradient band matted by the type |

## Still open

- No real After Effects reference render to compare against: EffectCraft's README says behaviour
  still differs in places. Look at every contact sheet.
- `.aep` files can't be opened, so the 15 Oct AE projects don't carry over; their `.jsx` scenes do.
- Brand fonts beyond Inter Display need installing per run (`~/.local/share/fonts` + `text.fonts {"rescan": true}`).
