#!/usr/bin/env bash
# AutoClip AI - Patch 0.1 - YouTube reachability probe.
# ONLY use with a livestream you own or have permission to use.
# It asks: can a free cloud machine (GitHub Actions) even read this stream?
# It saves at most ~10 seconds of the stream, only to see if bytes arrive.
# Usage: YT_URL="https://www.youtube.com/watch?v=..." bash youtube_probe.sh output
set -u
OUT="${1:-output}"
mkdir -p "$OUT"
REPORT="$OUT/youtube_probe.txt"
: > "$REPORT"
log() { echo "$@" | tee -a "$REPORT"; }

log "== AutoClip AI YouTube probe =="
log "date: $(date -u)"
log "runner public IP type check (cloud datacenter expected)"
log "yt-dlp version: $(yt-dlp --version 2>&1)"
log "node: $(node --version 2>&1)"

log ""
log "-- Step 1: can we read the stream metadata? --"
if yt-dlp --no-playlist --js-runtimes node -j "$YT_URL" > "$OUT/meta.json" 2> "$OUT/meta.err" \
   || yt-dlp --no-playlist -j "$YT_URL" > "$OUT/meta.json" 2> "$OUT/meta.err"; then
  python3 - "$OUT/meta.json" >> "$REPORT" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print("STEP1: OK")
print("title:", d.get("title"))
print("live_status:", d.get("live_status"), "| is_live:", d.get("is_live"))
print("formats offered:", len(d.get("formats", [])))
PY
else
  log "STEP1: FAILED"
  tail -n 5 "$OUT/meta.err" | tee -a "$REPORT"
  log "RESULT: BLOCKED_AT_METADATA"
  exit 0
fi

log ""
log "-- Step 2: do media bytes actually arrive? (max ~45 s) --"
timeout 45 yt-dlp --no-playlist --js-runtimes node -f "worst[height>=240]/worst" \
  --downloader ffmpeg --downloader-args "ffmpeg:-t 10" \
  -o "$OUT/probe.%(ext)s" "$YT_URL" > "$OUT/dl.log" 2>&1
ls -l "$OUT"/probe.* 2>/dev/null | tee -a "$REPORT"
tail -n 6 "$OUT/dl.log" | tee -a "$REPORT"
if ls "$OUT"/probe.* >/dev/null 2>&1 && [ "$(stat -c %s "$OUT"/probe.* | head -1)" -gt 50000 ]; then
  log "RESULT: MEDIA_REACHED_WORKER"
else
  log "RESULT: BLOCKED_AT_MEDIA"
fi
rm -f "$OUT"/probe.*   # never keep the stream data
