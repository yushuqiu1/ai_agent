# 🎙️ Voice Summarizer CLI — Text & Audio Summarization with Speech I/O

This project provides a **command-line tool** for summarizing both **text files** and **audio recordings**.  
It integrates **CrewAI agents** for summarization, **Whisper** for speech-to-text, and **Edge TTS** for text-to-speech.  
The result: a lightweight workflow where you can feed in text or spoken notes and receive both **concise markdown summaries** and **spoken summaries (mp3)**.

---

## 📂 Project Structure

- `voice_summarizer_cli.py` — CLI tool for summarization pipelines  
- `requirements.txt` — dependencies (CrewAI, Whisper, Edge TTS, audio utils)  
- `sample_input/notes.txt` — example meeting notes (plain text)  
- `sample_input/meeting.wav` — example meeting recording (WAV, 16 kHz mono)  
- `sample_output/summary.md` — example summary output from text/audio  
- `sample_output/summary.mp3` — example spoken summary (Edge TTS)  
- `sample_output/transcript.txt` — transcript generated from audio  

---

## ✨ Features

- **Text → Summary → Speech**  
  - Input: any `.txt` file  
  - Output: `summary.md` + `summary.mp3`  

- **Speech → Transcript → Summary**  
  - Input: any `.wav` (or `.m4a`, `.flac` if ffmpeg is installed)  
  - Output: `transcript.txt` + `summary.md`  

- **CrewAI summarizer agent**  
  - Produces 5–10 clear, plain-language bullets with short headers  
  - Keeps key numbers, names, and action items  

- **Edge TTS**  
  - High-quality neural voice synthesis (`en-US-JennyNeural` default)  
  - Saves summaries as `.mp3` audio files  

---

## ⚙️ Setup

### 1. Create environment
```bash
python -m venv .venv-voice
source .venv-voice/bin/activate   # Windows: .venv-voice\Scripts\activate
pip install -r requirements.txt
```

### 2. Set OpenAI API key  
CrewAI requires an OpenAI API key for summarization.

**PowerShell (Windows):**
```powershell
$env:OPENAI_API_KEY="sk-your-key-here"
```

**macOS/Linux (bash/zsh):**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

---

## 🚀 Usage

### Text → Summary → Speech
Summarize a text file and generate a spoken `.mp3`.

```bash
python voice_summarizer_cli.py text2summary2speech \
    -i sample_input/notes.txt \
    -S sample_output/summary.md \
    -o sample_output/summary.mp3 \
    -v en-US-JennyNeural
```

- Input: `sample_input/notes.txt`  
- Output:  
  - `sample_output/summary.md` (markdown summary)  
  - `sample_output/summary.mp3` (spoken summary)  

---

### Speech → Transcript → Summary
Transcribe audio, summarize the transcript, and save results.

```bash
python voice_summarizer_cli.py speech2summary2text \
    -i sample_input/meeting.wav \
    -t sample_output/transcript.txt \
    -S sample_output/summary.md
```

- Input: `sample_input/meeting.wav` (16 kHz mono WAV recommended)  
- Output:  
  - `sample_output/transcript.txt` (speech-to-text result)  
  - `sample_output/summary.md` (markdown summary)  

---

## ✅ Sample Runs

### Example 1: Text Notes
Input file: [`sample_input/notes.txt`](sample_input/notes.txt)  
Output: [`sample_output/summary.md`](sample_output/summary.md), [`sample_output/summary.mp3`](sample_output/summary.mp3)

### Example 2: Meeting Recording
Input file: [`sample_input/meeting.wav`](sample_input/meeting.wav)  
Output: [`sample_output/transcript.txt`](sample_output/transcript.txt), [`sample_output/summary.md`](sample_output/summary.md)

---

## 🔑 Requirements

See [`requirements.txt`](requirements.txt). Main libraries:
- `crewai>=0.51.0`
- `crewai-tools>=0.13.0`
- `openai-whisper` (STT, CPU-friendly)  
- `edge-tts` (TTS, no API key required)  
- `soundfile`, `scipy`, `numpy` (audio decode + resampling)  

---

## ⚠️ Notes & Tips
- Use `.wav` (16 kHz, mono, PCM) for maximum compatibility without ffmpeg.  
- `.m4a` and `.mp3` also work, but require ffmpeg installed and on PATH.  
- Summarization depends on your OpenAI quota and model availability.  

---

## 🤖 AI Assistance
Approximately **90% of this project was developed with AI assistance** (ChatGPT/GPT-5).  
The developer provided project direction, integration choices, and debugging.  

---
