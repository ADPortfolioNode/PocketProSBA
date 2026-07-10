"""Shared dual-path imports for backend.services / services package layouts."""


def import_from_services(module_name: str, *attr_names: str):
    """
    Import attributes from backend.services.<module> with fallback to services.<module>.

    Returns a single object if one attr is requested, else a tuple of attributes.
    """
    candidates = (
        f"backend.services.{module_name}",
        f"services.{module_name}",
    )
    last_error = None
    for dotted in candidates:
        try:
            module = __import__(dotted, fromlist=list(attr_names) or ["*"])
            if not attr_names:
                return module
            values = tuple(getattr(module, name) for name in attr_names)
            return values[0] if len(values) == 1 else values
        except Exception as exc:  # ImportError or missing attr
            last_error = exc
            continue
    raise ImportError(
        f"Could not import {', '.join(attr_names) or module_name} "
        f"from services.{module_name}: {last_error}"
    )
