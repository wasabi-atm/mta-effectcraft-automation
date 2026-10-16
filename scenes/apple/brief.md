# Apple sneak peek (demo)

**Status:** demo of the headless pipeline. Not a prospect, not for sending. The repo is public.

## Concept

One hero moment, shot like an Apple product film: a chip.

| Time | Beat | Built in |
|---|---|---|
| 0.00-0.50 s | A hairline of light splits open on a grazing macro of the lid's chamfered corner, f/1.4 | EffectCraft (band mask, light edges) over Blender |
| 0.00-1.90 s | A strip light sweeps a specular streak across the brushed aluminium | Blender (`3d/chip.py`) |
| 0.50-3.85 s | One continuous pull-back to a three-quarter top view; traces light up from the package outward in Apple's system palette, hot at the wavefront; the die floorplan glows last | Blender |
| 2.55-3.60 s | "Think different." over the traces, on a soft dark band | EffectCraft |
| 3.55-3.95 s | The chip flares to white | EffectCraft |
| 3.80-5.00 s | End card: "Think different." with a blue-to-pink shimmer, "Learn more" (filled) and "Buy" (outline) pills, apple.com, over a deeply blurred glow of the last 3D frame | EffectCraft |

## Brand (checked on apple.com, 16 Oct 2026: homepage HTML and /v/homepage/a/styles/main.built.css)

| Element | Value | Source |
|---|---|---|
| Background | `#000000` | dark homepage tiles |
| Type colour | `#F5F5F7` headline, `#86868B` secondary | apple.com text colours |
| CTA labels | "Learn more" (9 on the homepage), "Buy" (2) | homepage tiles |
| Primary pill | `.button`: `rgb(0, 113, 227)` `#0071E3`, white text | main.built.css |
| Secondary pill (dark tiles) | `.button-dark.button-secondary`: transparent, text and border `rgb(41, 151, 255)` `#2997FF` | homepage.built.css |
| Pill type | 17px, weight 400, letter-spacing -0.022em, padding 12px / 22px (scaled x1.7 for the 1280 comp) | main.built.css |
| Type | SF Pro Display, stood in by **Inter Display** SemiBold / Regular | SF Pro is licensed for Apple platforms only |
| Palette (traces, die, shimmer) | `#2997FF` `#7D7AFF` `#BF5AF2` `#FF375F` `#FF9F0A` | Apple system colours (blue, indigo, purple, pink, orange) |
| Line | "Think different." | Apple's slogan (1997 campaign). Current homepage lines include "Pro further." (iPhone 18 Pro) and "Designed for life at home." (HomeView) |

Not used, on purpose: the Apple logo (a trademark glyph we don't redraw in a public repo), product
names, chip names and any performance claim.

## Build

```bash
bin/sneakpeek run scenes/apple        # ~35 min of Blender (78 frames, Cycles CPU, 4 cores), ~1 min EffectCraft
```
