def format_currency(value) -> str:
    """
    Formats a numeric value as a currency string.
    Why: Visual consistency across revenue representation.
    """
    if value is None:
        return "0.00"
    try:
        val = float(value)
        return f"{val:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value, is_ratio=True) -> str:
    """
    Formats a numeric value as a percentage.
    If is_ratio is True, assumes value is e.g. 0.124 for 12.4%.
    If is_ratio is False, assumes value is e.g. 12.4 for 12.4%.
    Why: Direct growth metrics formatting.
    """
    if value is None:
        return "0.0%"
    try:
        val = float(value)
        if is_ratio:
            val = val * 100
        prefix = "+" if val > 0 else ""
        return f"{prefix}{val:.1f}%"
    except (ValueError, TypeError):
        return str(value)


def format_number(value) -> str:
    """
    Formats counts/integer sizes.
    Why: Handles customer counts and product volume.
    """
    if value is None:
        return "0"
    try:
        val = float(value)
        if val.is_integer():
            return f"{int(val):,}"
        return f"{val:,.2f}"
    except (ValueError, TypeError):
        return str(value)
