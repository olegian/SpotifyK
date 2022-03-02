import spotipy
from spotipy import SpotifyOAuth
from pymongo import MongoClient
from decouple import config

############  CONSTANTS  ###############
CLIENT_ID = config('CLIENT_ID')
CLIENT_SEC = config('CLIENT_SEC')
REDIRECT_URI = config('REDIRECT_URI')
SCOPE = config('SCOPE')
DB_PASS = config('DB_PASS')
DEVICE_ID = config('TARGET_DEVICE')
CARD_KEY = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

############  HELPERS  ###############
def getMongoDB():
    client = MongoClient(f"mongodb+srv://kavin:{DB_PASS}@spotifyk.zzmzw.mongodb.net/CardMap?retryWrites=true&w=majority", ssl=True)
    return client['CardMap']

def getSpotify():
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SEC,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    ))
    return spotify
