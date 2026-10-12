import { SiteFooter } from "~/components/SiteFooter";
import { SiteHeader } from "~/components/SiteHeader";
import type { Route } from "./+types/impressum";

export function meta(_: Route.MetaArgs) {
  return [
    { title: "Impressum – Grazer Gemeinderat Suche" },
    {
      name: "description",
      content: "Impressum der Grazer Gemeinderat Suche.",
    },
  ];
}

export default function Impressum() {
  return (
    <div className="flex min-h-screen flex-col bg-emerald-50/40 dark:bg-gray-950">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-emerald-900 focus:shadow-lg"
      >
        Zum Inhalt springen
      </a>

      <SiteHeader title="Impressum" compact />

      <main
        id="main-content"
        className="mx-auto w-full max-w-3xl flex-1 px-4 py-8 sm:py-10"
      >
        <article className="space-y-4 leading-relaxed text-gray-800 dark:text-gray-200">
          <p>
            Informationspflicht laut §5 E-Commerce Gesetz, §14 Unternehmensgesetzbuch, §63 Gewerbeordnung und Offenlegungspflicht laut §25 Mediengesetz.
          </p>
          <p>Michael Faschinger</p>
          <address>
            Ankerstraße 49<br />
            8054 Graz<br />
            Österreich
          </address>

          <p>Unternehmensgegenstand: IT Dienstleistungen</p>
          <p>UID-Nummer: ATU74085401</p>

          <p>Tel.: <a href="tel:+436502910662">+43 650 2910662</a></p>
          <p>E-Mail: <a href="mailto:michael@daredevels.com">michael@daredevels.com</a></p>

          <p>Berufsrecht: Gewerbeordnung: www.ris.bka.gv.at</p>

          <p>Aufsichtsbehörde/Gewerbebehörde: Bezirkshauptmannschaft Graz</p>
          <p>Berufsbezeichnung: Softwareentwickler</p>
          <p>Verleihungsstaat: Österreich</p>
          <h2 className="text-lg font-bold">EU-Streitschlichtung</h2>
    
          <p>
            Gemäß Verordnung über Online-Streitbeilegung in Verbraucherangelegenheiten (ODR-Verordnung) möchten wir Sie über die Online-Streitbeilegungsplattform (OS-Plattform) informieren.
          </p>
          <p>
            Verbraucher haben die Möglichkeit, Beschwerden an die Online-Streitbeilegungsplattform der Europäischen Kommission unter ec.europa.eu/consumers/odr zu richten. Die dafür notwendigen Kontaktdaten finden Sie weiter oben auf dieser Seite.
          </p>

          <p>
            Wir möchten Sie jedoch darauf hinweisen, dass wir nicht verpflichtet sind, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.
          </p>
          <h2 className="text-lg font-bold">Urheberrechtshinweis</h2>

          <p>
            Sie können alle Inhalte auf dieser Seite gerne weiterverwenden! Die auf dieser Seite verwendeten Icons kommen von Feather Icons, die gibt es übrigens auf GitHub.
          </p>
          <h2 className="text-lg font-bold">Datenschutzerklärung</h2>

          <p>
            Wir speichern keine Daten. Nichts, wirklich. Keine Cookies, keine Logs, nichts.
          </p>
        </article>
      </main>

      <SiteFooter />
    </div>
  );
}
