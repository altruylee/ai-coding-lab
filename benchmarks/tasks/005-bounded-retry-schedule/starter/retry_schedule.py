"""Construct retry delays."""


def build_retry_delays(attempts, base_delay, max_delay, jitter):
    """Return a basic exponential schedule."""

    return [
        base_delay * (2 ** index) * (1 + jitter[index])
        for index in range(attempts - 1)
    ]
