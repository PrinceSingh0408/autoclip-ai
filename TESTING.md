# TESTING.md — AutoClip AI

## Test A — Live pipeline on free CPU (Patch 0.1)
- **Expected:** `RESULT: PASS`; transcript contains the "most important secret" sentence; `clip.mp4` is ~14 s, vertical 720x1280, with audio; `stream_still_running_when_clip_finished: true`.
- **Actual:** _pending user run_
- **Numbers to record:** model, asr_seconds_per_audio_second, render_seconds, delay_after_highlight_s, peak_memory_mb_approx

## Test B — YouTube reachability from a free cloud runner (Patch 0.1, optional)
- **Expected outcomes:** MEDIA_REACHED_WORKER / BLOCKED_AT_MEDIA / BLOCKED_AT_METADATA
- **Actual:** _pending user run_

## Claude sandbox self-test (not a user test)
- 2026-11-17: tone audio + fake ASR → PASS for plumbing only (stream, buffer, 9:16 render). Real speech ASR and rolling-buffer deletion not exercised.

## Failed tests / fixed issues / remaining issues
None recorded.
