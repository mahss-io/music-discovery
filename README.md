Fuck I need a readme. There is no way this is going to be a small project.

Custom ListenBrainz Local Stored Playlist Format.
```json
{
    "listenbrainzId": "<uuid>",
    "listenbrainzUsername": "string",
    "year": 2025,
    "week": 52,
    "tracks": [
        {
            "musicBrainzId": "<uuid>",
            "trackName": "string",
            "artistName": "string",
            "albumName": "string",
            "addedInJellyfin": false
        }
    ]
}
```
Will store in the `playlists` folder, and will be the source of truth for this whole endever.

### Workflow - Runs every hour - Try and get it to run in under 60 seconds
1. Get playlists from LB
    * 2 API calls required per user
        1. Get a users playlists
        2. Get the users weekly explore playlist
            * Contains artist MB UUID, release MB UUID, etc
2. Get release group UUID from MB and add it on Lidarr
    1. Get release group UUID from MB from LB release UUID
        * 1 call to MB for lookup release-group (no more then 1 per second)
    2. Get/Lookup realse group in Lidarr, if it does not exist add it and start monitoring it (SLOW)
        * 2 call to lookup release group and possibly add new artist (SLOW)
            1. Get album from release group (SLOW)
            2. If already tracking artist, start monitoring new album from release group
            3. Else Add the artist and start monitoring the album
3. Create/Lookup Playlist in Jellyfin
    1. Lookup playlist with tags of LB UUID
        * Create it if not exists
4. Search each song in playlist file by name and artist if flagged to do so, get Jellyfin item id, add it to the target playlist
5. Cleanup playlist files if:
    * Matched 80%-100% of the playlist in Jellyfin or
    * It has been 3-5 weeks
6. Cleanup (hide playlists by assigning them to a different user not listed, and not letting them be public and zeroing out the Users field) Jellyfin playlists
    * After 6 weeks after playlist creation