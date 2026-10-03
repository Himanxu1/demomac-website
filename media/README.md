# The eleven demo clips

Drop an `.mp4` in here with the exact filename below and it appears in that
feature row automatically — no code change. Until a file exists, the row falls
back to the CSS illustration already built into it, so a half-finished set
still deploys cleanly.

## How to record them

**Film ScreenToast with the Mac's own screen recorder.** ScreenToast cannot film itself — a
release build sets `NSWindow.sharingType = .none` specifically to stop screen
recorders, and it does not know your recorder from anyone else's.

```sh
ScreenToast/Tools/demo-mode.sh          # launches it recordable
```

That flag lasts for that launch only. Quit and reopen normally and the app goes
back to being unrecordable.

### The one thing to get right

**Use a recorder with no auto-zoom or cursor smoothing of its own for `auto-zoom.mp4`,
`cursor-smoothing.mp4` and `follow-cursor.mp4`.**

Those three clips exist to show ScreenToast doing exactly those two things.
Film them through a competitor's version of the same effect and the motion a
buyer is watching is not the motion being sold — and it is the first thing they
will check against the app once they download it.

For the other eight, any recorder works.
Those clips are about what is on screen, not how the camera moves.

### Then

```sh
media/encode.sh ~/Movies/raw
```

Looks for `<name>.mov` or `<name>.mp4` per slot, writes `<name>.mp4` and
`poster-<name>.jpg` here, and warns on anything over 2 MB. All eleven load on
one page, so the budget is real.

## The shot list

Each clip: **6–12 s**, 16:10, no audio, and it has to loop — end roughly where
it started, or the cut back to the top reads as a glitch.

| File | The shot | Ends on |
|---|---|---|
| `area-lock.mp4` | Drag an area, then press 1–6 to snap it between 16:9, 9:16, 1:1 mid-drag | The shape you started with |
| `camera-split.mp4` | Camera bubble moved corner to corner, then switched to vertical split | Back to the bubble |
| `auto-zoom.mp4` | Drop a raw recording in; Auto Polish runs; zoom blocks appear on the timeline | Timeline with zooms visible |
| `cursor-smoothing.mp4` | Same pointer path with smoothing off, then on — jittery, then calm, clicks still landing on time | Whichever you opened on |
| `follow-cursor.mp4` | Hold a zoom while the pointer crosses the frame; the view tracks it | Pointer back near where it began |
| `backgrounds.mp4` | Cycle gradients, then a photo, then a device frame snapping on | First gradient again |
| `privacy-blur.mp4` | Drag a blur over an email address, then let a zoom move past while it stays put | Blur still covering it |
| `title-cards.mp4` | An intro card typed in, then the outro — timeline length unchanged | The card on screen |
| `trim-speed.mp4` | Drag a clip edge in, then set 2× on the middle section | Timeline showing both edits |
| `voiceover.mp4` | The script drafting itself from the recording, then playing back spoken | Script visible |
| `export.mp4` | One project exported at 16:9, then 9:16, then 1:1 | Back at 16:9 |

## Specs

| | |
|---|---|
| Container | MP4, H.264, `-pix_fmt yuv420p`, `+faststart` |
| Width | 1600 (twice the widest a slot displays, for Retina) |
| Length | 6–12 s, loops seamlessly |
| Audio | none — they autoplay muted |
| Size | under 2 MB each; eleven of them share one page |

`encode.sh` applies all of this. Encode by hand only if you need to:

```sh
ffmpeg -i raw.mov -an -vf "scale=1600:-2" -c:v libx264 -crf 24 \
  -pix_fmt yuv420p -movflags +faststart auto-zoom.mp4
```

## Worth saying on the page

Once these are real, the line *"every clip on this page was recorded on a Mac
and polished automatically"* is worth more than any feature bullet — provided
it is true. If another recorder's polish is doing the work in the motion clips, do
not write it.
