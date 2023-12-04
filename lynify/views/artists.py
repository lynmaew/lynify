from django.http import HttpResponse

from lynify.models.artists import ArtistModel
from lynify.views.html import SpotifyLogin, header


def artists(request):
    limit = request.GET.get("limit", "25")
    offset = request.GET.get("offset", "0")
    limit = int(limit)
    offset = int(offset)
    html = header()
    token_success, token_result = SpotifyLogin(request)
    if not token_success:
        html += token_result
        return HttpResponse(html)

    artist_list = ArtistModel.objects.all()[offset : offset + limit]  # .get_all_limit_offset(limit, offset)
    html += "<table>"
    html += "<tr><th>Artist</th><th>Genres</th><th>Popularity</th><th>Followers</th></tr>"
    for artist in artist_list:
        html += "<tr>"
        artist_link = '<a href="/artist?artist_id=' + artist.artist_id + '">' + artist.artist_name + "</a>"
        cols = [artist_link, str(artist.artist_genres), str(artist.artist_popularity), str(artist.artist_followers)]
        for col in cols:
            html += "<td>" + col + "</td>"
        html += "</tr>"
    html += "</table>"

    # add pagination
    html += '<div class="w3-bar w3-black">'
    if offset > 0:
        prev_offset = max(0, offset - limit)
        html += (
            '<a href="/artists?limit='
            + str(limit)
            + "&offset="
            + str(prev_offset)
            + '" class="w3-bar-item w3-button">Previous</a>'
        )
    if offset + limit < ArtistModel.objects.count():
        html += (
            '<a href="/artists?limit='
            + str(limit)
            + "&offset="
            + str(offset + limit)
            + '" class="w3-bar-item w3-button">Next</a>'
        )
    html += "</div>"
    return HttpResponse(html)
