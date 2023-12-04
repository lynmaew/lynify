from django.http import HttpResponse

from lynify.models.artists import ArtistModel
from lynify.views.html import SpotifyLogin, header


def artist(request):
    html = header()
    token_success, token_result = SpotifyLogin(request)
    if not token_success:
        html += token_result
        return HttpResponse(html)

    artist_id = request.GET.get("artist_id", "")
    if artist_id == "":
        html += "No artist ID provided"
        return HttpResponse(html)
    artist = ArtistModel.objects.get(artist_id=artist_id)
    html += "<table>"
    html += "<tr><th>Artist</th><th>Genres</th><th>Popularity</th><th>Followers</th></tr>"
    html += "<tr>"
    artist_link = '<a href="/artist?artist_id=' + artist.artist_id + '">' + artist.artist_name + "</a>"
    cols = [artist_link, str(artist.artist_genres), str(artist.artist_popularity), str(artist.artist_followers)]
    for col in cols:
        html += "<td>" + col + "</td>"
    html += "</tr>"
    html += "</table>"
    return HttpResponse(html)
