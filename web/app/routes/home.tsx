import { SearchForm } from "~/components/SearchForm";
import { SearchResults } from "~/components/SearchResults";
import { SiteFooter } from "~/components/SiteFooter";
import { SiteHeader } from "~/components/SiteHeader";
import { PAGE_SIZE, isSortOption, type SortOption } from "~/lib/search";
import { searchDocuments } from "~/lib/search-api";
import type { Route } from "./+types/home";

export function meta({ loaderData }: Route.MetaArgs) {
  const query = loaderData?.query;
  return [
    {
      title: query
        ? `„${query}“ – Grazer Gemeinderat Suche`
        : "Grazer Gemeinderat Suche",
    },
    {
      name: "description",
      content:
        "Durchsuchen Sie Protokolle, Anträge und Beschlüsse des Grazer Gemeinderats nach Stichwort, Datum und Sortierung.",
    },
  ];
}

function parseOffset(value: string | null): number {
  const parsed = Number.parseInt(value ?? "", 10);
  if (!Number.isFinite(parsed) || parsed < 0) {
    return 0;
  }
  return parsed;
}

function parseDate(value: string | null): string {
  if (!value) {
    return "";
  }
  if(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(value))
  {
    return value.slice(0, 10); // Extract the date part from the datetime string
  }

  return /^\d{4}-\d{2}-\d{2}$/.test(value) ? value : "";
}

export async function clientLoader({ request }: Route.ClientLoaderArgs) {
  const url = new URL(request.url);
  const query = url.searchParams.get("q")?.trim() ?? "";
  const sortParam = url.searchParams.get("sort") ?? "relevance";
  const sort: SortOption = isSortOption(sortParam) ? sortParam : "relevance";
  const dateFrom = parseDate(url.searchParams.get("date_from"));
  const dateTo = parseDate(url.searchParams.get("date_to"));
  const meeting = parseDate(url.searchParams.get("meeting"));
  const offset = parseOffset(url.searchParams.get("offset"));

  // A selected meeting narrows the search to that single day, independent of
  // the date_from/date_to range (which only scopes the meeting dropdown).
  const effectiveDateFrom = meeting || dateFrom;
  const effectiveDateTo = meeting || dateTo;
  console.log(url.searchParams);
  console.log({ effectiveDateFrom, effectiveDateTo, meeting });

  const outcome = await searchDocuments({
    query,
    sort,
    dateFrom: effectiveDateFrom || null,
    dateTo: effectiveDateTo || null,
    offset,
  });

  return {
    query,
    sort,
    dateFrom,
    dateTo,
    meeting,
    offset,
    ...outcome,
  };
}

export default function Home({ loaderData }: Route.ComponentProps) {
  const { query, sort, dateFrom, dateTo, meeting, offset, results, total, error } =
    loaderData;
  const hasSearched = query !== "";

  return (
    <div className="flex min-h-screen flex-col bg-emerald-50/40 dark:bg-gray-950">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-emerald-900 focus:shadow-lg"
      >
        Zum Inhalt springen
      </a>

      <SiteHeader
        title="Grazer Gemeinderat Suche"
        description="Durchsuchen Sie Protokolle, Anträge und Beschlüsse des Grazer Gemeinderats."
      />

      <main id="main-content" className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 sm:py-10">
        <SearchForm
          query={query}
          sort={sort}
          dateFrom={dateFrom}
          dateTo={dateTo}
          meeting={meeting}
        />

        <SearchResults
          results={results}
          error={error}
          query={query}
          hasSearched={hasSearched}
          offset={offset}
          total={total}
          pageSize={PAGE_SIZE}
          sort={sort}
          dateFrom={dateFrom}
          dateTo={dateTo}
          meeting={meeting}
        />
      </main>

      <SiteFooter />
    </div>
  );
}
