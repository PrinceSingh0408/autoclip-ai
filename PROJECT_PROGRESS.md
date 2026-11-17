# PROJECT_PROGRESS.md — AutoClip AI

_Last updated: 2026-11-17_

## Phase status
| Phase | Name | Status |
|---|---|---|
| 0 | Feasibility & research | **IN PROGRESS** |
| 1 | Project foundation | not started |
| 2 | Frontend | not started |
| 3 | Live ingestion | not started |
| 4 | Live transcription | not started |
| 5 | AI highlight engine | not started |
| 6 | Video clip engine | not started |
| 7 | Database & users | not started |
| 8 | Public beta | not started |
| 9 | Improvements | not started |

## Current patch
**Patch 0.1 — Live pipeline proof of concept** (written, awaiting user test)

## Pending patches (Phase 0)
- 0.1 Pipeline PoC on GitHub Actions (stream → rolling buffer → ASR → clip) + optional YouTube probe
- 0.2 Decide ingest method + free worker host from 0.1 results (inbound-stream test)
- 0.3 Phase 0 sign-off report

## Verified working
Nothing confirmed by the user yet.
(Claude self-test, 2026-11-17, sandbox with a tone instead of speech and a fake recognizer: stream → buffer → 9:16 clip plumbing ran. Real speech recognition NOT yet tested. This is not a user-confirmed result.)

## Not yet implemented
Everything except the Phase 0 test scripts.

## Known bugs / risks
- Free host for an always-on worker not yet identified (HF Spaces Docker now needs paid plan).
- YouTube URL pull from cloud likely blocked (Test B will tell for the user's own stream).
- Rolling-buffer deletion not exercised in the sandbox self-test (highlight came early).

## Next exact action
User runs Patch 0.1 (see response), reports Test A result (PASS/FAIL + numbers) and optionally Test B result.
