#!/usr/bin/env python3
import os
from typing import List, Tuple, Set

# HTTP (Streamable) MCP imports
from mcp.server import FastMCP
import uvicorn  # type: ignore

# --------------------------- Shared song logic ---------------------------
_SONGS: List[Tuple[str, str, Set[str]]] = [
    ("Blinding Lights", "The Weeknd", {"pop", "upbeat", "80s", "night", "energetic", "synth"}),
    ("Nights", "Frank Ocean", {"rnb", "moody", "late", "reflective", "chill"}),
    ("Mr. Brightside", "The Killers", {"rock", "indie", "upbeat", "anthem", "2000s"}),
    ("bad guy", "Billie Eilish", {"pop", "dark", "bass", "quirky"}),
    ("Levitating", "Dua Lipa", {"pop", "dance", "feelgood", "upbeat"}),
    ("Lose Yourself", "Eminem", {"hiphop", "motivational", "intense", "focus"}),
    ("Claire de Lune", "Debussy", {"classical", "piano", "calm", "study", "relax"}),
    ("First Love / Late Spring", "Mitski", {"indie", "melancholy", "dreamy"}),
    ("Adore You", "Harry Styles", {"pop", "warm", "romantic"}),
    ("HUMBLE.", "Kendrick Lamar", {"hiphop", "banger", "confident"}),
    ("Weightless", "Marconi Union", {"ambient", "relax", "sleep", "calm"}),
    ("Heat Waves", "Glass Animals", {"indie", "pop", "nostalgic", "summer"}),
    ("Titanium", "David Guetta ft. Sia", {"edm", "empower", "anthem", "energy"}),
    ("Godspeed", "Frank Ocean", {"rnb", "tender", "slow", "emotional"}),
]

_KEYWORDS = {
    "happy": {"upbeat", "feelgood", "dance", "anthem"},
    "sad": {"melancholy", "tender", "reflective"},
    "chill": {"chill", "calm", "relax", "ambient"},
    "study": {"study", "calm", "piano", "ambient"},
    "focus": {"focus", "intense"},
    "night": {"night", "late"},
    "romance": {"romantic", "tender", "warm"},
    "hype": {"banger", "energy", "energetic", "anthem"},
    "pop": {"pop"},
    "rock": {"rock"},
    "indie": {"indie"},
    "hiphop": {"hiphop"},
    "edm": {"edm"},
    "classical": {"classical", "piano"},
    "rnb": {"rnb"},
    "ambient": {"ambient"},
    "80s": {"80s", "synth"},
    "summer": {"summer", "nostalgic"},
    "dark": {"dark"},
}

def _score_prompt(prompt: str) -> List[Tuple[str, str, int]]:
    p = prompt.lower()
    wanted: Set[str] = set()
    for key, tags in _KEYWORDS.items():
        if key in p:
            wanted |= tags
    # pick up raw tag words (e.g., "ambient", "romantic")
    for word in p.replace(",", " ").replace(".", " ").split():
        if word in {t for _, _, ts in _SONGS for t in ts}:
            wanted.add(word)

    scored: List[Tuple[str, str, int]] = []
    for title, artist, tags in _SONGS:
        score = len(tags & wanted)
        if title.lower() in p:
            score += 3
        if artist.lower() in p:
            score += 2
        scored.append((title, artist, score))
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored

def _recommend_text(prompt: str, limit: int = 3) -> str:
    ranked = _score_prompt(prompt)
    top = [r for r in ranked if r[2] > 0][:limit] or ranked[:1]
    lines = [f'🎵 Song recommendations for: "{prompt}"']
    for i, (title, artist, score) in enumerate(top, 1):
        lines.append(f"{i}. {title} — {artist} (match score {score})")
    return "\n".join(lines)

# --------------------------- HTTP MCP (Streamable) ---------------------------
mcp_http = FastMCP("simple-mcp-server")

@mcp_http.tool()
async def get_greeting(name: str) -> str:
    return f"Hello, {name}! Welcome to the MCP server."

@mcp_http.tool()
async def add_numbers(a: float, b: float) -> str:
    return f"The sum of {a} and {b} is {a + b}"

@mcp_http.tool()
async def recommend_song(prompt: str, limit: int = 3) -> str:
    if not prompt.strip():
        return "Please provide a non-empty prompt."
    return _recommend_text(prompt, limit)

# ASGI app for uvicorn (SSE Streamable HTTP)
app = mcp_http.streamable_http_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
