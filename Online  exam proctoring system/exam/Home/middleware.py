from django.http import HttpResponseRedirect
from django.urls import reverse

class RedirectIfAuthenticatedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and (request.path == '/login' or request.path == '/signup'):  
            return HttpResponseRedirect(reverse('home'))  
        return self.get_response(request)
