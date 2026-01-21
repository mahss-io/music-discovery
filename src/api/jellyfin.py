import datetime

from .api import API

class JellyfinAPI(API):
    JELLYFIN_SEARCH_ENDPOINT = "/Search/Hints"
    JELLYFIN_PLAYLIST_ENDPOINT = "/Playlists"
    JELLYFIN_ITEM_ENDPOINT = "/Items"
    JELLYFIN_PLAYLIST_ITEMS_ENDPOINT = "/Playlists/{}/Items"

    JELLYFIN_WEEKLY_EXPLORE_TAG = "Weekly-Explore"
    JELLYFIN_WEEKLY_EXPLORE_USER_TAG = "Week-{}-{}-Explore-{}"
    JELLYFIN_WEEKLY_EXPLORE_NAME = "{} Weekly Explore - {} Week {}"

    def __init__(self, base_url, admin_user_id, api_key):
        self._base_url = base_url
        self.admin_user_id = admin_user_id
        self.api_key = api_key
        self._headers = {
            "Authorization": f"MediaBrowser Token=\"{api_key}\""
        }
    
    def add_song_to_playlist(self, jellyfin_playlist_id, jellyfin_item_id):
        query_params = {
            "userId": self.admin_user_id,
            "ids": jellyfin_item_id
        }
        self._post_request(self._create_url(f"{self._base_url}{self.JELLYFIN_PLAYLIST_ITEMS_ENDPOINT.format(jellyfin_playlist_id)}", query_params), {})
    
    def find_track(self, artist, album, song_name):
        query_params = {
            "searchTerm": song_name,
            "includeItemTypes": "Audio",
            "mediaType": "Audio"
        }
        results = self._get_request(self._create_url(f"{self._base_url}{self.JELLYFIN_SEARCH_ENDPOINT}", query_params)).get('SearchHints')
        # print(f"Results for: A:{artist} A:{album} S:{song_name}")
        # print(results)
        if (len(results) == 1 and results[0].get('AlbumArtist') == artist and results[0].get('Album') == album):
            return results[0]
        for result in results:
            match_count = 0
            for song_artist in result.get('Artist', []) + [result.get('AlbumArtist', []), "Various Artists"]: 
                if (song_artist == artist):
                    match_count += 1
            if (result.get('Album') == album):
                match_count += 1
            if (result.get('Name') == song_name):
                match_count += 1
            if (match_count >= 2):
                return result
        return {}
    
    def tag_playlist(self, jellyfin_playlist_id, week, listenbrainz_username, year, listenbrainz_playlist_id):
        jellyfin_playlist_data = self.get_playlist(jellyfin_playlist_id)
        before_count = len(jellyfin_playlist_data.get('Tags'))
        user_tag = self.JELLYFIN_WEEKLY_EXPLORE_USER_TAG.format(week, listenbrainz_username, year)
        if (user_tag not in jellyfin_playlist_data.get('Tags')):
            jellyfin_playlist_data.update({"Tags":jellyfin_playlist_data.get('Tags') + [user_tag]})
        if (listenbrainz_playlist_id not in jellyfin_playlist_data.get('Tags')):
            jellyfin_playlist_data.update({"Tags":jellyfin_playlist_data.get('Tags') + [listenbrainz_playlist_id]})
        if (self.JELLYFIN_WEEKLY_EXPLORE_TAG not in jellyfin_playlist_data.get('Tags')):
            jellyfin_playlist_data.update({"Tags":jellyfin_playlist_data.get('Tags') + [self.JELLYFIN_WEEKLY_EXPLORE_TAG]})
        if (before_count != len(jellyfin_playlist_data.get('Tags'))):
            self.update_playlist(jellyfin_playlist_id, jellyfin_playlist_data)

    def create_playlist_from_local(self, local_playlist, jellyfin_userids):
        query_params = {
            "userId": self.admin_user_id
        }
        body = {
            "Name": self.JELLYFIN_WEEKLY_EXPLORE_NAME.format(local_playlist.get('listenbrainzUsername'), local_playlist.get('year'), local_playlist.get('week')),
            "Ids": [],
            "UserId": self.admin_user_id,
            "MediaType": "Audio",
            "Users": [{"UserId": u, "CanEdit": True} for u in jellyfin_userids],
            "IsPublic": True
        }
        return self._post_request(self._create_url(f"{self._base_url}{self.JELLYFIN_PLAYLIST_ENDPOINT}", query_params), body)

    def get_playlists(self):
        query_params = {
            "searchTerm": "_",
            "includeItemTypes": "Playlist"
        }
        data = self._get_request(self._create_url(f"{self._base_url}{self.JELLYFIN_SEARCH_ENDPOINT}", query_params)).get('SearchHints', [])
        return data
    
    def get_playlist(self, jellyfin_playlist_id):
        query_params = {
            "userId": self.admin_user_id
        }
        return self._get_request(self._create_url(f"{self._base_url}{self.JELLYFIN_ITEM_ENDPOINT}/{jellyfin_playlist_id}", query_params))
    
    def update_playlist(self, jellyfin_playlist_id, jellyfin_playlist_data):
        query_params = {
            "userId": self.admin_user_id
        }
        return self._post_request(self._create_url(f"{self._base_url}{self.JELLYFIN_ITEM_ENDPOINT}/{jellyfin_playlist_id}", query_params), jellyfin_playlist_data)

    def get_playlist_created_date(self, jellyfin_playlist_id=None, jellyfin_playlist=None):
        jellyfin_playlist_data = None
        if (jellyfin_playlist_id is not None):
            jellyfin_playlist_data = self.get_playlist(jellyfin_playlist_id)
        else:
            jellyfin_playlist_data = jellyfin_playlist
        playlist_created_date = datetime.datetime.strptime(jellyfin_playlist_data.get('DateCreated')[:-2], "%Y-%m-%dT%H:%M:%S.%f")
        return playlist_created_date

    def delete_playlist(self, jellyfin_playlist_id):
        query_params = {
            "userId": self.admin_user_id,
        }
        try:
            self._delete_request(self._create_url(f"{self._base_url}{self.JELLYFIN_ITEM_ENDPOINT}/{jellyfin_playlist_id}", query_params))
            return True
        except:
            return False

    def is_playlist_weekly_explore(self, jellyfin_playlist):
        return "Weekly-Explore" in jellyfin_playlist.get('Tags', [])