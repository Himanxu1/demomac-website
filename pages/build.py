#!/usr/bin/env python3
"""Builds the content pages (features, guides, blog, 404) from pages/*.html.

Each source file starts with a JSON header inside an HTML comment, then the
page body. This wraps the body in the shared head, header and footer, so the
chrome and metadata are written once instead of six times:

    <!--
    {"path": "/features/auto-zoom", "title": "...", "description": "...",
     "crumbs": [["Features", null]], "schema": [...]}
    -->
    <h1>...</h1>

Blog posts (pages/blog-*.html) carry a "blog" object instead of hand-written
crumbs and schema — date, category, card title, excerpt, cover and related
posts — plus an optional "faq" list. From that the build writes the cover
figure, byline, FAQ section, related links, Article/FAQPage/Breadcrumb schema,
the /blog index and the blog's sitemap entries. In the body, {{COVER}},
{{FAQ}}, {{CTA}} and {{RELATED}} mark where those go. Covers are drawn by
pages/covers.py.

The output is plain static HTML at the page's path (/features/auto-zoom →
features/auto-zoom.html), committed like everything else — the site still has
no build step at deploy time. Run after editing a page, then add any new
non-blog path to sitemap.xml:

    python3 pages/covers.py   # only when a blog post is added or retitled
    python3 pages/build.py
"""
import datetime
import html
import json
import math
import pathlib
import re

SITE = "https://screentoast.com"
ROOT = pathlib.Path(__file__).resolve().parent.parent
# Keep in step with the homepage's download links; release flow bumps both.
DMG = "/ScreenToast-0.2.2.dmg"

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
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:image" content="{image}">
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
    <a href="/blog">Blog</a>
    <a href="/#pricing">Pricing</a>
    <a class="btn btn-primary btn-sm" href="{dmg}" download data-event="download-{slug}-nav">Download for Mac</a>
  </nav>
</div></header>
<main><div class="{wrap}">
{crumbs}"""

FOOT = """</div></main>
<footer class="bottom"><div class="wrap wide">
  <div class="cols">
    <a href="/">ScreenToast</a>
    <a href="/features/auto-zoom">Auto zoom</a>
    <a href="/features/vertical-screen-recording">Vertical recording</a>
    <a href="/features/ai-voiceover">AI voiceover</a>
    <a href="/guides/how-to-make-a-product-demo-video-on-mac">Make a product demo</a>
    <a href="/blog">Blog</a>
    <a href="/changelog">Changelog</a>
    <a href="/privacy">Privacy</a>
    <a href="/terms">Terms</a>
    <a href="mailto:support@screentoast.com">Support</a>
  </div>
  <p>© 2026 ScreenToast · Made for macOS 14 or later</p>
</div></footer>
<script src="/analytics.js" defer></script>
<script src="/download-gate.js" defer></script>
</body>
</html>
"""

# The closing call to action every blog post ends on.
CTA = """<div class="final">
  <h2>Try ScreenToast free.</h2>
  <p>Record and edit as much as you like, with no sign-in and no trial clock. Pro is $4.92 a month, billed yearly, when you're ready to export.</p>
  <div class="cta-row">
    <a class="btn btn-primary" href="{{DMG}}" download data-event="download-{{SLUG}}-final">Download free for Mac</a>
    <a class="btn btn-ghost" href="/#pricing">See pricing</a>
  </div>
  <p class="fine">macOS 14 or later · Apple silicon and Intel · Under 10 MB</p>
