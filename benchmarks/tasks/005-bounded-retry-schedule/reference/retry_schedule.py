"""Construct retry delays."""

import math


def _number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def build_retry_delays(attempts, base_delay, max_delay, jitter):
    """Return validated bounded exponential retry delays."""

    if (
        not isinstance(attempts, int)
        or isinstance(attempts, bool)
        or not 1 <= attempts <= 20
    ):
        raise ValueError("attempts must be an integer from 1 through 20")
    if not _number(base_delay) or base_delay <= 0:
        raise ValueError("base_delay must be a finite positive number")
    if not _number(max_delay) or max_delay <= 0:
        raise ValueError("max_delay must be a finite positive number")
    if max_delay < base_delay:
        raise ValueError("max_delay must be at least base_delay")
    if not isinstance(jitter, (list, tuple)):
        raise ValueError("jitter must be a list or tuple")
    if len(jitter) != attempts - 1:
        raise ValueError("jitter length must equal attempts minus one")
    if any(not _number(value) or not -0.5 <= value <= 0.5 for value in jitter):
        raise ValueError("jitter values must be finite numbers from -0.5 to 0.5")

    result = []
    for index, factor in enumerate(jitter):
        unjittered = min(float(max_delay), float(base_delay) * (2 ** index))
        adjusted = unjittered * (1 + factor)
        result.append(round(min(float(max_delay), max(0.0, adjusted)), 6))
    return result
