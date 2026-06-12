import { useCallback, useEffect, useRef, useState } from "react";

const RESTART_DELAY_MS = 350;
const IGNORED_ERRORS = new Set(["no-speech", "aborted", "network"]);

function getSpeechRecognition() {
  return window.SpeechRecognition || window.webkitSpeechRecognition;
}

/**
 * Continuous browser speech recognition without tearing down the React tree.
 * Restarts the engine after Chrome's ~60s session limit or idle timeouts.
 */
export function useSpeechRecognition({ enabled, onFinal, onError }) {
  const [interim, setInterim] = useState("");
  const [listening, setListening] = useState(false);
  const [supported] = useState(() => Boolean(getSpeechRecognition()));

  const enabledRef = useRef(enabled);
  const recognitionRef = useRef(null);
  const restartTimerRef = useRef(null);
  const startingRef = useRef(false);
  const onFinalRef = useRef(onFinal);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onFinalRef.current = onFinal;
  }, [onFinal]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    enabledRef.current = enabled;
  }, [enabled]);

  const clearRestartTimer = useCallback(() => {
    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current);
      restartTimerRef.current = null;
    }
  }, []);

  const scheduleRestart = useCallback(() => {
    if (!enabledRef.current) return;
    clearRestartTimer();
    restartTimerRef.current = setTimeout(() => {
      restartTimerRef.current = null;
      if (!enabledRef.current || !recognitionRef.current || startingRef.current) {
        return;
      }
      startingRef.current = true;
      try {
        recognitionRef.current.start();
      } catch {
        // Already running — safe to ignore.
      } finally {
        startingRef.current = false;
      }
    }, RESTART_DELAY_MS);
  }, [clearRestartTimer]);

  const stopEngine = useCallback(() => {
    clearRestartTimer();
    const recognition = recognitionRef.current;
    if (!recognition) return;

    recognition.onend = null;
    recognition.onerror = null;
    recognition.onresult = null;
    recognition.onstart = null;

    try {
      recognition.stop();
    } catch {
      // Ignore stop errors during teardown.
    }

    recognitionRef.current = null;
    setListening(false);
    setInterim("");
  }, [clearRestartTimer]);

  useEffect(() => {
    if (!enabled || !supported) {
      stopEngine();
      return;
    }

    const SpeechRecognition = getSpeechRecognition();
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setListening(true);
    };

    recognition.onend = () => {
      setListening(false);
      scheduleRestart();
    };

    recognition.onerror = (event) => {
      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        enabledRef.current = false;
        onErrorRef.current?.("Microphone permission denied");
        stopEngine();
        return;
      }

      if (IGNORED_ERRORS.has(event.error)) {
        scheduleRestart();
        return;
      }

      onErrorRef.current?.(`Mic error: ${event.error}`);
      scheduleRestart();
    };

    recognition.onresult = (event) => {
      let interimText = "";
      let finalText = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const text = result[0]?.transcript ?? "";
        if (result.isFinal) {
          finalText += text;
        } else {
          interimText += text;
        }
      }

      setInterim(interimText || finalText);

      if (finalText.trim()) {
        onFinalRef.current?.(finalText.trim());
        setInterim("");
      }
    };

    recognitionRef.current = recognition;
    startingRef.current = true;
    try {
      recognition.start();
    } catch {
      scheduleRestart();
    } finally {
      startingRef.current = false;
    }

    return () => {
      enabledRef.current = false;
      stopEngine();
    };
  }, [enabled, supported, scheduleRestart, stopEngine]);

  return { interim, listening, supported };
}
