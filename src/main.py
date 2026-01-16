import atexit

from api.jellyfin import JellyfinAPI
from api.lidarr import LidarrAPI
from api.listenbrainz import ListenBrainzAPI
from api.musicbrainz import MusicBrainzAPI
from util.config_manager import ConfigManager
from util.playlist_manager import PlaylistManager

update_local_playlists = True

cm = ConfigManager()
pm = PlaylistManager()

def exit_handler():
    pm.save_playlists()

atexit.register(exit_handler)

jf = JellyfinAPI(cm.get_jellyfin_base_url(), cm.get_jellyfin_userid("Admin") if cm.get_jellyfin_userid("Admin") is not None else cm.get_jellyfin_userids()[0], cm.get_jellyfin_api_token())
li = LidarrAPI(cm.get_lidarr_base_url(), cm.get_lidarr_api_token())
lb = ListenBrainzAPI(cm.get_listenbrainz_base_url(), cm.get_listenbrainz_api_token())
mb = MusicBrainzAPI(cm.get_musicbrainz_base_url())

# Load playlists
if (update_local_playlists):
    for listenbrainz_username in cm.get_listenbrainz_usernames():
        if pm.user_needs_playlists_update(listenbrainz_username):
            for user_playlist in lb.get_weekly_playlist_data(listenbrainz_username):
                if pm.playlists.get(user_playlist.get('listenbrainzId')) is None:
                    pm.update_playlist(user_playlist.get('listenbrainzId'), user_playlist)

# Load playlist tracks
for listenbrainzId, playlist_data in pm.playlists.items():
    if not pm.playlist_tracks_loaded(listenbrainzId):
        playlist_data['tracks'] = lb.get_playlist_tracks(listenbrainzId)
        pm.update_playlist(listenbrainzId, playlist_data)

# Lookup and attach musicbrainz release groups
for listenbrainzId, playlist_data in pm.playlists.items():
    for track_data in playlist_data.get('tracks'):
        if (track_data.get('musicbrainzReleaseGroupId') is None):
            track_data['musicbrainzReleaseGroupId'] = mb.get_release_group_from_release(track_data.get('musicBrainzReleaseId'))
            pm.update_playlist(listenbrainzId, playlist_data, update_file=False)
    pm.update_playlist(listenbrainzId, playlist_data)

# Lidarr
for listenbrainzId, playlist_data in pm.playlists.items():
    for track_data in playlist_data.get('tracks', []):
        if (track_data.get('lidarrAlbumId') is None or track_data.get('lidarrIsMonitoring') is None):
            lidarr_data = li.get_lidarr_tracking_data(track_data.get('musicBrainzReleaseId'), track_data.get('musicbrainzReleaseGroupId'))
            if (lidarr_data != {}):
                track_data['lidarrAlbumId'] = lidarr_data.get('lidarrAlbumId')
                track_data['lidarrIsMonitoring'] = lidarr_data.get('lidarrIsMonitoring')
        if (track_data.get('lidarrAlbumId') != 0 and not track_data.get('lidarrIsMonitoring') ):
            li.monitor_existing_album(track_data.get('lidarrAlbumId'), track_data.get('musicbrainzReleaseGroupId'))
            track_data['lidarrIsMonitoring'] = True
        elif (track_data.get('lidarrAlbumId' == 0)):
            print(li.request_new_artist_and_album(track_data.get('musicBrainzArtistId'), track_data.get('musicbrainzReleaseGroupId')))
            track_data['lidarrAlbumId'] = lidarr_data.get('lidarrAlbumId')
            track_data['lidarrIsMonitoring'] = True
            break


# Jellyfin
# Goes through each local playlist and will create jellyfin playlist for each.
# Then it will try and add tags if they are not already tagged.
# Then will add tracks that have not been added
for listenbrainzId, playlist_data in pm.playlists.items():
    if (playlist_data.get('jellyfinPlaylistId') is None):
        jellyfin_playlist_id = jf.create_playlist_from_local(playlist_data, cm.get_jellyfin_userids())
        playlist_data['jellyfinPlaylistId'] = jellyfin_playlist_id.get('Id')
        pm.update_playlist(listenbrainzId, playlist_data)
    jf.add_tags_to_playlist(playlist_data.get('jellyfinPlaylistId'), playlist_data.get('week'), playlist_data.get('listenbrainzUsername'), listenbrainzId)
    for track_data in playlist_data.get('tracks', []):
        if (not track_data.get('addedInJellyfin')):
            result = jf.find_track(track_data.get('artistName'), track_data.get('albumName'), track_data.get('trackName'))
            if result != {}:
                jf.add_song_to_playlist(playlist_data.get('jellyfinPlaylistId'), result.get('Id'))
                track_data['addedInJellyfin'] = True

# Cleanup local playlists
# TODO
# Cleanup Jellyfin playlists
# TODO
