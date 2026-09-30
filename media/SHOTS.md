# Shot scripts — the seven clips still to record

`README.md` says *what* each clip shows. This file says *how*: every beat, in
order, with timings, where it has to end so it loops, and how to tell a good
take from a bad one. Button and menu names are the app's real ones.

## Ground rules for every clip

- **Launch:** `ScreenToast/Tools/demo-mode.sh` (capture protection off for this
  launch only). Main window at **1600 × 1000** (16:10), centred, nothing else on
  screen, Dock hidden, menu bar clock hidden.
- **One project for everything:** `Onboarding demo.recproj`, a 20–30 s recording
  of a plain web app with **8–10 clicks** in different places (a sidebar item,
  a button, a text field, a tab). Record it once before filming; every clip
  opens it, so the set looks like one product.
- **Pointer:** driven by `Tools/democursor.swift` — eased moves, 0.5–0.9 s per
  move, a 0.3 s settle before every click. Never teleports, never linear.
- **Length:** 6–12 s. **Loop:** the last frame must match the first, or the
  cut back to the top reads as a glitch. Each script names its loop point.
- **No audio.** Clips autoplay muted.
- **Film with the Mac's own recorder** (`screencapture -v`), not a third-party
  one, so any polish on screen is ScreenToast's own.
- **Take check:** extract the first and last frame, and one per second; every
  "Proves" line below must be visible in those stills.

---

## 0 · `hero.mp4` — raw becomes polished (the big window at the top)

**Proves:** the headline — "Turn your screen recording into a product demo.
Automatically." **Length:** 12 s.

| Time | On screen | Pointer |
|---|---|---|
| 0.0–3.0 | Editor, preview playing the **raw** take: no zooms, jittery cursor, no background. Timeline zoom lane empty. | Resting over the Auto Polish panel |
| 3.0 | — | Moves to **Run again**, settles, clicks |
| 3.3–4.0 | Orange zoom blocks drop onto the timeline; background and rounded screen appear in the preview | Drifts off the panel to the right |
| 4.0–10.5 | Preview plays the **polished** take from the top: zoom lands on the first click, cursor calm, click ripple | Still |
| 10.5–12.0 | Playhead returns to 0:00 | Back to the resting spot |

**Loop:** it can't end raw on its own, so it loops by cross-fade: the
polished tail dissolves into the raw opening (`XFADE_CLIPS` includes `hero`).
Reset between takes with ⌘Z (undo Polish), off-camera.
**Bad take:** zoom blocks appear before the click, or the preview is paused.

## 1 · `area-lock.mp4` — an area that stays a publishing shape

**Proves:** press 1–6 mid-drag to snap the selection between shapes. **Length:** 9 s.

| Time | On screen | Pointer / keys |
|---|---|---|
| 0.0–0.8 | Recorder bar, **Area** highlighted | Moves to the canvas top-left |
| 0.8–2.5 | Mouse down, drag out a **16:9** box | Drags diagonally, still holding |
| 2.5 | Box snaps to **9:16** | Presses `2` |
| 4.0 | Box snaps to **1:1** | Presses `3` |
| 5.5 | Box snaps to **4:5** | Presses `4` |
| 7.0 | Box snaps back to **16:9** | Presses `1` |
| 7.0–9.0 | Mouse up; the size readout shows the 16:9 pixels | Releases, holds |

**Loop:** ends on 16:9 at the same size it started. Press **Esc** off-camera,
don't start recording.
**Bad take:** the anchor corner slides when the shape changes. It must stay put.

## 2 · `trim-speed.mp4` — cut it down, speed up the dull part

**Proves:** trim a clip edge; set 2× on a middle section. **Length:** 10 s.

| Time | On screen | Pointer |
|---|---|---|
| 0.0–0.8 | Editor, full timeline, playhead at 0 | Moves to the clip's right edge |
| 0.8–2.3 | Drag the right edge in about 20%; clip shortens | Drags left, releases |
| 2.8 | Playhead to ~⅓ | Clicks the ruler |
| 3.3 | Clip splits | **Split at playhead** |
| 4.3 | Playhead to ~⅔, split again | Clicks the ruler, **Split at playhead** |
| 5.5–7.0 | Middle piece → **Speed → 2×**; it visibly halves in length | Right-clicks the middle piece → **Speed** → **2×** |
| 7.0–10.0 | Timeline shows both edits; timecode total shorter | Rests |

**Loop:** not natural. End on a 1 s hold; `encode.sh` cross-fades the tail
into the opening (`XFADE_CLIPS` includes `trim-speed`).
**Bad take:** the zoom blocks don't move with the trim. They must ripple.

