import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE || "/api/v1";

export const api = axios.create({ baseURL, timeout: 30000 });

export interface Overview {
  episodes: {
    total: number;
    success: number;
    failed: number;
    success_rate: number;
    imported: number;
    pending: number;
    frames_total: number;
  };
  by_source: Record<string, { total: number; success: number; failed: number; imported: number; frames: number }>;
  jobs_7d: { total: number; success: number; failed: number };
  storage: { raw_gb: number; staging_gb: number; lerobot_gb: number; training_gb: number };
  updated_at: string;
}

export const fetchOverview = () => api.get<Overview>("/overview").then((r) => r.data);
export const fetchFunnel = () => api.get<{ stages: { name: string; label: string; count: number }[] }>("/funnel").then((r) => r.data);
export const fetchSourceDist = () => api.get<{ items: { key: string; total: number; success: number; failed: number }[] }>("/distribution/source").then((r) => r.data);
export const fetchDailyTrend = () => api.get<{ points: { date: string; total: number; success: number; failed: number; imported: number }[] }>("/trend/daily").then((r) => r.data);
export const fetchJobs = (limit = 20) => api.get<{ items: unknown[]; total: number }>(`/jobs?limit=${limit}`).then((r) => r.data);
export const fetchEpisodes = (params: Record<string, string | number | boolean>) =>
  api.get("/episodes", { params }).then((r) => r.data);
export const fetchStorage = () => api.get("/storage").then((r) => r.data);
export const triggerSync = () => api.post("/sync/trigger").then((r) => r.data);
