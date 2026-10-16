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

## Brand

| Element | Value | Source |
|---|---|---|
| Background | `#000000` | Apple product pages (dark sections) |
| Type colour | `#F5F5F7` headline, `#86868B` secondary | apple.com text colours |
| CTA | "Learn more" filled `#0071E3`, "Buy" outline `#2997FF`, pill radius | apple.com tile CTAs |
| Type | SF Pro Display, stood in by **Inter Display** SemiBold / Regular | SF Pro is macOS-only and licensed for Apple platforms |
| Palette (traces, die, shimmer) | `#2997FF` `#7D7AFF` `#BF5AF2` `#FF375F` `#FF9F0A` | Apple system colours (blue, indigo, purple, pink, orange) |
| Line | "Think different." | Apple's slogan (1997 campaign) |

Not used, on purpose: the Apple logo (a trademark glyph we don't redraw in a public repo), product
names, chip names and any performance claim.

## To verify before this pattern is used on a real Apple pitch

apple.com was not reachable from the cloud session (environment network policy), so the CTA labels
and colours above come from Apple's long-standing site conventions, not from a live pull. Run
`sneakpeek brand` against apple.com once the network allows it and replace anything that differs.

## Build

```bash
bin/sneakpeek run scenes/apple        # ~35 min of Blender (78 frames, Cycles CPU, 4 cores), ~1 min EffectCraft
```
