import { useCallback, useEffect, useRef, useState } from "react";
import { executeTrade, fetchHealth } from "./lib/api.js";
import { parseCommand } from "./lib/commands.js";
import { useSpeechRecognition } from "./hooks/useSpeechRecognition.js";

const COOLDOWN_MS = 2000;

function nowTime() {
  return new Date().toLocaleTimeString();
}

export default function App() {
  const [micOn, setMicOn] = useState(false);
  const [status, setStatus] = useState("Mic off");
  const [transcript, setTranscript] = useState("—");
  const [health, setHealth] = useState({ symbol: "XAUUSDr", lot_size: 0.1 });
  const [logs, setLogs] = useState([]);

  const lastActionAtRef = useRef(0);
  const micOnRef = useRef(false);

  useEffect(() => {
    micOnRef.current = micOn;
  }, [micOn]);

  const addLog = useCallback((message, type = "info") => {
    setLogs((prev) => [{ id: crypto.randomUUID(), time: nowTime(), message, type }, ...prev].slice(0, 50));
  }, []);

  const sendAction = useCallback(
    async (action, source = "voice") => {
      const now = Date.now();
      if (now - lastActionAtRef.current < COOLDOWN_MS) {
        addLog(`Skipped duplicate ${action} (cooldown)`, "warn");
        return;
      }

      addLog(`Sending ${action.toUpperCase()} (${source})...`, "info");
      setStatus(`Executing ${action}...`);

      try {
        const data = await executeTrade(action);
        lastActionAtRef.current = now;
        addLog(data.message, "ok");
      } catch (err) {
        addLog(err.message, "error");
      } finally {
        if (micOnRef.current) setStatus("Listening...");
        else setStatus("Mic off");
      }
    },
    [addLog],
  );

  const handleFinalTranscript = useCallback(
    (text) => {
      setTranscript(text);

      const action = parseCommand(text);
      if (!action) {
        addLog(`No command in: "${text}"`, "warn");
        return;
      }

      addLog(`Heard "${text}" → ${action.toUpperCase()}`, "info");
      sendAction(action, "voice");
    },
    [addLog, sendAction],
  );

  const handleSpeechError = useCallback(
    (message) => {
      addLog(message, "error");
      setMicOn(false);
      setStatus("Mic off");
    },
    [addLog],
  );

  const { interim, listening, supported } = useSpeechRecognition({
    enabled: micOn,
    onFinal: handleFinalTranscript,
    onError: handleSpeechError,
  });

  useEffect(() => {
    fetchHealth()
      .then((data) => {
        setHealth(data);
        addLog(`Connected — ${data.symbol} @ ${data.lot_size} lots`, "ok");
      })
      .catch(() => addLog("Backend not reachable", "error"));
  }, [addLog]);

  useEffect(() => {
    if (micOn && listening) setStatus("Listening...");
    else if (micOn) setStatus("Starting mic...");
    else setStatus("Mic off");
  }, [micOn, listening]);

  const toggleMic = () => {
    if (!supported) {
      addLog("Speech recognition not supported. Use Chrome or Edge.", "error");
      return;
    }
    setMicOn((on) => {
      const next = !on;
      if (next) addLog("Microphone on", "info");
      else addLog("Microphone off", "info");
      return next;
    });
  };

  return (
    <main className="panel">
      <header>
        <h1>Voice Trading Agent</h1>
        <p className="subtitle">
          Symbol <strong>{health.symbol}</strong> · Lot <strong>{health.lot_size}</strong>
        </p>
      </header>

      <section className="mic-section">
        <button
          type="button"
          className={`mic-btn ${micOn ? "active" : ""}`}
          aria-pressed={micOn}
          onClick={toggleMic}
        >
          <span className="mic-icon">🎤</span>
          <span>{micOn ? "Stop listening" : "Start listening"}</span>
        </button>
        <p className="status">{status}</p>
      </section>

      <section className="commands card">
        <h2>Keywords</h2>
        <div className="chips">
          <span className="chip buy">buy</span>
          <span className="chip sell">sell</span>
          <span className="chip close">close</span>
        </div>
        <p className="hint">
          Continuous listening in React. Aliases: bye → buy, sale → sell.
        </p>
      </section>

      <section className="card">
        <h2>Heard</h2>
        <p className="transcript">{interim || transcript}</p>
      </section>

      <section className="card">
        <h2>Activity</h2>
        <ul className="log">
          {logs.map((entry) => (
            <li key={entry.id} className={entry.type}>
              {entry.time} — {entry.message}
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h2>Manual test</h2>
        <div className="manual-btns">
          <button type="button" className="btn buy" onClick={() => sendAction("buy", "button")}>
            Buy
          </button>
          <button type="button" className="btn sell" onClick={() => sendAction("sell", "button")}>
            Sell
          </button>
          <button type="button" className="btn close" onClick={() => sendAction("close", "button")}>
            Close
          </button>
        </div>
      </section>
    </main>
  );
}
