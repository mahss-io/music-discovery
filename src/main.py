import atexit
import datetime

from api.jellyfin import JellyfinAPI
from api.lidarr import LidarrAPI
from api.listenbrainz import ListenBrainzAPI
from api.musicbrainz import MusicBrainzAPI
from util.config_manager import ConfigManager
from util.playlist_manager import PlaylistManager

update_local_playlists = True
cleanup_jellyfin_playlists = False

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

# Load/update counts counts
for listenbrainzId, playlist_data in pm.playlists.items():
    playlist_data['total_count'] = len(playlist_data.get('tracks', []))
    playlist_data['mon_count'] = [track_data.get('lidarrIsMonitoring', False) for track_data in playlist_data.get('tracks', [])].count(True)
    pm.update_playlist(listenbrainzId, playlist_data)

# Jellyfin
# Goes through each local playlist and will create jellyfin playlist for each.
# Then it will try and add tags if they are not already tagged.
# Then will add tracks that have not been added
for listenbrainzId, playlist_data in pm.playlists.items():
    if (playlist_data.get('jellyfinPlaylistId') is None):
        jellyfin_playlist_id = jf.create_playlist_from_local(playlist_data, cm.get_jellyfin_userids())
        playlist_data['jellyfinPlaylistId'] = jellyfin_playlist_id.get('Id')
        pm.update_playlist(listenbrainzId, playlist_data)
    jf.tag_playlist(playlist_data.get('jellyfinPlaylistId'), playlist_data.get('week'), playlist_data.get('listenbrainzUsername'), playlist_data.get('year'), listenbrainzId)
    for track_data in playlist_data.get('tracks', []):
        if (playlist_data.get('mon_count') > cm.get_lidarr_user_counts().get(playlist_data.get('listenbrainzUsername', 0))):
            break
        if (not track_data.get('addedInJellyfin')):
            result = jf.find_track(track_data.get('artistName'), track_data.get('albumName'), track_data.get('trackName'))
            if result != {}:
                jf.add_song_to_playlist(playlist_data.get('jellyfinPlaylistId'), result.get('Id'))
                track_data['addedInJellyfin'] = True
    pm.update_playlist(listenbrainzId, playlist_data)

# Lidarr
for listenbrainzId, playlist_data in pm.playlists.items():
    for track_data in playlist_data.get('tracks', []):
        if (playlist_data.get('mon_count') > cm.get_lidarr_user_counts().get(playlist_data.get('listenbrainzUsername', 0))):
            break
        release_group_id = track_data.get('musicbrainzReleaseGroupId')
        release_id = track_data.get('musicBrainzReleaseId')
        if (not track_data.get('addedInJellyfin') and release_group_id is not None):
            # Gets the relavent 
            lidarr_album_data = li.get_lidarr_album_tracking_data(release_group_id)
            lidarr_monitoring_album = lidarr_album_data.get('monitored', False)
            lidarr_monitoring_artist = lidarr_album_data.get('artist', {}).get('monitored', False)
            lidarr_album_id = lidarr_album_data.get('id', 0)
            lidarr_artist_id = lidarr_album_data.get('artistId', 0)
            lidarr_artist_path = lidarr_album_data.get('artist', {}).get('path', "/raid10/media/music/")

            # If Lidarr data has not been populated locally
            if (track_data.get('lidarrAlbumId') is None or track_data.get('lidarrIsMonitoring') is None):
                if (lidarr_album_data != {}):
                    track_data['lidarrAlbumId'] = lidarr_album_id
                    track_data['lidarrIsMonitoring'] = lidarr_monitoring_album
            # If it is not being tracked, start tracking it
            if (not lidarr_monitoring_artist and not lidarr_monitoring_album and lidarr_artist_id == 0 and lidarr_album_id == 0):
                li.request_new_artist_and_album(track_data.get('musicBrainzArtistId'), release_group_id)
                track_data['lidarrAlbumId'] = lidarr_album_id
                track_data['lidarrIsMonitoring'] = True
            # Else track only what is currently not being tracked
            elif (lidarr_artist_id != 0 and lidarr_album_id != 0):
                if (not lidarr_monitoring_album):
                    li.monitor_existing_album(lidarr_album_id, release_group_id)
                if (not lidarr_monitoring_artist):
                    li.monitor_existing_artist(lidarr_artist_id, lidarr_artist_path)
                track_data['lidarrAlbumId'] = lidarr_album_id
                track_data['lidarrIsMonitoring'] = True
    pm.update_playlist(listenbrainzId, playlist_data)

# Cleanup local playlists
to_delete = []
for listenbrainzId, playlist_data in pm.playlists.items():
    if datetime.datetime.now().isocalendar()[1] - playlist_data.get('week') >= 4:
        to_delete.append(listenbrainzId)
for listenbrainzId in to_delete:
    pm.delete_playlist(listenbrainzId)

# Cleanup Jellyfin playlists
if (cleanup_jellyfin_playlists):
    for jellyfin_playlist in jf.get_playlists():
        jellyfin_playlist = jf.get_playlist(jellyfin_playlist.get('Id'))
        jellyfin_playlist_created_date = jf.get_playlist_created_date(jellyfin_playlist=jellyfin_playlist)
        if (jf.is_playlist_weekly_explore(jellyfin_playlist)):
            # print(f"Trying to delete {jellyfin_playlist.get('Name')}")
            if datetime.datetime.now().isocalendar()[1] - jellyfin_playlist_created_date.isocalendar()[1] >= 6:
                jf.delete_playlist(jellyfin_playlist_id)
