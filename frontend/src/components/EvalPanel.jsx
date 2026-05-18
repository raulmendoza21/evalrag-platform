import { useEffect, useState } from "react";
import { listEvalRuns, runEval } from "../api/client.js";

function fmt(v, digits = 3) {
  if (v === null || v === undefined) return "—";
  return Number(v).toFixed(digits);
}

export default function EvalPanel() {
  const [dataset, setDataset] = useState("sample");
  const [k, setK] = useState(5);
  const [judge, setJudge] = useState(true);
  const [busy, setBusy] = useState(false);
  const [run, setRun] = useState(null);
  const [history, setHistory] = useState([]);
  const [err, setErr] = useState(null);

  async function reloadHistory() {
    try {
      setHistory(await listEvalRuns());
    } catch (e) {
      // history may simply be empty — non-fatal
    }
  }

  useEffect(() => {
    reloadHistory();
  }, []);

  async function handleRun(e) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    setRun(null);
    try {
      const res = await runEval({ dataset, k, judge });
      setRun(res);
      reloadHistory();
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold">Evaluation</h2>

      <form onSubmit={handleRun} className="flex flex-wrap items-end gap-3">
        <label className="text-xs">
          <span className="block text-slate-500">Dataset</span>
          <input
            value={dataset}
            onChange={(e) => setDataset(e.target.value)}
            className="mt-1 w-40 rounded border px-2 py-1 text-sm"
          />
        </label>
        <label className="text-xs">
          <span className="block text-slate-500">k</span>
          <input
            type="number"
            min={1}
            max={20}
            value={k}
            onChange={(e) => setK(Number(e.target.value))}
            className="mt-1 w-16 rounded border px-2 py-1 text-sm"
          />
        </label>
        <label className="flex items-center gap-1 text-xs text-slate-600">
          <input
            type="checkbox"
            checked={judge}
            onChange={(e) => setJudge(e.target.checked)}
          />
          LLM judge
        </label>
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {busy ? "Running…" : "Run eval"}
        </button>
      </form>

      {err && <p className="mt-3 text-sm text-red-700">{err}</p>}

      {run && (
        <div className="mt-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Latest run · {run.dataset_name} · n={run.num_items} · k={run.k}
          </h3>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Metric label="recall@k" value={fmt(run.recall_at_k)} />
            <Metric label="MRR@k" value={fmt(run.mrr_at_k)} />
            <Metric label="faithfulness" value={fmt(run.faithfulness)} />
            <Metric label="relevance (1-5)" value={fmt(run.answer_relevance, 2)} />
          </div>

          <details className="mt-3 rounded border">
            <summary className="cursor-pointer px-3 py-2 text-xs text-slate-600">
              Per-item results ({run.items.length})
            </summary>
            <ul className="divide-y">
              {run.items.map((it, i) => (
                <li key={i} className="space-y-1 p-3 text-xs">
                  <p className="font-medium text-slate-900">Q: {it.question}</p>
                  <p className="whitespace-pre-wrap text-slate-700">A: {it.answer}</p>
                  <p className="text-[10px] text-slate-500">
                    recall@k={fmt(it.recall_at_k)} · rr={fmt(it.reciprocal_rank)} ·
                    faith={fmt(it.faithfulness)} · rel={it.answer_relevance ?? "—"} ·
                    {" "}
                    {it.latency_ms} ms
                  </p>
                  {it.judge_rationale && (
                    <p className="text-[10px] italic text-slate-500">
                      judge: {it.judge_rationale}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </details>
        </div>
      )}

      {history.length > 0 && (
        <div className="mt-5">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Past runs
          </h3>
          <table className="w-full text-xs">
            <thead className="text-slate-500">
              <tr>
                <th className="py-1 text-left">when</th>
                <th className="py-1 text-left">dataset</th>
                <th className="py-1 text-right">recall</th>
                <th className="py-1 text-right">MRR</th>
                <th className="py-1 text-right">faith</th>
                <th className="py-1 text-right">rel</th>
              </tr>
            </thead>
            <tbody>
              {history.map((r) => (
                <tr key={r.id} className="border-t">
                  <td className="py-1">{new Date(r.created_at).toLocaleString()}</td>
                  <td className="py-1">{r.dataset_name}</td>
                  <td className="py-1 text-right">{fmt(r.recall_at_k)}</td>
                  <td className="py-1 text-right">{fmt(r.mrr_at_k)}</td>
                  <td className="py-1 text-right">{fmt(r.faithfulness)}</td>
                  <td className="py-1 text-right">{fmt(r.answer_relevance, 2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded border bg-slate-50 px-3 py-2">
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className="text-lg font-semibold tabular-nums">{value}</div>
    </div>
  );
}
