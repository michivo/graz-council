/**
 * Client-side data access for the Flask search API. The app is built in SPA
 * mode (no SSR), so this fetch runs in the browser, and the API base URL
 * must be a public, build-time Vite env var (`VITE_API_BASE_URL`) rather
 * than a Node-only `process.env` value.
 */
import type { SearchOutcome, SortOption } from "./search";
import { PAGE_SIZE } from "./search";

interface SearchApiResponse {
  query: string;
  count: number;
  results: SearchOutcome["results"];
}

interface SearchApiError {
  error: string;
}

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:5000"
).replace(/\/+$/, "");

export async function searchDocuments(params: {
  query: string;
  sort: SortOption;
  dateFrom: string | null;
  dateTo: string | null;
  offset: number;
}): Promise<SearchOutcome> {
  if (!params.query) {
    return { results: [], count: 0, error: null };
  }

  const url = new URL("/search", API_BASE_URL);
  url.searchParams.set("q", params.query);
  url.searchParams.set("sort", params.sort);
  url.searchParams.set("limit", String(PAGE_SIZE));
  url.searchParams.set("offset", String(params.offset));
  if (params.dateFrom) {
    url.searchParams.set("date_from", params.dateFrom);
  }
  if (params.dateTo) {
    url.searchParams.set("date_to", params.dateTo);
  }

  let response: Response;
  try {
    response = await fetch(url);
  } catch {
    return {
      results: [],
      count: 0,
      error:
        "Die Such-API ist derzeit nicht erreichbar. Bitte versuchen Sie es später erneut.",
    };
  }

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      (payload as SearchApiError | null)?.error ??
      "Die Suche ist fehlgeschlagen. Bitte versuchen Sie es erneut.";
    return { results: [], count: 0, error: message };
  }

  const data = payload as SearchApiResponse;
  return { results: data.results, count: data.count, error: null };
}
