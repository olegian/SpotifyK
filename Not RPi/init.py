import spotipy
from spotipy.oauth2 import SpotifyOAuth
from decouple import config
import os
import json
import pymongo
from pymongo import MongoClient
import certifi

########### FIELDS ###########
CLIENT_ID = config('CLIENT_ID')
CLIENT_SEC = config('CLIENT_SEC')
REDIRECT_URI = config('REDIRECT_URI')
SCOPE = config('SCOPE')
DB_PASS = config('DB_PASS')

########### HELPERS ###########
def getTypeInput(prompt, integer=False):
    ret = None
    repeat = True
    while (repeat):
        ret = input(prompt)
        if (integer):
            try:
                ret = int(ret)
            except:
                print('Invalid Input')
            else: 
                repeat = False
        else:
            if len(ret) == 0:
                print('Invalid Input')
            else:
                repeat = False
    return ret

########### SERVICES ###########
def connectToDB(clusterName):
    cluster = MongoClient(f"mongodb+srv://kavin:{DB_PASS}@spotifyk.zzmzw.mongodb.net/CardMap?retryWrites=true&w=majority", tlsCAFile=certifi.where())
    return cluster['CardMap'][clusterName]

def getSpotify():
    try:
        s = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SEC,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            show_dialog=True,
            open_browser=True
        ))
    except:
        print('\nUnable to connect to spotify servers.\nThis should never happen. Call Oleg.')
    else:
        return s

########### MENU METHODS ###########
def authorize():
    if os.path.exists('.cache'):
        os.remove('.cache')
        
    spotify = getSpotify()
    spotify.devices() #kinda cheesy way of generating cache file

    authColl = connectToDB('AuthInfo')
    with open(".cache", "r") as f:
        cache = json.load(f)
    cache.update({'_id': 'authInfo'}) 
    authColl.delete_one({'_id' : 'authInfo'})
    authColl.insert_one(cache)

def searchAlbum():
    spotify = getSpotify()

    data = []
    while not data:
        repeat = True
        album_search = getTypeInput("\nWhat album are you searching for? ")
        search_res = spotify.search(album_search, type='album')['albums']['items']
        if search_res :
            print('\nSearch Results:')
            for idx, album in enumerate(search_res):
                print('[', str(idx + 1), '] : ', album['name'], ' - ', album['artists'][0]['name'])
            index = getTypeInput('Enter the index of the song you want to write (enter 0 to do another search): ', True) - 1
            if index >= 0:
                data = search_res[index]
        else:
            print('Search inconclusive, try another one.')

    cardColl = connectToDB('CardMap')
    pipeline = [{'$sort': {"_id": pymongo.DESCENDING}}, {'$limit': 1}]
    for result in cardColl.aggregate(pipeline):
        max = result['_id'] + 1

    cardInfo = {'_id': max, 'uri' : data['uri'], 'key' : 'temp'}
    cardColl.insert_one(cardInfo)

    print('\nPlace target card on the dock')
    input('Hit enter to continue...\n')

def changePreset():
    spotify = getSpotify()

    data = []
    while not data:
        playlists = spotify.current_user_playlists()['items']
        if playlists:
            print('\nYour playlists:')
            for idx, playlist in enumerate(playlists):
                print('[', idx + 1, '] : ', playlist['name'])
            index = getTypeInput('Enter the number of the playlist ', True) - 1
            if index >= 0:
                data = playlists[index]
        else:
            print('You have no available playlists.')
    
    cardColl = connectToDB('CardMap')
    cardColl.find_one_and_update({'_id' : 0}, {'$set' : {'uri' : data['uri']}}, upsert=True)

def cleanup():
    cmdb = connectToDB('CardMap')
    aidb = connectToDB('AuthInfo')
    
    cmdb.delete_many({'key' : 'temp'})
    aidb.delete_many({})

def printMenu():
    print("\n\nMain Menu:")
    print('[1] Authorize Device')
    print('[2] Write Album to Card')
    print('[3] Change Preset Playlist')

########### ENTRY ###########
if __name__ == '__main__':
    print("\n\n\n\n\n\n\n\nWelcome to SpotifyK!\n")
    repeat = True
    while (repeat):
        printMenu()
        try:
            select = getTypeInput('\nWhat would you like to do? (Enter 0 to exit) ', True)
            match select:
                case 1:
                    authorize()
                    print('\n-------   Done!   -------')
                case 2:
                    searchAlbum()
                    print('\n-------   Done!   -------')
                case 3:
                    changePreset()
                    print('\n-------   Done!   -------')
                case _:
                    cleanup()
                    print('\nAdios!\n\n')
                    repeat = False
        except Exception as ex:
            print('\n An error occurred. Call Oleg ig lol. \n[', ex, ']\n')
