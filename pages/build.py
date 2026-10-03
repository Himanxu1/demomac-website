#!/usr/bin/env python3
"""Builds the content pages (features, guides, 404) from pages/*.html.

Each source file starts with a JSON header inside an HTML comment, then the
page body. This wraps the body in the shared head, header and footer, so the
chrome and metadata are written once instead of six times:

    <!--
    {"path": "/features/auto-zoom", "title": "...", "description": "...",
     "crumbs": [["Features", null]], "schema": [...]}
    -->
    <h1>...</h1>

The output is plain static HTML at the page's path (/features/auto-zoom →
features/auto-zoom.html), committed like everything else — the site still has
no build step at deploy time. Run after editing a page, then add any new path
to sitemap.xml:

    python3 pages/build.py
"""
import html
import json
import pathlib
import re

SITE = "https://screentoast.com"
ROOT = pathlib.Path(__file__).resolve().parent.parent
# Keep in step with the homepage's download links; release flow bumps both.
DMG = "/ScreenToast-0.2.0.dmg"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="theme-color" content="#08080a">
{robots}<link rel="canonical" href="{url}">
<meta property="og:site_name" content="ScreenToast">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{site}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{site}/og.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@700;800&family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<link rel="stylesheet" href="/site.css">
{schema}</head>
<body>
<header class="top"><div class="wrap wide">
  <a class="mark" href="/"><span class="dot"></span>ScreenToast</a>
  <nav>
    <a href="/features/auto-zoom">Auto zoom</a>
    <a href="/features/vertical-screen-recording">Vertical</a>
    <a href="/#pricing">Pricing</a>
    <a class="btn btn-primary btn-sm" href="{dmg}" download data-event="download-{slug}-nav">Download for Mac</a>
  </nav>
</div></header>
<main><div class="wrap">
{crumbs}"""

FOOT = """</div></main>
<footer class="bottom"><div class="wrap wide">
  <div class="cols">
    <a href="/">ScreenToast</a>
    <a href="/features/auto-zoom">Auto zoom</a>
    <a href="/features/vertical-screen-recording">Vertical recording</a>
    <a href="/features/ai-voiceover">AI voiceover</a>
    <a href="/guides/how-to-make-a-product-demo-video-on-mac">Make a product demo</a>
    <a href="/changelog">Changelog</a>
    <a href="/privacy">Privacy</a>
    <a href="/terms">Terms</a>
    <a href="mailto:support@screentoast.com">Support</a>
  </div>
  <p>© 2026 ScreenToast · Made for macOS 14 or later</p>
</div></footer>
<script src="/analytics.js" defer></script>
</body>
</html>
"""


def build(src: pathlib.Path) -> str:
    text = src.read_text()
    m = re.match(r"\s*<!--\s*(\{.*?\})\s*-->\s*", text, re.S)
    if not m:
        raise SystemExit(f"{src.name}: missing JSON header")
    meta = json.loads(m.group(1))
    body = text[m.end():]
    path = meta["path"]
    url = SITE + path if path != "/404" else SITE + "/"
    slug = meta.get("slug") or path.strip("/").replace("/", "-")

    # Breadcrumbs: visible trail, plus the same trail as BreadcrumbList.
    crumbs = [["ScreenToast", "/"]] + meta.get("crumbs", [])
    trail, items = [], []
    for i, (name, href) in enumerate(crumbs):
        target = href or path
        trail.append(f'<a href="{target}">{html.escape(name)}</a>' if href else html.escape(name))
        items.append({"@type": "ListItem", "position": i + 1, "name": name, "item": SITE + target})
    schema = list(meta.get("schema", []))
    crumb_html = ""
    if meta.get("crumbs"):
        schema.append({"@type": "BreadcrumbList", "itemListElement": items})
        crumb_html = '<p class="crumbs">' + " / ".join(trail) + "</p>\n"

    schema_html = ""
    if schema:
        graph = {"@context": "https://schema.org", "@graph": schema}
        schema_html = ('<script type="application/ld+json">\n'
                       + json.dumps(graph, indent=1, ensure_ascii=False) + "\n</script>\n")

    head = HEAD.format(
        title=html.escape(meta["title"]),
        description=html.escape(meta["description"]),
        url=url, site=SITE, dmg=DMG, slug=slug,
        og_type=meta.get("og_type", "website"),
        robots='<meta name="robots" content="noindex">\n' if meta.get("noindex") else "",
        schema=schema_html,
        crumbs=crumb_html,
    )
    return head + body.replace("{{DMG}}", DMG).replace("{{SLUG}}", slug) + FOOT


def main():
    for src in sorted((ROOT / "pages").glob("*.html")):
        meta = json.loads(re.match(r"\s*<!--\s*(\{.*?\})\s*-->", src.read_text(), re.S).group(1))
        out = ROOT / (meta["path"].strip("/") + ".html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build(src))
        print(f"{src.name:44} → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
