from machine import freq, Pin
from micropython import const
import time, ntptime, struct
import requests
import boot
from fsm import *
from spwm import *

class Datetime:
    @staticmethod
    def diff_from_now_in_seconds(datetime_str: str) -> int:
        """
        Args:
            datetime_str (str): UTC datetime string in "YYYY-MM-DDTHH:MM:SS.sssZ" format.
        Returns:
            int: The difference in seconds (positive if the time is in the future).
        """
        # Parse the ISO 8601 string manually
        year = int(datetime_str[0:4])
        month = int(datetime_str[5:7])
        day = int(datetime_str[8:10])
        hour = int(datetime_str[11:13])
        minute = int(datetime_str[14:16])
        second = int(datetime_str[17:19])
        
        # mktime tuple: (year, month, mday, hour, minute, second, weekday, yearday)
        # We set weekday and yearday to -1 to let mktime calculate them.
        parsed_time_tuple = (year, month, day, hour, minute, second, -1, -1)
        
        parsed_seconds = time.mktime(parsed_time_tuple)
        
        # Get current time in seconds since the epoch (UTC)
        current_seconds = time.time()
        
        return int(parsed_seconds - current_seconds)

    @staticmethod
    def diff(datetime_str: str) -> int:
        return Datetime.diff_from_now_in_seconds(datetime_str)

    @staticmethod
    def diff_minute(datetime_str: str) -> int:
        return int(Datetime.diff(datetime_str) / 60)

    @staticmethod
    def diff_hour(datetime_str: str) -> int:
        return int(Datetime.diff(datetime_str) / 3600)

class Desklight:
    def __init__(self, light_pin:int, spwm_pin:int, trigger_pin:int, amp_pin:int):
        self._light = Pin(light_pin, Pin.OUT)
        self._light.on()
        self._spwm = SPWM(spwm_pin)
        self._trg = Pin(trigger_pin, Pin.OUT)
        self._trg.off()
        self._amp = Pin(amp_pin, Pin.OUT)
        self._amp.off()

    def play(self):
        self._amp.on()
        with open('./audio.bin', 'rb') as f:
            while True:
                data = f.read(4)
                if not data: #EOF
                    break
                freq, duration = struct.unpack('<HH', data)
                if freq == 0:
                    self._spwm.stop()
                    time.sleep_us(duration*1000)
                    continue
                self._spwm.start(freq)
                self._trg.on()
                time.sleep_us(1000)
                self._trg.off()
                time.sleep_us((duration-1)*1000)
        self._amp.off()
        self._spwm.stop()
    
    def light_on(self):
        self._light.on()

    def light_off(self):
        self._light.off()

class Holodex:
    def __init__(self, token, channel_id):
        self._token = token
        self._channel_id = channel_id

    def _get_live_url(self):
        base = 'https://holodex.net/api/v2/live'
        params = []
        params.append(f'channel_id={self._channel_id}')
        params.append(f'status=live,upcoming')
        params.append(f'limit=5')
        params.append(f'order=asc')
        params.append(f'sort=start_scheduled')
        params.append(f'include=live_info')
        return base + '?' + '&'.join(params)

    # Blokcing api call
    def get_live(self):
        response = requests.get(self._get_live_url(), headers={'X-APIKEY': self._token})
        if response.status_code != 200:
            return None, response.status_code
        return response.json(), response.status_code

class YoutubeData:
    def __init__(self, token):
        self._token = token
        self._channel_id = ''
        self._video_id = ''
        self._video_etag = ''

    def set_channel_id(self, channel_id):
        self._channel_id = channel_id

    def set_video_id(self, video_id):
        self._video_id = video_id

    def get_video_list(self):
        base = 'https://www.googleapis.com/youtube/v3/videos'
        params = []
        params.append(f'part=liveStreamingDetails')
        params.append(f'id={self._video_id}')
        params.append(f'key={self._token}')

        headers = {'If-None-Match': self._video_etag}

        response = requests.get(base + '?' + '&'.join(params), headers=headers)
        
        # 304: Duplicated response(If-None-Match) >> Not updated
        # 404: Video ID is not valid >> Upcomming live is removed
        if response.status_code != 200:
            return None, response.status_code
        result = response.json()
        self._video_etag = result['etag']
        return result, response.status_code

