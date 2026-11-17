# ARCHITECTURE.md — AutoClip AI

_Provisional (Phase 0). Updated 2026-11-17._

## Target data flow
AUTHORIZED INPUT → INGEST → ROLLING BUFFER (2 s segments) → AUDIO EXTRACT → ASR → HIGHLIGHT SCORING → CLIP BOUNDARIES → FFMPEG RENDER (+subtitles, 9:16) → MP4 → DASHBOARD

## Authorized input options (candidates)
| Option | Needs inbound server? | Status |
|---|---|---|
| A. User's streaming app sends a second copy (RTMP/SRT) to our worker | Yes (open TCP/UDP port) | To verify — free hosts rarely allow it |
| B. Browser/phone capture sent over HTTPS/WebSocket to worker | No (port 443 OK) | Candidate, to test in 0.2 |
| C. Worker pulls the user's own YouTube stream | No | Test B checks; likely blocked from datacenter IPs |
| D. Upload recording (secondary feature) | No | Later phase |

## Frontend / Backend / DB / API / Worker
Not built yet. Planned: `frontend/` (static, Vercel), `backend/` (FastAPI), `worker/` (ingest, buffer, asr, highlights, render modules), Supabase for auth/jobs.

## Phase 0 code
- `worker/feasibility/pipeline_test.py` — generates a real-time HLS "livestream" (speech by espeak-ng), ingests into rolling buffer, transcribes 10 s chunks with faster-whisper, picks a highlight by keyword/question, renders a 9:16 MP4 while the stream still runs.
- `worker/feasibility/youtube_probe.sh` — checks if a free cloud runner can read an owned YouTube stream.

## External dependencies
FFmpeg, faster-whisper (CTranslate2), espeak-ng (tests only), yt-dlp (probe only).
