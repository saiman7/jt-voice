export async function fetchHealth() {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error("Backend not reachable");
  return res.json();
}

export async function executeTrade(action) {
  const res = await fetch("/api/trade", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Trade failed");
  }
  return data;
}
