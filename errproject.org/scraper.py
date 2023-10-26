from typing import Generator

from bs4 import BeautifulSoup, Tag
import requests
from attribute_parser import AttributeParser


def scrape_cards(offset: int = 1, limit: int = 10) -> Generator[dict, None, None]:
    cursor = offset

    while cursor <= limit:
        url = "https://errproject.org/jeudepaume/card_show.php?Query=&StartDoc=" + str(cursor)
        response = requests.get(url)

        if response.status_code == 302:
            # we've reached the end of the results
            break

        page_html = response.content

        card = scrape_card(response.url, page_html)
        yield card

        cursor += 1


def scrape_card(page_url: str, page_html: bytes) -> dict:
    # determine card id from url
    card_id = int(page_url.split("?CardId=")[1])

    soup = BeautifulSoup(page_html, "html.parser")
    table_headers = soup.select("table tr th")
    parser = AttributeParser.from_table_headers(table_headers)

    collection_code, collection_name = parse_collection_string(parser.get_as_text("Collection:"))

    return {
        "id": card_id,
        "url": page_url,
        "owner": {
            "id": parser.get_as_id("Owner:", "Owner__ownerid"),
            "name": parser.get_as_text("Owner:"),
            "url": parser.get_as_link("Owner:")
        },
        "collection": {
            "id": parser.get_as_id("Collection:", "Collection__collectionid"),
            "code": collection_code,
            "name": collection_name,
            "url": parser.get_as_link("Collection:")
        },
        "inventory_number": parser.get_as_text("Inventory No.:"),
        "artist": parser.get_as_text("Artist:"),
        "medium": parser.get_as_text("Medium:"),
        "title": parser.get_as_text("Title:"),
        "description": parser.get_as_text("Description:"),
        "literature": parser.get_as_text("Literature:"),
        "provenance_and_comments": parser.get_as_text("Provenance and Comments:"),
        "archival_sources": parser.get_as_text("Archival Sources:"),
        "measurements": parser.get_as_text("Measurements:"),
        "signed": parser.get_as_bool("Signed?"),
        "framed": parser.get_as_bool("Framed?"),
        "munich_number": parser.get_as_text("Munich No.:"),
        "intake_place": parser.get_as_text("Intake place:"),
        "intake_date": parser.get_as_text("Intake date:"),
        "transfers": parse_transfers(parser.get_all(["Transfer place:", "Transfer date:"])),
        "restituted": parser.get_as_bool("Restituted?"),
        "restitution_date": parser.get_as_text("Restitution date:"),
        "repatriated_to_france": parser.get_as_bool("Repatriated to France?"),
        "repatriation_date": parser.get_as_text("Repatriation date:"),
        "image_urls": parser.get_as_image_urls("Images:"),
        "unstructured_data": parser.get_serializable_unvisited_rows()
    }


def parse_collection_string(collection_string: str) -> tuple[str, str]:
    opening_parantheses = 0

    for index, character in enumerate(collection_string):
        if character == "(":
            opening_parantheses += 1
        elif character == ")":
            if opening_parantheses == 1:
                collection_code = collection_string[1:index].strip()
                collection_name = collection_string[index + 1:].strip()
                return collection_code, collection_name

            opening_parantheses -= 1


def parse_transfers(rows: list[str, Tag]):
    transfers = []
    transfer_place = None

    for title, tag in rows:
        if title == "Transfer place:" and transfer_place is None:
            # Transfer has a place, might have a date next
            transfer_place = tag.text.strip()

        elif title == "Transfer place:" and transfer_place is not None:
            # Transfer doesn't have a date, process previous transfer before looking at new one
            transfers.append({
                "place": transfer_place,
                "date": None
            })
            transfer_place = tag.text.strip()

        elif title == "Transfer date:":
            # Transfer has a date
            transfers.append({
                "place": transfer_place,
                "date": tag.text.strip()
            })
            transfer_place = None

    if transfer_place is not None:
        # Last transfer doesnt have a date
        transfers.append({
            "place": transfer_place,
            "date": None
        })

    return transfers
