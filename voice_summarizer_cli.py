#!/usr/bin/env python3
"""
Command-line voice + summarize utilities (CPU only).

Subcommands:
  text2summary2speech  : Text file -> CrewAI summary -> MP3 (Edge TTS)
  speech2summary2text  : Audio file -> Whisper transcript -> CrewAI summary (both .txt)

Requirements:
  pip install openai-whisper edge-tts crewai crewai-tools

Notes:
  - Uses Whisper on CPU (no GPU needed).
  - Uses Edge TTS (no API key).
  - Reuses your CrewAI summarizer agent exactly as provided.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional

# ---------- STT (CPU) ----------
import whisper  # openai-whisper

# ---------- TTS (CPU, no key) ----------
import edge_tts

# ---------- CrewAI (your summarizer) ----------
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileWriterTool

# ==================== Your CrewAI Summarizer (unchanged) ====================

def create_summarizer_agent():
    return Agent(
        role='Concise Summarizer',
        goal=('Distill any provided text into short, well-structured bullet points '
              'with headers and clear takeaways.'),
        backstory=("You are Yushu's digital twin lite for summarization—crisp, plain language, "
                   'and action-oriented. Preserve key numbers and names.'),
        verbose=True,
        allow_delegation=False,
        tools=[FileWriterTool()]
    )

def create_summarize_task(agent, text: str):
    return Task(
        description=('Summarize the following content into crisp bullets grouped by 2–3 short headers. '
                     'Aim for 5–10 bullets; keep language plain.\n\nCONTENT:\n' + text),
        expected_output=('Markdown summary with a title, 5–10 bullets across a few sections, '
                         'and (if relevant) action items. Also save to "summary.md".'),
        agent=agent
    )

def run_crewai_summarizer(raw_text: str) -> str:
    """Run your CrewAI summarizer and return the markdown summary string."""
    agent = create_summarizer_agent()
    task = create_summarize_task(agent, raw_text)
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    result = crew.kickoff()
    # FileWriterTool will also write "summary.md" in the working directory.
    return str(result).strip()

# ==================== STT: audio -> text ====================

def transcribe_audio_to_text(audio_path: str, model_size: str = "small") -> str:
    """
    Transcribe audio to text with Whisper (CPU). Tries pure-Python decode for WAV/FLAC/OGG
    to avoid requiring ffmpeg. Falls back to path/ffmpeg for other formats (e.g., m4a).
    """
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly

    model = whisper.load_model(model_size)  # CPU if no GPU

    ext = Path(audio_path).suffix.lower()
    try:
        # Try python-native read first (works for WAV/FLAC/OGG/AIFF, etc.)
        data, sr = sf.read(audio_path, dtype="float32", always_2d=False)
        if data.ndim == 2:                      # downmix stereo -> mono
            data = data.mean(axis=1)
        if sr != 16000:                         # resample to 16 kHz for Whisper
            data = resample_poly(data, 16000, sr)
        # Pass NumPy directly; this bypasses ffmpeg entirely
        result = model.transcribe(data, fp16=False)
    except Exception:
        # Fallback for formats soundfile can't decode (e.g., .m4a) -> requires ffmpeg
        result = model.transcribe(audio_path, fp16=False)

    return (result.get("text") or "").strip()


# ==================== TTS: text -> mp3 ====================

async def _edge_tts_async(text: str, out_audio_path: str, voice: str):
    communicate = edge_tts.Communicate(text, voice=voice)
    with open(out_audio_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])

def text_to_speech(text: str, out_audio_path: str, voice: str = "en-US-JennyNeural") -> str:
    asyncio.run(_edge_tts_async(text, out_audio_path, voice))
    return out_audio_path

# ==================== CLI pipelines ====================

def cmd_text2summary2speech(args: argparse.Namespace) -> int:
    in_txt = Path(args.input).expanduser()
    if not in_txt.exists():
        print(f"[ERROR] Text file not found: {in_txt}", file=sys.stderr)
        return 1

    raw_text = in_txt.read_text(encoding="utf-8")
    if not raw_text.strip():
        print("[ERROR] Input text is empty.", file=sys.stderr)
        return 1

    print("[1/3] Summarizing text with CrewAI…")
    summary_md = run_crewai_summarizer(raw_text)

    # Also save a local copy of the summary (CrewAI writes summary.md too)
    out_summary = Path(args.summary_out).expanduser()
    out_summary.write_text(summary_md, encoding="utf-8")
    print(f"[2/3] Saved summary markdown to: {out_summary} (CrewAI also wrote summary.md)")

    out_mp3 = Path(args.audio_out).expanduser()
    print("[3/3] Synthesizing speech with Edge TTS…")
    text_to_speech(summary_md, str(out_mp3), voice=args.voice)
    print(f"[DONE] MP3 saved: {out_mp3}")
    return 0

def cmd_speech2summary2text(args: argparse.Namespace) -> int:
    in_audio = Path(args.input).expanduser()
    if not in_audio.exists():
        print(f"[ERROR] Audio file not found: {in_audio}", file=sys.stderr)
        return 1

    print("[1/3] Transcribing audio with Whisper (CPU)…")
    transcript = transcribe_audio_to_text(str(in_audio), model_size=args.model_size)

    out_transcript = Path(args.transcript_out).expanduser()
    out_transcript.write_text(transcript, encoding="utf-8")
    print(f"[2/3] Transcript saved: {out_transcript}")

    print("[3/3] Summarizing transcript with CrewAI…")
    summary_md = run_crewai_summarizer(transcript)
    out_summary = Path(args.summary_out).expanduser()
    out_summary.write_text(summary_md, encoding="utf-8")
    print(f"[DONE] Summary saved: {out_summary} (CrewAI also wrote summary.md)")
    return 0

# ==================== Main / CLI ====================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Voice + Summarize CLI (CPU-only): two pipelines using Whisper + CrewAI + Edge TTS."
    )
    sub = p.add_subparsers(dest="command", required=True)

    # text2summary2speech
    p_t2s = sub.add_parser(
        "text2summary2speech",
        help="Text file -> CrewAI summary -> MP3 (Edge TTS)"
    )
    p_t2s.add_argument("-i", "--input", required=True, help="Path to input text file")
    p_t2s.add_argument("-S", "--summary-out", default="summary.md", help="Where to save summary markdown (default: summary.md)")
    p_t2s.add_argument("-o", "--audio-out", default="summary.mp3", help="Where to save MP3 (default: summary.mp3)")
    p_t2s.add_argument("-v", "--voice", default="en-US-JennyNeural", help="Edge TTS voice (default: en-US-JennyNeural)")
    p_t2s.set_defaults(func=cmd_text2summary2speech)

    # speech2summary2text
    p_s2t = sub.add_parser(
        "speech2summary2text",
        help="Audio file -> Whisper transcript -> CrewAI summary (both saved as .txt/.md)"
    )
    p_s2t.add_argument("-i", "--input", required=True, help="Path to input audio file (.wav/.mp3/…)")
    p_s2t.add_argument("-m", "--model-size", default="small", help="Whisper model size (tiny/base/small/medium/large-v3)")
    p_s2t.add_argument("-t", "--transcript-out", default="transcript.txt", help="Where to save transcript text (default: transcript.txt)")
    p_s2t.add_argument("-S", "--summary-out", default="summary.md", help="Where to save summary markdown (default: summary.md)")
    p_s2t.set_defaults(func=cmd_speech2summary2text)

    return p

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        rc = args.func(args)
    except KeyboardInterrupt:
        print("\n[Interrupted]")
        rc = 130
    sys.exit(rc)

if __name__ == "__main__":
    main()
