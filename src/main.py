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
    def __init__(self, token, channelId):
        self.token = token
        self.channelId = channelId

    def __get_live_url(self):
        base_url = 'https://holodex.net/api/v2/live'
        query_params = []
        query_params.append(f'channel_id={self.channelId}')
        query_params.append(f'status=live,upcoming')
        query_params.append(f'limit=5')
        query_params.append(f'order=asc')
        query_params.append(f'sort=start_scheduled')
        query_params.append(f'include=live_info')
        return base_url + '?' + '&'.join(query_params)

    # Blokcing api call
    def get_live(self):
        response = requests.get(self.__get_live_url(), headers={'X-APIKEY': self.token})
        return response.json(), response.status_code

# Global status / data class
class Context:
    def __init__(self):
        self.upcomming: dict = None # Holodex api response
        self.__timer = time.ticks_ms()
        self.token = boot.config['token']
        self.channelId = boot.config['channelId']
        self.api = Holodex(boot.config['token'], boot.config['channelId'])
        self.desklight = Desklight(11, 34, 33, 12) #self.desklight = Desklight(11, 34, 33, 35)
    
    def log(self, msg):
        print(f'{msg}')
        pass
    
    def set_timer(self):
        self.__timer = time.ticks_ms()
    
    def get_timer(self):
        return time.ticks_diff(time.ticks_ms(), self.__timer)
    
    def clear_timer(self):
        self.__timer = 0


#### Main FSM

def GetUpcomming(ctx):
    resp, code = ctx.api.get_live()
    if code != 200:
        ctx.log(f'[Error] API call failed with code {code}')
        return ctx.upcomming
    
    if len(resp) == 0:
        ctx.log(f'[API] Upcomming is empty')
        ctx.upcomming = None
        return None
    
    ctx.log(f'[API] Upcomming found: {resp[0]["title"]}, {resp[0]["start_scheduled"]}')
    ctx.upcomming = resp[0]
    return ctx.upcomming

class IdleState(State):
    def update(self, ctx):
        if ctx.get_timer() < const(5 * 60 * 1000):
            return None
        ctx.set_timer()

        GetUpcomming(ctx)
        if ctx.upcomming is None:
            return None

        if ctx.upcomming['status'] == 'live':
            return OnAir

        if Datetime.diff_minute(ctx.upcomming['start_scheduled']) < 10:
            return Waiting
        return None

class Waiting(State):
    def update(self, ctx):
        if ctx.get_timer() < const(10 * 1000):
            return None
        ctx.set_timer()
        
        GetUpcomming(ctx)
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
        if ctx.get_timer() < const(5 * 60 * 1000):
            return None
        ctx.set_timer()
        
        GetUpcomming(ctx)
        if ctx.upcomming is None:
            return IdleState
        if ctx.upcomming['status'] != 'live':
            return IdleState
        return None

####

def init():
    freq(240_000_000) # Highst frequency of ESP32-S2
    for _ in range(10):
        try:
            ntptime.settime()
        except:
            continue
        break

def main():
    init()
    context = Context()

    fsm = StateMachine(context)
    fsm.add_state(IdleState())
    fsm.add_state(Waiting())
    fsm.add_state(OnAir())

    fsm.start(IdleState)
    while True :
        fsm.run_cycle()
        time.sleep(1)

if __name__ == '__main__' :
    main()
