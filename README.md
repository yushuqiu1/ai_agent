# CrewAI Minimal — Two Agents (Summarizer & Q&A)

This project is a **CrewAI assignment implementation** with **three files**:

- `main.py` — all code in one file (agents, tasks, crew, runner)  
- `README.md` — this documentation  
- `requirements.txt` — dependencies  

It demonstrates how to build a **CrewAI system with two agents** that embody a “digital twin lite” persona of a student (Yushu).  

---

## ✨ Design

### Agents
1. **Concise Summarizer**  
   - **Role:** Condenses text into clear, structured bullet points  
   - **Goal:** Produce 5–10 plain-language bullets with short headers  
   - **Persona (backstory):** Yushu’s “digital twin lite” for summarization — concise, action-oriented, preserving key numbers/names  

2. **Practical Q&A Specialist**  
   - **Role:** Answers user questions based on context (or via optional web search)  
   - **Goal:** Provide direct answers, with short explanation + next steps/tips  
   - **Persona (backstory):** Evidence-minded, pragmatic, includes short “how I got this” notes  

### Tasks
- **Summarization Task**  
  - Input: free-form text  
  - Output: Markdown bullets with title, sections, and optional action items  
  - Saved to `summary.md` if `FileWriterTool` is used  

- **Q&A Task**  
  - Input: a user’s question, plus optional context  
  - Output: Direct markdown answer + explanation (+ sources if applicable)  
  - Saved to `answer.md` if `FileWriterTool` is used  

### Crew
- Orchestration mode: **sequential** (summarizer runs before Q&A in demo mode)  
- Agents cannot delegate to each other (each handles its own task directly)  
- Tools:  
  - `FileWriterTool()` (both agents)  
  - `SerperDevTool()` (Q&A agent, only if `SERPER_API_KEY` is set)  

---

## ⚙️ Workflow

1. **Startup:**  
   - User runs `python main.py` and selects a mode (`demo`, `summarize`, or `qa`).  

2. **Agent Creation:**  
   - Summarizer agent is always available.  
   - Q&A agent is created only if `demo` or `qa` mode is chosen.  

3. **Task Assignment:**  
   - Summarization task: created with input text.  
   - Q&A task: created with question + context.  

4. **Crew Execution:**  
   - CrewAI runs tasks sequentially.  
   - Agents generate outputs.  
   - Results are printed to the terminal (and optionally saved to files).  

---

## 🖥️ Modes

### 1. Demo mode
- **Input:** built-in sample about Federated Learning.  
- **Process:**  
  1. Summarizer creates bullets from sample text.  
  2. Q&A agent answers: *“What are the key challenges mentioned?”*  
- **Output:** printed summary + Q&A in terminal, with possible files saved.  

### 2. Summarize mode
- **Input:**  
  - User pastes custom text into terminal (or presses ENTER for a default short sample).  
- **Process:**  
  - Summarizer condenses input into 5–10 bullets.  
- **Output:** printed summary, optionally saved to `summary.md`.  

### 3. QA mode
- **Input:**  
  - User provides a question.  
  - User may optionally paste context text (or leave blank).  
- **Process:**  
  - Q&A agent answers using context; if insufficient and web search is available, it can search.  
- **Output:** printed direct answer + short explanation, optionally saved to `answer.md`.  

---

## 🚀 How to Use

### 1. Set up environment
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set API key
You need an **OpenAI API key**.

#### PowerShell (Windows)
```powershell
$env:OPENAI_API_KEY="sk-your-key-here"
```

#### macOS/Linux
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

*(Optional)* If you want the Q&A agent to use **web search**:
```bash
export SERPER_API_KEY="your-serper-key"
```

### 3. Run the program
```bash
python main.py
```

Choose one of:
- `demo` → run both summarizer + Q&A with a sample text  
- `summarize` → paste your own text for summarization  
- `qa` → ask a question, optionally provide context  

---

## ✅ Test Cases

1. **Demo (default)**  
   ```text
   Choose mode: [demo | summarize | qa]
   demo
   ```
   - Expected: Summary of federated learning, then an answer listing challenges (client heterogeneity, stragglers, privacy, connectivity).  

2. **Summarize custom text**  
   ```
   summarize
   Text: "Harvard's Data Science program combines statistics, machine learning, and computation..."
   ```
   - Expected: 5–10 bullets about program highlights.  

3. **Q&A with context**  
   ```
   qa
   Question: What is the main advantage of AI summarization?
   Context: AI summarization reduces reading time by extracting key points automatically.
   ```
   - Expected: Answer: “The main advantage is efficiency/time-savings.”  

4. **Q&A without context** (SERPER key enabled)  
   ```
   qa
   Question: Who invented federated learning?
   Context: [press ENTER]
   ```
   - Expected: Web search + answer (Google researchers, 2016).  

---

## 🧪 Notes & Tips
- If you get `RateLimitError` or `insufficient_quota`, check your OpenAI **billing/quota**.  
- Default model: CrewAI uses GPT-4 class unless overridden. You can save costs by specifying `gpt-4o-mini` in agent definitions.  
- CrewAI’s logging is verbose: you’ll see task execution steps in your terminal.  

---

## 📂 File Overview

- **main.py** → agents, tasks, crew, runner (all-in-one)  
- **requirements.txt** → dependencies (`crewai`, `crewai-tools`)  
- **README.md** → this documentation  
