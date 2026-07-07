from django.http import JsonResponse


def home(request):
    return JsonResponse({
        "success": True,
        "message": "University Project & Thesis Management API is Running 🚀",
        "version": "1.0.0"
    })