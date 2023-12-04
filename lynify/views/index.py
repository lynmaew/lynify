from django.http import HttpResponse

from lynify.views.html import SpotifyLogin, display_currently_playing, header


def index(request):
    html = header()
    token_success, token_result = SpotifyLogin(request)
    if not token_success:
        html += token_result
        return HttpResponse(html)

    html += display_currently_playing()
    return HttpResponse(html)
