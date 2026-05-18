import { useRef, useState } from "react";
import { uploadDocument } from "../api/client.js";

export default function UploadPanel({ onUploaded }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [err, setErr] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setMsg(null);
    setErr(null);
    const file = inputRef.current?.files?.[0];
    if (!file) {
      setErr("Pick a PDF first.");
      return;
    }
    setBusy(true);
    try {
      const data = await uploadDocument(file);
      setMsg(
        data.deduplicated
          ? `Already indexed: ${data.document.filename}`
          : `Indexed: ${data.document.filename}`
      );
      inputRef.current.value = "";
      onUploaded?.();
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg border bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold">Upload PDF</h2>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="block w-full text-sm file:mr-3 file:rounded file:border-0 file:bg-slate-900 file:px-3 file:py-2 file:text-white hover:file:bg-slate-700"
      />
      <button
        type="submit"
        disabled={busy}
        className="mt-3 rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
      >
        {busy ? "Indexing…" : "Index document"}
      </button>
      {msg && <p className="mt-2 text-sm text-emerald-700">{msg}</p>}
      {err && <p className="mt-2 text-sm text-red-700">{err}</p>}
    </form>
  );
}
