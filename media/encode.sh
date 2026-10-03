#!/bin/bash
# Turns raw screen recordings into the eleven clips this page expects.
#
#   media/encode.sh ~/Movies/raw
#
# Looks for <name>.mov or <name>.mp4 in that folder for each slot below, and
# writes <name>.mp4 plus poster-<name>.jpg here. Anything missing is skipped —
# the page falls back to its CSS illustration, so a half-finished set still
# deploys cleanly.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?usage: encode.sh <folder of raw recordings>}"

# The hero loop, then the eleven feature slots in the order they appear.
SLOTS=(hero area-lock camera-split auto-zoom cursor-smoothing follow-cursor
       backgrounds privacy-blur title-cards trim-speed voiceover export)

# 1600 wide is twice the widest a slot is ever displayed, so it stays sharp on
# a Retina screen without paying for a full 4K clip eleven times over.
WIDTH=1600
# CRF 24 lands most 8-second UI clips near 1 MB. UI is flat colour and large
# areas of it do not move, which compresses far better than camera footage.
CRF=24

made=0
skipped=0

for name in "${SLOTS[@]}"; do
    in=""
    for ext in mov mp4 MOV MP4; do
        [[ -f "$SRC/$name.$ext" ]] && { in="$SRC/$name.$ext"; break; }
    done
    if [[ -z "$in" ]]; then
        printf '  ·  %-18s no source\n' "$name"
        skipped=$((skipped + 1))
        continue
    fi

    out="$HERE/$name.mp4"

    # A clip that doesn't end where it began gets a seamless loop: its opening
    # XFADE seconds are cross-faded onto the tail, so the last frame flows into
    # the first. Opt in per clip: XFADE_CLIPS="hero trim-speed voiceover".
    scale="scale=$WIDTH:-2:flags=lanczos"
    vf="$scale"
    if [[ " ${XFADE_CLIPS:-} " == *" $name "* ]]; then
        x="${XFADE:-0.4}"
        d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
        off=$(echo "$d - 2 * $x" | bc -l)
        vf="[0:v]split[a][b];[a]trim=start=$x,setpts=PTS-STARTPTS[body];"
        vf+="[b]trim=end=$x,setpts=PTS-STARTPTS[head];"
        vf+="[body][head]xfade=transition=fade:duration=$x:offset=$off,$scale"
    fi

    # -an: these autoplay muted, so the audio track is pure weight.
    # yuv420p + faststart: what Safari needs to play it at all, and to start
    # before the whole file has arrived.
    ffmpeg -y -loglevel error -i "$in" \
        -an \
        -filter_complex "$vf" \
        -c:v libx264 -crf "$CRF" -preset slow -pix_fmt yuv420p \
        -movflags +faststart \
        "$out"

    # A poster means the row is not empty while the clip loads. Taken a beat
    # in, because frame zero of a screen recording is usually a static window
    # before anything has happened.
    ffmpeg -y -loglevel error -ss 0.6 -i "$out" -frames:v 1 -q:v 4 \
        "$HERE/poster-$name.jpg" 2>/dev/null || true

    size=$(du -h "$out" | cut -f1 | tr -d ' ')
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out" | cut -d. -f1)
    flag=""
    # The page loads all eleven. Two megabytes each is already 22 MB.
    [[ $(stat -f%z "$out") -gt 2097152 ]] && flag="  ← over 2 MB, trim it or drop CRF"
    printf '  ✓  %-18s %5s  %ss%s\n' "$name" "$size" "${dur:-?}" "$flag"
    made=$((made + 1))
done

echo
echo "$made encoded, $skipped still to record."
[[ $made -gt 0 ]] && echo "Total: $(du -ch "$HERE"/*.mp4 2>/dev/null | tail -1 | cut -f1)"
