import { useState } from "react";
import { Form } from "react-router";
import { SORT_OPTIONS, type SortOption } from "~/lib/search";
import { SearchIcon } from "./icons";
import { MeetingFilter } from "./MeetingFilter";

interface SearchFormProps {
  query: string;
  sort: SortOption;
  dateFrom: string;
  dateTo: string;
}

export function SearchForm({ query, sort, dateFrom, dateTo }: SearchFormProps) {
  const [currentDateFrom, setCurrentDateFrom] = useState(dateFrom);
  const [currentDateTo, setCurrentDateTo] = useState(dateTo);
  const hasFilters = sort !== "relevance" || dateFrom !== "" || dateTo !== "";

  return (
    <Form method="get" role="search" aria-label="Dokumentensuche" className="space-y-4">
      <div>
        <label
          htmlFor="q"
          className="mb-1 block text-sm font-medium text-emerald-950 dark:text-emerald-100"
        >
          Suchbegriff
        </label>
        <div className="flex flex-col gap-2 sm:flex-row">
          <div className="relative flex-1">
            <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-emerald-700 dark:text-emerald-400" />
            <input
              id="q"
              name="q"
              type="search"
              required
              defaultValue={query}
              placeholder="z. B. Radweg, Budget, Murkraftwerk"
              autoComplete="off"
              className="w-full rounded-lg border border-emerald-300 bg-white py-2.5 pl-10 pr-3 text-base text-gray-900 shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-50"
            />
          </div>
          <button
            type="submit"
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-700 px-5 py-2.5 text-base font-semibold text-white shadow-sm transition hover:bg-emerald-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:bg-emerald-600 dark:hover:bg-emerald-500"
          >
            <SearchIcon className="h-5 w-5" />
            Suchen
          </button>
        </div>
      </div>

      <details className="group rounded-lg border border-emerald-200 bg-emerald-50/60 px-4 py-3 dark:border-emerald-800 dark:bg-emerald-950/40" open={hasFilters}>
        <summary className="cursor-pointer select-none text-sm font-medium text-emerald-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:text-emerald-200">
          Erweiterte Suche (Sortierung &amp; Zeitraum)
        </summary>
        <fieldset className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <legend className="sr-only">Sortierung und Zeitraum eingrenzen</legend>
          <div>
            <label
              htmlFor="sort"
              className="mb-1 block text-sm font-medium text-emerald-950 dark:text-emerald-100"
            >
              Sortierung
            </label>
            <select
              id="sort"
              name="sort"
              defaultValue={sort}
              className="w-full rounded-lg border border-emerald-300 bg-white px-3 py-2 text-base text-gray-900 shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-50"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label
              htmlFor="date_from"
              className="mb-1 block text-sm font-medium text-emerald-950 dark:text-emerald-100"
            >
              Datum von
            </label>
            <input
              id="date_from"
              name="date_from"
              type="date"
              value={currentDateFrom}
              onChange={(e) => setCurrentDateFrom(e.target.value)}
              className="w-full rounded-lg border border-emerald-300 bg-white px-3 py-2 text-base text-gray-900 shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-50"
            />
          </div>
          <div>
            <label
              htmlFor="date_to"
              className="mb-1 block text-sm font-medium text-emerald-950 dark:text-emerald-100"
            >
              Datum bis
            </label>
            <input
              id="date_to"
              name="date_to"
              type="date"
              value={currentDateTo}
              onChange={(e) => setCurrentDateTo(e.target.value)}
              className="w-full rounded-lg border border-emerald-300 bg-white px-3 py-2 text-base text-gray-900 shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-50"
            />
          </div>
          <MeetingFilter dateFrom={currentDateFrom || null} dateTo={currentDateTo || null}>
          </MeetingFilter>
        </fieldset>
      </details>
    </Form>
  );
}
