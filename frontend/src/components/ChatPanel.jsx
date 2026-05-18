import { useState } from "react";
import { chat } from "../api/client.js";

export default function ChatPanel() {
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);

  async function handleAsk(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setBusy(true);
    setErr(null);
    setResult(null);
    try {
      setResult(await chat(query.trim(), 5));
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally {
      setBusy(false);
    }
  }

  const citedIds = new Set((result?.citations || []).map((c) => c.chunk_id));

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold">Ask your documents</h2>
      <form onSubmit={handleAsk} className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="What does the report say about Q3 revenue?"
          className="flex-1 rounded border px-3 py-2 text-sm focus:border-emerald-600 focus:outline-none"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {busy ? "Thinking…" : "Ask"}
        </button>
      </form>

      {err && <p className="mt-3 text-sm text-red-700">{err}</p>}

      {result && (
        <div className="mt-4 space-y-4">
          <div className="rounded border bg-slate-50 p-3">
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{result.answer}</p>
            <p className="mt-2 text-xs text-slate-500">
              {result.latency_ms} ms · {result.retrieved.length} chunks retrieved ·{" "}
              {result.citations.length} cited
            </p>
          </div>

          {result.citations.length > 0 && (
            <div>
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Citations
              </h3>
              <ul className="space-y-1 text-xs">
                {result.citations.map((c) => (
                  <li key={c.chunk_id} className="font-mono">
                    doc <span className="text-slate-500">{c.document_id.slice(0, 8)}…</span>{" "}
                    page <span className="font-semibold">{c.page}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <details className="rounded border bg-white">
            <summary className="cursor-pointer px-3 py-2 text-xs text-slate-600">
              Retrieved chunks ({result.retrieved.length})
            </summary>
            <ul className="divide-y">
              {result.retrieved.map((r) => (
                <li
                  key={r.chunk_id}
                  className={`p-3 text-xs ${
                    citedIds.has(r.chunk_id) ? "bg-emerald-50" : ""
                  }`}
                >
                  <div className="mb-1 flex flex-wrap gap-2 text-[10px] text-slate-500">
                    <span>page {r.page}</span>
                    <span>score {r.score.toFixed(4)}</span>
                    <span>[{r.sources.join("+")}]</span>
                    {citedIds.has(r.chunk_id) && (
                      <span className="font-semibold text-emerald-700">cited</span>
                    )}
                  </div>
                  <p className="whitespace-pre-wrap text-slate-700">{r.text}</p>
                </li>
              ))}
            </ul>
          </details>
        </div>
      )}
    </div>
  );
}
