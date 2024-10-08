from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.core.cache import cache

class RateLimitMiddleware(MiddlewareMixin):
    RATE_LIMIT = 100  # Number of allowed requests
    TIME_PERIOD = 60  # Time period in seconds

    def process_request(self, request):
        ip = self.get_client_ip(request)
        key = f'rate-limit-{ip}'
        
        request_count = cache.get(key)
        if request_count is None:
            cache.set(key, 0, timeout=self.TIME_PERIOD)
            request_count = 0
        
        if request_count >= self.RATE_LIMIT:
            return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
        
        cache.incr(key)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip