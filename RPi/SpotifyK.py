from connections import getSpotify, getMongoDB, CARD_KEY, DEVICE_ID
import RPi.GPIO as GPIO
import MFRC522
import random
import json
import signal

############  HELPERS  ###############
def empty():
    print('fuck!')
    
def stringify(data):
    strings = [str(i) for i in data]
    return ''.join(strings)

def readerWait(writer, writeData=None):
    data = []
    while not data:
        (status, TagType) = writer.MFRC522_Request(writer.PICC_REQIDL)
        if status == writer.MI_OK:
            (status, uid) = writer.MFRC522_Anticoll()
            writer.MFRC522_SelectTag(uid)
            status = writer.MFRC522_Auth(writer.PICC_AUTHENT1A, 8, CARD_KEY, uid)
            if status == writer.MI_OK:
                data = writer.MFRC522_Read(8)
                if writeData is not None:
                    writer.MFRC522_Write(8, writeData)
                writer.MFRC522_StopCrypto1()
            else:
                print('Auth Error')
    
    GPIO.cleanup() 
    return data

############  ENTRY  ###############
if __name__ == '__main__':
    print('Running SpotifyK...')

    # GET SERVICES
    db = getMongoDB()
    spotify = getSpotify()
    pipeline = [{'$match' : {'operationType' : 'insert'}}]
    
    # INIT GPIO
    GPIO.setmode(GPIO.BOARD)
    reader = MFRC522.MFRC522()
    signal.signal(signal.SIGINT, empty)
    
    # LOCKS
    oldRead = []
    
    #### MAIN LOOP ####
    while True:
        print('----- RELOOP -----')
        try: 
            #Check database for any updates
            with db.watch(pipeline) as stream:
                change = stream.try_next()
                if change is not None:
                    changeCollection = change['ns']['coll']
                    
                    #Change in CardMap
                    if changeCollection == 'CardMap':
                        print('CARD UPDATE')
                        repeat = True
                        while repeat:
                            try:
                                newKey = random.sample(range(0, 255), 16)
                                oldKey = readerWait(reader, newKey)
                                db[changeCollection].delete_one({'key' : stringify(oldKey)})
                                db[changeCollection].find_one_and_update({'_id' : change['documentKey']['_id']}, {'$set' : {'key' : stringify(newKey)}})
                                repeat = False
                            except:
                                print('Encountered error writing, trying again...')

                    #Change in AuthInfo
                    elif changeCollection == 'AuthInfo':
                        print('AUTH UPDATE')
                        if change['documentKey']['_id'] == 'authInfo':
                            with open('.cache', 'w') as outfile:
                                outfile.write(json.dumps(change['fullDocument']))
                            db[changeCollection].delete_one({'_id' : 'authInfo'})
            
            #Check Card Read
            (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)
            if status == reader.MI_OK:
                print('READ')
                (status, uid) =  reader.MFRC522_Anticoll()
                reader.MFRC522_SelectTag(uid)
                status = reader.MFRC522_Auth(reader.PICC_AUTHENT1A, 8, CARD_KEY, uid)
                if status  == reader.MI_OK:
                    read = reader.MFRC522_Read(8)
                    
                    #If placed card is new (doesnt play duplicates)
                    if read != oldRead:
                        albumEntry = db['CardMap'].find_one({'key' : stringify(read)})
                        spotify.shuffle(False)
                        spotify.start_playback(device_id=DEVICE_ID, context_uri=albumEntry['uri'])
                        spotify.repeat('context', device_id=DEVICE_ID)
                        oldRead = read

                    reader.MFRC522_StopCrypto1()
                else: 
                    print('Card Read, but not Authenticated')
            
            
            print('- no exceptions')
        except Exception as ex:
            GPIO.cleanup()
            GPIO.setmode(GPIO.BOARD)
            reader = MFRC522.MFRC522()
            signal.signal(signal.SIGINT, empty)

            print('- ', ex)
            
    