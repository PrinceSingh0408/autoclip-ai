# PROJECT_MEMORY.md — AutoClip AI

_Last updated: 2026-11-17 (Patch 0.1)_

## Vision
Public, responsive web app. User connects an **authorized** livestream; AI finds interesting moments and produces downloadable short MP4 clips (9:16 option, subtitles, titles) **while the stream is still live**.

## Permanent constraints (never forget)
- Developer: Android phone only. Acode/Spck + GitHub + browser. Beginner level. Avoid Termux.
- Budget: Rs 0. Free/open-source only. No paid APIs/servers/subscriptions without explicit approval.
- Never promise unlimited processing, 24/7 uptime or unlimited users on free infrastructure.
- Only process media the user owns or has permission for. Never bypass access controls, DRM or platform restrictions.
- Never show a fake LIVE status. Never mark a feature "done" until a test confirms it.
- Patch-based work: one small testable patch at a time, wait for user's result before next.
- No secret keys in frontend code. Don't store user videos indefinitely.
- These repo files are the project memory; Claude's built-in memory is NOT a substitute.

## Technical direction (provisional — see DECISIONS.md)
Frontend: HTML/CSS/JS (Vercel). Backend: Python FastAPI. Media: FFmpeg. ASR: faster-whisper (CPU, int8). Highlights: Python scoring. DB/Auth: Supabase. Worker must be movable to a better server.

## Key Phase 0 findings (researched 2026-11-17)
1. A YouTube watch URL gives no authorized raw media. YouTube blocks datacenter IPs for downloads (seen in yt-dlp and other projects' issue trackers in 2026), and a yt-dlp maintainer said YouTube is deprecating DASH/HLS live support. Pulling a YouTube stream from a free cloud machine is therefore unreliable and may violate YouTube terms for streams that aren't the user's own.
2. Hugging Face docs now say Docker and Gradio Spaces need a paid plan to create (PRO); only Static Spaces are free (plus 2 ZeroGPU Gradio Spaces). Free CPU Basic = 2 vCPU/16 GB, non-persistent disk, sleeps when idle, only ports 80/443/8080 outbound. **HF Spaces is NOT confirmed usable for a Rs 0 worker.**
3. GitHub Actions: free for public repos on standard runners; 2,000 min/month for private. Good for batch tests, not for a public always-on worker.
4. faster-whisper tiny/base on CPU int8 is reported ~15-20x real-time on modern CPUs (third-party figures; we measure ourselves in Test A).

## Current status
Phase 0, Patch 0.1 written, **not yet run by the user**. See PROJECT_PROGRESS.md.
