from machine import SoftSPI, Pin
from safe_pin import SafePin

# Vaccum Fluorescent Display, Futaba's 8 digit
# Reference: https://github.com/3KUdelta/Futaba-VFD-16bit_ESP32/blob/main/vfd_controls.h
class Vfd:

    DIGITS = 8

    def _bit_swap(self, data: int) -> int:
        temp = '{:08b}'.format(data)
        temp = ''.join(reversed(temp))
        return int(temp, 2)

    def _write(self, data): # data: int or list(int)
        if type(data) == int:
            data = [data]
        elif type(data) != list:
            return
        buf = [self._bit_swap(d) for d in data]
        self._cs.off()
        self._spi.write(bytes(buf))
        self._cs.on()

    def set_brightness(self, brightness):
        self._write([0xE4, brightness])

    def set_standby(self, standby:bool):
        if standby:
            buf=[0xED]
        else :
            buf=[0xEC]
        self._write(buf)

    def clear(self):
        buf = [0x20]
        for i in range(self.DIGITS):
            buf.append(0x20)
        buf.append(0xE8) # Refresh
        self._write(buf)

    def _init_display(self) :
        self._write([0xE0, 0x07]) # 8 Digit VFD
        self.set_brightness(50) # Initial Brightness
        self.set_standby(False) # Wake up
        self.clear()
        self._write([0xE8]) # Refresh

    '''
    pos: 0-self.DIGITS - 1, 0~7
    '''
    def write(self, pos: int, data): # data: str or list(int)

        if pos > self.DIGITS - 1:
            return
        length = len(data)
        buf = [0x20 + pos] # 0x20: base register DCRAM 0H
        
        if type(data) == str:
            buf += [ord(c) for c in data[0:min(length, self.DIGITS)]]
        elif type(data) == list:
            buf += data[0:min(length, self.DIGITS)]
        else:
            return
        self._write(buf)

    '''
    VFD use DO in SPI, but dueto SoftSPI class, dummy pin is required.
    '''
    def __init__(self, DO, CLK, CS, RST, DUMMY) -> None:

        self._do = SafePin(DO, owner_key='vfd')
        self._do.acquire()
        
        self._clk = SafePin(CLK, owner_key='vfd')
        self._clk.acquire()

        self._dummy = SafePin(DUMMY, owner_key='vfd')
        self._dummy.acquire()

        self._spi = SoftSPI(baudrate=100_000, polarity=1, phase=1, 
            sck=self._clk.unwrap(), mosi=self._do.unwrap(), miso=self._dummy.unwrap())
        
        self._cs = SafePin(CS, owner_key='vfd')
        self._rst = SafePin(RST, owner_key='vfd')
        
        self._cs.init(Pin.OUT)
        self._rst.init(Pin.OUT)

        self._cs.acquire()
        self._rst.acquire()

        self._cs.on()
        self._rst.on()
        self._init_display()

    def deinit(self):
        self.clear()
        self.set_standby(True)
        
        self._do.release()
        self._clk.release()
        self._dummy.release()
        self._cs.release()
        self._rst.release()


