def singleton(cls, *args, **kw):
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


def check_for_token():
    oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-read-currently-playing",
    )
    if AccessToken().has_token(SPOTIFY_USER_ID):
        token = AccessToken().get_token(SPOTIFY_USER_ID)
        return True, token
    token = oauth.get_cached_token()
    if token:
        AccessToken().add_token(
            SPOTIFY_USER_ID,
            token["access_token"],
            token["refresh_token"],
            int(time.time() * 1000) + token["expires_in"] * 1000,
        )
        return True, token["access_token"]
    else:
        url = request.url
        code = oauth.parse_response_code(url)
        if code != url:
            token = oauth.get_access_token(code)
            if token:
                AccessToken().add_token(
                    SPOTIFY_USER_ID,
                    token["access_token"],
                    token["refresh_token"],
                    int(time.time() * 1000) + token["expires_in"] * 1000,
                )
                return True, token["access_token"]
        else:
            auth_url = oauth.get_authorize_url()
            htmlLoginButton = "<a href='" + auth_url + "'>Login to Spotify</a>"
            return False, htmlLoginButton