# Global status / data class
class Context:
    def __init__(self):
        self.upcomming: dict = None # Holodex api response
        self.on_air: dict = None # Youtube api response
        self.__timer = time.ticks_ms()
        self.api = Holodex(boot.config['key_holodex'], boot.config['channelId'])
        self.youtube = YoutubeData(boot.config['key_youtube'])

        self.desklight = Desklight(35, 34, 33, 12) # original
        # self.desklight = Desklight(11, 34, 33, 12) # test board
    
    def log(self, msg):
        # print(f'{msg}') # for debugging
        pass
    
    def set_timer(self):
        self.__timer = time.ticks_ms()
    
    def get_timer(self):
        return time.ticks_diff(time.ticks_ms(), self.__timer)
    
    def clear_timer(self):
        self.__timer = 0


#### Main FSM

def get_upcomming(ctx):
    try :
        resp, code = ctx.api.get_live()
    except :
        ctx.log(f'[Error] API call failed with exception (network related)')
        return None # Using cached response.
    
    # Using cached response.
    if resp is None:
        ctx.log(f'[Error] API call failed with code {code}')
        return None
    
    # Upcomming live is removed
    # Remove cached response.
    if len(resp) == 0:
        ctx.log(f'[API] Upcomming is empty')
        ctx.upcomming = None
        return None
    
    # Update cached response
    ctx.log(f'[API] Upcomming found: {resp[0]["title"]}, {resp[0]["start_scheduled"]}')
    ctx.upcomming = resp[0]
    return ctx.upcomming

def get_on_air(ctx):
    try :
        resp, code = ctx.youtube.get_video_list()
    except :
        ctx.log(f'[Error] API call failed with exception (network related)')
        return None # Using cached response.
    
    # Data is no updated (Still upcommnig)
    # Using cached response. 
    if code == 304 :
        # ctx.log(f'[API] Data is not updated') #
        return None

    # Upcomming live is removed
    # Remove cached response.
    if code == 404 :
        ctx.youtube = None
        ctx.upcomming = None
        ctx.log(f'[API] Upcomming live is removed')
        return None

    # Using cached response.
    if code != 200 :
        ctx.log(f'[Error] API call failed with code {code}')
        return None

    # Update cached response.
    ctx.on_air = resp['items'][0]
    
    # Assume snippet.liveBroadcastContent 
    #   by existence of liveStreamingDetails.actualStartTime
    # Workaround due to large size response of snippet
    if 'actualStartTime' in ctx.on_air['liveStreamingDetails']:
        ctx.onair['status'] = 'live'
    else:
        ctx.on_air['status'] = 'upcoming'
    return ctx.on_air

class IdleState(State):
    def update(self, ctx):
        # Every 5 minutes. Reducing API call count.
        if ctx.get_timer() < const(5 * 60 * 1000):
            return None
        ctx.set_timer()

        get_upcomming(ctx)
        if ctx.upcomming is None:
            return None

        if ctx.upcomming['status'] == 'live':
            return OnAir

        if Datetime.diff_minute(ctx.upcomming['start_scheduled']) < 10:
            return Waiting
        return None

class Waiting(State):
    def update(self, ctx):
        # Every 10 seconds.
        if ctx.get_timer() < const(10 * 1000):
            return None
        ctx.set_timer()
        
        get_upcomming(ctx)
        if ctx.upcomming is None:
            return IdleState

        if ctx.upcomming['status'] == 'live':
            return OnAir

        if Datetime.diff_minute(ctx.upcomming['start_scheduled']) > 10:
            return IdleState
        return None

class OnAir(State):
    def on_enter(self, ctx):
        boot.DisableWifi()
        ctx.desklight.light_off()
        ctx.desklight.play()
        boot.EnableWifi()

    def on_exit(self, ctx):
        ctx.desklight.light_on()

    def update(self, ctx):
        # Every 5 minutes. Reducing API call count.
        if ctx.get_timer() < const(5 * 60 * 1000):
            return None
        ctx.set_timer()
        
        get_upcomming(ctx)
        if ctx.upcomming is None:
            return IdleState
        if ctx.upcomming['status'] != 'live':
            return IdleState
        return None

####

def init():
    freq(240_000_000) # Highst clock of ESP32-S2
    for _ in range(10):
        try:
            ntptime.settime()
        except:
            continue
        break

def main():
    init()
    context = Context()
    led = Pin(11, Pin.OUT)
    led.off()

    fsm = StateMachine(context)
    fsm.add_state(IdleState())
    fsm.add_state(Waiting())
    fsm.add_state(OnAir())

    fsm.start(OnAir) # For audio test run at power up. After audio playing, states fallbacks to IdleState.
    while True :
        fsm.run_cycle()
        led.value(not led.value())
        time.sleep(1)

if __name__ == '__main__' :
    main()
