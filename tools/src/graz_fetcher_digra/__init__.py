import configparser
import hashlib
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pymupdf
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://digra.graz.at"
TIMETABLE_URL = f"{BASE_URL}/timetable"
CONFIG_PATH = Path(__file__).parents[2] / "config.ini"
MEETING_LINK = re.compile(r"^\d+\.\s*Gemeinderatssitzung\b", re.IGNORECASE)
DATE = re.compile(r"\b(\d{2}\.\d{2}\.\d{4})\b")
INVITATION_DATE = re.compile(
    r"\bam\s+[^,]{2,40},\s*dem\s+(\d{2}\.\d{2}\.\d{4})\b", re.IGNORECASE
)


@dataclass(frozen=True)
class DownloadLink:
    url: str
    name: str


def read_pdf_folder(config_path: Path = CONFIG_PATH) -> Path:
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(config_path, encoding="utf-8"):
        raise RuntimeError(f"Unable to load configuration from {config_path}")
    try:
        value = config.get("paths", "PDF_FOLDER").strip()
    except (configparser.NoOptionError, configparser.NoSectionError) as exc:
        raise RuntimeError(
            f"Configuration file {config_path} must define PDF_FOLDER in [paths]"
        ) from exc
    if not value:
        raise RuntimeError(
            f"Configuration file {config_path} must define a non-empty PDF_FOLDER value"
        )
    return Path(value)


def page_soup(session: requests.Session, url: str) -> BeautifulSoup:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


def period_links(soup: BeautifulSoup, page_url: str) -> list[str]:
    links = []
    for anchor in soup.select("a[href]"):
        label = " ".join(anchor.get_text(" ", strip=True).split())
        if label.lower().startswith("sitzungen"):
            links.append(urljoin(page_url, anchor["href"]))
    return links


def discover_meeting_links(session: requests.Session) -> list[tuple[str, str, str]]:
    pending = [TIMETABLE_URL]
    visited_periods: set[str] = set()
    meetings: dict[str, tuple[str, str, str]] = {}

    while pending:
        period_url = pending.pop(0)
        if period_url in visited_periods:
            continue
        visited_periods.add(period_url)
        soup = page_soup(session, period_url)
        pending.extend(
            url for url in period_links(soup, period_url) if url not in visited_periods
        )
        for anchor in soup.select("a[href]"):
            title = " ".join(anchor.get_text(" ", strip=True).split())
            if not MEETING_LINK.match(title):
                continue
            meeting_url = urljoin(period_url, anchor["href"])
            context = " ".join(anchor.parent.get_text(" ", strip=True).split())
            date_match = DATE.search(context)
            meetings.setdefault(
                meeting_url,
                (meeting_url, title, date_match.group(1) if date_match else ""),
            )
    return list(meetings.values())


def meeting_date(soup: BeautifulSoup, fallback: str = "") -> str:
    text = " ".join(soup.get_text(" ", strip=True).split())
    match = INVITATION_DATE.search(text)
    if not match:
        match = DATE.search(fallback) or DATE.search(text)
    if not match:
        raise ValueError("Could not determine the meeting date from its page")
    return datetime.strptime(match.group(1), "%d.%m.%Y").strftime("%Y%m%d")


def tab_indices(soup: BeautifulSoup) -> list[tuple[str, int]]:
    tabs = []
    for anchor in soup.select('[role="tab"][data-index]'):
        if not anchor.get("id", "").startswith("contentForm:"):
            continue
        tabs.append((anchor.get_text(" ", strip=True), int(anchor["data-index"])))
    return tabs


