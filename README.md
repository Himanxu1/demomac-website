# ScreenToast — website

Static. `index.html` is the whole landing page; `privacy.html`, `terms.html`
and `changelog.html` are standalone pages sharing the same tokens.

## Content pages (SEO)

The comparison, feature and guide pages, plus `404.html`, are generated from
`pages/*.html` by `pages/build.py`, which adds the shared head, header, footer,
canonical URL, social tags and breadcrumbs. Edit the source in `pages/`, then:

```sh
python3 pages/build.py
```

The output (`features/*.html`, `guides/*.html`,
`404.html`) is committed, so deploying still needs no build step. Add any new
page's URL to `sitemap.xml`. Every claim about the app is checked against the
code, and every claim about a competitor carries the date it was checked.

## What ships here

| File | Why it is here |
|---|---|
| `ScreenToast-0.2.2.dmg` | The download (9.8 MB). Notarised and stapled. |
| `appcast.xml` | The Sparkle feed. **Must** be served at the `SUFeedURL` the app was built with — `https://screentoast.com/appcast.xml`. |
| `og.png` | 1200×630 social card. |

## Hosting — Cloudflare Workers (static assets)

DNS and hosting are both on Cloudflare. The site is the `screentoast-site`
Worker: this folder as static assets, plus `worker/index.js` for the few
`/api/` routes (launch seats, feature requests). Config is `wrangler.jsonc`.
**Pushing to git does not deploy** — deploy from this folder with:

```sh
wrangler deploy
```

Feature requests live in the `screentoast-requests` D1 database. Schema
changes go in `worker/migrations/` and are applied with
`wrangler d1 migrations apply screentoast-requests --remote`.

`.assetsignore` keeps `.git` and other local files out of the upload.

`_headers` keeps `appcast.xml` fresh and the DMG immutable. On a host that
does not read it, the update feed will be served stale.

## Releasing a new version

1. Bump `VERSION` and `BUILD_NUMBER` in `ScreenToast/build.sh`. Sparkle
   compares `CFBundleVersion`, so `BUILD_NUMBER` must increase or nobody sees
   the update.
2. `DEV_ID="Developer ID Application: …" ./release/package.sh`
3. Copy the new `.dmg` and `appcast.xml` here, delete the old `.dmg`, update
   the download links in `index.html` and `DMG` in `pages/build.py` (then run
   it), and add an entry to `changelog.html`.
4. Deploy (see Hosting above).

The DMG lives in the repo so one deploy publishes both the site and the
download. If releases get frequent, move the binaries to GitHub Releases and
point `appcast.xml` and the download links there instead — git is a poor place
to keep 10 MB blobs forever.

## Telling search engines about new pages

Google: the sitemap is submitted in Search Console (property
`https://screentoast.com/`, verified by the meta tag in `index.html`, so keep
it). New URLs in `sitemap.xml` are picked up on Google's next read.

Bing, Yandex and other IndexNow engines: after deploying new or changed pages,
push every sitemap URL. The key file `266b504e4c928e79cc00f7fef06e77b8.txt`
must stay at the site root.

```sh
python3 -c "import re,json;print(json.dumps({'host':'screentoast.com','key':'266b504e4c928e79cc00f7fef06e77b8','urlList':re.findall(r'<loc>(.*?)</loc>',open('sitemap.xml').read())}))" \
  | curl -s -X POST https://api.indexnow.org/indexnow -H 'Content-Type: application/json' --data @-
```
