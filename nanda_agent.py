#!/usr/bin/env python3
"""
CrewAI + NANDA bridge: registers an agent and exposes your summarize/QA logic via NANDA.

How it decides what to do for each inbound message:
1) JSON payload (preferred):
   {"mode":"summarize","text":"..."}  or  {"mode":"qa","question":"...","context":"..."}
2) Command prefixes:
   - "summarize: <text>"
   - "qa: <question> ::: <optional context>"
3) Fallback: demo run.

Env you likely want to set:
- ANTHROPIC_API_KEY (if you use Anthropic models/tools elsewhere)
- OPENAI_API_KEY    (CrewAI/OpenAI if used by your tools)
- DOMAIN_NAME       (e.g., ysqiu.com) to run HTTPS
- CERT_FILE, KEY_FILE (absolute paths to LE certs if HTTPS)
- AGENT_BASE_URL    (optional, e.g. https://ysqiu.com:6001, helps logs/registry)
- REGISTRY_URL      (overridden by registry_url.txt if present)
"""

import os
import json
from typing import Tuple, Optional

from nanda_adapter import NANDA
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileWriterTool, SerperDevTool

# -----------------------
# Your existing agents
# -----------------------
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

def create_answer_agent():
    tools = [FileWriterTool()]
    if os.getenv('SERPER_API_KEY'):
        tools.append(SerperDevTool())
    return Agent(
        role='Practical Q&A Specialist',
        goal=('Answer questions accurately using provided context first; if insufficient '
              'and search is available, do a brief search and synthesize a reliable answer.'),
        backstory=('A fast, evidence-minded assistant that explains clearly and includes a short '
                   '"How I got this" note when helpful.'),
        verbose=True,
        allow_delegation=False,
        tools=tools
    )

def create_summarize_task(agent, text: str):
    return Task(
        description=('Summarize the following content into crisp bullets grouped by 2–3 short headers. '
                     'Aim for 5–10 bullets; keep language plain.\n\nCONTENT:\n' + text),
        expected_output=('Markdown summary with a title, 5–10 bullets across a few sections, '
                         'and (if relevant) action items. Also save to "summary.md".'),
        agent=agent
    )

def create_answer_task(agent, question: str, context: str = ''):
    ctx = context.strip() or '(no explicit context provided)'
    return Task(
        description=('Answer the user\'s question using the provided context. '
                     'If insufficient and a search tool is available, run a brief search (<=3 queries). '
                     'Return a short direct answer, a brief explanation, and tips/next steps if useful.\n\n'
                     f'QUESTION: {question}\nCONTEXT: {ctx}'),
        expected_output=('Helpful answer in markdown followed by a short explanation; '
                         'mention sources if used. Also save to "answer.md".'),
        agent=agent
    )

