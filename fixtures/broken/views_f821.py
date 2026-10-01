from django.http import JsonResponse


def health(request):
    # flake8 F821: undefined name
    return JsonResponse({"ok": ok})
