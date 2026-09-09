"""Published generation fleet and seasonal capacity forecasts."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ._legacy_load import _number
from ._load import _workbooks
from ._public_tables import _PublicTable, _ResourceFiles

Season = Literal["summer", "winter", "spring", "fall"]


class _ForecastRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sourceRow: int


class SeasonalGenerationCapability(BaseModel):
    """Reported seasonal rating in MW, not dispatch availability or ELCC.

    period preserves winter year spans. Blank values remain None, not zero.
    """

    model_config = ConfigDict(extra="forbid")
    season: Season
    period: str
    capacityMW: Decimal | None
    sourceColumn: int


class GenerationResourceCapacity(_ForecastRow):
    """One Unit Details row, including ties and the published aggregate entry.

    Unit codes can repeat for fuel conversions or other source scenarios.
    inServiceDate is the published date, not proof of commercial operation.
    """

    name: str
    interconnectionRequest: str | None
    unitCode: str | None
    technology: str
    fuel: str
    cdrStatus: str
    cdrResourceAttribute: str
    county: str | None
    zone: str | None
    inServiceDate: date | None
    installedCapacityMW: Decimal | None
    capabilities: list[SeasonalGenerationCapability]


class GenerationCategoryCapacity(_ForecastRow):
    """A published subtotal or total; parent and child rows overlap.

    categoryPath includes this category and follows worksheet indentation.
    Keep operational and planned sections separate; do not sum all rows.
    """

    section: Literal["operational", "planned", "total"]
    categoryPath: list[str]
    sourceIndent: int
    installedCapacityMW: Decimal | None
    capabilities: list[SeasonalGenerationCapability]


class GenerationCapacityRegion(_ForecastRow):
    """CDR county mapping; these differ from production-forecast regions."""

    fuel: Literal["wind", "solar"]
    county: str
    region: str


class GenerationCapacityNote(_ForecastRow):
    sourceSheet: str
    sourceColumn: int
    text: str


class GenerationCapacityForecast(BaseModel):
    """One source workbook, retaining its qualifications and reference tables.

    The May 2026 publication uses April fleet data. It contains no load forecast
    or planning reserve margin; it is not a history of observed production.
    """

    model_config = ConfigDict(extra="forbid")
    sourceMember: str
    resources: list[GenerationResourceCapacity]
    categories: list[GenerationCategoryCapacity]
    regions: list[GenerationCapacityRegion]
    notes: list[GenerationCapacityNote]


def _capabilities(
    cells: Sequence[object],
    headers: Sequence[object],
    start: int,
    seasons: Sequence[Season],
) -> list[SeasonalGenerationCapability]:
    return [
        SeasonalGenerationCapability(
            season=season,
            period=str(headers[column]),
            capacityMW=_number(cells[column]),
            sourceColumn=column + 1,
        )
        for block, season in enumerate(seasons)
        for column in range(start + block * 5, start + (block + 1) * 5)
    ]


class GenerationCapacity(_ResourceFiles, _PublicTable[GenerationCapacityForecast]):
    """Generation Resource Capacity Forecast workbooks; needs tinyercot[files]."""

    title_pattern = r"Generation Resource Capacity Forecast"

    def _read(self, data: bytes, filename: str) -> Iterator[GenerationCapacityForecast]:
        try:
            import openpyxl
        except ImportError as exc:
            raise ImportError(
                "Install tinyercot[files] to read Excel workbooks"
            ) from exc
        found = False
        for member, content in _workbooks(data):
            book = openpyxl.load_workbook(
                BytesIO(content), read_only=True, data_only=True
            )
            try:
                units = list(book["Unit Details"].values)
                if (
                    units[2][0] != "UNIT NAME"
                    or units[2][10] != "INSTALLED CAPACITY\n(MW)"
                ):
                    raise ValueError(f"{member}: unrecognized Unit Details header")
                document = GenerationCapacityForecast(
                    sourceMember=filename if member == "workbook.xlsx" else member,
                    resources=[],
                    categories=[],
                    regions=[],
                    notes=[],
                )
                fields = (
                    "name",
                    "interconnectionRequest",
                    "unitCode",
                    "technology",
                    "fuel",
                    "cdrStatus",
                    "cdrResourceAttribute",
                    "county",
                    "zone",
                    "inServiceDate",
                )
                for number, cells in enumerate(units[3:], 4):
                    if cells[0] is None:
                        continue
                    document.resources.append(
                        GenerationResourceCapacity.model_validate(
                            dict(
                                zip(fields, cells[:10]),
                                sourceRow=number,
                                installedCapacityMW=_number(cells[10]),
                                capabilities=_capabilities(
                                    cells,
                                    units[2],
                                    11,
                                    ("summer", "winter", "spring", "fall"),
                                ),
                            )
                        )
                    )
                summary = list(book["Capacity by Resource Category"].rows)
                headers = tuple(c.value for c in summary[1])
                section: Literal["operational", "planned", "total"] = "operational"
                parents: list[tuple[int, str]] = []
                for number, row in enumerate(summary[2:], 3):
                    label = row[1].value
                    if label == "Planned Resources [5]":
                        section = "planned"
                        parents.clear()
                    if label == "Total Resources, MW":
                        section = "total"
                        parents.clear()
                    if not isinstance(row[2].value, (int, float)):
                        continue
                    indent = int(row[1].alignment.indent)
                    while parents and parents[-1][0] >= indent:
                        parents.pop()
                    parents.append((indent, str(label)))
                    document.categories.append(
                        GenerationCategoryCapacity(
                            sourceRow=number,
                            section=section,
                            sourceIndent=indent,
                            categoryPath=[name for _, name in parents],
                            installedCapacityMW=_number(row[2].value),
                            capabilities=_capabilities(
                                tuple(c.value for c in row),
                                headers,
                                3,
                                ("summer", "winter"),
                            ),
                        )
                    )
                mapping = list(book["Wind-Solar Region Mapping"].values)
                for number, cells in enumerate(mapping[4:], 5):
                    for fuel, column in (("wind", 0), ("solar", 3)):
                        if cells[column] is not None:
                            document.regions.append(
                                GenerationCapacityRegion.model_validate(
                                    {
                                        "sourceRow": number,
                                        "fuel": fuel,
                                        "county": cells[column],
                                        "region": cells[column + 1],
                                    }
                                )
                            )
                for sheet in book:
                    for number, cells in enumerate(sheet.values, 1):
                        if sheet.title == "Unit Details" and number > 3:
                            continue
                        if (
                            sheet.title == "Capacity by Resource Category"
                            and 3 <= number <= 51
                        ):
                            continue
                        if sheet.title == "Wind-Solar Region Mapping" and number > 4:
                            continue
                        for column, value in enumerate(cells, 1):
                            if isinstance(value, str) and value.strip():
                                document.notes.append(
                                    GenerationCapacityNote(
                                        sourceSheet=sheet.title,
                                        sourceRow=number,
                                        sourceColumn=column,
                                        text=value,
                                    )
                                )
                found = True
                yield document
            finally:
                book.close()
        if not found:
            raise ValueError("Download contains no generation capacity workbooks")
