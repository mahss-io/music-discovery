import datetime
import os

from .file_manager import FileManager

class PlaylistManager(FileManager):
    PLAYLISTS_FOLDER_PATH = "../playlists/"

    playlists = {}

    def __init__(self):
        if not os.path.isdir(self.PLAYLISTS_FOLDER_PATH):
            os.makedirs(self.PLAYLISTS_FOLDER_PATH)

        # Load playlists
        for file in os.listdir(self.PLAYLISTS_FOLDER_PATH):
            if os.path.isfile(f"{self.PLAYLISTS_FOLDER_PATH}{file}"):
                data = self._read_file(f"{self.PLAYLISTS_FOLDER_PATH}{file}")
                self.playlists.update({data.get('listenbrainzId'): data})

    def save_playlists(self):
        for listenbrainzUUID, data in self.playlists.items():
            self._write_file(f"{self.PLAYLISTS_FOLDER_PATH}{listenbrainzUUID}{self.JSON_FILE_EXT}", data)

    def playlist_tracks_loaded(self, listenbrainzId):
        return self.playlists.get(listenbrainzId,{}).get('tracks', []) != []

    def user_needs_playlists_update(self, listenbrainzUsername):
        current_week = datetime.datetime.now().isocalendar()[1]
        for listenbrainzUUID, playlist_data in self.playlists.items():
            if playlist_data.get('week') == current_week and playlist_data.get('listenbrainzUsername') == listenbrainzUsername:
                return False
        return True

    def is_tracking_playlistr(self, listenbrainzUUID):
        return listenbrainzUUID in self.playlists.keys()
        # File version of is tracking playlist
        # return os.path.isfile(f"{self.PLAYLISTS_FOLDER_PATH}/{listenbrainzUUID}{self.JSON_FILE_EXT}")

    def update_playlist(self, listenbrainzUUID, data, update_file=True):
        self.playlists.update({listenbrainzUUID: data})
        if (update_file):
            self._write_file(f"{self.PLAYLISTS_FOLDER_PATH}{listenbrainzUUID}{self.JSON_FILE_EXT}", data)

    def delete_playlist(self, listenbrainzUUID):
        if (self.playlists.get(listenbrainzUUID) is not None):
            del self.playlists[listenbrainzUUID]
            self._delete_file(f"{self.PLAYLISTS_FOLDER_PATH}{listenbrainzUUID}{self.JSON_FILE_EXT}")
            return True
        return False