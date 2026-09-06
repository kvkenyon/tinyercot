"""Optional, source-specific CSV decoding for the public NP3-988-ER archive.

Source: https://www.ercot.com/mp/data-products/data-product-details?id=np3-988-er
Every field remains source text; identifier zeros, blanks, and flags are retained.
"""

import csv
import hashlib
import io
import zipfile
import zlib
from collections.abc import Generator
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, StrictStr

from ._http import AccessDeniedError, LimitError, SchemaMismatchError
from .api import BASE
from .api_archives import APIArchiveFile
from .archives import checked_zip

_HEADER = (
    "OWNER RE",
    "RESOURCE NAME",
    "TYPE",
    "SPLIT GEN RESOURCE",
    "DME",
    "DME DUNS",
    "RMR",
)


class ResourceDmeRow(BaseModel):
    """One source-backed public resource decision-making entity CSV row.

    Attributes:
        owner_re: Original owner resource-entity text.
        resource_name: Original resource identifier.
        resource_type: Original TYPE text, without an inferred enumeration.
        split_gen_resource: Original split-generation-resource text.
        dme: Original decision-making-entity text.
        dme_duns: Original identifier text, preserving leading zeros.
        rmr: Original RMR flag text, without inferred boolean semantics.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    owner_re: StrictStr
    resource_name: StrictStr
    resource_type: StrictStr
    split_gen_resource: StrictStr
    dme: StrictStr
    dme_duns: StrictStr
    rmr: StrictStr


@dataclass(frozen=True)
class ResourceDmeRecord:
    """A public CSV row with its logical record and archive identities.

    Attributes:
        row: Source text fields with exact observed header meanings.
        record_number: One-based CSV record number, including the header.
        member: Original ZIP member name.
        source_sha256: Exact selected source ZIP hash.
    """

    row: ResourceDmeRow
    record_number: int
    member: str
    source_sha256: str


def iter_resource_dme(
    archive_file: APIArchiveFile,
    *,
    max_rows: int | None = 1000,
    max_expanded_bytes: int = 4_000_000,
) -> Generator[ResourceDmeRecord, None, None]:
    """Decode the verified seven-column NP3-988-ER CSV as source text.

    Args:
        archive_file: One selected public NP3-988-ER ZIP with its matching receipt.
        max_rows: Record budget, or None for complete selected-document iteration.
        max_expanded_bytes: Maximum combined advertised ZIP expansion in bytes.

    Yields:
        Typed rows without trimming, coercing, normalizing identifiers, or changing
        source order. Close the generator if stopping early to release ZIP streams.

    Raises:
        ValueError: A caller-selected budget is invalid.
        PublicDataError: Source identity, receipt, ZIP, encoding, schema, or budget
            checks fail. Exhaustion never silently reports a complete result.
    """
    if max_rows is not None and (type(max_rows) is not int or max_rows < 1):
        raise ValueError("max_rows must be positive or None")
    if type(max_expanded_bytes) is not int or max_expanded_bytes < 1:
        raise ValueError("max_expanded_bytes must be positive")
    document = archive_file.document
    if document.emil_id != "np3-988-er":
        raise AccessDeniedError("Only public NP3-988-ER resource CSVs are supported")
    receipt = archive_file.receipt
    if (
        receipt.source_url != BASE + "/archive/np3-988-er/download"
        or receipt.byte_count != len(archive_file.body)
        or receipt.sha256 != hashlib.sha256(archive_file.body).hexdigest()
    ):
        raise SchemaMismatchError("Resource CSV archive differs from its receipt")
    try:
        with checked_zip(
            archive_file.body, max_members=4, max_expanded_bytes=max_expanded_bytes
        ) as archive:
            members = [member for member in archive.infolist() if not member.is_dir()]
            if (
                len(members) != 1
                or not members[0].filename.lower().endswith(".csv")
                or not members[0].filename.startswith(f"{document.document_id}.")
                or tuple(member.filename for member in members) != archive_file.members
            ):
                raise SchemaMismatchError("Unknown resource CSV archive container")
            member = members[0].filename
            with (
                archive.open(member) as binary,
                io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as stream,
            ):
                records = csv.reader(stream, strict=True)
                if tuple(next(records, ())) != _HEADER:
                    raise SchemaMismatchError("Unknown resource CSV schema epoch")
                for number, cells in enumerate(records, start=2):
                    if max_rows is not None and number - 1 > max_rows:
                        raise LimitError(
                            "Resource CSV row budget reached before completion"
                        )
                    if len(cells) != len(_HEADER):
                        raise SchemaMismatchError("Resource CSV column count changed")
                    yield ResourceDmeRecord(
                        ResourceDmeRow(
                            owner_re=cells[0],
                            resource_name=cells[1],
                            resource_type=cells[2],
                            split_gen_resource=cells[3],
                            dme=cells[4],
                            dme_duns=cells[5],
                            rmr=cells[6],
                        ),
                        number,
                        member,
                        receipt.sha256,
                    )
    except (
        csv.Error,
        UnicodeError,
        zipfile.BadZipFile,
        zlib.error,
        NotImplementedError,
    ):
        raise SchemaMismatchError(
            "Resource CSV decoding differs from the observed contract"
        ) from None
