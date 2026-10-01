from django.conf import settings
from django.core.checks import Error, register


@register()
def broken_on_purpose_check(app_configs, **kwargs):
    """Demo hook: manage.py check must fail when this flag is on."""
    if getattr(settings, "BROKEN_ON_PURPOSE", False):
        return [
            Error(
                "BROKEN_ON_PURPOSE is True. A system check failure like this "
                "is what used to reach staging.",
                id="catalog.E001",
            )
        ]
    return []
