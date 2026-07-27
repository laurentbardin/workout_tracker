from django import template

register = template.Library()

@register.simple_tag
def classes(**kwclasses):
    """
    The `classes` template tag conditionally outputs a list of classes
    separated by spaces. It should be used when the desired classes can each be
    easily evaluted against a boolean value. For example, assuming the book
    model has boolean fields indicating if it's been read and/or lent to
    somebody:

    {% for book in books %}
        <div class="book {% classes read=book.read lent=book.lent %}">
        ...
        </div>
    {% endfor %}

    Depending on the value of those fields, this can produce any of the
    following strings: "read lent", "read", "lent", or "".
    """
    return ' '.join([name for name, test in kwclasses.items() if test])

