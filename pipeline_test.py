#!/usr/bin/env python3
"""
AutoClip AI - Patch 0.1 - Pipeline feasibility test (no YouTube needed).

What it proves (all on a free CPU machine):
  1. A LIVE stream (HLS, like real live streams) is being produced in real time.
  2. An "ingest" process reads that live stream into a rolling buffer of small segments.
  3. Audio is cut from the buffer and transcribed by faster-whisper (CPU, int8).
  4. A simple highlight rule picks a moment.
  5. A 9:16 MP4 clip is rendered from the buffer WHILE THE STREAM IS STILL RUNNING.

Run:  python worker/feasibility/pipeline_test.py --model base --out output
"""
import argparse
import json
import os
import platform
import re
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path

SEG_SECONDS = 2        # one buffer segment = 2 seconds
CHUNK_SEGS = 5         # transcribe in 10-second chunks
PRE, POST = 8, 6       # clip = 8s before the highlight, 6s after
BUFFER_SEGS = 20       # rolling buffer keeps ~40 seconds
KEYWORDS = re.compile(r"important|secret|amazing|incredible|surpris|remember|never", re.I)

SPEECH = (
    "Welcome everyone to today's live class. We will start with a quick revision of last week. "
    "Please keep your notebooks ready and follow along carefully. "
    "The topic today is how cells produce energy. Cells use glucose and oxygen to make a molecule called ATP. "
    "This process happens inside the mitochondria. "
    "And now here is the most important secret of this whole chapter. "
    "Almost every question in the exam comes from this one idea. Remember it forever. "
    "Does anyone know why the mitochondria is called the powerhouse of the cell? "
    "We will answer that after a short break. Thank you for joining the stream."
)


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def probe_duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", str(path)]).stdout.strip()
    return float(out)


def make_speech(work, fake):
    wav = work / "speech.wav"
    if fake:  # local self-test only: a tone instead of speech
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=50", str(wav)])
    else:
        run(["espeak-ng", "-s", "150", "-w", str(wav), SPEECH])
    return wav, probe_duration(wav)


class Asr:
    def __init__(self, model_name, fake):
        self.fake = fake
        self.load_time = 0.0
        if not fake:
            from faster_whisper import WhisperModel
            t = time.time()
            self.model = WhisperModel(model_name, device="cpu", compute_type="int8")
            self.load_time = time.time() - t

    def transcribe(self, wav):
        if self.fake:
            return [(0.5, 4.0, "this is the most important secret")]
        segs, _ = self.model.transcribe(str(wav), language="en", beam_size=1, vad_filter=False)
        return [(s.start, s.end, s.text.strip()) for s in segs]


