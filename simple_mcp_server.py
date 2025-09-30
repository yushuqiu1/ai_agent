#!/usr/bin/env python3
import os
import asyncio
from typing import List, Tuple, Set

from mcp.server import Server
from mcp.server.stdio import stdio_server
try:
    # Fast (HTTP) transport pieces. These are optional unless MCP_TRANSPORT=http
    from mcp.server import FastMCP
    import uvicorn  # type: ignore
except Exception:
    FastMCP = None  # type: ignore

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
    lines = [f"🎵 Song recommendations for: \"{prompt}\""]
    for i, (title, artist, score) in enumerate(top, 1):
        lines.append(f"{i}. {title} — {artist} (match score {score})")
    return "\\n".join(lines)

# --------------------------- STDIO (Option A) ---------------------------
stdio_srv = Server("simple-mcp-server")

from mcp.types import Tool, TextContent, Resource  # only for stdio registration

@stdio_srv.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_greeting",
            description="Returns a personalized greeting message",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string", "description": "The name to greet"}},
                "required": ["name"],
            },
        ),
        Tool(
            name="add_numbers",
            description="Adds two numbers together",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        ),
        Tool(
            name="recommend_song",
            description="Recommends songs based on a free-text prompt (mood, genre, vibe, era, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Describe what you want (e.g., 'chill night study music, indie/ambient')."},
                    "limit": {"type": "integer", "description": "Max number of results (default 3).", "minimum": 1, "maximum": 10},
                },
                "required": ["prompt"],
            },
        ),
    ]

@stdio_srv.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_greeting":
        person_name = arguments.get("name", "friend")
        message = f"Hello, {person_name}! Welcome to the MCP server."
        return [TextContent(type="text", text=message)]
    elif name == "add_numbers":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        return [TextContent(type="text", text=f"The sum of {a} and {b} is {a + b}")]
    elif name == "recommend_song":
        prompt = (arguments.get("prompt") or "").strip()
        limit = int(arguments.get("limit") or 3)
        if not prompt:
            return [TextContent(type="text", text="Please provide a non-empty prompt.")]
        return [TextContent(type="text", text=_recommend_text(prompt, limit))]
    else:
        raise ValueError(f"Unknown tool: {name}")

@stdio_srv.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(uri="demo://info", name="Server Information", mimeType="text/plain", description="Information about this MCP server")
    ]

@stdio_srv.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "demo://info":
        return (
            "Simple MCP Server\\n\\n"
            "- get_greeting: Returns a personalized greeting\\n"
            "- add_numbers: Adds two numbers together\\n"
            "- recommend_song: Recommends songs based on a free-text prompt\\n"
            "Built with the Python MCP SDK."
        )
    raise ValueError(f"Unknown resource: {uri}")

# --------------------------- HTTP (Option B) ---------------------------
# We define an HTTP app only if the optional deps are available.
http_app = None
if FastMCP is not None:
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

    # Exportable ASGI app (FastAPI/Starlette) for uvicorn
    http_app = mcp_http.streamable_http_app()

# --------------------------- Entrypoint ---------------------------
async def run_stdio():
    async with stdio_server() as (r, w):
        await stdio_srv.run(r, w, stdio_srv.create_initialization_options())

def run_http():
    if http_app is None:
        raise RuntimeError("HTTP transport requested but FastMCP/uvicorn not available. Install 'uvicorn' and a recent 'mcp'.")
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(http_app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        run_http()
    else:
        asyncio.run(run_stdio())
