import axios from "axios";
import type {
  Obligation,
  NettingWindow,
  Summary,
  ParticipantBalance,
  NettingPositionsResponse,
  PaginatedResponse
} from "./types";


const baseURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

export async function getSummary(): Promise<Summary> {
  const res = await api.get<Summary>("/netting-windows/summary/");
  return res.data;
}

export async function getParticipants(): Promise<ParticipantBalance[]> {
  const res = await api.get<PaginatedResponse<ParticipantBalance>>("/participants/");
  return res.data.results;
}


// ----------------- Obligations -----------------
export async function createObligation(payload: Partial<Obligation>): Promise<Obligation> {
  const res = await api.post<Obligation>("/obligations/", payload);
  return res.data;
}

export async function getObligations(params?: {
  page?: number;
  search?: string;
}): Promise<PaginatedResponse<Obligation>> {
  const res = await api.get<PaginatedResponse<Obligation>>("/obligations/", { params });
  return res.data;
}

export async function bulkUploadObligations(
  file?: File,
  json?: string
): Promise<{ created_count: number, errors_count: number }> {
  if (file) {
    const formData = new FormData();
    formData.append("file", file);
    const res  = await api.post(
      "/obligations/bulk/",
      formData,
      { headers: { "Content-Type": "multipart/form-data" }}
    );
    return res.data
  }
  const payload = JSON.parse(json || "[]");
  const res = await api.post("obligations/bulk/", payload);
  return res.data;
}


// --------------- Netting Windows ---------------
export async function getNettingWindows(params?: { page?: number }): Promise <PaginatedResponse<NettingWindow>> {
  const res = await api.get<PaginatedResponse<NettingWindow>>("/netting-windows/", { params });
  return res.data;
}

export async function getNettingWindow(id: number): Promise<NettingWindow> {
  const res = await api.get<NettingWindow>(`/netting-windows/${id}/`);
  return res.data;
}

export async function triggerNetting(file: File): Promise<{ task_id: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post<{ task_id: string }>(
    "/netting-windows/trigger_netting/",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return res.data;
}

export async function getLatestPositions(): Promise<NettingPositionsResponse> {
  const res = await api.get<NettingPositionsResponse>(
    "/netting-windows/positions/", 
    { params: { window: "latest" } }
  );
  return res.data;
}