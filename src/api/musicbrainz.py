from .api import API

class MusicBrainzAPI(API):
    MUSICBRAINZ_RELEASE_GROUP_LOOKUP = "/ws/2/release-group?release={}"

    def __init__(self, base_url):
        self._base_url = base_url
        self._headers = {
            "User-Agent": "MusicDiscovery/HourlyScript (ross.mcwilliams@mahss.io)",
            "Accept": "application/json"
        }
    
    def get_release_group_from_release(self, release):
        data = self._get_request(self._create_url(f"{self._base_url}{self.MUSICBRAINZ_RELEASE_GROUP_LOOKUP.format(release)}"), delay=1)
        if (len(data.get('release-groups',[])) <= 0):
            return None
        return data.get('release-groups',[])[0].get('id')
