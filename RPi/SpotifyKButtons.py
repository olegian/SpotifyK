from connections import getSpotify, getMongoDB, DEVICE_ID
import RPi.GPIO as GPIO
import os
from time import sleep

############  PORTS  ###############
SKIP = 40
PAUSE_PLAY = 37
PREV = 38
PRESET = 36
SHUTDOWN = 5 # NEVER CHANGE THIS

############  ENTRY  ###############
if __name__ == '__main__':
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(PAUSE_PLAY, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SKIP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PREV, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PRESET, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SHUTDOWN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    buttonUnlock = True
    spotify = getSpotify()
    db = getMongoDB()

    while True:
        print('----- RELOOP BUTTONS -----')
        try:
            #Check shutdown
            if GPIO.input(SHUTDOWN) == GPIO.HIGH:
                print('Shutting down...')
                GPIO.cleanup()
                os.system('sudo shutdown -h now')

            #Check buttons
            if buttonUnlock:
                if GPIO.input(PAUSE_PLAY) == GPIO.LOW:
                    print('Pausing Playback...')
                    if spotify.current_playback()['is_playing']:
                        spotify.pause_playback()
                    else:
                        spotify.start_playback()
                    buttonUnlock = False
                elif GPIO.input(SKIP) == GPIO.LOW:
                    print('Skipping Song...')
                    spotify.next_track()
                    buttonUnlock = False
                elif GPIO.input(PREV) == GPIO.LOW:
                    print('Prev Song...')
                    spotify.previous_track()
                    buttonUnlock = False
                elif GPIO.input(PRESET) == GPIO.LOW:
                    print('Playing Preset...')
                    playlistEntry = db['CardMap'].find_one({'_id' : 0})
                    spotify.start_playback(device_id=DEVICE_ID, context_uri=playlistEntry['uri'])
                    spotify.shuffle(True)
                    spotify.repeat('context', device_id=DEVICE_ID)
                    spotify.next_track()
                    buttonUnlock = False
            elif not buttonUnlock and GPIO.input(PAUSE_PLAY) == GPIO.HIGH and GPIO.input(SKIP) == GPIO.HIGH and GPIO.input(PREV) == GPIO.HIGH and GPIO.input(PRESET) == GPIO.HIGH:
                buttonUnlock = True

            sleep(0.1)
        except Exception as ex:
            print('- ', ex)