</div>"""

ORG = {"@type": "Organization", "name": "ScreenToast", "url": SITE + "/"}
PUBLISHER = dict(ORG, logo={"@type": "ImageObject", "url": SITE + "/logo.png"})


def read_meta(src: pathlib.Path):
    text = src.read_text()
    m = re.match(r"\s*<!--\s*(\{.*?\})\s*-->\s*", text, re.S)
    if not m:
        raise SystemExit(f"{src.name}: missing JSON header")
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise SystemExit(f"{src.name}: bad JSON header: {e}")
    return meta, text[m.end():]


def read_minutes(body: str) -> int:
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    return max(1, math.ceil(words / 230))


def nice_date(iso: str) -> str:
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


def blog_parts(meta, body, posts):
    """Fills a post's placeholders and returns (body, crumbs, schema)."""
    b, path = meta["blog"], meta["path"]
    url = SITE + path
    image = SITE + b["image"]
    mins = read_minutes(body)

    cover = (f'<p class="byline"><span class="tag">{html.escape(b["category"])}</span>'
             f'<time datetime="{b["date"]}">{nice_date(b["date"])}</time> · {mins} min read</p>\n'
             f'<figure class="cover"><img src="{b["image"]}" width="1200" height="630" '
             f'alt="{html.escape(b["alt"])}" fetchpriority="high"></figure>')

    faq_html, faq = "", meta.get("faq") or []
    if faq:
        faq_html = '<section class="faq">\n<h2>Frequently asked questions</h2>\n' + "".join(
            f"<details><summary>{html.escape(q)}</summary><p>{a}</p></details>\n" for q, a in faq
        ) + "</section>"

    related = []
    for slug in b.get("related", []):
        other = posts.get(slug)
        if not other:
            raise SystemExit(f"{path}: related post {slug!r} does not exist")
        related.append(f'<li><a href="/blog/{slug}">{html.escape(other["blog"]["card"])}'
                       f'<span>{html.escape(other["blog"]["category"])}</span></a></li>')
    for href, name, note in b.get("links", []):
        related.append(f'<li><a href="{href}">{html.escape(name)}<span>{html.escape(note)}</span></a></li>')
    related_html = ('<nav class="related" aria-label="Related">\n  <h2>Keep reading</h2>\n  <ul>\n    '
                    + "\n    ".join(related) + "\n  </ul>\n</nav>") if related else ""

    for key, value in (("{{COVER}}", cover), ("{{FAQ}}", faq_html), ("{{CTA}}", CTA), ("{{RELATED}}", related_html)):
        if key not in body:
            raise SystemExit(f"{path}: body is missing {key}")
        body = body.replace(key, value)

    schema = [{
        "@type": "BlogPosting", "headline": meta.get("headline", b["card"]),
        "description": meta["description"], "image": image,
        "datePublished": b["date"], "dateModified": b.get("modified", b["date"]),
        "author": ORG, "publisher": PUBLISHER, "mainEntityOfPage": url,
        "articleSection": b["category"], "keywords": ", ".join(b.get("keywords", [])),
    }]
    if faq:
        schema.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in faq]})
    return body, [["Blog", "/blog"], [b["card"], None]], schema, image, mins


def build(meta, body, posts) -> str:
    path = meta["path"]
    url = SITE + path if path != "/404" else SITE + "/"
    slug = meta.get("slug") or path.strip("/").replace("/", "-")
    crumbs_meta = meta.get("crumbs", [])
    schema = list(meta.get("schema", []))
    image = SITE + meta.get("image", "/og.png")
    if "blog" in meta:
        body, crumbs_meta, schema, image, _ = blog_parts(meta, body, posts)

    # Breadcrumbs: visible trail, plus the same trail as BreadcrumbList.
    crumbs = [["ScreenToast", "/"]] + crumbs_meta
    trail, items = [], []
    for i, (name, href) in enumerate(crumbs):
        target = href or path
        trail.append(f'<a href="{target}">{html.escape(name)}</a>' if href else html.escape(name))
        items.append({"@type": "ListItem", "position": i + 1, "name": name, "item": SITE + target})
    crumb_html = ""
    if crumbs_meta:
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
        url=url, site=SITE, dmg=DMG, slug=slug, image=image,
        og_type=meta.get("og_type", "article" if "blog" in meta else "website"),
        robots='<meta name="robots" content="noindex">\n' if meta.get("noindex") else "",
        schema=schema_html,
        crumbs=crumb_html,
        wrap=meta.get("wrap", "wrap"),
    )
    return head + body.replace("{{DMG}}", DMG).replace("{{SLUG}}", slug) + FOOT


