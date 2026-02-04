from machine import freq, Pin, Timer
import time, ntptime
import boot
from safe_pin import SafePin
from sound import NotiSound
from vfd import Vfd

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
    def __init__(self, light_pin:int, trigger_pin:int, amp_pin:int, spwm_pins:list[int]):
        self._light = SafePin(light_pin, owner_key='desklight')
        self._light.acquire()
        self._light.init(Pin.OUT)
        self.light_off()

        self._amp = SafePin(amp_pin, owner_key='desklight')
        self._amp.acquire()
        self._amp.init(Pin.OUT)
        self._amp.off()

        self._trigger_pin_number = trigger_pin
        self._spwm_pin_numbers = spwm_pins

    def play(self):
        sound = NotiSound(self._spwm_pin_numbers, self._trigger_pin_number)
        self._amp.on()
        sound.play('./audio.bin')
        self._amp.off()
        sound.deinit()

    def light_on(self):
        self._light.off()

    def light_off(self):
        self._light.on()

    def deinit(self):
        self._light.release()
        self._amp.release()

####

vfd = None # Global VFD instance
last_vfd_update = 0

def init():
    freq(240_000_000) # Highst clock of ESP32-S2
    desklight = Desklight(35, 33, 12, [34]) # original
    desklight.play()
    desklight.deinit()
    boot.EnableWifi()
    ntp_task(None)  # Initial NTP sync

    led = SafePin(11, owner_key='init')
    led.init(Pin.OUT)
    led.off()
    global vfd
    vfd = Vfd(DO=11, CLK=34, CS=33, RST=13, DUMMY=14)
    vfd.write(0, '00:00:00')

def led_task(htim):
    led = SafePin(10, owner_key='led_task')
    led.toggle()

def clock_task(htim):
    global vfd, last_vfd_update

    current_time = time.time()
    if current_time - last_vfd_update >= 1:
        tm = time.localtime(current_time + 9 * 3600)  # JST
        tm_string = f'{tm[3]:02}:{tm[4]:02}:{tm[5]:02}'
        first_changed_index = 0

        if last_vfd_update == 0:
            first_changed_index = 0
        else:
            tm_before = time.localtime(last_vfd_update + 9 * 3600)  # JST
            tm_before_string = f'{tm_before[3]:02}:{tm_before[4]:02}:{tm_before[5]:02}'

            for i in range(len(tm_string)):
                if tm_string[i] != tm_before_string[i]:
                    first_changed_index = i
                    break

        vfd.write(first_changed_index, tm_string[first_changed_index:])

        # update the last update time
        last_vfd_update = current_time

def ntp_task(htim):
    try:
        ntptime.settime()
    except:
        pass

def main():
    init()

    timer = Timer(0)
    timer.init(freq=2, mode=Timer.PERIODIC, callback=led_task)

    timer2 = Timer(1)
    timer2.init(period=(1000 * 60 * 20), mode=Timer.PERIODIC, callback=ntp_task)

    timer3 = Timer(2)
    timer3.init(freq=10, mode=Timer.PERIODIC, callback=clock_task)

    while True :
        time.sleep(1)

if __name__ == '__main__' :
    main()
