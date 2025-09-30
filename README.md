# Simple MCP Server — Song Recommender Demo

[![smithery badge](https://smithery.ai/badge/@yushuqiu1/ai_agent_new)](https://smithery.ai/server/@yushuqiu1/ai_agent_new)

This is a **Model Context Protocol (MCP)** server written in Python.  
It exposes three tools over **stdio** for MCP-native clients (e.g., Claude Desktop):

- `get_greeting(name: string)` — return a friendly greeting
- `add_numbers(a: number, b: number)` — add two numbers
- `recommend_song(prompt: string, limit?: integer)` — keyword/vibe-based song recommendations

> Server name: `simple-mcp-server`


## 1) Prerequisites

- Python 3.10+ (3.11 recommended)
- `pip` (or `uv`/`pipx` if you prefer)
- An MCP client (e.g., **Claude Desktop**)


## 2) Install

Create and activate a virtual environment (recommended), then install deps:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```


## 3) Project Layout

```
.
├── simple_mcp_server.py          # your MCP server (the code you shared)
├── requirements.txt   # Python dependencies
|── smitery.YAML / Dockerfile # for smithery deployment
└── README.md          # this file
```


## 4) Run with Claude Desktop (recommended)

1. **Add the MCP server to Claude Desktop config.**  
   Open (or create) your Claude Desktop config file and add an entry like:

   ```json
   {
     "mcpServers": {
       "simple-mcp-server": {
         "command": "python",
         "args": ["<ABSOLUTE_PATH>/simple_mcp_server.py"]
       }
     }
   }
   ```

   - Replace `<ABSOLUTE_PATH>/simple_mcp_server.py` with the full path to your `simple_mcp_server.py`.

2. **Restart Claude Desktop.** It will spawn the server and register the tools automatically.

3. **Test inside Claude.** Try any of these messages:
   - *“Use the `recommend_song` tool with prompt = 'chill ambient study at night' and limit = 3.”*
   - *“Recommend a hype pop banger for a workout.”*
   - *“Call `get_greeting` for Yushu.”*
   - *“Add 41 and 59 with the `add_numbers` tool.”*


## 5) (Optional) Run directly from a terminal

This server speaks MCP over **stdio**, so it’s meant to be launched by an MCP client.  
If you just want to check that it **starts** without errors:

```bash
python server.py
```

It will wait for stdio messages from an MCP client. You can press `Ctrl+C` to exit.


## 6) Tool Schemas (for reference)

### `recommend_song`
- **description:** Recommends songs based on a free-text prompt (mood/genre/vibe/era).
- **input:**
  ```json
  {
    "prompt": "string (required)",
    "limit": 1..10 (optional, default 3)
  }
  ```
- **output:** Text with a small ranked list and match scores.

### `get_greeting`
- **input:** `{ "name": "string" }` → text greeting

### `add_numbers`
- **input:** `{ "a": number, "b": number }` → text with the sum


## 7) Troubleshooting

- **Claude Desktop doesn’t see the server**  
  - Make sure the path in your config is correct and absolute.  
  - Confirm Python can import the `mcp` package: `python -c "import mcp; print(mcp.__version__)"`  
  - Check whether your `simple_mcp_server.py` runs: `python simple_mcp_server.py` (it should block, waiting on stdio).

- **Windows (WSL) path issues**  
  - If your code lives on `D:` but you run through WSL, ensure the path and command are correct.  
  - You can also set the Claude entry to use `wsl`:
    ```json
    {
      "command": "wsl",
      "args": ["bash", "-lc", "python /mnt/d/harvard/fall2025/ai_agent/mcp-time/server.py"]
    }
    ```

- **Virtual environment not picked up**  
  - Point `command` to the venv’s Python:
    - Windows: `"<ABS_PATH>/.venv/Scripts/python.exe"`  
    - macOS/Linux: `"<ABS_PATH>/.venv/bin/python"`


## 8) License

MIT (or your preferred license).

Enjoy building with MCP! 🎶
