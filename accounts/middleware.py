from django.utils import timezone


class UpdateLastActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Update last_active timestamp
            try:
                request.user.userprofile.last_active = timezone.now()
                request.user.userprofile.save(update_fields=["last_active"])
            except:
                pass  # If there's any error, just continue

        return response
