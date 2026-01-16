import json
import datetime

from .api import API

class ListenBrainzAPI(API):
    LISTENBRAINZ_CREATED_FOR_USER = "/1/user/{LB_USERNAME}/playlists/createdfor"
    LISTENBRAINZ_FETCH_PLAYLIST = "/1/playlist/{LB_PLAYLIST_ID}"

    def __init__(self, base_url, api_key):
        self._base_url = base_url
        self.api_key = api_key
        self._headers = {
            "User-Agent": "MusicDiscovery/HourlyScript (ross.mcwilliams@mahss.io)",
            "Accept": "application/json",
            "Authorization": f"Token {api_key}"
        }
    
    def get_weekly_playlist_data(self, username):
        weekly_playlist_data = []
        listenbrainz_playlist_data = self._get_request(self._create_url(f"{self._base_url}{self.LISTENBRAINZ_CREATED_FOR_USER.format(LB_USERNAME=username)}"))
        for playlist_data in listenbrainz_playlist_data.get('playlists', []):
            playlist_data = playlist_data.get('playlist',{})
            date =  datetime.datetime.strptime(playlist_data.get('date'), "%Y-%m-%dT%H:%M:%S.%f%z")
            # Add conditional to only check for this weeks
            # date.isocalendar()[1] == datetime.datetime.now().isocalendar()[1] and 
            if (playlist_data.get('extension',{}).get('https://musicbrainz.org/doc/jspf#playlist',{}).get('additional_metadata',{}).get('algorithm_metadata',{}).get('source_patch') == "weekly-exploration"):
                weekly_playlist_data.append({
                    "listenbrainzId": playlist_data.get('identifier').split('/')[-1],
                    "listenbrainzUsername": username,
                    "jellyfinPlaylistId": None,
                    "year": date.year,
                    "week": date.isocalendar()[1],
                    "tracks": []
                })
        return weekly_playlist_data


    def get_playlist_tracks(self, listenbrainzId):
        listenbrainz_playlist = self._get_request(self._create_url(f"{self._base_url}{self.LISTENBRAINZ_FETCH_PLAYLIST.format(LB_PLAYLIST_ID=listenbrainzId)}"))
        listenbrainz_playlist = listenbrainz_playlist.get('playlist', {})

        tracks = []
        for listenbrainz_playlist_track in listenbrainz_playlist.get('track'):
            additional_metadata = listenbrainz_playlist_track.get('extension',{}).get('https://musicbrainz.org/doc/jspf#track',{}).get('additional_metadata',{})
            musicbrainz_release_id = additional_metadata.get('caa_release_mbid')
            musicbrainz_artists = additional_metadata.get('artists', [])
            if musicbrainz_release_id is not None:
                tracks.append({
                        "musicBrainzArtistId": musicbrainz_artists[0].get('artist_mbid') if len(musicbrainz_artists) > 0 else None,
                        "musicBrainzReleaseId": musicbrainz_release_id,
                        "musicbrainzReleaseGroupId": None,
                        "trackName": listenbrainz_playlist_track.get('title'),
                        "artistName": listenbrainz_playlist_track.get('creator'),
                        "albumName": listenbrainz_playlist_track.get('album'),
                        "addedInJellyfin": False
                    })

        return tracks