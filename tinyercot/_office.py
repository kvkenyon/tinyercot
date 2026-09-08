"""Read Excel's default workbook protection on public historical files."""

from collections.abc import Callable
from io import BytesIO
from typing import Protocol, cast


class _OfficeFile(Protocol):
    def load_key(self, *, password: str) -> None: ...
    def decrypt(self, outfile: BytesIO) -> None: ...


def _unprotect_excel(data: bytes) -> bytes:
    try:
        import msoffcrypto
    except ImportError as error:
        raise ImportError(
            "Install tinyercot[files] to read protected historical Excel files"
        ) from error
    # Excel/LibreOffice use this public, built-in key for workbook protection.
    # A different password fails normally; no credentials are requested or tried.
    factory = cast(Callable[[BytesIO], _OfficeFile], msoffcrypto.OfficeFile)
    office = factory(BytesIO(data))
    office.load_key(password="VelvetSweatshop")
    output = BytesIO()
    office.decrypt(output)
    return output.getvalue()
