from django.http import HttpResponse

from lynify.models.tracks import TrackModel
from lynify.views.html import SpotifyLogin, header


def tracks(request):
    limit = request.GET.get("limit", "25")
    offset = request.GET.get("offset", "0")
    limit = int(limit)
    offset = int(offset)
    html = header()
    token_success, token_result = SpotifyLogin(request)
    if not token_success:
        html += token_result
        return HttpResponse(html)

    tracks = TrackModel.objects.all()[offset : offset + limit]
    html += "<table>"
    col_names = [
        "Track",
        "Artist",
        "Album",
        "Duration",
        "Popularity",
        "Release Date",
        "Explicit",
        "Genres",
        "Artist IDs",
    ]
    html += "<tr>"
    for col_name in col_names:
        html += "<th>" + col_name + "</th>"
    html += "</tr>"
    for track in tracks:
        html += "<tr>"
        track_link = '<a href="/track?track_id=' + track.track_id + '">' + track.track_name + "</a>"
        artists = track.track_artists.all()
        artist_links = []
        for artist in artists:
            artist_links.append('<a href="/artist?artist_id=' + artist.artist_id + '">' + artist.artist_name + "</a>")
        artist_links = ", ".join(artist_links)
        cols = [
            track_link,
            artist_links,
            track.track_album,
            str(track.track_duration),
            str(track.track_popularity),
            track.track_release_date.strftime("%Y-%m-%d"),
            str(track.track_explicit),
        ]
        for col in cols:
            html += "<td>" + col + "</td>"
        html += "</tr>"
    html += "</table>"
    # add pagination
    html += '<div class="w3-bar w3-black">'
    if offset > 0:
        prev_offset = max(0, offset - limit)
        html += (
            '<a href="/tracks?limit='
            + str(limit)
            + "&offset="
            + str(prev_offset)
            + '" class="w3-bar-item w3-button">Previous</a>'
        )
    if offset + limit < TrackModel.objects.count():
        html += (
            '<a href="/tracks?limit='
            + str(limit)
            + "&offset="
            + str(offset + limit)
            + '" class="w3-bar-item w3-button">Next</a>'
        )
    html += "</div>"
    return HttpResponse(html)
