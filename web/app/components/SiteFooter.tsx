import { Link } from "react-router";

export function SiteFooter() {
  return (
    <footer className="border-t border-emerald-200 bg-white px-4 py-6 text-center text-sm text-gray-500 dark:border-emerald-900 dark:bg-gray-950 dark:text-gray-400">
      <p>
        Quelle: Archiv des{" "}
        <a
          href="https://www.graz.at/cms/beitrag/10134085/7768145/Gemeinderat_ArchivNachlese.html"
          target="_blank"
          rel="noreferrer noopener"
          className="font-medium text-emerald-700 underline-offset-2 hover:underline dark:text-emerald-400"
        >
          Grazer Gemeinderats
        </a>
        . Dieses Projekt steht in keiner Verbindung zur Stadt Graz.
      </p>
      <nav aria-label="Rechtliches" className="mt-3 flex items-center justify-center gap-4">
        <Link
          to="/datenschutz"
          className="font-medium text-emerald-700 underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:text-emerald-400"
        >
          Datenschutzerklärung
        </Link>
        <span aria-hidden="true" className="text-gray-300 dark:text-gray-700">
          ·
        </span>
        <Link
          to="/impressum"
          className="font-medium text-emerald-700 underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:text-emerald-400"
        >
          Impressum
        </Link>
        <Link to="https://github.com/michivo/graz-council/"
        className="font-medium text-emerald-700 underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:text-emerald-400"
        >
          GitHub
        </Link>
      </nav>
    </footer>
  );
}