def blog_index(posts, minutes) -> tuple[dict, str]:
    """The /blog page: a filterable grid of every post, newest first."""
    ordered = sorted(posts.items(), key=lambda kv: (kv[1]["blog"]["date"], kv[1]["blog"].get("order", 0)), reverse=True)
    cats = []
    for _, m in ordered:
        if m["blog"]["category"] not in cats:
            cats.append(m["blog"]["category"])
    chips = ['<button type="button" class="chip on" data-cat="">All</button>'] + [
        f'<button type="button" class="chip" data-cat="{html.escape(c)}">{html.escape(c)}</button>' for c in cats]
    cards = []
    for slug, m in ordered:
        b = m["blog"]
        cards.append(f"""  <article class="card" data-cat="{html.escape(b['category'])}">
    <a class="card-img" href="/blog/{slug}" tabindex="-1" aria-hidden="true"><img src="{b['image']}" width="1200" height="630" alt="" loading="lazy"></a>
    <p class="byline"><span class="tag">{html.escape(b['category'])}</span><time datetime="{b['date']}">{nice_date(b['date'])}</time> · {minutes[slug]} min read</p>
    <h2><a href="/blog/{slug}">{html.escape(b['card'])}</a></h2>
    <p>{html.escape(b['excerpt'])}</p>
    <a class="more" href="/blog/{slug}">Read article →</a>
  </article>""")
    body = f"""<h1>The ScreenToast blog</h1>
<p class="lede">Honest comparisons of Mac screen recorders, plain guides to recording your screen, and how to turn a raw take into a demo people actually watch.</p>
<div class="chips" role="toolbar" aria-label="Filter by topic">{''.join(chips)}</div>
<div class="cards">
{chr(10).join(cards)}
</div>
<script>
document.querySelector('.chips').addEventListener('click', function (e) {{
  var c = e.target.closest('.chip'); if (!c) return;
  document.querySelectorAll('.chip').forEach(function (x) {{ x.classList.toggle('on', x === c); }});
  document.querySelectorAll('.card').forEach(function (a) {{ a.hidden = !!c.dataset.cat && a.dataset.cat !== c.dataset.cat; }});
}});
</script>
"""
    meta = {
        "path": "/blog", "wrap": "wrap wide",
        "title": "Mac Screen Recording Guides & Comparisons – ScreenToast",
        "description": "Comparisons of Mac screen recorders, Screen Studio and Loom alternatives, and step-by-step guides to recording your screen on a Mac.",
        "crumbs": [["Blog", None]],
        "schema": [{"@type": "Blog", "name": "The ScreenToast blog", "url": SITE + "/blog", "publisher": PUBLISHER,
                    "blogPost": [{"@type": "BlogPosting", "headline": m["blog"]["card"], "url": f"{SITE}/blog/{s}",
                                  "datePublished": m["blog"]["date"], "image": SITE + m["blog"]["image"]} for s, m in ordered]}],
    }
    return meta, body


def write_sitemap(posts):
    """Keeps the hand-kept part of sitemap.xml and regenerates the blog lines."""
    path = ROOT / "sitemap.xml"
    lines = [l for l in path.read_text().splitlines() if "/blog" not in l]
    newest = max(m["blog"].get("modified", m["blog"]["date"]) for m in posts.values())
    blog = [f"  <url><loc>{SITE}/blog</loc><lastmod>{newest}</lastmod></url>"] + [
        f"  <url><loc>{SITE}/blog/{s}</loc><lastmod>{m['blog'].get('modified', m['blog']['date'])}</lastmod></url>"
        for s, m in sorted(posts.items())]
    end = lines.index("</urlset>")
    path.write_text("\n".join(lines[:end] + blog + lines[end:]) + "\n")


def main():
    sources = {src: read_meta(src) for src in sorted((ROOT / "pages").glob("*.html"))}
    posts = {m["path"].removeprefix("/blog/"): m for m, _ in sources.values() if "blog" in m}
    minutes = {}
    for src, (meta, body) in sources.items():
        out = ROOT / (meta["path"].strip("/") + ".html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build(meta, body, posts))
        if "blog" in meta:
            minutes[meta["path"].removeprefix("/blog/")] = read_minutes(body)
        print(f"{src.name:44} → {out.relative_to(ROOT)}")
    if posts:
        meta, body = blog_index(posts, minutes)
        (ROOT / "blog.html").write_text(build(meta, body, posts))
        write_sitemap(posts)
        print(f"{'(index of ' + str(len(posts)) + ' posts)':44} → blog.html, sitemap.xml")


if __name__ == "__main__":
    main()
