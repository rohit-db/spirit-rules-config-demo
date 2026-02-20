import { create } from "zustand";
import api from "../api/client";
import type { RuleHeader, RuleLine, AuditEntry } from "../types";

interface Filters {
  status: string;
  cost_category: string;
  search: string;
}

interface RulesState {
  headers: RuleHeader[];
  selectedHeaderId: string | null;
  lines: RuleLine[];
  auditLog: AuditEntry[];
  filters: Filters;
  loading: boolean;
  error: string | null;

  // Actions
  setFilters: (filters: Partial<Filters>) => void;
  fetchHeaders: () => Promise<void>;
  selectHeader: (id: string | null) => Promise<void>;
  createHeader: (data: Partial<RuleHeader>) => Promise<RuleHeader>;
  updateHeader: (id: string, data: Partial<RuleHeader>) => Promise<void>;
  deleteHeader: (id: string) => Promise<void>;
  cloneHeader: (id: string) => Promise<RuleHeader>;
  updateStatus: (id: string, status: string) => Promise<void>;
  createLine: (headerId: string, data: Partial<RuleLine>) => Promise<void>;
  updateLine: (
    headerId: string,
    lineId: string,
    data: Partial<RuleLine>
  ) => Promise<void>;
  deleteLine: (headerId: string, lineId: string) => Promise<void>;
  importCSV: (headerId: string, file: File) => Promise<{ imported: number; errors: { row: number; error: string }[] }>;
  exportCSV: (headerId: string) => Promise<void>;
  fetchLines: (headerId: string) => Promise<void>;
  fetchAudit: (headerId: string) => Promise<void>;
}

export const useRulesStore = create<RulesState>((set, get) => ({
  headers: [],
  selectedHeaderId: null,
  lines: [],
  auditLog: [],
  filters: { status: "", cost_category: "", search: "" },
  loading: false,
  error: null,

  setFilters: (filters) => {
    set((state) => ({
      filters: { ...state.filters, ...filters },
    }));
    // Re-fetch headers with new filters
    get().fetchHeaders();
  },

  fetchHeaders: async () => {
    set({ loading: true, error: null });
    try {
      const { filters } = get();
      const params: Record<string, string> = {};
      if (filters.status) params.status = filters.status;
      if (filters.cost_category) params.cost_category = filters.cost_category;
      if (filters.search) params.search = filters.search;

      const res = await api.get("/rules", { params });
      set({ headers: res.data, loading: false });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to fetch headers";
      set({ error: message, loading: false });
    }
  },

  selectHeader: async (id) => {
    set({ selectedHeaderId: id, lines: [], auditLog: [] });
    if (id) {
      await Promise.all([get().fetchLines(id), get().fetchAudit(id)]);
    }
  },

  fetchLines: async (headerId) => {
    try {
      const res = await api.get(`/rules/${headerId}/lines`);
      set({ lines: res.data });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to fetch lines";
      set({ error: message });
    }
  },

  fetchAudit: async (headerId) => {
    try {
      const res = await api.get(`/rules/${headerId}/audit`);
      set({ auditLog: res.data });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to fetch audit log";
      set({ error: message });
    }
  },

  createHeader: async (data) => {
    const res = await api.post("/rules", data);
    await get().fetchHeaders();
    return res.data;
  },

  updateHeader: async (id, data) => {
    await api.put(`/rules/${id}`, data);
    await get().fetchHeaders();
    // Refresh selected header data if it's the one we updated
    if (get().selectedHeaderId === id) {
      await get().selectHeader(id);
    }
  },

  deleteHeader: async (id) => {
    await api.delete(`/rules/${id}`);
    if (get().selectedHeaderId === id) {
      set({ selectedHeaderId: null, lines: [], auditLog: [] });
    }
    await get().fetchHeaders();
  },

  cloneHeader: async (id) => {
    const res = await api.post(`/rules/${id}/clone`);
    await get().fetchHeaders();
    return res.data;
  },

  updateStatus: async (id, status) => {
    await api.put(`/rules/${id}/status`, { status });
    await get().fetchHeaders();
    if (get().selectedHeaderId === id) {
      await get().selectHeader(id);
    }
  },

  createLine: async (headerId, data) => {
    await api.post(`/rules/${headerId}/lines`, data);
    await get().fetchLines(headerId);
    await get().fetchAudit(headerId);
  },

  updateLine: async (headerId, lineId, data) => {
    await api.put(`/rules/${headerId}/lines/${lineId}`, data);
    await get().fetchLines(headerId);
  },

  deleteLine: async (headerId, lineId) => {
    await api.delete(`/rules/${headerId}/lines/${lineId}`);
    await get().fetchLines(headerId);
    await get().fetchAudit(headerId);
  },

  importCSV: async (headerId, file) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await api.post(`/rules/${headerId}/import`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    await get().fetchLines(headerId);
    await get().fetchAudit(headerId);
    return res.data;
  },

  exportCSV: async (headerId) => {
    const res = await api.get(`/rules/${headerId}/export`, {
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `rule_${headerId}_lines.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
}));