def concat_list(files, path):
    path.write_text("".join(f"file '{Path(f).resolve()}'\n" for f in files))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="base")
    ap.add_argument("--out", default="output")
    ap.add_argument("--fake-asr", action="store_true", help="local self-test without whisper/espeak")
    args = ap.parse_args()

    out = Path(args.out)
    work = Path("work")
    for d in (out, work):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    live, buf = work / "live", work / "buffer"
    live.mkdir()
    buf.mkdir()

    res = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "cpu_count": os.cpu_count(),
           "python": platform.python_version(), "model": args.model, "steps": {}, "errors": []}

    # --- 1. make the fake "livestream" audio and start streaming it in real time
    wav, dur = make_speech(work, args.fake_asr)
    res["speech_seconds"] = round(dur, 1)
    asr = Asr(args.model, args.fake_asr)
    res["model_load_seconds"] = round(asr.load_time, 1)

    src = subprocess.Popen([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-re",
        "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=25", "-i", str(wav),
        "-map", "0:v", "-map", "1:a", "-t", str(dur),
        "-c:v", "libx264", "-preset", "ultrafast", "-g", "50", "-keyint_min", "50",
        "-sc_threshold", "0", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k",
        "-f", "hls", "-hls_time", "2", "-hls_list_size", "6", "-hls_flags", "delete_segments",
        "-hls_segment_filename", str(live / "s%05d.ts"), str(live / "live.m3u8")])
    t0 = time.time()

    for _ in range(60):
        if (live / "live.m3u8").exists() and list(live.glob("s*.ts")):
            break
        time.sleep(0.5)
    else:
        res["errors"].append("live stream never started")
        return finish(res, out, False, src, None)

    # --- 2. ingest: read the live stream into a rolling buffer of 2s segments
    ing = subprocess.Popen([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-live_start_index", "0",
        "-i", str(live / "live.m3u8"), "-c", "copy", "-f", "segment",
        "-segment_time", str(SEG_SECONDS), "-segment_format", "mpegts",
        "-reset_timestamps", "1", str(buf / "seg_%05d.ts")])
    res["steps"]["live_stream_started"] = True

    transcript, highlight, clip_info = [], None, None
    next_chunk, deleted, asr_time, asr_audio = 0, 0, 0.0, 0.0
    deadline = time.time() + dur + 90

    while time.time() < deadline:
        segs = sorted(buf.glob("seg_*.ts"))
        # newest segment may still be written; ignore it while ingest runs
        complete = len(segs) + deleted - (0 if ing.poll() is not None else 1)
        complete = max(complete, 0)

        # --- 3. transcribe every finished 10-second chunk
        while (next_chunk + 1) * CHUNK_SEGS <= complete:
            first = next_chunk * CHUNK_SEGS
            files = [buf / f"seg_{i:05d}.ts" for i in range(first, first + CHUNK_SEGS)]
            if not all(f.exists() for f in files):
                next_chunk += 1
                continue
            concat_list(files, work / "chunk.txt")
            cwav = work / f"chunk_{next_chunk}.wav"
            run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                 "-i", str(work / "chunk.txt"), "-vn", "-ac", "1", "-ar", "16000", str(cwav)])
            t = time.time()
            parts = asr.transcribe(cwav)
            asr_time += time.time() - t
            asr_audio += CHUNK_SEGS * SEG_SECONDS
            base = first * SEG_SECONDS
            for (s, e, text) in parts:
                transcript.append({"start": round(base + s, 1), "end": round(base + e, 1), "text": text})
                hit = KEYWORDS.search(text) or text.endswith("?")
                if hit and highlight is None:
                    highlight = {"time": base + s, "text": text, "found_at_wall": time.time() - t0}
            cwav.unlink(missing_ok=True)
            next_chunk += 1

        # --- 4/5. render the clip once enough "after" context exists
        if highlight and complete * SEG_SECONDS >= highlight["time"] + POST:
            start = max(0.0, highlight["time"] - PRE)
            i0, i1 = int(start // SEG_SECONDS), int((highlight["time"] + POST) // SEG_SECONDS)
            files = [buf / f"seg_{i:05d}.ts" for i in range(i0, i1 + 1)]
            missing = [f.name for f in files if not f.exists()]
            if missing:
                res["errors"].append(f"segments already deleted from buffer: {missing}")
                break
            concat_list(files, work / "clip.txt")
            t = time.time()
            run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                 "-i", str(work / "clip.txt"),
                 "-vf", "crop=ih*9/16:ih,scale=720:1280,setsar=1",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                 "-c:a", "aac", "-movflags", "+faststart", str(out / "clip.mp4")])
            render = time.time() - t
            now = time.time() - t0
            clip_info = {
                "highlight_text": highlight["text"],
                "highlight_stream_time_s": round(highlight["time"], 1),
                "clip_segments": f"{i0}..{i1}",
                "clip_duration_s": round(probe_duration(out / "clip.mp4"), 1),
                "render_seconds": round(render, 1),
                "stream_still_running_when_clip_finished": src.poll() is None,
                "stream_time_elapsed_s": round(now, 1),
                "stream_length_s": round(dur, 1),
                "delay_after_highlight_s": round(now - highlight["time"], 1),
            }
            break

        # rolling buffer: delete segments older than BUFFER_SEGS
        for f in segs:
            idx = int(f.stem.split("_")[1])
            if idx < complete - BUFFER_SEGS:
                f.unlink(missing_ok=True)
                deleted += 1
        if src.poll() is not None and ing.poll() is not None and not highlight and next_chunk * CHUNK_SEGS >= complete:
            break
        time.sleep(1)

    res["steps"]["transcription"] = bool(transcript)
    res["steps"]["highlight_found"] = highlight is not None
    res["steps"]["rolling_buffer_segments_deleted"] = deleted
    res["asr_seconds_per_audio_second"] = round(asr_time / asr_audio, 3) if asr_audio else None
    ok = bool(clip_info and clip_info["stream_still_running_when_clip_finished"]
              and (out / "clip.mp4").exists())
    if highlight is None:
        res["errors"].append("no highlight found (transcript may be inaccurate)")
    (out / "transcript.json").write_text(json.dumps(transcript, indent=2))
    res["clip"] = clip_info
    finish(res, out, ok, src, ing)


def finish(res, out, ok, src, ing):
    for p in (src, ing):
        if p and p.poll() is None:
            p.terminate()
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss + resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    res["peak_memory_mb_approx"] = round(r / 1024)
    res["RESULT"] = "PASS" if ok else "FAIL"
    (out / "results.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
