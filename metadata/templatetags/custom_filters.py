from django import template

# Register the library under a specific name
register = template.Library()

@register.filter(name='replace')
def replace(value, arg):
    """
    Replaces all occurrences of a substring with another string.
    Usage: {{ value|replace:"from,to" }}
    """
    if not isinstance(value, str):
        return value
        
    try:
        # The argument should be a comma-separated string: "old,new"
        old, new = arg.split(',', 1)
    except ValueError:
        # Handle cases where arg is not correctly formatted
        return value 
    
    return value.replace(old, new)