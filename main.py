#!/usr/bin/env python3
"""
CrewAI Minimal: Two Agents (Summarizer & Q&A) in ONE file.

- Summarizer agent -> condenses text into crisp bullets.
- Q&A agent -> answers questions using provided context (and optional web search).
- Two tasks orchestrated by a Crew running sequentially.
- Terminal interaction for quick demos.
"""

import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileWriterTool, SerperDevTool

# ---- Environment (expects actual keys set by user) ----
# os.environ['OPENAI_API_KEY'] = 'sk-...'
# os.environ['SERPER_API_KEY'] = '...'(optional for web search)

# ---- Agents ----
def create_summarizer_agent():
    return Agent(
        role='Concise Summarizer',
        goal=(
            'Distill any provided text into short, well-structured bullet points '
            'with headers and clear takeaways.'
        ),
        backstory=(
            'You are Yushu\'s digital twin lite for summarization—crisp, plain language, '
            'and action-oriented. Preserve key numbers and names.'
        ),
        verbose=True,
        allow_delegation=False,
        tools=[FileWriterTool()]
    )

def create_answer_agent():
    tools = [FileWriterTool()]
    # Add web search only if SERPER_API_KEY exists
    if os.getenv('SERPER_API_KEY'):
        tools.append(SerperDevTool())
    return Agent(
        role='Practical Q&A Specialist',
        goal=(
            'Answer questions accurately using provided context first; if insufficient '
            'and search is available, do a brief search and synthesize a reliable answer.'
        ),
        backstory=(
            'A fast, evidence-minded assistant that explains clearly and includes a short '
            '"How I got this" note when helpful.'
        ),
        verbose=True,
        allow_delegation=False,
        tools=tools
    )

# ---- Tasks ----
def create_summarize_task(agent, text):
    return Task(
        description=(
            'Summarize the following content into crisp bullets grouped by 2–3 short headers. '
            'Aim for 5–10 bullets; keep language plain.\n\nCONTENT:\n' + text
        ),
        expected_output=(
            'Markdown summary with a title, 5–10 bullets across a few sections, '
            'and (if relevant) action items. Also save to "summary.md".'
        ),
        agent=agent
    )

def create_answer_task(agent, question, context=''):
    ctx = context.strip() or '(no explicit context provided)'
    return Task(
        description=(
            'Answer the user\'s question using the provided context. '
            'If insufficient and a search tool is available, run a brief search (<=3 queries). '
            'Return a short direct answer, a brief explanation, and tips/next steps if useful.\n\n'
            f'QUESTION: {question}\nCONTEXT: {ctx}'
        ),
        expected_output=(
            'Helpful answer in markdown followed by a short explanation; '
            'mention sources if used. Also save to "answer.md".'
        ),
        agent=agent
    )

# ---- Terminal runner ----
def main():
    print('Choose mode: [demo | summarize | qa]')
    mode = input().strip().lower() or 'demo'

    if mode == 'demo':
        sample_text = (
            'Federated learning enables clients to train locally and only share model updates. '
            'FedAvg reduces communication by taking multiple local SGD steps before averaging. '
            'Benefits: privacy, bandwidth savings, edge compute usage. Challenges: client heterogeneity, '
            'stragglers, privacy guarantees, unreliable connectivity.'
        )
        summarizer = create_summarizer_agent()
        answerer = create_answer_agent()

        t1 = create_summarize_task(summarizer, sample_text)
        t2 = create_answer_task(answerer, 'What are the key challenges mentioned?', context=sample_text)

        crew = Crew(agents=[summarizer, answerer], tasks=[t1, t2], process=Process.sequential, verbose=True)
        result = crew.kickoff()
        print('\n=== FINAL RESULT ===\n')
        print(result)
        return

    if mode == 'summarize':
        print('Paste text to summarize (press ENTER for a short sample):')
        text = input().strip() or 'AI systems can summarize text to save time. Key tradeoffs include faithfulness and coverage.'
        agent = create_summarizer_agent()
        task = create_summarize_task(agent, text)
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()
        print('\n=== SUMMARY ===\n')
        print(result)
        return

    if mode == 'qa':
        print('Enter your question:')
        q = input().strip()
        print('\nOptional context (press ENTER to skip):')
        ctx = input()
        agent = create_answer_agent()
        task = create_answer_task(agent, q, context=ctx)
        crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
        result = crew.kickoff()
        print('\n=== ANSWER ===\n')
        print(result)
        return

    print('Unknown mode. Choose one of: demo | summarize | qa')

if __name__ == '__main__':
    if not os.getenv('OPENAI_API_KEY'):
        print('WARNING: OPENAI_API_KEY is not set; set it before running.')
    main()
