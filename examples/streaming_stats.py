"""
Streaming Statistical Processor
===============================

First Principles: When processing large datasets, the naive approach
buffers all data before computing statistics. This is O(n) memory.

Welford's Online Algorithm computes running mean and variance in O(1)
memory using a single pass. As each datum arrives, we update:

    count += 1
    delta = x - mean
    mean += delta / count
    M2 += delta * (x - mean)
    variance = M2 / count

This demo streams ERCOT price data page-by-page, computing statistics
incrementally. Watch the numbers converge as data flows in.

Usage:
    uv run --env-file .env python examples/streaming_stats.py
"""

import asyncio
import sys
from dataclasses import dataclass
from datetime import date, timedelta

import tinyercot


@dataclass
class StreamingStats:
    """
    Welford's Online Algorithm for streaming mean/variance.

    Reference: Welford, B.P. (1962). "Note on a method for calculating
    corrected sums of squares and products". Technometrics. 4 (3): 419-420.
    """

    count: int = 0
    mean: float = 0.0
    m2: float = 0.0  # Sum of squared differences from mean
    min_val: float = float("inf")
    max_val: float = float("-inf")
    unique_points: set = None  # Track unique settlement points

    def __post_init__(self):
        self.unique_points = set()

    def update(self, x: float, point: str = None) -> None:
        """Update running statistics with new observation."""
        self.count += 1
        delta = x - self.mean
        self.mean += delta / self.count
        delta2 = x - self.mean
        self.m2 += delta * delta2
        self.min_val = min(self.min_val, x)
        self.max_val = max(self.max_val, x)
        if point:
            self.unique_points.add(point)

    @property
    def variance(self) -> float:
        return self.m2 / self.count if self.count > 1 else 0.0

    @property
    def std(self) -> float:
        return self.variance**0.5


def clear_line():
    """Clear current line and move cursor to beginning."""
    sys.stdout.write("\033[2K\033[G")
    sys.stdout.flush()


def move_up(n: int = 1):
    """Move cursor up n lines."""
    sys.stdout.write(f"\033[{n}A")
    sys.stdout.flush()


def print_stats_header():
    """Print the statistics display header."""
    print()
    print("=" * 74)
    print("STREAMING PRICE ANALYSIS :: ALL TEXAS SETTLEMENT POINTS")
    print("=" * 74)
    print()
    print(
        "  Records   |  Nodes  |    Mean    |   Std Dev  |     Min    |     Max"
    )
    print("-" * 74)
    print()  # Placeholder for stats line
    print()  # Placeholder for status line
    print("-" * 74)


def update_display(stats: StreamingStats, pages: int, status: str):
    """Update the live display with current statistics."""
    move_up(3)
    clear_line()

    if stats.count > 0:
        nodes = len(stats.unique_points)
        print(
            f"  {stats.count:>7,}   |  {nodes:>5,}  |  "
            f"${stats.mean:>8.2f}  |  "
            f"${stats.std:>8.2f}  |  "
            f"${stats.min_val:>8.2f}  |  "
            f"${stats.max_val:>8.2f}"
        )
    else:
        print("  Waiting for data...")

    clear_line()
    print(f"  [{pages} pages fetched] {status}")
    print("-" * 74)


async def stream_prices(start: date, end: date, stats: StreamingStats):
    """
    Stream price data and update statistics in real-time.

    Key insight: The async generator yields data page-by-page as it
    arrives from the API. We process each datum immediately rather
    than buffering the entire dataset.

    Fetches ALL settlement points across Texas for maximum data volume.
    """
    page_count = 0
    record_count = 0

    print_stats_header()
    update_display(stats, 0, "Initializing...")

    # No settlementPoint filter = ALL points across Texas (massive dataset)
    async for row in tinyercot.np4_190_cd.dam_stlmnt_pnt_prices_iter_async(
        deliveryDateFrom=start,
        deliveryDateTo=end,
    ):
        # Update streaming statistics with new price
        price = float(row.settlementPointPrice)
        stats.update(price, point=row.settlementPoint)
        record_count += 1

        # Update display every 500 records (avoid flicker)
        if record_count % 500 == 0:
            page_count = (record_count // 1000) + 1
            update_display(
                stats, page_count, f"Processing... {record_count:,} records"
            )

    # Final update
    page_count = (record_count // 1000) + 1
    update_display(stats, page_count, "Complete")

    return stats


async def main():
    print(__doc__)

    # Configure date range - 3 days of ALL settlement points = massive data
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=2)

    print(f"Date Range: {start} to {end}")
    print("Settlement Points: ALL (thousands of nodes across Texas)")
    print()
    print("Streaming data with rate limiting (30 req/min)...")
    print("Watch statistics converge as data flows in.")

    # Initialize streaming statistics
    stats = StreamingStats()

    # Stream and process
    start_time = asyncio.get_event_loop().time()
    await stream_prices(start, end, stats)
    elapsed = asyncio.get_event_loop().time() - start_time

    # Final summary
    print()
    print("=" * 74)
    print("FINAL RESULTS")
    print("=" * 74)
    print()
    print(f"  Total Records:     {stats.count:,}")
    print(f"  Unique Nodes:      {len(stats.unique_points):,}")
    print(f"  Processing Time:   {elapsed:.1f} seconds")
    print(f"  Throughput:        {stats.count / elapsed:,.0f} records/sec")
    print()
    print("  Price Statistics ($/MWh):")
    print(f"    Mean:            ${stats.mean:.2f}")
    print(f"    Std Deviation:   ${stats.std:.2f}")
    print(f"    Minimum:         ${stats.min_val:.2f}")
    print(f"    Maximum:         ${stats.max_val:.2f}")
    print(f"    Range:           ${stats.max_val - stats.min_val:.2f}")
    print()

    # Compute coefficient of variation (volatility measure)
    cv = (stats.std / stats.mean * 100) if stats.mean > 0 else 0
    print(f"  Volatility (CV):   {cv:.1f}%")

    if cv > 50:
        print("  Assessment:        HIGH volatility - significant price swings")
    elif cv > 25:
        print(
            "  Assessment:        MODERATE volatility - typical market conditions"
        )
    else:
        print("  Assessment:        LOW volatility - stable pricing period")

    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
