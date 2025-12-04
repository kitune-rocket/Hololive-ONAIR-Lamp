from machine import Pin, PWM, Timer, mem32
from micropython import const
import array

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
SINE_INDEX = array.array('i', [0])
SINE_TABLE = array.array('i', [64, 76, 88, 99, 108, 116, 122, 126, 127, 126, 122, 116, 108, 99, 88, 76, 
                                        64, 51, 39, 28, 19, 11, 5, 1, 0, 1, 5, 11, 19, 28, 39, 51,])

@micropython.viper
def ledc_ch0_isr(htim) :
    global SINE_INDEX, SINE_TABLE
    index = ptr32(SINE_INDEX)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH0_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH0_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH0_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch1_isr(htim) :
    global SINE_INDEX, SINE_TABLE
    index = ptr32(SINE_INDEX)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH1_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH1_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH1_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch2_isr(htim) :
    global SINE_INDEX, SINE_TABLE
    index = ptr32(SINE_INDEX)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH2_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH2_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH2_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch3_isr(htim) :
    global SINE_INDEX, SINE_TABLE
    index = ptr32(SINE_INDEX)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH3_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH3_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH3_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch4_isr(htim) :
    global SINE_INDEX, SINE_TABLE
    index = ptr32(SINE_INDEX)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH4_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH4_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH4_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch5_isr(htim) :
    global SINE_INDEX, SINE_TABLE
    index = ptr32(SINE_INDEX)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH5_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH5_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH5_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch6_isr(htim) :
    global SINE_INDEX, SINE_TABLE
    index = ptr32(SINE_INDEX)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH6_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH6_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH6_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

@micropython.viper
def ledc_ch7_isr(htim) :
    global SINE_INDEX, SINE_TABLE
    index = ptr32(SINE_INDEX)
    table = ptr32(SINE_TABLE)

    duty_val = table[index[0]]
    index[0] = (index[0] + 1) & 0x0000001F # table size = 32
    
    ptr32(LEDC_CH7_DUTY_REG)[0] = (duty_val << 4)
    ptr32(LEDC_CH7_CONF1_REG)[0] |= uint(LEDC_DUTY_CHG_START_MASK) 
    ptr32(LEDC_CH7_CONF0_REG)[0] |= uint(LEDC_PARAM_UPDATE_MASK)

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
        if ch_num == 0:
            return ledc_ch0_isr
        elif ch_num == 1:
            return ledc_ch1_isr
        elif ch_num == 2:
            return ledc_ch2_isr
        elif ch_num == 3:
            return ledc_ch3_isr
        elif ch_num == 4:
            return ledc_ch4_isr
        elif ch_num == 5:
            return ledc_ch5_isr
        elif ch_num == 6:
            return ledc_ch6_isr
        elif ch_num == 7:
            return ledc_ch7_isr
        else:
            raise RuntimeError(f'Invalid channel number: {ch_num}')

    def __init__(self, pin_num: int):
        self._pin = Pin(pin_num, Pin.OUT)
        self._timer_id = self._allocate_id()
        self._timer = Timer(self._timer_id)
        # LEDC_CLK=80MHz, Divider=1, Duty resolution=7bit
        self._pwm = PWM(self._pin, freq=80_000_000//(1*128), duty=0)
        _ch_num = self._get_ledc_ch_number(pin_num)
        self._isr = self._allocate_isr(_ch_num)

    def start(self, freq):
        self.stop()
        self._timer.init(freq=int(freq*self._SPWM_MULTIPLE), mode=Timer.PERIODIC, callback=self._isr)

    def stop(self):
        self._timer.deinit()
