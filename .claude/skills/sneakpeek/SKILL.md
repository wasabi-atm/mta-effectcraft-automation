---
name: sneakpeek
description: Build Motion The Agency's bespoke 5-second email 3 sneak-peek GIFs headlessly (EffectCraft for 2D/compositing, Blender bpy for 3D), review them, host them on ImageKit and hand back SneakPeekUrl values for an Instantly campaign. Use for any sneak-peek, styleframe GIF, concept GIF or "email 3 media" task, or when porting an After Effects scene.
---

# Sneak-peek GIFs, headless

Feeds `SneakPeekUrl` (email 3 image) in `mta-instantly-campaiign` runs. One GIF per company, shared
by every contact there.

## The bar (from the user's feedback on the AE runs, 12-15 Oct)

- **One cinematic hero moment per company, built on its own story.** CarOnSale v3 is "the level":
  their car, bidders arcing in from across Europe, real 3D "SOLD", their CTA.
- **Few words.** v1 had too many tags and was "hard to follow". But not bare: "just a car and a
  price" was too plain.
- **Real 3D** where it helps (Blender pass), their own brand colours, fonts and imagery.
- **Their own lines and their own CTA** on an end card. Ends on the CTA; the email's ask is "reply
  for the full video".
- **Bespoke, never templated.** Two template GIFs were pulled from hosting on 12 Oct for this.
- Stock footage is fine when the story needs real-world shots (Unleash live, CartonCloud).

## Steps

1. **Gate.** `bin/sneakpeek doctor`. If EffectCraft or Blender is missing, run `scripts/setup.sh`
   (EffectCraft builds from source in about 11 minutes). Say plainly if a stage can't run.
2. **Inputs.** The run's `media/sneakpeek/concepts.csv` (`Domain,Company`) and each company's
   research file. Read the research before designing anything.
3. **Brand.** `bin/sneakpeek brand concepts.csv scenes/_brand [domain ...]` pulls logo (keyed PNG),
   CTA text and computed colours, H1 and font, hero background and a homepage capture. Needs
   Playwright (`scripts/setup.sh --with-brand`) and network access to the site. When the site is
   blocked, say so and do not invent brand values.
4. **Concept.** Per company, write `scenes/<slug>/brief.md` (`bin/sneakpeek new scenes/<slug>`):
   beats with times, brand table with source URLs, every on-screen word with its source. Batch the
   concepts for the user's review before building more than one or two.
5. **Build.**
   - 3D passes in `scenes/<slug>/3d/*.py` (`M` = `sneakpeek/blender/mta3d.py`). Preview stills first:
     run the pass with `ARGS = {"preview": {"pct": 50, "samples": 24, "frames": [...]}}` (see
     `scenes/apple/3d/chip.py`), look at them, then render the sequence.
   - `scene.jsx`: After Effects-style ExtendScript with `MTA.*`; create the comp with
     `MTA.newComp(MTA.COMP, bg)`; bring Blender frames in with `MTA.sequence(c, MTA.OUT3D + "<pass>/f_0001.png")`.
   - `bin/sneakpeek run scenes/<slug>` = 3d + build + render + gif + contact sheet.
6. **Review.** Open `out/<slug>_sheet.png` and individual frames (`effectcraft-cli render-frame
   --project out/scene.ecproj --comp SP_<slug> --time T --out f.png`) and look at them. Fix, re-run.
   Then show the user the GIF and sheet. **Nothing is hosted before the user approves it.**
7. **Host.** `bin/sneakpeek host scenes/<slug> --prefix <run prefix, e.g. eu1015> --domain <domain>
   --company <Company> --csv <run>/media/sneakpeek-urls.csv`. It prints the `?v=<sha1>` URL and
   refuses if it doesn't answer 200. Hosting needs `IMAGEKIT_PRIVATE_KEY` in `.env` and network
   access to upload.imagekit.io.
8. **Hand back** `sneakpeek-urls.csv` (`Company,Domain,SneakPeekUrl,SizeKB`) to the campaign run;
   its `lint_campaign.py` treats `SneakPeekUrl` as step 3 media.

## EffectCraft notes (v0.10, pinned in scripts/setup.sh)

- `lib_mta.jsx` runs unchanged except `MTA.extrude3d` / `MTA.ernst` (no Cinema 4D renderer, no
  extrusion group). Real extrusion goes in a Blender pass.
- Fonts: SF Pro names silently fall back to Inter **Regular**. `MTA.F` maps to Inter Display
  (`InterDisplay-SemiBold`...). For a brand font, install it (`~/.local/share/fonts`, then
  `text.fonts {"rescan": true}`) and use its PostScript name.
- Scripts may only read files beside themselves unless "Allow Scripts to Write Files" is on; the
  runner turns it on in a private config dir (`.tools/config`), never in a desktop install.
- Track mattes: `layer.setTrackMatte(matte, TrackMatteType.ALPHA)`.
- CC Light Sweep is invisible on white or near-white layers; use a gradient band matted by the type
  (see the end card in `scenes/apple/scene.jsx`).
- Turn motion blur off on thin fast lines (light edges, rings): blurred they read as grey bars.

## Blender notes (bpy 5.2.2, Python 3.13)

- Cycles on the CPU is the default (`M.reset`). EEVEE needs EGL and runs about 15x slower on a
  software rasteriser here.
- Render 3D at 75% (960x540): the GIF is 640x360. A detailed scene costs about 25-30 s a frame on
  4 cores at 40 samples, so 78 frames is about 35 minutes. Start it in the background, then build
  the composite against the frames that exist.
- Uniform area lights reflect as flat white slabs on metal and glass; for product-shot reflections
  use an emissive gradient card hidden from the camera (`softbox()` in `scenes/apple/3d/chip.py`).
- `M.key(obj, "dof.aperture_fstop", ...)`: nested properties are keyed by path on the ID.

## GIF size

Budget 2.2 MB at 640x360, 20 fps. `gifmake.py` holds sub-threshold pixel changes (renderers dither
by +-1 per frame) and ladders 128 -> 64 colours, then 15 fps. The hold refreshes a held pixel once
the source has settled there, so a slow fade into a light end card leaves no ghost (card outline,
stripes); that costs about 0.2-0.3 MB per GIF. What blows the budget: animated
fractal noise backgrounds, full-frame grain, constant camera motion over textured surfaces. Black
backgrounds and play-then-hold beats keep it small.
Before the global palette, the ladder gives each of 3 segments (cut at the biggest frame-to-frame
changes, joined by gifsicle) its own palette so soft glows don't band. A held pixel is refreshed
once the source settles, so a slow dissolve into a light end card leaves no ghost.
