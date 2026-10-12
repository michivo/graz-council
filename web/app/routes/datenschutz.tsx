import { SiteFooter } from "~/components/SiteFooter";
import { SiteHeader } from "~/components/SiteHeader";
import type { Route } from "./+types/datenschutz";
import { Link } from "react-router";

export function meta(_: Route.MetaArgs) {
  return [
    { title: "Datenschutzerklärung – Grazer Gemeinderat Suche" },
    {
      name: "description",
      content: "Datenschutzerklärung der Grazer Gemeinderat Suche.",
    },
  ];
}

export default function Datenschutz() {
  return (
    <div className="flex min-h-screen flex-col bg-emerald-50/40 dark:bg-gray-950">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-emerald-900 focus:shadow-lg"
      >
        Zum Inhalt springen
      </a>

      <SiteHeader title="Datenschutzerklärung" compact />

      <main
        id="main-content"
        className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 sm:py-10"
      >
        <article className="space-y-4 leading-relaxed text-gray-800 dark:text-gray-200">
          <h2 className="text-lg font-bold">The greatest privacy statement</h2>
          <p>
            We do not store any of your data. Nothing, nada, niente. No cookies, no logs, nothing. Feel free to go back to the <Link className="font-medium text-emerald-700 underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:text-emerald-400" to="/">main page</Link> or stay here and relax a little.
          </p>
          <h2 className="text-lg font-bold">Die beste Datenschutzerklärung</h2>
          <p>
            Wir speichern keine Daten. Nichts, wirklich. Keine Cookies, keine Logs, nichts. Sie können gerne zur <Link className="font-medium text-emerald-700 underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-700 dark:text-emerald-400" to="/">Hauptseite</Link> zurückkehren oder die Ruhe hier genießen.
          </p>
        </article>
      </main>

      <SiteFooter />
    </div>
  );
}
