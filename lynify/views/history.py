from django.http import HttpResponse

from lynify.models.history import HistoryModel
from lynify.models.tracks import TrackModel
from lynify.views.html import SpotifyLogin, header


def history(request):
    limit = request.GET.get("limit", "25")
    offset = request.GET.get("offset", "0")
    limit = int(limit)
    offset = int(offset)
    html = header()
    token_success, token_result = SpotifyLogin(request)
    if not token_success:
        html += token_result
        return HttpResponse(html)
    # left join to reduce sql calls
    entries = HistoryModel.objects.all()[offset : offset + limit]
    html += "<table>"
    html += "<tr><th>Track</th><th>Artist</th><th>Album</th><th>Date</th><th>Time</th></tr>"
    for entry in entries:
        try:
            track = TrackModel.objects.get(track_id=entry.track.track_id)
        except TrackModel.DoesNotExist:
            track = TrackModel.from_spotify(entry.track.track_id)
        if track is None:
            continue
        html += "<tr>"
        track_link = '<a href="/track?track_id=' + track.track_id + '">' + track.track_name + "</a>"
        artists = track.track_artists.all()
        artist_links = []
        for artist in artists:
            artist_links.append('<a href="/artist?artist_id=' + artist.artist_id + '">' + artist.artist_name + "</a>")
        artist_links = ", ".join(artist_links)
        entry_dt = entry.timestamp
        date = entry_dt.strftime("%Y-%m-%d")
        time = entry_dt.strftime("%H:%M:%S")
        cols = [
            track_link,
            artist_links,
            track.track_album,
            date,
            time,
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
            '<a href="/history?limit='
            + str(limit)
            + "&offset="
            + str(prev_offset)
            + '" class="w3-bar-item w3-button">Previous</a>'
        )
    if offset + limit < HistoryModel.objects.count():
        html += (
            '<a href="/history?limit='
            + str(limit)
            + "&offset="
            + str(offset + limit)
            + '" class="w3-bar-item w3-button">Next</a>'
        )
    html += "</div>"
    return HttpResponse(html)
