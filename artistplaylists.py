import spotipy
import config
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, render_template, request

artist_playlists_app = Flask(__name__)
auth = SpotifyOAuth(client_id=config.SPOTIPY_CLIENT_ID, client_secret=config.SPOTIPY_CLIENT_SECRET, redirect_uri=config.SPOTIPY_REDIRECT_URI, scope=config.scope)

#creates and populates a dictionary with artist name as the key and a list of track uri's as the value
def collect_liked_songs(sp):

    results = sp.current_user_saved_tracks()
    artist_song_dict = dict()
    offset = 0
    while len(results['items']) > 0:
        results = sp.current_user_saved_tracks(limit=50,offset=offset)
        offset = offset + 50
        for idx, item in enumerate(results['items']):
            track = item['track']
            track_uri = track['uri']
            name = track['artists'][0]['name']
            if name not in artist_song_dict:
                artist_song_dict[name] = list()
            artist_song_dict[name].append(track_uri)

    make_artist_playlists(sp,artist_song_dict)

#creates playlists on user's Spotify account from the dictionary created in the collect_like_congs function
def make_artist_playlists (sp,artist_song_dict):

    for artist in artist_song_dict:
        num_songs = len(artist_song_dict[artist])
        matching_playlist_info = playlist_already_exists(artist, sp)
        if matching_playlist_info is not None:
            for song in artist_song_dict[artist]:
                if not song_already_in_playlist(song, matching_playlist_info[1],sp):
                    sp.playlist_add_items(matching_playlist_info[1], [song], position=None)
        else:
            playlist = sp.user_playlist_create(sp.me()['id'], artist)
            num_songs = len(artist_song_dict[artist])
            if num_songs > 100:
                idx = 0
                while num_songs - idx > 100:
                    sp.playlist_add_items(playlist['id'], artist_song_dict[artist][idx:idx+100], position=None)
                    idx = idx + 100
                sp.playlist_add_items(playlist['id'], artist_song_dict[artist][idx:num_songs-1], position=None)
            else:
                sp.playlist_add_items(playlist['id'], artist_song_dict[artist], position=None)

#check to see if artist from your liked songs already has an existing playlist. If so, a tuple of the artist name and playlist id is returned
def playlist_already_exists(artist,sp):

    current_user_playlists = sp.current_user_playlists(limit=50)
    playlists = current_user_playlists['items']
    playlist_count = current_user_playlists['total']

    existing_playlist_names = list()
    existing_playlist_ids = list()

    if playlist_count <= 50:
        for idx in range (0,playlist_count):
            existing_playlist_names.append(playlists[idx]['name'])
            existing_playlist_ids.append(playlists[idx]['id'])
    else:
        offset = 0
        while offset < playlist_count-50:
            for idx in range (0,50):
                existing_playlist_names.append(playlists[idx]['name'])
                existing_playlist_ids.append(playlists[idx]['id'])
            offset +=50
            current_user_playlists = sp.current_user_playlists(limit=50,offset=offset)
            playlists = current_user_playlists['items']

        for idx in range (0,playlist_count-(offset+1)):
            existing_playlist_names.append(playlists[idx]['name'])
            existing_playlist_ids.append(playlists[idx]['id'])


    if artist in existing_playlist_names:
        idx_of_existing_playlist = existing_playlist_names.index(artist)
        return (artist, existing_playlist_ids[idx_of_existing_playlist])
    else:
        return None

#check to see if song by artist with an existing playlist has already been added to the playlist
def song_already_in_playlist(song,artist_playlist,sp):
    songs_in_playlist = sp.playlist_items(artist_playlist, limit=100)
    num_songs_in_playlist = songs_in_playlist['total']
    songs_in_playlist_ids = list()

    if num_songs_in_playlist > 100:
        offset = 0
        while num_songs_in_playlist - offset > 0:
            for idx in range (0,100):
                songs_in_playlist_ids.append(songs_in_playlist['items'][idx]['track']['uri'])
            offset += 100
            songs_in_playlist = sp.playlist_items(artist_playlist, limit=100, offset = offset)

    else:
        for idx in range (0,num_songs_in_playlist):
            songs_in_playlist_ids.append(songs_in_playlist['items'][idx]['track']['uri'])

    if song in songs_in_playlist_ids:
        return True
    else:
        return False



#render home page
@artist_playlists_app.route("/")
def index():
    return render_template('index.html', PageTitle = "Landing page")

#collects access token from text field. runs collect_liked_songs function after creating spotipy opject
@artist_playlists_app.route("/",  methods = ["POST"])
def get_token():
    token = request.form['text']
    sp = spotipy.Spotify(auth=token, auth_manager=auth)
    collect_liked_songs(sp)
    return "done"




#if __name__ == '__main__':
#   artist_playlists_app.run()
