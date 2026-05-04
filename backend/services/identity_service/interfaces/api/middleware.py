class AuditRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        else:
            ip_address = request.META.get("REMOTE_ADDR", "")
        request.audit_context = {
            "ip_address": ip_address,
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        }
        return self.get_response(request)
