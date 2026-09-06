"""Check direct installed-wheel module types without running a data request."""

from typing import assert_type

from tinyercot.public.api import Credentials
from tinyercot.public.api_archives import APIArchiveFile, APIArchivePage, APIBundlePage
from tinyercot.public.archive_api import ArchiveAPIClient
from tinyercot.public.archive_http import Exchange
from tinyercot.public.archive_rows import (
    ArchiveRowSample,
    CapacityRow,
    sample_capacity_bundle,
)
from tinyercot.public.esr_api import ESRAPIClient, RawESRPage


def contracts(credentials: Credentials) -> None:
    """Check public return types without calling this function.

    Args:
        credentials: Explicit account credentials required by both clients.
    """
    with ESRAPIClient(credentials) as esr:
        assert_type(esr.current(), RawESRPage)
        assert_type(esr.exchanges, tuple[Exchange, ...])
    with ArchiveAPIClient(credentials) as archive:
        archive.products()
        page = archive.archives("NP3-988-ER")
        assert_type(page, APIArchivePage)
        assert_type(archive.bundles("NP4-190-CD"), APIBundlePage)
        assert_type(archive.download(page.documents[0]), APIArchiveFile)
        file = archive.download(page.documents[0])
        assert_type(
            sample_capacity_bundle(file, member="selected.zip"),
            ArchiveRowSample[CapacityRow],
        )
