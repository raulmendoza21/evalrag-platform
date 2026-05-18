import { useEffect, useState } from "react";
import { deleteDocument, listDocuments } from "../api/client.js";

export default function DocumentList({ refreshKey, onChanged }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  async function reload() {
    setLoading(true);
    setErr(null);
    try {
      setDocs(await listDocuments());
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    reload();
  }, [refreshKey]);

  async function handleDelete(id) {
    if (!confirm("Delete this document and all its chunks?")) return;
    try {
      await deleteDocument(id);
      onChanged?.();
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    }
  }

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Indexed documents</h2>
        <button
          onClick={reload}
          className="text-xs text-slate-500 hover:text-slate-900"
        >
          Refresh
        </button>
      </div>
      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {err && <p className="text-sm text-red-700">{err}</p>}
      {!loading && docs.length === 0 && (
        <p className="text-sm text-slate-500">No documents yet. Upload one above.</p>
      )}
      <ul className="divide-y">
        {docs.map((d) => (
          <li key={d.id} className="flex items-center justify-between py-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{d.filename}</p>
              <p className="text-xs text-slate-500">
                {d.status} · {d.page_count ?? "?"} pages · {d.chunk_count ?? "?"} chunks
              </p>
            </div>
            <button
              onClick={() => handleDelete(d.id)}
              className="ml-3 text-xs text-red-600 hover:text-red-800"
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
