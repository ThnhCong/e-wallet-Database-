from decimal import Decimal


def money(value, currency="VND"):
    amount = Decimal(str(value or 0))
    return f"{amount:,.2f} {currency}"


def display(value):
    return "-" if value is None or value == "" else str(value)


def short_time(value):
    return value.strftime("%Y-%m-%d %H:%M") if hasattr(value, "strftime") else display(value)
