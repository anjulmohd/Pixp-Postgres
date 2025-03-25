from django import template

register = template.Library()

@register.filter
def abs_value(value):
    """Returns the absolute value of a number."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value  # Return original value if conversion fails