def fetch_tab_soup(
    session: requests.Session, meeting_url: str, tab_index: int
) -> BeautifulSoup:
    soup = page_soup(session, meeting_url)
    form = soup.find("form", id="contentForm")
    if form is None:
        raise RuntimeError(f"Meeting page has no content form: {meeting_url}")
    tab = next(
        (
            anchor
            for anchor in soup.select('[role="tab"][data-index]')
            if anchor.get("id", "").startswith("contentForm:")
        ),
        None,
    )
    if tab is None:
        raise RuntimeError(f"Meeting page has no tab view: {meeting_url}")
    tab_view_id = tab["id"].rsplit(":", 1)[0]
    data = {
        element["name"]: element.get("value", "")
        for element in form.select("input[name]")
    }
    data.update(
        {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": tab_view_id,
            "javax.faces.partial.execute": tab_view_id,
            "javax.faces.partial.render": tab_view_id,
            tab_view_id: tab_view_id,
            f"{tab_view_id}_activeIndex": str(tab_index),
            "javax.faces.behavior.event": "tabChange",
            "javax.faces.partial.event": "tabChange",
        }
    )
    action = urljoin(meeting_url, form.get("action") or meeting_url)
    response = session.post(
        action,
        data=data,
        headers={
            "Faces-Request": "partial/ajax",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": meeting_url,
        },
        timeout=30,
    )
    response.raise_for_status()
    update_start = response.text.find(f'<update id="{tab_view_id}">')
    if update_start < 0:
        raise RuntimeError(f"Tab {tab_index} was not returned for {meeting_url}")
    cdata_start = response.text.find("<![CDATA[", update_start)
    if cdata_start < 0:
        raise RuntimeError(f"Malformed tab response for {meeting_url}")
    content_start = cdata_start + len("<![CDATA[")
    content_end = response.text.find("</update>", content_start)
    if content_end < 0:
        content_end = response.text.find("<script", content_start)
    if content_end < 0:
        content_end = len(response.text)
    return BeautifulSoup(response.text[content_start:content_end], "html.parser")


def panel_links(soup: BeautifulSoup, page_url: str) -> list[tuple[str, str]]:
    links = []
    for anchor in soup.select("a[href]"):
        path = urlparse(anchor["href"]).path.rstrip("/").lower()
        if path.rsplit("/", 1)[-1] != "document":
            continue
        title = " ".join(anchor.get_text(" ", strip=True).split()) or anchor.get("title", "")
        links.append((urljoin(page_url, anchor["href"]), title or "document"))
    return links


def _menu_links(soup: BeautifulSoup, menu_title: str) -> list[BeautifulSoup]:
    matches = []
    for menu in soup.select(".menu"):
        title = menu.select_one(".menu-title")
        if title and " ".join(title.get_text(" ", strip=True).split()).casefold() == menu_title.casefold():
            matches.extend(menu.select("a[href]"))
    return matches


def _is_anlage_section_link(anchor: BeautifulSoup) -> bool:
    menu = anchor.find_parent(class_="menu")
    title = menu.select_one(".menu-title") if menu else None
    return bool(
        title
        and " ".join(title.get_text(" ", strip=True).split()).casefold() == "anlagen"
    )


def _is_allowed_anlage_file(name: str, href: str) -> bool:
    filename = urlparse(href).path.rsplit("/", 1)[-1]
    searchable = f"{name} {filename}".casefold()
    return "einladung" in searchable or "protokoll" in searchable


def pdf_links(soup: BeautifulSoup, page_url: str) -> list[DownloadLink]:
    found: dict[str, DownloadLink] = {}
    for anchor in soup.select("a[href]"):
        href = anchor["href"]
        path = urlparse(href).path.lower()
        label = " ".join(anchor.get_text(" ", strip=True).split())
        title = anchor.get("title", "")
        if path.endswith(".pdf") or "/pdf" in path or title.lower().endswith(".pdf"):
            name = title or label or "document"
            if _is_anlage_section_link(anchor) and not _is_allowed_anlage_file(
                f"{name} {label}", href
            ):
                continue
            absolute_url = urljoin(page_url, href)
            found.setdefault(
                absolute_url,
                DownloadLink(absolute_url, name),
            )
    for menu_title in ("PDF herunterladen", "Anlagen"):
        for anchor in _menu_links(soup, menu_title):
            href = anchor["href"]
            label = anchor.get("title") or anchor.get_text(" ", strip=True) or "document"
            if menu_title == "Anlagen" and not label.lower().endswith(".pdf"):
                continue
            if menu_title == "Anlagen" and not _is_allowed_anlage_file(label, href):
                continue
            absolute_url = urljoin(page_url, href)
            found.setdefault(absolute_url, DownloadLink(absolute_url, label))
    return list(found.values())


