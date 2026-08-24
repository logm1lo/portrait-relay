#!/usr/bin/env python3
"""Record repeatable media throughput and peak-memory characterization."""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import time
from pathlib import Path

import psutil


def run_once(command: list[str]) -> tuple[float, int]:
    """Run one benchmark command and return seconds and peak RSS bytes."""

    started = time.perf_counter()
    process = subprocess.Popen(command)
    observed_peak = 0
    monitored = psutil.Process(process.pid)
    while process.poll() is None:
        try:
            observed_peak = max(observed_peak, monitored.memory_info().rss)
        except psutil.Error:
            break
        time.sleep(0.05)
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command)
    return time.perf_counter() - started, observed_peak


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--runs", type=int, default=3)
    arguments = parser.parse_args()
    if arguments.runs < 3:
        parser.error("--runs must be at least 3")
    arguments.output_directory.mkdir(parents=True, exist_ok=True)
    timings: list[float] = []
    peaks: list[int] = []
    for index in range(arguments.runs):
        output = arguments.output_directory / f"run-{index}.mp4"
        command = [
            "portrait-relay",
            "--source",
            str(arguments.source),
            "--target",
            str(arguments.target),
            "--output",
            str(output),
            "--execution-provider",
            arguments.provider,
        ]
        seconds, peak = run_once(command)
        timings.append(seconds)
        peaks.append(peak)
    result = {
        "provider": arguments.provider,
        "runs": arguments.runs,
        "median_seconds": statistics.median(timings),
        "maximum_peak_rss_bytes": max(peaks),
        "timings_seconds": timings,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
