import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const tenant = import.meta.env.VITE_TENANT || "default";

export const api = axios.create({
  baseURL,
  headers: { "X-Tenant": tenant },
  timeout: 60000,
});

export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post("/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function listDocuments() {
  const res = await api.get("/documents");
  return res.data;
}

export async function deleteDocument(id) {
  await api.delete(`/documents/${id}`);
}

export async function chat(query, topK = 5) {
  const res = await api.post("/chat", { query, top_k: topK });
  return res.data;
}
