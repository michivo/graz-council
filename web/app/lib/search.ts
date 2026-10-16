/**
 * Types and constants shared between the server-only search loader and the
 * client-rendered search UI. Keep this module free of server secrets (such
 * as the API base URL) so it can safely be bundled for the client.
 */

export const PAGE_SIZE = 10;

export type SortOption = "relevance" | "date_asc" | "date_desc";

export const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "relevance", label: "Relevanz" },
  { value: "date_asc", label: "Datum (aufsteigend)" },
  { value: "date_desc", label: "Datum (absteigend)" },
];

export function isSortOption(value: string): value is SortOption {
  return SORT_OPTIONS.some((option) => option.value === value);
}

export interface SearchResultItem {
  filename: string;
  page: number;
  source_url: string;
  document_date: string;
  document_title: string;
  snippet: string;
}

export interface SearchOutcome {
  results: SearchResultItem[];
  count: number;
  total: number;
  error: string | null;
}

export interface CouncilDatesOutcome {
  dates: string[];
  error: string | null;
}
