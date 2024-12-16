# templatetags.py en tu aplicación (panel_admin o tienda)
from django import template

register = template.Library()

@register.filter
def get(dictionary, key):
    """Obtiene un valor de un diccionario usando la clave."""
    return dictionary.get(key)