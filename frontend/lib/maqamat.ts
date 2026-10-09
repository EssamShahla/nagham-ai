import { api } from "@/lib/api"
import type { MaqamResponse, SongResponse, SongListResponse } from "@/lib/types"

export type MaqamItem = MaqamResponse

export async function fetchMaqamat(
  { search }: { search?: string } = {},
  signal?: AbortSignal,
): Promise<MaqamItem[]> {
  return api<MaqamItem[]>("/maqamat", {
    query: { search },
    signal,
    cache: "no-store",
  })
}

export async function fetchMaqam(id: number, signal?: AbortSignal): Promise<MaqamItem> {
  return api<MaqamItem>(`/maqamat/${id}`, {
    signal,
    cache: "no-store",
  })
}

export async function fetchRelatedSongs(
  maqamId: number,
  signal?: AbortSignal,
): Promise<SongResponse[]> {
  const data = await api<SongListResponse>("/songs", {
    query: { maqam_id: maqamId, page_size: 12 },
    signal,
    cache: "no-store",
  })

  return data.items
}
