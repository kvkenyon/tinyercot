"""Sample two observed public nested CSV formats with exact source identities."""

import csv
import datetime
import hashlib
import io
import re
import zipfile
import zlib
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Generic, TypeVar

from ._http import AccessDeniedError, LimitError, Receipt, SchemaMismatchError
from .api import BASE
from .api_archives import APIArchiveFile, APIBundle
from .archives import checked_zip

CAPACITY_HEADER = ("DeliveryDate", "HourEnding", "AncillaryType", "MCPC", "DSTFlag")
OFFERS_HEADER = (
    "DeliveryDate",
    "HourEnding",
    "REGDN",
    "REGUP",
    "RRSPFR",
    "RRSFFR",
    "RRSUFR",
    "ECRSSD",
    "ECRSMD",
    "NSPIN",
    "DSTFlag",
)


@dataclass(frozen=True)
class CapacityRow:
    """Preserve one observed DAM capacity-price CSV row.

    Attributes:
        delivery_date: Source delivery date, without a timezone assumption.
        hour_ending: Source hour-ending text, including 24:00.
        ancillary_type: Original source ancillary-service identifier.
        mcpc: Finite decimal source price.
        dst_flag: Original source DST flag, without an inferred UTC interval.
    """

    delivery_date: datetime.date
    hour_ending: str
    ancillary_type: str
    mcpc: Decimal
    dst_flag: str


@dataclass(frozen=True)
class OfferedCapacityRow:
    """Preserve one retired NP4-179-CD total ancillary-offer CSV row.

    Attributes:
        delivery_date: Source delivery date.
        hour_ending: Original hour-ending text.
        regdn: REGDN source quantity.
        regup: REGUP source quantity.
        rrspfr: RRSPFR source quantity.
        rrsffr: RRSFFR source quantity.
        rrsufr: RRSUFR source quantity.
        ecrssd: ECRSSD source quantity.
        ecrsmd: ECRSMD source quantity.
        nspin: NSPIN source quantity.
        dst_flag: Original DST flag; no UTC conversion is asserted.
    """

    delivery_date: datetime.date
    hour_ending: str
    regdn: Decimal
    regup: Decimal
    rrspfr: Decimal
    rrsffr: Decimal
    rrsufr: Decimal
    ecrssd: Decimal
    ecrsmd: Decimal
    nspin: Decimal
    dst_flag: str


Row = TypeVar("Row", CapacityRow, OfferedCapacityRow)


@dataclass(frozen=True)
class ArchiveRowSample(Generic[Row]):
    """Bind a partial typed sample to both ZIP members and the outer receipt.

    Attributes:
        rows: Typed source rows up to the caller's limit.
        outer_member: Explicitly selected nested ZIP name.
        inner_member: Validated CSV name inside that ZIP.
        receipt: Exact outer public file identity.
        truncated: Whether the selected CSV has another row.
    """

    rows: tuple[Row, ...]
    outer_member: str
    inner_member: str
    receipt: Receipt
    truncated: bool