## 3 · `follow-cursor.mp4` — the zoom that keeps up

**Proves:** a held zoom tracks the pointer across the frame. **Length:** 8 s.

Setup (off-camera): add one zoom at 1.8× over a 6 s stretch of the take where
the pointer crosses the screen; select it; turn **Follow the cursor** on.

| Time | On screen | Pointer |
|---|---|---|
| 0.0–0.6 | Preview at the zoom's start, zoomed in on the pointer's left position | Still (on the preview, it's the recording's pointer) |
| 0.6–6.5 | Playback: recorded pointer travels left → right; the zoomed frame follows smoothly | Real pointer stays still off the preview |
| 6.5–8.0 | Zoom eases out to full frame | — |

**Loop:** the recorded pointer must end near where it began. Pick a stretch of
the take that goes out and back, or record a dedicated take for it.
**Bad take:** the frame jerks or lags. This clip exists to sell "keeps up".
**Note:** zoom added by hand; say nothing on the page implying Auto Polish chose it.

## 4 · `cursor-smoothing.mp4` — jittery, then calm

**Proves:** the same pointer path, smoothing off vs on, and clicks still land on
time. **Length:** 10 s.

Setup: needs a take with a **visibly shaky hand**. Record a dedicated 5 s take
with deliberately wobbly, fast mouse moves between 3 clicks.

| Time | On screen | Pointer |
|---|---|---|
| 0.0–0.8 | Auto Polish panel, **Smooth cursor** off | Moves to the toggle |
| 0.8–4.5 | Preview plays: cursor jitters | Rests on the panel |
| 4.5 | **Smooth cursor** on → **Run again** | Clicks both |
| 4.8–9.0 | Same stretch replays: same path, calm; ripples on the same frames | Rests |
| 9.0–10.0 | — | Clicks **Smooth cursor** off to return to the first state |

**Loop:** ends in the "off" state it opened with.
**Bad take:** a click ripple lands away from the smoothed cursor. Clicks are
pinned by design; if one misses, the take (or the build) is wrong.

## 5 · `camera-split.mp4` — the camera goes where the content isn't

**Proves:** the camera bubble moves corner to corner; then a split layout.
**Length:** 11 s. **Needs:** the webcam on and permitted, and a take recorded
with **Camera** on.

| Time | On screen | Pointer |
|---|---|---|
| 0.0–0.6 | Editor, **Camera** tool open, bubble **Bottom Right** | Moves to **Placement** |
| 0.6–4.0 | Bubble → **Top Right** → **Top Left** → **Bottom Left**, animated each time | Picks each from **Placement** |
| 4.5 | Canvas becomes a split: screen + camera | **Split** |
| 5.5–8.0 | **Camera left** → **Camera on top** | Changes the side menu |
| 8.5–11.0 | Back to **Single**, bubble **Bottom Right** | **Single**, **Placement → Bottom Right** |

**Loop:** ends on the opening bubble.
**Bad take:** anything private visible in the camera frame. Check the background.

## 6 · `voiceover.mp4` — the script writes itself, then speaks

**Proves:** a script drafted from what happened in the recording, then spoken.
**Length:** 12 s. **Needs:** an ElevenLabs key in ScreenToast for the spoken
half. Without one, film only to 6.0 s and say "writes the script" on the page,
not "speaks it".

| Time | On screen | Pointer |
|---|---|---|
| 0.0–0.8 | Editor, **Voiceover** tab, empty **SCRIPT** | Moves to the draft button |
| 0.8–1.2 | — | Clicks (tooltip "Draft a script from what happened in the recording") |
| 1.2–6.0 | Script lines appear, timed to the take's clicks | Rests |
| 6.0–7.0 | Voice picked | Picks a voice |
| 7.0 | Audio generates | **Generate Voiceover** |
| 8.0–12.0 | Playback: waveform under the timeline, lines highlight as they're spoken | Rests |

**Loop:** not natural. End on a 1 s hold; cross-faded like `trim-speed`.
**Bad take:** "characters to generate" shows a big number. Keep the script short
(3 lines) so it reads as fast and cheap.

---

## After filming

```sh
XFADE_CLIPS="hero trim-speed voiceover" media/encode.sh ~/Movies/raw
```

1600 wide, H.264, faststart, a poster each, a warning over 2 MB. Clips named
in `XFADE_CLIPS` lose their first 0.4 s (`XFADE=`) to a cross-fade onto the
tail, so a clip that doesn't end where it began still loops without a jump.

Then look at every clip in its row on a local copy of the page (Chrome **and
Safari**), and `npx wrangler deploy` from `website/`.
