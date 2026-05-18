import { useState } from "react";
import ChatPanel from "./components/ChatPanel.jsx";
import DocumentList from "./components/DocumentList.jsx";
import UploadPanel from "./components/UploadPanel.jsx";

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0);
  const bump = () => setRefreshKey((k) => k + 1);

  return (
    <div className="mx-auto max-w-6xl p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">EvalRAG</h1>
        <p className="text-sm text-slate-500">
          Hybrid retrieval (dense + BM25 · RRF fusion) · grounded answers with mandatory citations
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="space-y-6 md:col-span-1">
          <UploadPanel onUploaded={bump} />
          <DocumentList refreshKey={refreshKey} onChanged={bump} />
        </div>
        <div className="md:col-span-2">
          <ChatPanel />
        </div>
      </div>
    </div>
  );
}
