from django.http import JsonResponse


def health(request):
<<<<<<< HEAD
    return JsonResponse({"ok": True})
=======
    return JsonResponse({"ok": False})
>>>>>>> feature/health
