import { Link } from "react-router";

interface SiteHeaderProps {
  title: string;
  description?: string;
  compact?: boolean;
}

export function SiteHeader({ title, description, compact = false }: SiteHeaderProps) {
  return (
    <header className="bg-gradient-to-b from-emerald-800 to-emerald-700 text-white dark:from-emerald-950 dark:to-emerald-900">
      <div
        className={
          compact
            ? "mx-auto flex max-w-3xl flex-col items-center gap-2 px-4 py-8 text-center"
            : "mx-auto flex max-w-3xl flex-col items-center gap-3 px-4 py-10 text-center sm:py-14"
        }
      >
        <Link
          to="/"
          className="flex flex-col items-center gap-3 rounded-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-white"
        >
          <h1
            className={
              compact
                ? "text-xl font-bold tracking-tight sm:text-2xl"
                : "text-2xl font-bold tracking-tight sm:text-3xl"
            }
          >
            {title}
          </h1>
        </Link>
        {description && (
          <p className="max-w-xl text-sm text-emerald-100 sm:text-base">
            {description}
          </p>
        )}
      </div>
    </header>
  );
}
