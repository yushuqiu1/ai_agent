from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource
import asyncio

# Create server instance
server = Server("simple-mcp-server")

# ---------- Tiny in-memory "catalog" + matcher ----------
_SONGS = [
    # (title, artist, tags)
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
    # moods
    "happy": {"upbeat", "feelgood", "dance", "anthem"},
    "sad": {"melancholy", "tender", "reflective"},
    "chill": {"chill", "calm", "relax", "ambient"},
    "study": {"study", "calm", "piano", "ambient"},
    "focus": {"focus", "intense"},
    "night": {"night", "late"},
    "romance": {"romantic", "tender", "warm"},
    "hype": {"banger", "energy", "energetic", "anthem"},
    # genres
    "pop": {"pop"},
    "rock": {"rock"},
    "indie": {"indie"},
    "hiphop": {"hiphop"},
    "edm": {"edm"},
    "classical": {"classical", "piano"},
    "rnb": {"rnb"},
    "ambient": {"ambient"},
    # vibes/eras
    "80s": {"80s", "synth"},
    "summer": {"summer", "nostalgic"},
    "dark": {"dark"},
}

def _score_prompt(prompt: str) -> list[tuple[str, str, int]]:
    p = prompt.lower()
    wanted = set()
    for key, tags in _KEYWORDS.items():
        if key in p:
            wanted |= tags
    # also split raw words to match tags directly
    for word in p.replace(",", " ").replace(".", " ").split():
        if word in {t for _, _, ts in _SONGS for t in ts}:
            wanted.add(word)

    scored = []
    for title, artist, tags in _SONGS:
        score = len(tags & wanted)
        # small bonus for exact title/artist mentions
        if title.lower() in p: score += 3
        if artist.lower() in p: score += 2
        scored.append((title, artist, score))
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored

# -------------------------------------------------------

# Define tools
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_greeting",
            description="Returns a personalized greeting message",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The name to greet"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="add_numbers",
            description="Adds two numbers together",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            }
        ),
        Tool(
            name="recommend_song",
            description="Recommends songs based on a free-text prompt (mood, genre, vibe, era, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Describe what you want (e.g., 'chill night study music, indie/ambient')."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of results (default 3).",
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["prompt"]
            }
        )
    ]

# Implement tool handlers
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_greeting":
        person_name = arguments.get("name", "friend")
        message = f"Hello, {person_name}! Welcome to the MCP server."
        return [TextContent(type="text", text=message)]

    elif name == "add_numbers":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        result = a + b
        return [TextContent(type="text", text=f"The sum of {a} and {b} is {result}")]

    elif name == "recommend_song":
        prompt = (arguments.get("prompt") or "").strip()
        limit = int(arguments.get("limit") or 3)
        if not prompt:
            return [TextContent(type="text", text="Please provide a non-empty prompt.")]

        ranked = _score_prompt(prompt)
        top = [r for r in ranked if r[2] > 0][:limit] or ranked[:1]  # fall back to a single general pick

        lines = [f"🎵 Song recommendations for: \"{prompt}\""]
        for i, (title, artist, score) in enumerate(top, 1):
            lines.append(f"{i}. {title} — {artist} (match score {score})")
        return [TextContent(type="text", text="\n".join(lines))]

    else:
        raise ValueError(f"Unknown tool: {name}")

# Define resources
@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="demo://info",
            name="Server Information",
            mimeType="text/plain",
            description="Information about this MCP server"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "demo://info":
        return """Simple MCP Server

This is a demonstration MCP server with basic functionality:
- get_greeting: Returns a personalized greeting
- add_numbers: Adds two numbers together
- recommend_song: Recommends songs based on a free-text prompt

Built with the Python MCP SDK."""
    else:
        raise ValueError(f"Unknown resource: {uri}")

async def main():
    """Run the server using stdio transport"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
