from safe_pin import SafePin
from machine import Pin
from spwm import SPWM
import time

class NotiSound:
    def __init__(self, spwm_pins: list[int], trigger_pin: int):
        self._spwms = [SPWM(pin) for pin in spwm_pins]
        self._trigger_pin = SafePin(trigger_pin, owner_key='noti_sound')
        self._trigger_pin.acquire()
        self._trigger_pin.init(Pin.OUT)
        self._trigger_pin.off()
        self._spwm_count = len(self._spwms)

    def play(self, audio_file: str):
        with open(audio_file, 'rb') as f:
            # Duration: 2B
            # Frequencies: 2B * note count
            buf_size = 2 + self._spwm_count * 2
            buf = bytearray(buf_size)
            while True:
                n = f.readinto(buf)
                if not n or n < buf_size:
                    break
                duration = buf[0] | (buf[1] << 8)
                for i in range(self._spwm_count):
                    freq = buf[2 + i*2] | (buf[3 + i*2] << 8)
                    if freq > 0:
                        self._spwms[i].start(freq)
                    else:
                        self._spwms[i].stop()
                self._trigger_pin.on()
                time.sleep_us(1000)
                self._trigger_pin.off()
                time.sleep_us((duration - 1) * 1000)
            for spwm in self._spwms:
                spwm.stop()

    def deinit(self):
        for spwm in self._spwms:
            spwm.deinit()
        self._trigger_pin.release()