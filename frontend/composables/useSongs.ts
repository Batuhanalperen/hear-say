// Backend API client.
import type { MaybeRefOrGetter } from "vue";

export type SongMode = "solo" | "full-band";
export type SongStatus = "pending" | "running" | "completed" | "failed";

export interface SongSummary {
  id: number;
  title: string;
  original_filename: string;
  mode: SongMode;
  status: SongStatus;
  current_step: string | null;
  progress_pct: number;
  duration_seconds: number | null;
  created_at: string;
  has_levels: boolean;
}

export interface LevelFiles {
  midi: string;
  musicxml: string | null;
}

export interface SongDetail extends SongSummary {
  error_message: string | null;
  levels: Record<string, LevelFiles>;
  stems: string[];
  updated_at: string;
}

export interface SongStatusResponse {
  id: number;
  status: SongStatus;
  current_step: string | null;
  progress_pct: number;
  error_message: string | null;
}

export function useApiBase(): string {
  const config = useRuntimeConfig();
  return config.public.apiBase;
}

export function useSongList() {
  const api = useApiBase();
  return useFetch<SongSummary[]>("/api/songs", {
    baseURL: api,
    key: "songs-list",
    default: () => [],
  });
}

export function useSongDetail(id: MaybeRefOrGetter<number | string>) {
  const api = useApiBase();
  return useFetch<SongDetail>(() => `/api/songs/${toValue(id)}`, {
    baseURL: api,
    key: () => `song-${toValue(id)}`,
  });
}

export async function fetchSongStatus(id: number): Promise<SongStatusResponse> {
  const api = useApiBase();
  return await $fetch(`/api/songs/${id}/status`, { baseURL: api });
}

export async function uploadSong(params: {
  title: string;
  mode: SongMode;
  file: File;
}): Promise<{ id: number; title: string; status: SongStatus; mode: SongMode }> {
  const api = useApiBase();
  const form = new FormData();
  form.append("title", params.title);
  form.append("mode", params.mode);
  form.append("file", params.file);

  return await $fetch("/api/songs/upload", {
    baseURL: api,
    method: "POST",
    body: form,
  });
}

export async function deleteSong(id: number): Promise<void> {
  const api = useApiBase();
  await $fetch(`/api/songs/${id}`, {
    baseURL: api,
    method: "DELETE",
  });
}

export function levelMidiUrl(songId: number, levelName: string): string {
  return `${useApiBase()}/api/songs/${songId}/files/${levelName}/midi`;
}

export function levelMusicXmlUrl(songId: number, levelName: string): string {
  return `${useApiBase()}/api/songs/${songId}/files/${levelName}/musicxml`;
}

export function originalAudioUrl(songId: number): string {
  return `${useApiBase()}/api/songs/${songId}/audio`;
}

export function stemAudioUrl(songId: number, stemName: string): string {
  return `${useApiBase()}/api/songs/${songId}/stems/${stemName}`;
}
