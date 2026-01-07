from django.conf import settings
from django.utils import timezone

class TimezoneMiddleware:
    """
    Activate the local timezone for the request.

    This should be a per-user setting in a real multi-user scenario, but that's
    not planned for now so this will have to do.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.current_timezone = getattr(
            settings, "USER_TIME_ZONE", settings.TIME_ZONE
        )

    def __call__(self, request):
        timezone.activate(self.current_timezone)

        return self.get_response(request)
