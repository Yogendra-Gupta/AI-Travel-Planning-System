# AviationStack MCP - uv configuration

This project now launches AviationStack MCP using the same command verified manually:

```powershell
cd aviationstack-mcp
uv run -m aviationstack_mcp mcp run
```

The application uses `uv` with `aviationstack-mcp` as the working directory:

```text
uv run -m aviationstack_mcp mcp run
```

Run the main application from the project root:

```powershell
streamlit run frontend.py
```

The `aviationstack-mcp` directory must exist beside `frontend.py`, because the MCP client sets it as the subprocess working directory.

Optional `.env` override:

```text
UV_COMMAND=uv
```

The `AVIATIONSTACK_API_KEY` environment variable is passed to the MCP subprocess.
