def client_ip(request):
    """Best-effort client IP, honoring a single proxy hop via X-Forwarded-For."""
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
