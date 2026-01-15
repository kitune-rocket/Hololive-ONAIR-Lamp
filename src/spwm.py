from machine import Pin, PWM, Timer, mem32
from micropython import const
import array
from safe_pin import SafePin

__all__ = ['SPWM']

# LEDC(PWM) control register
LEDC_BASE = const(0x3F41_9000)
LEDC_CH0_CONF0_REG = const(LEDC_BASE + 0x0000)
LEDC_CH0_CONF1_REG = const(LEDC_BASE + 0x000C)
LEDC_CH0_DUTY_REG = const(LEDC_BASE + 0x0008)

LEDC_CH1_CONF0_REG = const(LEDC_BASE + 0x0000 + 0x0014 * 1)
LEDC_CH1_CONF1_REG = const(LEDC_BASE + 0x000C + 0x0014 * 1)
LEDC_CH1_DUTY_REG = const(LEDC_BASE + 0x0008 + 0x0014 * 1)

LEDC_CH2_CONF0_REG = const(LEDC_BASE + 0x0000 + 0x0014 * 2)
LEDC_CH2_CONF1_REG = const(LEDC_BASE + 0x000C + 0x0014 * 2)
LEDC_CH2_DUTY_REG = const(LEDC_BASE + 0x0008 + 0x0014 * 2)

LEDC_CH3_CONF0_REG = const(LEDC_BASE + 0x0000 + 0x0014 * 3)
LEDC_CH3_CONF1_REG = const(LEDC_BASE + 0x000C + 0x0014 * 3)
LEDC_CH3_DUTY_REG = const(LEDC_BASE + 0x0008 + 0x0014 * 3)

LEDC_CH4_CONF0_REG = const(LEDC_BASE + 0x0000 + 0x0014 * 4)
LEDC_CH4_CONF1_REG = const(LEDC_BASE + 0x000C + 0x0014 * 4)
LEDC_CH4_DUTY_REG = const(LEDC_BASE + 0x0008 + 0x0014 * 4)

LEDC_CH5_CONF0_REG = const(LEDC_BASE + 0x0000 + 0x0014 * 5)
LEDC_CH5_CONF1_REG = const(LEDC_BASE + 0x000C + 0x0014 * 5)
LEDC_CH5_DUTY_REG = const(LEDC_BASE + 0x0008 + 0x0014 * 5)

LEDC_CH6_CONF0_REG = const(LEDC_BASE + 0x0000 + 0x0014 * 6)
LEDC_CH6_CONF1_REG = const(LEDC_BASE + 0x000C + 0x0014 * 6)
LEDC_CH6_DUTY_REG = const(LEDC_BASE + 0x0008 + 0x0014 * 6)

LEDC_CH7_CONF0_REG = const(LEDC_BASE + 0x0000 + 0x0014 * 7)
LEDC_CH7_CONF1_REG = const(LEDC_BASE + 0x000C + 0x0014 * 7)
LEDC_CH7_DUTY_REG = const(LEDC_BASE + 0x0008 + 0x0014 * 7)

LEDC_PARAM_UPDATE_MASK = const(1 << 4)
LEDC_DUTY_CHG_START_MASK = const(1 << 31)
LEDC_LS_SIG_OUT0 = const(79)

# GPIO control register
GPIO_MATRIX_BASE = const(0x6000_4000)
GPIO_FUNC0_OUT_SEL_CFG_REG = const(GPIO_MATRIX_BASE + 0x0554)

# SPWM look up table
SINE_INDEX0 = array.array('i', [0])
SINE_INDEX1 = array.array('i', [0])
SINE_INDEX2 = array.array('i', [0])
SINE_INDEX3 = array.array('i', [0])
SINE_INDEX4 = array.array('i', [0])
SINE_INDEX5 = array.array('i', [0])
SINE_INDEX6 = array.array('i', [0])
SINE_INDEX7 = array.array('i', [0])
SINE_INDEX = [SINE_INDEX0, SINE_INDEX1, SINE_INDEX2, SINE_INDEX3, SINE_INDEX4, SINE_INDEX5, SINE_INDEX6, SINE_INDEX7]
SINE_TABLE = array.array('i', [64, 76, 88, 99, 108, 116, 122, 126, 127, 126, 122, 116, 108, 99, 88, 76, 
                                        64, 51, 39, 28, 19, 11, 5, 1, 0, 1, 5, 11, 19, 28, 39, 51,])

