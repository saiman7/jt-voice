# Voice Trading Agent

Web-based voice trading for **MetaTrader 5**. **React** frontend with continuous browser speech recognition (Google in Chrome/Edge). **FastAPI** backend executes trades on **XAUUSDr** at **0.1** lots.

## MT5 Python API

[MetaTrader 5 Python Integration](https://www.mql5.com/en/docs/python_metatrader5)

## Voice Commands

| Say | Action |
|-----|--------|
| **buy** (also: bye, by, you why) | Open 0.1 lot BUY |
| **sell** (also: sale, cell) | Open 0.1 lot SELL |
| **close** | Close all XAUUSDr positions |

## Prerequisites

1. **MetaTrader 5** running and logged in
2. **Node.js** (for React build)
3. **Python 3.13+** and [uv](https://docs.astral.sh/uv/)
4. **Chrome or Edge** (Web Speech API)

## Setup

**Server machine:**

```bash
uv sync
```

**Frontend machine** (can be the same PC):

```bash
cd frontend
npm install
```

## Run

**Server** (machine with MT5):

```bash
uv run voice-server
```

The API listens on **0.0.0.0:8000** by default. Use `/api/health` or `/docs` to verify — the UI is served separately from `frontend/`.

Server settings (optional, in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Listen port |
| `CORS_ORIGINS` | `*` | Allowed browser origins (comma-separated) |

### Frontend on another machine

On the **server** machine, run `uv run voice-server` and note its LAN IP (e.g. `192.168.1.100`).

On the **client** machine:

```bash
cd frontend
cp .env.example .env
# Edit .env: VITE_API_BASE_URL=http://192.168.1.100:8000
npm install
npm run dev
```

Open the Vite URL shown in the terminal (e.g. **http://192.168.1.50:5173**). API calls go to the server IP from `.env`.

For a production build on the client, set `VITE_API_BASE_URL` before `npm run build`, then serve `frontend/dist/` with any static file server.

### Dev mode (same machine, hot reload UI)

Terminal 1 — backend:

```bash
uv run voice-server
```

Terminal 2 — React dev server:

```bash
cd frontend
npm run dev
```

Open **http://127.0.0.1:5173** (proxies `/api` to backend when `VITE_API_BASE_URL` is unset).

## Project Layout

```
api.py              # FastAPI API (no bundled UI)
trader.py           # MT5 operations
frontend/           # React app (Vite) — run separately
  src/
    hooks/useSpeechRecognition.js
    App.jsx
```

## API

```http
POST /api/trade
{ "action": "buy" | "sell" | "close" }
```
