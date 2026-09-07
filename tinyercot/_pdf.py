"""Optional extraction of explicitly mapped tables from public report PDFs."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from itertools import pairwise
from time import strptime
from typing import TYPE_CHECKING, TypeVar, cast

from pydantic import BaseModel

from ._client import Transport
from ._history import Archive, _archive_files

if TYPE_CHECKING:
    from pypdf import PageObject
    from pypdf.generic import DictionaryObject

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


class PdfChartArchive(Archive[T]):
    """Printed hourly percentages in ESR report charts, without digitizing bars."""

    def __init__(
        self,
        client: Transport,
        product: str,
        row: type[T],
        columns: dict[str, str],
        dates: dict[str, str],
        *,
        charts: dict[str, tuple[int, str]],
    ) -> None:
        super().__init__(client, product, row, columns, dates)
        self._charts = charts

    def read(self, data: bytes) -> Iterator[T]:
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise ImportError("Install tinyercot[pdf] to read PDF archives") from error
        found = False
        for filename, content in _archive_files(data, "*.pdf"):
            found = True
            book = PdfReader(BytesIO(content))
            try:
                header = re.search(
                    r"ESR Integration Report\s*:\s*(\d{2}/\d{2}/\d{4})",
                    book.pages[0].extract_text() if book.pages else "",
                )
                if header is None:
                    raise ValueError("Unsupported ESR Integration Report header")
                report_date = date(*strptime(header[1], "%m/%d/%Y")[:3])
                rows: list[dict[str, object]] = []
                for field, (page_number, legend) in self._charts.items():
                    if page_number > len(book.pages):
                        raise ValueError(f"Missing chart page {page_number}")
                    values = _chart_percentages(book.pages[page_number - 1], legend)
                    hours = [hour for hour, _ in values]
                    if not rows:
                        rows = [
                            {"reportDate": report_date, "hourEnding": h} for h in hours
                        ]
                    elif hours != [r["hourEnding"] for r in rows]:
                        raise ValueError("Chart hour labels disagree")
                    for row, (_, value) in zip(rows, values, strict=True):
                        row[field] = value
                for row in rows:
                    yield self._row.model_validate(row)
            except ValueError as error:
                raise ValueError(f"{filename}: {error}") from error
        if not found:
            raise ValueError("Download contains no PDF reports")


def _chart_percentages(
    page: PageObject, legend: str
) -> list[tuple[str, Decimal | None]]:
    charts: list[list[tuple[str, float]]] = []
    resources = cast("DictionaryObject", page["/Resources"])
    for reference in resources.get("/XObject", {}).values():
        form = reference.get_object()
        if form.get("/Subtype") != "/Form":
            continue
        chunks: list[tuple[str, float]] = []

        def visit(
            text: str,
            cm: list[float],
            tm: list[float],
            font: object,
            size: float,
            *,
            output: list[tuple[str, float]] = chunks,
        ) -> None:
            # Use each form's local coordinates, including text/user transforms.
            output.append((text.strip(), tm[4] * cm[0] + tm[5] * cm[2] + cm[4]))

        text = page.extract_xform_text(form, visitor_text=visit)
        if legend in [line.strip() for line in text.splitlines()]:
            charts.append(chunks)
    if len(charts) != 1:
        raise ValueError(f"Expected one chart for {legend!r}")
    chunks = charts[0]
    hours = sorted(
        ((text, x) for text, x in chunks if re.fullmatch(r"\d{2}", text)),
        key=lambda h: h[1],
    )
    if len(hours) < 2:
        raise ValueError(f"Missing hour axis for {legend!r}")
    spacing = min(b[1] - a[1] for a, b in pairwise(hours))
    if spacing <= 0:
        raise ValueError("Ambiguous chart hour positions")
    values: list[Decimal | None] = [None] * len(hours)
    for text, x in chunks:
        if not re.fullmatch(r"-?\d+(?:\.\d+)?%", text):
            continue
        # The percentage-axis ticks sit to the left of the hour axis.
        if x < hours[0][1] - spacing / 2:
            continue
        distances = [abs(x - hour_x) for _, hour_x in hours]
        index = distances.index(min(distances))
        if distances[index] >= spacing / 2 or values[index] is not None:
            raise ValueError(f"Ambiguous chart label {text!r}")
        values[index] = Decimal(text.removesuffix("%"))
    return [(hour, value) for (hour, _), value in zip(hours, values, strict=True)]
