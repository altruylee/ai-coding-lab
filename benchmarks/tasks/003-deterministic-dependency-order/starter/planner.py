"""Plan task execution from declared dependencies."""


def resolve_task_order(tasks: dict[str, list[str]]) -> list[str]:
    """Return tasks after adding each task's direct dependencies."""

    result: list[str] = []
    for task, dependencies in tasks.items():
        for dependency in dependencies:
            if dependency not in result:
                result.append(dependency)
        if task not in result:
            result.append(task)
    return result
