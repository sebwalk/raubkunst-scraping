from dataclasses import field, dataclass
from typing import List, Tuple
from urllib.parse import urlparse, parse_qs, urljoin
from bs4 import ResultSet, Tag


@dataclass
class AttributeParser:
    table_rows: list[tuple[str, Tag]]
    visited_table_rows: set[int] = field(default_factory=set)

    @staticmethod
    def from_table_headers(table_headers: ResultSet[Tag]):
        table_rows = [(header.text.strip(), header.find_next_sibling("td")) for header in table_headers]
        return AttributeParser(table_rows)

    def get_first(self, titles: str | list[str]) -> Tag | None:
        titles = [titles] if isinstance(titles, str) else titles

        for index, row in enumerate(self.table_rows):
            if row[0] in titles:
                self.visited_table_rows.add(index)
                return row[1]

        return None

    def get_all(self, titles: str | list[str]) -> list[tuple[str, Tag]]:
        titles = [titles] if isinstance(titles, str) else titles
        elements = []

        for index, row in enumerate(self.table_rows):
            if row[0] in titles:
                self.visited_table_rows.add(index)
                elements.append(row)

        return elements

    def get_as_text(self, title: str) -> str | None:
        element = self.get_first(title)

        if element is None:
            return None

        cleaned_text = element.get_text(separator="\n").strip()
        return cleaned_text if cleaned_text != "" else None

    def get_as_bool(self, title: str) -> bool | None:
        text = self.get_as_text(title)
        match text:
            case "Yes":
                return True
            case "No":
                return False
            case None:
                return None
            case _:
                raise ValueError("Unexpected value for boolean: " + text)

    def get_as_link(self, title: str, base_url: str | None = None) -> str | None:
        element = self.get_first(title)

        if element is None:
            return None

        path = element.find("a").attrs.get("href")
        return path if path is None else urljoin(base_url, path)

    def get_as_id(self, title: str, id_parameter: str) -> int | None:
        url = self.get_as_link(title)

        if url is None:
            return None

        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        return int(query[id_parameter][0])

    def get_as_image_urls(self, title: str) -> list[str]:
        image_container = self.get_first(title)

        if image_container is None:
            return []

        image_items = image_container.select('div.highslide-gallery table tr:first-child td a')
        return [image_item.attrs.get('href') for image_item in image_items]

    def get_unvisited_rows(self):
        return [row for index, row in enumerate(self.table_rows) if index not in self.visited_table_rows]

    def get_serializable_unvisited_rows(self):
        return [{"title": row[0], "value": row[1].text.strip()} for index, row in enumerate(self.get_unvisited_rows())]
