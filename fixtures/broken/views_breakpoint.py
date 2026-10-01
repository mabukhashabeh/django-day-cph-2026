from django.http import JsonResponse


def health(request):
    breakpoint()  # demo 1: debug-statements must block this
    return JsonResponse({"ok": True})