@micropython.viper
def ledc_ch0_isr(htim) :
    global SINE_INDEX0, SINE_TABLE
    index = ptr32(SINE_INDEX0)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH0_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH0_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH0_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch1_isr(htim) :
    global SINE_INDEX1, SINE_TABLE
    index = ptr32(SINE_INDEX1)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH1_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH1_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH1_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch2_isr(htim) :
    global SINE_INDEX2, SINE_TABLE
    index = ptr32(SINE_INDEX2)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH2_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH2_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH2_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch3_isr(htim) :
    global SINE_INDEX3, SINE_TABLE
    index = ptr32(SINE_INDEX3)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH3_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH3_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH3_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch4_isr(htim) :
    global SINE_INDEX4, SINE_TABLE
    index = ptr32(SINE_INDEX4)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH4_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH4_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH4_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch5_isr(htim) :
    global SINE_INDEX5, SINE_TABLE
    index = ptr32(SINE_INDEX5)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH5_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH5_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH5_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch6_isr(htim) :
    global SINE_INDEX6, SINE_TABLE
    index = ptr32(SINE_INDEX6)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH6_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH6_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH6_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch7_isr(htim) :
    global SINE_INDEX7, SINE_TABLE
    index = ptr32(SINE_INDEX7)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH7_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH7_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH7_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

LEDC_ISR = [ledc_ch0_isr, ledc_ch1_isr, ledc_ch2_isr, ledc_ch3_isr,
            ledc_ch4_isr, ledc_ch5_isr, ledc_ch6_isr, ledc_ch7_isr]

# SPWM generation class in audio frequency range
class SPWM:

    _used_ids = set()
    _MAX_TIMERS = 4 # ESP32-S2 Max = 4, Adjust this parameter value to use timers elsewhere.
    _SPWM_MULTIPLE = 32 # SPWM LUT size, Sine wave generation resolution 

    @classmethod
    def _allocate_id(cls):
        for i in range(cls._MAX_TIMERS):
            if i not in cls._used_ids:
                cls._used_ids.add(i)
                return i
        
        # Raise if there is no available timer
        raise RuntimeError("All hardware timer is in use")

    def _get_ledc_ch_number(self, pin_num: int):
        sig_out = mem32[GPIO_FUNC0_OUT_SEL_CFG_REG + 4 * pin_num]
        return (sig_out & 0xFF) - LEDC_LS_SIG_OUT0

    def _allocate_isr(self, ch_num: int):
        global LEDC_ISR
        if ch_num < 8:
            return LEDC_ISR[ch_num]
        else:
            raise RuntimeError(f'Invalid channel number: {ch_num}')

    def __init__(self, pin_num: int):
        self._pin = SafePin(pin_num, owner_key='spwm')
        self._pin.acquire()
        self._pin.init(Pin.OUT)

        self._timer_id = self._allocate_id()
        self._timer = Timer(self._timer_id)
        # LEDC_CLK=80MHz, Divider=1, Duty resolution=7bit
        self._pwm = PWM(self._pin.unwrap(), freq=80_000_000//(1*128), duty=512)
        _ch_num = self._get_ledc_ch_number(self._pin.id())
        self._isr = self._allocate_isr(_ch_num)
        global SINE_INDEX
        self._sine_index = SINE_INDEX[_ch_num]

    def start(self, freq):
        self._sine_index[0] = 0
        self._timer.init(freq=int(freq*self._SPWM_MULTIPLE), mode=Timer.PERIODIC, callback=self._isr)

    def stop(self):
        self._timer.deinit()
        self._sine_index[0] = 0
        self._pwm.duty(512)

    def deinit(self):
        self.stop()
        self._pwm.deinit()
        self._used_ids.remove(self._timer_id)
        self._pin.release()