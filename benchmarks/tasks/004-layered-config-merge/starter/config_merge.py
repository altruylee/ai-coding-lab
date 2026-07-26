"""Merge configuration layers."""


def merge_config_layers(layers):
    """Return a shallow merge of configuration layers."""

    result = {}
    for layer in layers:
        result.update(layer)
    return result
