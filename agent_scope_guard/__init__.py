"""Guard AI coding changes with explicit repository scope policies."""

from .policy import Policy, PolicyError, ScopeViolation, evaluate_paths, load_policy

__all__ = [
    "Policy",
    "PolicyError",
    "ScopeViolation",
    "evaluate_paths",
    "load_policy",
]

__version__ = "0.1.0"
