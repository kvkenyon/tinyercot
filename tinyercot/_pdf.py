"""Optional extraction of explicitly mapped tables from public report PDFs."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date, datetime
from io import BytesIO
from time import strptime
from typing import TypeVar

from pydantic import BaseModel

from ._client import Transport
from ._history import Archive, _archive_files

T = TypeVar("T", bound=BaseModel)


class PdfArchive(Archive[T]):
    """Typed ESR Integration Report tables; requires the ``pdf`` extra.

    Reads the published summary page, without estimating values from charts.
    Publication filtering and archive/bundle downloads work as for CSV readers.
    """

    def __init__(
        self,
        client: Transport,
        product: str,
        row: type[T],
        columns: dict[str, str],
        dates: dict[str, str],
        *,
        start: str,
        end: str,
        pattern: str,
        numbers: tuple[str, ...],
        datetimes: dict[str, str],
        records: bool = False,
        notes: bool = False,
    ) -> None:
        super().__init__(client, product, row, columns, dates)
        self._start = start
        self._end = end
        self._pattern = re.compile(pattern)
        self._numbers = numbers
        self._pdf_datetimes = datetimes
        self._records = records
        self._notes = notes

    def read(self, data: bytes) -> Iterator[T]:
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise ImportError("Install tinyercot[pdf] to read PDF archives") from error
        found = False
        for filename, content in _archive_files(data, "*.pdf"):
            found = True
            book = PdfReader(BytesIO(content))
            text = " ".join(book.pages[0].extract_text().split()) if book.pages else ""
            try:
                yield from self._read_text(text)
            except ValueError as error:
                raise ValueError(f"{filename}: {error}") from error
        if not found:
            raise ValueError("Download contains no PDF reports")

    def _read_text(self, text: str) -> Iterator[T]:
        header = re.search(r"ESR Integration Report\s*:\s*(\d{2}/\d{2}/\d{4})", text)
        if header is None or "Current Daily Values:" not in text:
            raise ValueError("Unsupported ESR Integration Report header")
        report_date = date(*strptime(header[1], "%m/%d/%Y")[:3])
        notes_at = text.find("* Sum")
        if notes_at < 0:
            raise ValueError("Missing report definitions")
        # The 2023 report has no all-time record section at all.
        if self._records and "All Time Record Values:" not in text:
            if "Record" in text[:notes_at]:
                raise ValueError("Unsupported PDF record section")
            return
        start = re.search(self._start, text)
        end = re.search(self._end, text[start.end() :]) if start else None
        if start is None or end is None:
            raise ValueError("Unsupported PDF table headings")
        section = text[start.end() : start.end() + end.start()].strip()
        position = 0
        while position < len(section):
            match = self._pattern.match(section, position)
            if match is None:
                raise ValueError(
                    f"Unsupported PDF table values: {section[position:][:80]}"
                )
            values: dict[str, object] = dict(match.groupdict())
            values["reportDate"] = report_date
            if self._notes:
                values["sourceNotes"] = text[notes_at:]
            for field in self._numbers:
                values[field] = str(values[field]).replace(",", "")
            for field, fmt in self._pdf_datetimes.items():
                # Preserve ERCOT's clock without inventing a timezone.
                values[field] = datetime.strptime(str(values[field]), fmt)  # noqa: DTZ007
            yield self._row.model_validate(values)
            position = match.end()
            while position < len(section) and section[position].isspace():
                position += 1
        if not section:
            raise ValueError("Empty PDF table")
