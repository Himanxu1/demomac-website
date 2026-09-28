# Demo clips

Drop an `.mp4` in here with the exact filename below and it appears in that
feature row automatically — no code change. Until a file exists, the page falls
back to the CSS illustration already built into that row, so the page is never
broken by a missing clip.

**Specs for every clip**

| | |
| --- | --- |
| Container | MP4, H.264 (`-c:v libx264 -pix_fmt yuv420p`) |
| Aspect | 16:10, e.g. 1600 × 1000 |
| Length | 6–12 s, must loop seamlessly |
| Audio | none — these autoplay muted, strip the track |
| Size | aim under 2 MB each; these all load on one page |

Encode with:

```sh
ffmpeg -i raw.mov -an -vf "scale=1600:-2" -c:v libx264 -crf 24 -pix_fmt yuv420p -movflags +faststart auto-zoom.mp4
```

**Filenames, and what each clip needs to show**

| File | Show this |
| --- | --- |
| `auto-zoom.mp4` | A raw recording dropped in, Auto Polish running, zooms appearing on the timeline |
| `cursor-smoothing.mp4` | Before/after of the pointer path — jittery, then calm, with clicks still landing on time |
| `follow-cursor.mp4` | A zoom held while the pointer drags across the frame, camera tracking it |
| `area-lock.mp4` | The area picker: dragging, then pressing 1–6 to switch shape mid-drag |
| `camera-split.mp4` | Camera bubble moving between corners, then the vertical split layout |
| `backgrounds.mp4` | Cycling gradients, a photo background, then a MacBook frame snapping on |
| `privacy-blur.mp4` | Dragging a blur over an email address, then a zoom moving past it while it stays put |
| `voiceover.mp4` | The script drafting itself from the recording, then playing back spoken |
| `title-cards.mp4` | An intro card being typed, then the outro, with the timeline unchanged |
| `trim-speed.mp4` | Dragging a clip edge, then setting a 2× speed on the middle section |
| `export.mp4` | One project exporting to 16:9, then 9:16, then 1:1 |

A `poster-<name>.jpg` next to a clip is used as its first frame if present.