def _sample(file, member, max_rows, *, product, kind, header, model):
    """Check source identity and both ZIP layers before sampling one CSV.

    Args:
        file: Complete bounded public archive with a source receipt.
        member: Explicit selected outer ZIP member name.
        max_rows: Positive sample ceiling, at most 1000.
        product: Exact supported public product.
        kind: Exact archive or bundle download route.
        header: Pinned source CSV header.
        model: Supported row constructor.

    Returns:
        A typed partial sample with nested member and receipt identities.

    Raises:
        PublicDataError: Identity, size, ZIP, or CSV checks fail.
        ValueError: The sample budget is invalid.
    """
    if type(max_rows) is not int or not 1 <= max_rows <= 1000:
        raise ValueError("max_rows must be between 1 and 1000")
    if (
        file.document.emil_id != product
        or isinstance(file.document, APIBundle) != (kind == "bundle")
        or file.receipt.source_url != f"{BASE}/{kind}/{product}/download"
        or file.receipt.status != 200
    ):
        raise AccessDeniedError("Unsupported public file identity")
    if len(file.body) > 4_000_000:
        raise LimitError("CSV sample input byte budget exceeded")
    if (
        file.receipt.byte_count != len(file.body)
        or file.receipt.sha256 != hashlib.sha256(file.body).hexdigest()
    ):
        raise SchemaMismatchError("Public file differs from its receipt")
    try:
        with checked_zip(
            file.body, max_members=64, max_expanded_bytes=4_000_000
        ) as outer:
            if member not in file.members or not member.endswith(".zip"):
                raise SchemaMismatchError("Select an observed nested ZIP member")
            nested = outer.read(member)
        with checked_zip(nested, max_members=1, max_expanded_bytes=4_000_000) as inner:
            entries = inner.infolist()
            if (
                len(entries) != 1
                or entries[0].is_dir()
                or not entries[0].filename.endswith(".csv")
            ):
                raise SchemaMismatchError("Expected one CSV inside the selected ZIP")
            inner_name = entries[0].filename
            text = inner.read(entries[0]).decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        if tuple(next(reader, ())) != header:
            raise SchemaMismatchError("CSV header differs from the observed schema")
        rows = []
        truncated = False
        for raw in reader:
            if len(rows) == max_rows:
                truncated = True
                break
            if len(raw) != len(header):
                raise ValueError
            if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", raw[0]):
                raise ValueError
            month, day, year = (int(value) for value in raw[0].split("/"))
            date = datetime.date(year, month, day)
            if not re.fullmatch(r"(?:0[1-9]|1\d|2[0-4]):00", raw[1]) or raw[-1] not in {
                "Y",
                "N",
            }:
                raise ValueError
            numbers = [
                Decimal(v) for v in (raw[3:4] if model is CapacityRow else raw[2:-1])
            ]
            if any(not n.is_finite() for n in numbers):
                raise ValueError
            if model is CapacityRow:
                if not raw[2] or len(raw[2]) > 64:
                    raise ValueError
                rows.append(CapacityRow(date, raw[1], raw[2], numbers[0], raw[-1]))
            else:
                rows.append(OfferedCapacityRow(date, raw[1], *numbers, raw[-1]))
        return ArchiveRowSample(
            tuple(rows), member, inner_name, file.receipt, truncated
        )
    except (
        KeyError,
        ValueError,
        UnicodeError,
        csv.Error,
        InvalidOperation,
        zipfile.BadZipFile,
        zlib.error,
        NotImplementedError,
        RuntimeError,
    ):
        raise SchemaMismatchError(
            "Public nested CSV differs from its observed contract"
        ) from None


def sample_capacity_bundle(
    file: APIArchiveFile,
    *,
    member: str,
    max_rows: int = 4,
) -> ArchiveRowSample[CapacityRow]:
    """Sample one observed NP4-188-CD nested CSV from a selected bundle.

    Args:
        file: Public capacity bundle with a verified receipt.
        member: Exact selected outer member name.
        max_rows: Sample ceiling from 1 through 1000.

    Returns:
        Typed partial rows with source and member identities.

    Raises:
        PublicDataError: Source identity, ZIP, or CSV checks fail.
        ValueError: The row budget is invalid.
    """
    return _sample(
        file,
        member,
        max_rows,
        product="np4-188-cd",
        kind="bundle",
        header=CAPACITY_HEADER,
        model=CapacityRow,
    )


def sample_retired_offers(
    file: APIArchiveFile,
    *,
    member: str,
    max_rows: int = 4,
) -> ArchiveRowSample[OfferedCapacityRow]:
    """Sample one observed retired NP4-179-CD archive CSV.

    Args:
        file: Public retired offer archive with a verified receipt.
        member: Exact selected outer member name.
        max_rows: Sample ceiling from 1 through 1000.

    Returns:
        Typed partial rows without a claim about other retired formats.

    Raises:
        PublicDataError: Source identity, ZIP, or CSV checks fail.
        ValueError: The row budget is invalid.
    """
    return _sample(
        file,
        member,
        max_rows,
        product="np4-179-cd",
        kind="archive",
        header=OFFERS_HEADER,
        model=OfferedCapacityRow,
    )
