"""Merge configuration layers."""

from copy import deepcopy


def _validate_mapping(value):
    for key, child in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError("configuration keys must be non-empty strings")
        if isinstance(child, dict):
            _validate_mapping(child)


def _sorted_copy(value):
    if isinstance(value, dict):
        return {
            key: _sorted_copy(value[key])
            for key in sorted(value)
        }
    return deepcopy(value)


def _merge(current, incoming):
    result = deepcopy(current) if isinstance(current, dict) else {}
    for key, value in incoming.items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict):
            result[key] = _merge(result.get(key), value)
        else:
            result[key] = deepcopy(value)
    return result


def merge_config_layers(layers):
    """Return a deterministic deep merge of configuration layers."""

    if not isinstance(layers, (list, tuple)):
        raise ValueError("layers must be a list or tuple")

    result = {}
    for layer in layers:
        if not isinstance(layer, dict):
            raise ValueError("each layer must be a dictionary")
        _validate_mapping(layer)
        result = _merge(result, layer)
    return _sorted_copy(result)
