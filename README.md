# ScreenToast — website

Static. `index.html` is the whole landing page; `privacy.html`, `terms.html`
and `changelog.html` are standalone pages sharing the same tokens.

## What ships here

| File | Why it is here |
|---|---|
| `ScreenToast-0.1.0.dmg` | The download. Notarised and stapled. |
| `appcast.xml` | The Sparkle feed. **Must** be served at the `SUFeedURL` the app was built with — `https://screentoast.com/appcast.xml`. |
| `og.png` | 1200×630 social card. |

## Releasing a new version

1. Bump `VERSION` and `BUILD_NUMBER` in `ScreenToast/build.sh`. Sparkle
   compares `CFBundleVersion`, so `BUILD_NUMBER` must increase or nobody sees
   the update.
2. `DEV_ID="Developer ID Application: …" ./release/package.sh`
3. Copy the new `.dmg` and `appcast.xml` here, delete the old `.dmg`, update
   the two download links in `index.html` and add an entry to
   `changelog.html`.
4. Deploy.

The DMG lives in the repo so one deploy publishes both the site and the
download. If releases get frequent, move the binaries to GitHub Releases and
point `appcast.xml` and the download links there instead — git is a poor place
to keep 7MB blobs forever.