# -----------------------
# Input parsing helpers
# -----------------------
def _parse_message(msg: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Returns (mode, text_or_question, context)
    mode in {"summarize","qa","demo"}
    """
    msg = (msg or "").strip()
    if not msg:
        return "demo", None, None

    # JSON envelope?
    try:
        data = json.loads(msg)
        mode = (data.get("mode") or "demo").strip().lower()
        if mode == "summarize":
            return "summarize", data.get("text", ""), None
        if mode == "qa":
            return "qa", data.get("question", ""), data.get("context", "")
    except Exception:
        pass

    # Prefixes?
    lower = msg.lower()
    if lower.startswith("summarize:"):
        return "summarize", msg.split(":", 1)[1].strip(), None

    if lower.startswith("qa:"):
        # allow "qa: question ::: context"
        body = msg.split(":", 1)[1].strip()
        if "::: " in body or ":::" in body:
            parts = body.split(":::", 1)
            question = parts[0].strip()
            context = parts[1].strip() if len(parts) > 1 else ""
            return "qa", question, context
        return "qa", body, ""

    # default
    return "demo", None, None

# -----------------------
# Crew “improvement” callable for NANDA
# -----------------------
def crew_improvement(message_text: str) -> str:
    """Maps an inbound message to summarize/qa/demo and returns the result text."""
    try:
        mode, x, ctx = _parse_message(message_text)
        if mode == "summarize":
            text = x or "AI systems can summarize text to save time. Key tradeoffs include faithfulness and coverage."
            agent = create_summarizer_agent()
            task = create_summarize_task(agent, text)
            crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
            return str(crew.kickoff()).strip()

        if mode == "qa":
            question = x or "What are the benefits and challenges of federated learning?"
            agent = create_answer_agent()
            task = create_answer_task(agent, question, context=(ctx or ""))
            crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
            return str(crew.kickoff()).strip()

        # demo mode
        sample_text = ('Federated learning enables clients to train locally and only share model updates. '
                       'FedAvg reduces communication by taking multiple local SGD steps before averaging. '
                       'Benefits: privacy, bandwidth savings, edge compute usage. Challenges: client heterogeneity, '
                       'stragglers, privacy guarantees, unreliable connectivity.')
        summarizer = create_summarizer_agent()
        answerer = create_answer_agent()
        t1 = create_summarize_task(summarizer, sample_text)
        t2 = create_answer_task(answerer, 'What are the key challenges mentioned?', context=sample_text)
        crew = Crew(agents=[summarizer, answerer], tasks=[t1, t2], process=Process.sequential, verbose=True)
        return str(crew.kickoff()).strip()

    except Exception as e:
        return f"Error running crew: {e}"

# -----------------------
# Registry URL helper
# -----------------------
def _read_registry_url() -> str:
    path = os.path.join(os.getcwd(), "registry_url.txt")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                url = f.read().strip()
                if url:
                    print(f"Using registry URL from file: {url}")
                    return url
        except Exception as e:
            print(f"Could not read registry_url.txt: {e}")
    env_url = os.getenv("REGISTRY_URL")
    if env_url:
        print(f"Using registry URL from env: {env_url}")
        return env_url
    default_url = "https://chat.nanda-registry.com"
    print(f"Using default registry URL: {default_url}")
    return default_url

# -----------------------
# Main: start NANDA server & print enrollment link
# -----------------------
def main():
    # Initialize NANDA with your Crew callable
    nanda = NANDA(crew_improvement)

    # Optionally help NANDA form correct public URLs
    base_url = os.getenv("AGENT_BASE_URL")
    if base_url:
        try:
            setattr(nanda, "public_base_url", base_url)
            print(f"AGENT_BASE_URL set: {base_url}")
        except Exception:
            pass

    # Pick HTTP vs HTTPS
    domain = os.getenv("DOMAIN_NAME", "localhost").strip()
    cert_file = os.getenv("CERT_FILE")
    key_file = os.getenv("KEY_FILE")

    print("Starting CrewAI agent (summarize/qa) behind NANDA...")
    if domain != "localhost" and cert_file and key_file:
        print(f"Launching HTTPS API for domain: {domain}")
        print(f"Using certs: cert={cert_file}, key={key_file}")
        # NANDA’s start_server_api usually takes (api_key, domain, cert_file, key_file)
        # If your build expects different params, keep the first two and pass certs by name.
        nanda.start_server_api(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY", ""), domain,
                               cert_file=cert_file, key_file=key_file)
    else:
        if domain != "localhost":
            print("WARNING: DOMAIN_NAME set but CERT_FILE/KEY_FILE missing—starting HTTP dev server instead.")
        nanda.start_server()

    # Enrollment link
    try:
        # Some builds expose nanda.agent_id, others stash it on nanda.bridge
        agent_id = getattr(nanda, "agent_id", None) or getattr(getattr(nanda, "bridge", None), "agent_id", None)
        if agent_id:
            reg = _read_registry_url().rstrip("/")
            print("\n******************************************************")
            print("You can assign your agent using this link")
            print(f"{reg}/landing.html?agentId={agent_id}")
            print("******************************************************\n")
        else:
            print("Agent started (agentId not available to script). Check logs for the link.")
    except Exception as e:
        print(f"Could not print enrollment link: {e}")

if __name__ == "__main__":
    main()
