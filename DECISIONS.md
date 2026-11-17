# DECISIONS.md — AutoClip AI

## D-001 — Prove the pipeline first with a synthetic live stream (2026-11-17)
- **Decision:** Test ingest→buffer→ASR→clip on a self-generated HLS stream before touching YouTube.
- **Reason:** Separates "can our pipeline work on free CPU" from "can media legally/technically reach the worker".
- **Alternatives:** Test directly on a YouTube stream (too many failure causes at once).
- **Limits:** Does not prove YouTube ingestion.

## D-002 — Use GitHub Actions as the Phase 0 test machine (2026-11-17)
- **Decision:** Run feasibility tests in GitHub Actions, triggered from the phone browser.
- **Reason:** No laptop/Termux needed; free (public repo: standard runners unlimited; private: 2,000 min/month); has FFmpeg, apt, pip.
- **Alternatives:** Hugging Face Spaces (Docker Spaces now need a paid plan per HF docs; free-account behavior reported inconsistent on forums), Termux (rejected by user).
- **Limits:** Jobs are temporary, cannot accept inbound connections, not a production host.

## D-003 — faster-whisper tiny/base (CPU, int8) as first ASR candidate (2026-11-17)
- **Reason:** Open source, CPU-friendly, third-party reports of ~15-20x real-time for tiny/base. We will measure our own number in Test A.
- **Alternatives:** whisper.cpp, small model (slower).
- **Limits:** Free 2-vCPU machines are slower than reported desktop figures; accuracy of tiny is lower.

## D-004 — Authorized input: not decided yet (2026-11-17)
Waiting for Test B and an inbound-stream test (Patch 0.2). Will not pull third-party YouTube streams.
