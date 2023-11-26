import os
from datetime import datetime

from bottle import request, route, run

from src.database.artists import Artist, ArtistTable
from src.database.history import HistoryTable, PlayingHistoryEntry
from src.database.tracks import TrackEntry, TrackTable
from src.html import SpotifyLogin, display_currently_playing, header


@route("/")
def index():
    html = header()
    token_success, token_result = SpotifyLogin(request.url)
    if not token_success:
        return html + token_result

    return html + display_currently_playing(token_result)


@route("/history")
def history():
    limit = request.query.limit or 25
    offset = request.query.offset or 0
    limit = int(limit)
    offset = int(offset)
    html = header()
    token_success, token_result = SpotifyLogin(request.url)
    if not token_success:
        return html + token_result
    result = HistoryTable().get_all_limit_offset(limit, offset)
    html += "<table>"
    html += "<tr><th>Track</th><th>Artist</th><th>Album</th><th>Date</th><th>Time</th></tr>"
    for row in result:
        entry = PlayingHistoryEntry.from_sql_result(row)
        track = entry.get_track()
        if track is None:
            continue
        html += "<tr>"
        track_link = '<a href="/tracks/' + track.track_id + '">' + track.track_name + "</a>"
        artist_ids = track.artist_ids[1:-1].split(", ")
        artist_id = artist_ids[0][1:-1]
        artist_link = '<a href="/artists/' + artist_id + '">' + track.track_artist + "</a>"
        cols = [
            track_link,
            artist_link,
            track.track_album,
            entry.date,
            datetime.fromtimestamp(int(entry.timestamp) / 1000.0).strftime("%H:%M:%S"),
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
    if offset + limit < HistoryTable().get_track_count():
        html += (
            '<a href="/history?limit='
            + str(limit)
            + "&offset="
            + str(offset + limit)
            + '" class="w3-bar-item w3-button">Next</a>'
        )
    html += "</div>"
    return html


@route("/artists")
def artists():
    limit = request.query.limit or 25
    offset = request.query.offset or 0
    limit = int(limit)
    offset = int(offset)
    html = header()
    token_success, token_result = SpotifyLogin(request.url)
    if not token_success:
        return html + token_result

    artist_table = ArtistTable()
    result = artist_table.get_all_limit_offset(limit, offset)
    html += "<table>"
    html += "<tr><th>Artist</th><th>Genres</th><th>Popularity</th><th>Followers</th></tr>"
    for row in result:
        artist = Artist.from_sql(row[0])
        html += "<tr>"
        artist_link = '<a href="/artists/' + artist.artist_id + '">' + artist.artist_name + "</a>"
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
    if offset + limit < artist_table.get_artist_count():
        html += (
            '<a href="/artists?limit='
            + str(limit)
            + "&offset="
            + str(offset + limit)
            + '" class="w3-bar-item w3-button">Next</a>'
        )
    html += "</div>"
    return html


@route("/artists/<artist_id>")
def artist(artist_id):
    html = header()
    token_success, token_result = SpotifyLogin(request.url)
    if not token_success:
        return html + token_result

    artist = Artist.from_sql(artist_id)
    html += "<table>"
    html += "<tr><th>Artist</th><th>Genres</th><th>Popularity</th><th>Followers</th></tr>"
    html += "<tr>"
    artist_link = '<a href="/artists/' + artist.artist_id + '">' + artist.artist_name + "</a>"
    cols = [artist_link, str(artist.artist_genres), str(artist.artist_popularity), str(artist.artist_followers)]
    for col in cols:
        html += "<td>" + col + "</td>"
    html += "</tr>"
    html += "</table>"
    return html


@route("/tracks")
def tracks():
    limit = request.query.limit or 25
    offset = request.query.offset or 0
    limit = int(limit)
    offset = int(offset)
    html = header()
    token_success, token_result = SpotifyLogin(request.url)
    if not token_success:
        return html + token_result

    track_table = TrackTable()
    result = track_table.get_all_limit_offset(limit, offset)
    html += "<table>"
    html += "<tr><th>Track</th><th>Artist</th><th>Album</th><th>Duration</th><th>Popularity</th><th>Release Date</th><th>Explicit</th><th>Genres</th><th>Artist IDs</th></tr>"
    for row in result:
        track = TrackEntry.from_sql_result(row)
        html += "<tr>"
        track_link = '<a href="/tracks/' + track.track_id + '">' + track.track_name + "</a>"
        artist_ids = track.artist_ids[1:-1].split(", ")
        artist_id = artist_ids[0][1:-1]
        artist_link = '<a href="/artists/' + artist_id + '">' + track.track_artist + "</a>"
        cols = [
            track_link,
            artist_link,
            track.track_album,
            str(track.track_duration),
            str(track.track_popularity),
            track.track_release_date,
            str(track.track_explicit),
            str(track.artist_genres),
            str(track.artist_ids),
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
    if offset + limit < track_table.get_track_count():
        html += (
            '<a href="/tracks?limit='
            + str(limit)
            + "&offset="
            + str(offset + limit)
            + '" class="w3-bar-item w3-button">Next</a>'
        )
    html += "</div>"
    return html


@route("/tracks/<track_id>")
def track(track_id):
    html = header()
    token_success, token_result = SpotifyLogin(request.url)
    if not token_success:
        return html + token_result

    track = TrackTable().get_track(track_id)
    html += "<table>"
    html += "<tr><th>Track</th><th>Artist</th><th>Album</th><th>Duration</th><th>Popularity</th><th>Release Date</th><th>Explicit</th><th>Genres</th><th>Artist IDs</th></tr>"
    html += "<tr>"
    track_link = '<a href="/tracks/' + track.track_id + '">' + track.track_name + "</a>"
    artist_ids = track.artist_ids[1:-1].split(", ")
    artist_id = artist_ids[0][1:-1]
    artist_link = '<a href="/artists/' + artist_id + '">' + track.track_artist + "</a>"
    cols = [
        track_link,
        artist_link,
        track.track_album,
        str(track.track_duration),
        str(track.track_popularity),
        track.track_release_date,
        str(track.track_explicit),
        str(track.artist_genres),
        str(track.artist_ids),
    ]
    for col in cols:
        html += "<td>" + col + "</td>"
    html += "</tr>"
    html += "</table>"
    return html


def run_app():
    print("Starting server...\n")
    print("APP_LOCATION: " + os.environ.get("APP_LOCATION") + "\nPORT: " + os.environ.get("PORT"))
    if os.environ.get("APP_LOCATION") == "heroku":
        run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    else:
        run(host="localhost", port=8080, debug=True)
