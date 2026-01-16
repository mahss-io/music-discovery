from .file_manager import FileManager

class ConfigManager(FileManager):
    CONFIG_FOLDER_PATH = "config"

    def __init__(self):
        self.CONFIG_FILE_PATH = f"{self.CONFIG_FOLDER_PATH}/config{self.JSON_FILE_EXT}"
        self.USER_CONFIG_FILE_PATH = f"{self.CONFIG_FOLDER_PATH}/users{self.JSON_FILE_EXT}"
        if not os.path.isdir(f"../{self.CONFIG_FOLDER_PATH}"):
            os.makedirs(f"../{self.CONFIG_FOLDER_PATH}")
        self._get_config()
        self._get_user_config()

    def _get_config(self):
        self.config = self._read_file(f"../{self.CONFIG_FILE_PATH}")

    def _get_user_config(self):
        self.user_config = self._read_file(f"../{self.USER_CONFIG_FILE_PATH}")

    def get_user_data(self):
        return self.user_config
    
    def get_jellyfin_userid(self, get_name):
        for name, data in self.user_config.items():
            if data.get('jellyfinUserId') != None and name == get_name:
                return data.get('jellyfinUserId') 
    
    def get_listenbrainz_usernames(self):
        return [i.get('listenbrainzUsername') for i in self.user_config.values() if i.get('listenbrainzUsername') != None]

    def get_jellyfin_userids(self):
        return [i.get('jellyfinUserId') for i in self.user_config.values() if i.get('jellyfinUserId') != None]

    def get_jellyfin_base_url(self):
        return self.config.get('jellyfin_base_url')

    def get_jellyfin_api_token(self):
        return self.config.get('jellyfin_api_token')

    def get_lidarr_base_url(self):
        return self.config.get('lidarr_base_url')

    def get_lidarr_api_token(self):
        return self.config.get('lidarr_api_token')

    def get_listenbrainz_base_url(self):
        return self.config.get('listenbrainz_base_url')

    def get_listenbrainz_api_token(self):
        return self.config.get('listenbrainz_api_token')

    def get_musicbrainz_base_url(self):
        return self.config.get('musicbrainz_base_url')