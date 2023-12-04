from django.http import HttpResponse

from lynify.models.tracks import TrackModel
from lynify.views.html import SpotifyLogin, header


def track(request):
    track_id = request.GET.get("track_id", "")
    if track_id == "":
        html = header()
        html += "No track ID provided"
        return HttpResponse(html)
    html = header()
    token_success, token_result = SpotifyLogin(request)
    if not token_success:
        html += token_result
        return HttpResponse(html)

    try:
        track = TrackModel.objects.get(track_id=track_id)
    except TrackModel.DoesNotExist:
        track = TrackModel.from_spotify(track_id)
    if track is None:
        html += "Track not found"
        return HttpResponse(html)
    html += "<table>"
    col_names = [
        "Track",
        "Artists",
        "Album",
        "Duration",
        "Popularity",
        "Release Date",
        "Explicit",
    ]
    html += "<tr>"
    for col_name in col_names:
        html += "<th>" + col_name + "</th>"
    html += "</tr>"
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
    return HttpResponse(html)