def safe_filename(name: str, url: str) -> str:
    name = re.sub(r"(?i)\.pdf$", "", name.strip())
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9]+", "_", normalized).strip("_").lower()
    if not slug:
        ref = re.search(r"(?:ref|att)=([^&]+)", url)
        slug = f"document_{(ref.group(1) if ref else hashlib.sha1(url.encode()).hexdigest()[:8])}"
    return slug[:100]


def save_pdf(
    session: requests.Session,
    link: DownloadLink,
    day: str,
    output_folder: Path,
    used_names: set[str],
) -> Path | None:
    slug = safe_filename(link.name, link.url)
    if slug.casefold().endswith("_signiert"):
        counterpart_slug = slug[: -len("_signiert")]
    else:
        counterpart_slug = f"{slug}_signiert"
    counterpart_filename = f"{day}_{counterpart_slug}.pdf".casefold()
    if counterpart_filename in used_names:
        print(f"Skipped alternate signed edition: {link.name}")
        return None

    response = session.get(link.url, timeout=60)
    response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise RuntimeError(f"Download is not a PDF: {link.url}")
    filename = f"{day}_{slug}.pdf"
    if filename.casefold() in used_names:
        suffix = hashlib.sha1(link.url.encode()).hexdigest()[:8]
        filename = f"{day}_{slug}_{suffix}.pdf"
        duplicate = 2
        while filename.casefold() in used_names:
            filename = f"{day}_{slug}_{suffix}_{duplicate}.pdf"
            duplicate += 1
    used_names.add(filename.casefold())
    path = output_folder / filename
    path.write_bytes(response.content)
    print(f"Downloaded: {path.name}")
    return path


def merge_day(paths: list[Path], output: Path) -> None:
    with pymupdf.open() as merged:
        for path in paths:
            with pymupdf.open(path) as source:
                if source.needs_pass or source.page_count == 0:
                    raise RuntimeError(f"Unable to merge invalid or protected PDF: {path}")
                merged.insert_pdf(source)
        merged.save(output, garbage=4, deflate=True)


def fetch_meeting(
    session: requests.Session,
    meeting_url: str,
    meeting_title: str,
    fallback_date: str,
    output_folder: Path,
    used_names: set[str] | None = None,
) -> tuple[str, list[Path]]:
    soup = page_soup(session, meeting_url)
    day = meeting_date(soup, fallback_date)
    links: dict[str, DownloadLink] = {
        link.url: link for link in pdf_links(soup, meeting_url)
    }
    tabs = tab_indices(soup)
    active = next(
        (int(tab["data-index"]) for tab in soup.select('[role="tab"][data-index]') if tab.get("aria-selected") == "true"),
        0,
    )
    contents = [(soup, active)]
    contents.extend(
        (fetch_tab_soup(session, meeting_url, index), index)
        for _, index in tabs
        if index != active
    )
    documents: dict[str, str] = {}
    for content, _ in contents:
        documents.update(panel_links(content, meeting_url))
    for document_url, document_name in documents.items():
        document_soup = page_soup(session, document_url)
        for link in pdf_links(document_soup, document_url):
            links.setdefault(link.url, link)
    if used_names is None:
        used_names = set()
    paths = []
    for link in links.values():
        path = save_pdf(session, link, day, output_folder, used_names)
        if path is not None:
            paths.append(path)
    if not paths:
        print(f"No new PDFs to save for {meeting_title} ({day})")
    return day, paths


def main() -> None:
    output_folder = read_pdf_folder() / "digra"
    output_folder.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "graz-fetcher-digra/1.0"})
    meetings = discover_meeting_links(session)
    grouped_paths: dict[str, list[Path]] = defaultdict(list)
    used_names: set[str] = set()
    failures = 0
    for meeting_url, title, fallback_date in meetings:
        print(f"Processing: {title} ({meeting_url})")
        try:
            day, paths = fetch_meeting(
                session, meeting_url, title, fallback_date, output_folder, used_names
            )
            grouped_paths[day].extend(paths)
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            failures += 1
            print(f"Failed: {title}: {exc}")
    for day, paths in sorted(grouped_paths.items()):
        unique_paths = list(dict.fromkeys(paths))
        output = output_folder / f"{day}.pdf"
        merge_day(unique_paths, output)
        print(f"Merged {len(unique_paths)} PDF(s) into {output.name}")
    print(f"Processed {len(meetings)} meeting(s); {failures} failed.")
    if failures:
        raise SystemExit(1)