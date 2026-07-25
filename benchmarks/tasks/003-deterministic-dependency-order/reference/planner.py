"""Plan task execution from declared dependencies."""

from heapq import heappop, heappush


def resolve_task_order(
    tasks: dict[str, list[str] | tuple[str, ...]],
) -> list[str]:
    """Return a deterministic topological order for declared tasks."""

    if not isinstance(tasks, dict):
        raise ValueError("tasks must be a dictionary")

    names = set(tasks)
    if any(not isinstance(name, str) or not name for name in names):
        raise ValueError("task names must be non-empty strings")

    normalized: dict[str, set[str]] = {}
    for task, dependencies in tasks.items():
        if not isinstance(dependencies, (list, tuple)):
            raise ValueError(
                f"dependencies for {task} must be a list or tuple"
            )
        if any(
            not isinstance(dependency, str) or not dependency
            for dependency in dependencies
        ):
            raise ValueError(
                f"dependencies for {task} must be non-empty strings"
            )
        normalized[task] = set(dependencies)

    unknown = sorted(
        (task, dependency)
        for task, dependencies in normalized.items()
        for dependency in dependencies
        if dependency not in names
    )
    if unknown:
        task, dependency = unknown[0]
        raise ValueError(f"unknown dependency: {task} -> {dependency}")

    indegree = {
        task: len(dependencies)
        for task, dependencies in normalized.items()
    }
    dependents: dict[str, set[str]] = {task: set() for task in names}
    for task, dependencies in normalized.items():
        for dependency in dependencies:
            dependents[dependency].add(task)

    ready = [task for task, count in indegree.items() if count == 0]
    ready.sort()
    result: list[str] = []
    while ready:
        task = heappop(ready)
        result.append(task)
        for dependent in sorted(dependents[task]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heappush(ready, dependent)

    if len(result) != len(names):
        blocked = sorted(names - set(result))
        raise ValueError("dependency cycle: " + ", ".join(blocked))
    return result
