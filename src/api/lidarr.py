from .api import API

class LidarrAPI(API):
    LIDARR_ALBUM = "/api/v1/album"
    LIDARR_ARTIST = "/api/v1/artist"
    LIDARR_SEARCH = "/api/v1/search?term=lidarr:{SEARCH_UUID}"
    LIDARR_ALBUM_LOOKUP_ENDPOINT = "/api/v1/album/lookup?term=lidarr:{}"

    def __init__(self, base_url, api_key):
        self._base_url = base_url
        self.api_key = api_key
        self._headers = {
            "Authorization": f"Bearer {api_key}"
        }
    
    def get_lidarr_album_tracking_data(self, release_group_id):
        all_lidarr_album_lookup_data = self._get_request(f"{self._base_url}{self.LIDARR_ALBUM_LOOKUP_ENDPOINT.format(release_group_id)}")
        if (all_lidarr_album_lookup_data != {} and len(all_lidarr_album_lookup_data) > 0):
            return all_lidarr_album_lookup_data[0]
        return {}

    def _add_artist_album_payload(self, artist_id, release_group_id):
        return {
            "artist": {
                "rootFolderPath": "/raid10/media/music/",
                "foreignArtistId": artist_id,
                "qualityProfileId": 1,
                "metadataProfileId": 1,
                "monitored": True,
                "monitorNewItems": "none",
                "monitor": "missing",
                "albumsToMonitor": []
            },
            "foreignAlbumId": release_group_id,
            "monitored": True,
            "anyReleaseOk": True,
            "addOptions": {
                "addType": "automatic",
                "searchForNewAlbum": True
            }
        }

    def _monitor_album_payload(self, release_group_id):
        return {
            "monitored": True,
            "foreignAlbumId": release_group_id
        }

    def _monitor_artist_payload(self, lidarr_artist_path):
        return {
            "monitored": True,
            "path": lidarr_artist_path,
            "qualityProfileId": 1,
            "metadataProfileId": 1,
            "monitorNewItems": "none",
            "monitor": "missing"
        }

    def monitor_existing_album(self, lidarr_album_id, release_group_id):
        data = self._put_request(f"{self._base_url}{self.LIDARR_ALBUM}/{lidarr_album_id}", body=self._monitor_album_payload(release_group_id))

    def monitor_existing_artist(self, lidarr_artist_id, lidarr_artist_path):
        data = self._put_request(f"{self._base_url}{self.LIDARR_ARTIST}/{lidarr_artist_id}", body=self._monitor_artist_payload(lidarr_artist_path))

    def request_new_artist_and_album(self, artist_id, release_group_id):
        data = self._post_request(f"{self._base_url}{self.LIDARR_ALBUM}", self._add_artist_album_payload(artist_id, release_group_id))