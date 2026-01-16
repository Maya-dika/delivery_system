from django import template
from core.models import Currency

register = template.Library()

@register.filter
def format_currency(amount, currency=None):
    """
    Formats numbers with commas and currency symbol.
    Usage: {{ amount|format_currency:order.currency }}
    """
    if amount is None:
        return "-"
    
    if currency is None:
        currency = Currency.objects.filter(name="USD").first()
    
    symbol = getattr(currency, "symbol", "")
    try:
        formatted = f"{amount:,.2f}"
    except Exception:
        formatted = str(amount)

    if symbol in ["$", "€", "£"]:
        return f"{symbol}{formatted}"
    return f"{formatted} {symbol}".strip()


@register.filter
def display_order_price(order):
    """Return order price string with optional secondary currency.
    Usage: {{ order|display_order_price }}
    """
    try:
        primary_amt = getattr(order, 'order_price', None)
        primary_curr = getattr(order, 'currency', None)
        secondary_amt = getattr(order, 'order_price_secondary', None)
        secondary_curr = getattr(order, 'currency_secondary', None)

        primary = format_currency(primary_amt, primary_curr) if primary_amt is not None else ''
        if primary == '-':
            primary = ''
        secondary = ''
        if secondary_amt is not None and secondary_curr is not None:
            secondary = format_currency(secondary_amt, secondary_curr)
            if secondary == '-':
                secondary = ''

        if primary and secondary:
            return f"{primary} + {secondary}"
        return primary or secondary or '-'
    except Exception:
        return '-'
