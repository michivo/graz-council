import configparser
import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from graz_fetcher.file_metadata import FileMetadata
from graz_fetcher.pdf_info import PDFInfo

# Base URL
archive_base_url = "https://www.graz.at/cms/beitrag/10134085/7768145/Gemeinderat_ArchivNachlese.html"
current_base_url = "https://www.graz.at/cms/beitrag/10142612/7768145/Gemeinderat_Archiv.html"

# List of years
years = range(2004, 2022)  # From 2004 to 2021

CONFIG_PATH = Path(__file__).parents[2] / "config.ini"
config = configparser.ConfigParser()
if not config.read(CONFIG_PATH, encoding="utf-8"):
    raise RuntimeError(f"Unable to load configuration from {CONFIG_PATH}")

try:
    PDF_FOLDER = config.get("paths", "PDF_FOLDER").strip()
except (configparser.NoOptionError, configparser.NoSectionError) as exc:
    raise RuntimeError(
        f"Configuration file {CONFIG_PATH} must define PDF_FOLDER in [paths]"
    ) from exc

if not PDF_FOLDER:
    raise RuntimeError(
        f"Configuration file {CONFIG_PATH} must define a non-empty PDF_FOLDER value"
    )

# Create a folder to store downloaded PDFs
os.makedirs(PDF_FOLDER, exist_ok=True)

# Flags to determine whether metadata and/or content should be exported
export_pdfs = True
export_metadata = True


def main() -> None:
    all_metadata = []

    # for year in years:
    #     print(f"Processing year: {year}")
    #     year_links = get_meeting_links_from_year(year)
    #     for meeting_link in year_links:
    #         meeting_details = get_meeting_details(meeting_link, year)
    #         for detail in meeting_details:
    #             pdf_links = get_pdf_links_from_year(detail.council_url)

    #             for pdf_url in pdf_links:
    #                 metadata = export_metadata_for_pdf(pdf_url, detail)                    
    #                 if export_pdfs:
    #                     download_pdf(pdf_url.pdf_url, detail)
    #                 if export_metadata:
    #                     all_metadata.append(metadata)

    current_meeting_details = get_meeting_details(current_base_url)
    for current_detail in current_meeting_details:
        current_pdf_links = get_pdf_links_from_year(current_detail.council_url, current_base_url)

        for current_pdf_url in current_pdf_links:
            current_metadata = export_metadata_for_pdf(current_pdf_url, current_detail, current_base_url)                
            if export_pdfs:
                    download_pdf(current_pdf_url.pdf_url, current_detail, current_base_url)
            if export_metadata:
                all_metadata.append(current_metadata)

    print("All PDFs downloaded.")
    if export_metadata:
        print("All metadata exported.")
        filename = "all_metadata.json"
        with open(os.path.join(PDF_FOLDER, filename), "w") as f:
            json.dump(all_metadata, f)  
    
def get_meeting_links_from_year(year: int) -> list[str]:
    response = requests.get(archive_base_url)
    soup = BeautifulSoup(response.text, "html.parser")
    meeting_links = []
    for link in soup.find_all("a", href=True):
        if "GR-Sitzungen" in link.text and str(year) in link.text:
            meeting_links.append(link["href"])
    return meeting_links

def get_meeting_details(meeting_url: str, year: int = 0, base_url: str = archive_base_url) -> list[FileMetadata]:
    url = urljoin(base_url, meeting_url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    meeting_details = []
    for link in soup.find_all("a", href=True):
        match = re.search(r"(\d\d\.\d\d\.\d\d\d\d)", link.text)
        if ((year == 0 or str(year) in link.text) and match) or (link.text.lower() == "übersicht" and link["title"] != "Terminkalender 2025"):
            date = match.group(1) if match else get_date(link)
            meeting_details.append(FileMetadata(council_url=urljoin(base_url, link["href"]), year=year, date=date, year_url=urljoin(base_url, meeting_url)))
    return meeting_details

def get_date(link):
    print(f'Getting date for link: {link!s}')
    first_sibling = link.previous_sibling
    print(f'Initial previous sibling: {first_sibling}')
    while first_sibling.previous_sibling is not None:
        first_sibling = first_sibling.previous_sibling
    match = re.search(r"(\d\d\.\d\d\.\d\d\d\d)", first_sibling.text) if hasattr(first_sibling, "text") else None
    return match.group(1) if match else (first_sibling.text if hasattr(first_sibling, "text") else str(first_sibling))

# Function to get all PDF links from a given year page
def get_pdf_links_from_year(meeting_url: str, base_url: str = archive_base_url) -> list[PDFInfo]:
    url = urljoin(base_url, meeting_url)
    print(f"Processing meeting URL: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    pdf_links = []
    for link in soup.find_all("a", href=True):
        if link["href"].endswith(".pdf"):
            pdf_links.append(PDFInfo(pdf_url=link["href"], document_title=link.text))
    return pdf_links


# Function to download a PDF
def download_pdf(url: str, metadata: FileMetadata, base_url: str = archive_base_url) -> None:
    url = urljoin(base_url, url)
    response = requests.get(url)
    filename = url.split("/")[-1]
    filename = prefix_filename_with_date(filename, metadata)
    with open(os.path.join(PDF_FOLDER, filename), "wb") as f:
        f.write(response.content)
    print(f"Downloaded: {filename}")

def prefix_filename_with_date(filename: str, metadata: FileMetadata) -> str:
    filename_prefix = re.match(r"^\d{6}", filename)
    if not filename_prefix:
        date = datetime.strptime(metadata.date, "%d.%m.%Y")
        filename = f"{date.year:02d}{date.month:02d}{date.day:02d}_{filename}"
    return filename

# Function to export metadata for a PDF
def export_metadata_for_pdf(pdf_url: PDFInfo, metadata: FileMetadata, base_url: str = archive_base_url):
    filename = pdf_url.pdf_url.split("/")[-1].lower().replace(".pdf", ".json")
    filename = prefix_filename_with_date(filename, metadata)
    print(f"Exporting metadata for PDF: {pdf_url.pdf_url} and title: {pdf_url.document_title}")
    with open(os.path.join(PDF_FOLDER, filename), "w") as f:
        export_data = {
            "council_url": metadata.council_url,
            "year": metadata.year,
            "date": datetime.strptime(metadata.date, "%d.%m.%Y").isoformat(),
            "year_url": metadata.year_url,
            "pdf_url": urljoin(base_url, pdf_url.pdf_url),
            "document_title": pdf_url.document_title,
        }
        json.dump(export_data, f)
        return export_data
