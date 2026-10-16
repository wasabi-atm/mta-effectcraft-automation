#!/usr/bin/env python3
"""Pull brand inputs per company: logo (transparent PNG), CTA text + colours from computed CSS, hero bg, h1 font.
Usage: brand_extract.py <concepts.csv> <outdir> [domain ...]
Reads only public pages; clicks nothing; blocks the Qualified chat widget."""
import csv, json, os, re, sys
from playwright.sync_api import sync_playwright
from PIL import Image

JS = r"""
() => {
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity || 1) > 0.1; };
  const bgOf = el => { while (el) { const c = getComputedStyle(el).backgroundColor; if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent') return c; el = el.parentElement; } return 'rgb(255, 255, 255)'; };
  // logo
  const sels = ['header a[href="/"] img','header a[href="/"] svg','a[href="/"] img','a[href="/"] svg','[class*="logo" i] img','[class*="logo" i] svg','img[alt*="logo" i]','header img','header svg','nav img','nav svg'];
  let logo = null;
  for (const s of sels) { for (const el of document.querySelectorAll(s)) { const r = el.getBoundingClientRect();
      if (vis(el) && r.top < 160 && r.left < 700 && r.width >= 40 && r.height >= 12 && r.width < 420) { logo = el; break; } } if (logo) break; }
  let logoBox = null; if (logo) { const r = logo.getBoundingClientRect(); logoBox = {x: r.x, y: r.y, w: r.width, h: r.height, bg: bgOf(logo)}; logo.setAttribute('data-mta-logo', '1'); }
  // CTA: header first, then hero
  const re = /(book a demo|request a demo|get a demo|see a demo|schedule a demo|get started|start free|start for free|try .* free|try for free|sign up|talk to sales|contact sales|get a quote|request a quote|book a call|talk to us|demo)/i;
  const cands = [...document.querySelectorAll('a, button')].filter(el => vis(el) && re.test((el.innerText || '').trim()) && (el.innerText || '').trim().length < 32);
  const score = el => { const s = getComputedStyle(el); const bg = s.backgroundColor; const filled = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent'; const r = el.getBoundingClientRect(); return (filled ? 10 : 0) + (r.top < 140 ? 3 : 0) + (r.top < 800 ? 1 : 0); };
  cands.sort((a, b) => score(b) - score(a));
  const ctas = cands.slice(0, 3).map(el => { const s = getComputedStyle(el); const r = el.getBoundingClientRect();
    return {text: (el.innerText || '').trim().replace(/\s+/g, ' '), bg: s.backgroundColor, fg: s.color, radius: s.borderRadius, border: s.borderTopWidth + ' ' + s.borderTopStyle + ' ' + s.borderTopColor,
            font: s.fontFamily, weight: s.fontWeight, upper: s.textTransform, top: r.top, w: r.width, h: r.height}; });
  // hero + headings
  const h1 = document.querySelector('h1');
  const h1s = h1 ? getComputedStyle(h1) : null;
  const heroEl = document.elementFromPoint(640, 330);
  const heroBg = heroEl ? bgOf(heroEl) : getComputedStyle(document.body).backgroundColor;
  let heroImg = ''; { let el = heroEl; while (el) { const bi = getComputedStyle(el).backgroundImage; if (bi && bi !== 'none') { heroImg = bi.slice(0, 300); break; } el = el.parentElement; } }
  return {logoBox, ctas, h1: h1 ? {text: h1.innerText.slice(0, 120), font: h1s.fontFamily, weight: h1s.fontWeight, color: h1s.color, size: h1s.fontSize} : null,
          heroBg, heroImg, bodyBg: getComputedStyle(document.body).backgroundColor, title: document.title};
}
"""

STRIP = r"""
() => { for (const el of document.querySelectorAll('body *')) { const s = getComputedStyle(el); if (s.position !== 'fixed') continue;
  const r = el.getBoundingClientRect(); const n = (el.id || '') + ' ' + (el.getAttribute('class') || '') + ' ' + (el.innerText || '').slice(0, 200);
  if (/cookie|consent|gdpr|chat|intercom|drift|hubspot-messages|newsletter|popup|modal/i.test(n) || (r.top > 300 && r.height < 400)) el.remove(); } }
"""


def key_out(path):
    """Make the logo's flat background transparent, keyed on the corner colour."""
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    bg = max(set(corners), key=corners.count)[:3]
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            d = max(abs(r - bg[0]), abs(g - bg[1]), abs(b - bg[2]))
            if d < 18:
                px[x, y] = (r, g, b, 0)
            elif d < 60:
                px[x, y] = (r, g, b, int(a * (d - 18) / 42))
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    im.save(path)
    return "#%02x%02x%02x" % bg


def main():
    concepts, out = sys.argv[1], sys.argv[2]
    only = set(sys.argv[3:])
    rows = list(csv.DictReader(open(concepts)))
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--hide-scrollbars"])
        for r in rows:
            d = r["Domain"]
            if only and d not in only:
                continue
            od = os.path.join(out, d)
            os.makedirs(od, exist_ok=True)
            ctx = b.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=3, locale="en-US",
                                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
            ctx.route(re.compile(r"https?://[^/]*qualified\.com/"), lambda route: route.abort())
            pg = ctx.new_page()
            info = {"domain": d, "company": r["Company"]}
            try:
                home = "https://" + (d if d.count(".") > 1 else "www." + d) if d not in ("fireworks.ai",) else "https://fireworks.ai"
                try:
                    pg.goto(home, wait_until="domcontentloaded", timeout=40000)
                except Exception:
                    pg.goto("https://" + d, wait_until="domcontentloaded", timeout=40000)
                try:
                    pg.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass
                pg.wait_for_timeout(2500)
                pg.evaluate(STRIP)
                info.update(pg.evaluate(JS))
                pg.screenshot(path=os.path.join(od, "home.png"))
                lg = pg.query_selector('[data-mta-logo="1"]')
                if lg:
                    lg.screenshot(path=os.path.join(od, "logo.png"), omit_background=True)
                    info["logoKeyedBg"] = key_out(os.path.join(od, "logo.png"))
                info["status"] = "ok"
            except Exception as e:
                info["status"] = "error: " + str(e)[:200]
            json.dump(info, open(os.path.join(od, "brand.json"), "w"), indent=1)
            print(d, info.get("status"), "| logo:", bool(info.get("logoBox")), "| cta:", [c["text"] for c in info.get("ctas", [])][:2], "| heroBg:", info.get("heroBg"), flush=True)
            ctx.close()
        b.close()


if __name__ == "__main__":
    main()
