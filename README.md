# demomac-website

Landing page for [Demomac](https://github.com/Himanxu1) — a native macOS
product-demo studio. Record, polish, narrate, publish.

A single self-contained `index.html`. No build step, no dependencies beyond
Google Fonts.

## Run it

```sh
open index.html
```

Or serve it, if you want to test the video slots with correct MIME types:

```sh
python3 -m http.server 8000
```

## Deploy

Point Vercel (or Netlify, or GitHub Pages) at the repo root. There is nothing
to build — set the framework preset to **Other** and leave the build command
empty.

## Adding the feature clips

Eleven feature rows each have a video slot layered over a CSS illustration.
The video only fades in once the file actually loads, so the page renders
complete while `media/` is empty.

Drop an MP4 into `media/` using the filenames in
[`media/README.md`](media/README.md) and it appears automatically — no code
change. That file also lists what each clip should show and the ffmpeg command
to encode it.

Clips load lazily as they scroll into view, play only while on screen, and are
skipped entirely for visitors who prefer reduced motion.

## Before going live

- [ ] Point the two **Get Demomac** buttons at the Dodo checkout URL
- [ ] Write the Changelog, Support, Privacy and Terms pages
- [ ] Record the eleven feature clips
- [ ] Add an `og:image` for link previews
