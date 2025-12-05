from machine import soft_reset
from time import sleep
import network, json

config = {}
with open('./config.json') as f :
    s = f.read()
    config = json.loads(s)

wlan = network.WLAN()
def EnableWifi() :
    global wlan
    wlan.active(True)
    wlan.connect(config['ssid'], config['password'])
    for _ in range(10) :
        if wlan.isconnected() :
            break
        sleep(1)

def DisableWifi() :
    global wlan
    wlan.active(False)
    sleep(1)

EnableWifi()

if wlan.isconnected() == False :
    soft_reset()

try :
    import requests
except :
    import mip
    mip.install('requests')
    soft_reset()
