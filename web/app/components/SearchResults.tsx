import { Link } from "react-router";
import type { SearchResultItem, SortOption } from "~/lib/search";
import { ChevronLeftIcon, ChevronRightIcon } from "./icons";

interface SearchResultsProps {
  results: SearchResultItem[];
  error: string | null;
  query: string;
  hasSearched: boolean;
  offset: number;
  total: number;
  pageSize: number;
  sort: SortOption;
  dateFrom: string;
  dateTo: string;
  meeting: string;
}

function formatDate(isoDate: string): string {
  // document_date values are usually "YYYY-MM-DD" but some indexed entries
  // fall back to a full "YYYY-MM-DD HH:MM:SS" timestamp. Only the date
  // portion is relevant for display.
  const datePart = isoDate.slice(0, 10);
  const parsed = new Date(`${datePart}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) {
    return isoDate;
  }
  return new Intl.DateTimeFormat("de-AT", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(parsed);
}

/**
 * Splits a snippet containing literal `<mark>`/`</mark>` markers (produced
 * by SQLite's FTS5 `snippet()` function) into text nodes so that React
 * renders every other character as plain, escaped text. This highlights
 * matches without using `dangerouslySetInnerHTML`.
 */
function renderSnippet(snippet: string) {
  const tokens = snippet.split(/(<mark>|<\/mark>)/);
  let highlighted = false;

  return tokens.map((token, index) => {
    if (token === "<mark>") {
      highlighted = true;
      return null;
    }
    if (token === "</mark>") {
      highlighted = false;
      return null;
    }
    if (token === "") {
      return null;
    }
    return highlighted ? (
      <mark
        key={index}
        className="rounded bg-amber-200 px-0.5 text-gray-900 dark:bg-amber-400/80 dark:text-gray-950"
      >
        {token}
      </mark>
    ) : (
      <span key={index}>{token}</span>
    );
  });
}

function buildPageLink(params: {
  query: string;
  sort: SortOption;
  dateFrom: string;
  dateTo: string;
  meeting: string;
  offset: number;
}): string {
  const searchParams = new URLSearchParams();
  searchParams.set("q", params.query);
  if (params.sort !== "relevance") {
    searchParams.set("sort", params.sort);
  }
  if (params.dateFrom) {
    searchParams.set("date_from", params.dateFrom);
  }
  if (params.dateTo) {
    searchParams.set("date_to", params.dateTo);
  }
  if (params.meeting) {
    searchParams.set("meeting", params.meeting);
  }
  if (params.offset > 0) {
    searchParams.set("offset", String(params.offset));
  }
  return `/?${searchParams.toString()}`;
}

export function SearchResults({
  results,
  error,
  query,
  hasSearched,
  offset,
  total,
  pageSize,
  sort,
  dateFrom,
  dateTo,
  meeting,
}: SearchResultsProps) {
  if (!hasSearched) {
    return (
      <p className="mt-8 text-center text-gray-600 dark:text-gray-300">
        Geben Sie oben einen Suchbegriff ein, um Protokolle, Anträge und
        Beschlüsse des Grazer Gemeinderats zu durchsuchen.
      </p>
    );
  }

  if (error) {
    return (
      <div
        role="alert"
        className="mt-8 rounded-lg border border-red-300 bg-red-50 p-4 text-red-800 dark:border-red-800 dark:bg-red-950/50 dark:text-red-200"
      >
        {error}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <p role="status" className="mt-8 text-center text-gray-600 dark:text-gray-300">
        Keine Ergebnisse für &bdquo;{query}&ldquo; gefunden.
      </p>
    );
  }

  const from = offset + 1;
  const to = offset + results.length;
  const hasPrevious = offset > 0;
  const hasNext = to < total;
  const currentPage = Math.floor(offset / pageSize) + 1;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <section aria-label="Suchergebnisse" className="mt-8">
      <p role="status" className="mb-4 text-sm text-gray-600 dark:text-gray-300">
        Ergebnisse {from}–{to} von {total} für &bdquo;{query}&ldquo;
      </p>

      <ul className="space-y-4">
        {results.map((result, index) => (
          <li
            key={`${result.filename}-${result.page}-${index}`}
            className="rounded-xl border border-emerald-200 bg-white p-4 shadow-sm transition hover:shadow-md dark:border-emerald-900 dark:bg-emerald-950/30 sm:p-5"
          >
            <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
              <h2 className="text-lg font-semibold text-emerald-900 dark:text-emerald-100">
                {result.document_title}
              </h2>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {formatDate(result.document_date)}
              </span>
            </div>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {result.filename} · Seite {result.page}
            </p>
            <p className="mt-3 leading-relaxed text-gray-800 dark:text-gray-200">
              {renderSnippet(result.snippet)}
            </p>
            <a
              href={result.source_url}
              target="_blank"
              rel="noreferrer noopener"
              className="mt-3 inline-block text-sm font-medium text-emerald-700 underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:text-emerald-400"
            >
              Dokument öffnen (neuer Tab)
            </a>
          </li>
        ))}
      </ul>

      <nav
        aria-label="Seitennavigation"
        className="mt-6 flex items-center justify-between gap-4"
      >
        {hasPrevious ? (
          <Link
            to={buildPageLink({
              query,
              sort,
              dateFrom,
              dateTo,
              meeting,
              offset: Math.max(0, offset - pageSize),
            })}
            className="inline-flex items-center gap-1 rounded-lg border border-emerald-300 px-3 py-2 text-sm font-medium text-emerald-800 hover:bg-emerald-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:border-emerald-800 dark:text-emerald-200 dark:hover:bg-emerald-900/40"
          >
            <ChevronLeftIcon className="h-4 w-4" />
            Zurück
          </Link>
        ) : (
          <span
            aria-disabled="true"
            className="inline-flex cursor-not-allowed items-center gap-1 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-400 dark:border-gray-800 dark:text-gray-600"
          >
            <ChevronLeftIcon className="h-4 w-4" />
            Zurück
          </span>
        )}

        <span className="text-sm text-gray-600 dark:text-gray-300">
          Seite {currentPage} von {totalPages}
        </span>

        {hasNext ? (
          <Link
            to={buildPageLink({
              query,
              sort,
              dateFrom,
              dateTo,
              meeting,
              offset: offset + pageSize,
            })}
            className="inline-flex items-center gap-1 rounded-lg border border-emerald-300 px-3 py-2 text-sm font-medium text-emerald-800 hover:bg-emerald-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:border-emerald-800 dark:text-emerald-200 dark:hover:bg-emerald-900/40"
          >
            Weiter
            <ChevronRightIcon className="h-4 w-4" />
          </Link>
        ) : (
          <span
            aria-disabled="true"
            className="inline-flex cursor-not-allowed items-center gap-1 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-400 dark:border-gray-800 dark:text-gray-600"
          >
            Weiter
            <ChevronRightIcon className="h-4 w-4" />
          </span>
        )}
      </nav>
    </section>
  );
}
