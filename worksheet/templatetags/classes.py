from django import template

register = template.Library()

@register.simple_tag
def classes(**kwclasses):
    return ' '.join([name for name, test in kwclasses.items() if test])

