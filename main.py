#!/usr/bin/env python3
"""
CrewAI Minimal: Two Agents (Summarizer & Q&A) in ONE file.
Non-interactive version: accepts MODE via CLI or env, no input().
"""

import os
import sys
import argparse
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileWriterTool, SerperDevTool

# ---- Agents ----
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

# ---- Tasks ----
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

def main():
    # -------- Args & env --------
    parser = argparse.ArgumentParser(description="CrewAI Minimal (non-interactive)")
    parser.add_argument('mode', nargs='?', default=os.getenv('MODE', 'demo'),
                        choices=['demo', 'summarize', 'qa'],
                        help='Run mode (default: %(default)s)')
    parser.add_argument('--text', default=os.getenv('TEXT', '').strip(),
                        help='Text to summarize (for summarize mode)')
    parser.add_argument('--question', default=os.getenv('QUESTION', '').strip(),
                        help='Question (for qa mode)')
    parser.add_argument('--context', default=os.getenv('CONTEXT', '').strip(),
                        help='Optional context (for qa mode)')
    args = parser.parse_args()

    mode = (args.mode or 'demo').strip().lower()

    if not os.getenv('OPENAI_API_KEY'):
        print('WARNING: OPENAI_API_KEY is not set; set it before running.')

    if mode == 'demo':
        sample_text = ('Federated learning enables clients to train locally and only share model updates. '
                       'FedAvg reduces communication by taking multiple local SGD steps before averaging. '
                       'Benefits: privacy, bandwidth savings, edge compute usage. Challenges: client heterogeneity, '
                       'stragglers, privacy guarantees, unreliable connectivity.')
        summarizer = create_summarizer_agent()
        answerer = create_answer_agent()

        t1 = create_summarize_task(summarizer, sample_text)
        t2 = create_answer_task(answerer, 'What are the key challenges mentioned?', context=sample_text)

        crew = Crew(agents=[summarizer, answerer], tasks=[t1, t2],
                    process=Process.sequential, verbose=True)
        result = crew.kickoff()
        print('\n=== FINAL RESULT (demo) ===\n')
        print(result)
        return

    if mode == 'summarize':
        text = args.text or 'AI systems can summarize text to save time. Key tradeoffs include faithfulness and coverage.'
        agent = create_summarizer_agent()
        task = create_summarize_task(agent, text)
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()
        print('\n=== SUMMARY ===\n')
        print(result)
        return

    if mode == 'qa':
        q = args.question or 'What are the benefits and challenges of federated learning?'
        ctx = args.context
        agent = create_answer_agent()
        task = create_answer_task(agent, q, context=ctx)
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()
        print('\n=== ANSWER ===\n')
        print(result)
        return

if __name__ == '__main__':
    main()
