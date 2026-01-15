from machine import Pin

class _PinCore:
    """
    Internal singleton class that manages the actual machine.Pin object and its lock state.
    Users should not instantiate this directly.
    """
    _instances = {}

    def __new__(cls, id, *args, **kwargs):
        if id not in cls._instances:
            cls._instances[id] = super().__new__(cls)
            cls._instances[id]._initialized = False
        return cls._instances[id]

    def __init__(self, id, *args, **kwargs):
        # Initialize only once for the singleton 
        if not self._initialized:
            self.id = id
            # Contruct the actual machine.Pin object with additional args
            self.pin = Pin(id, *args, **kwargs)
            self.owner_key = None # Current owner key for mutex (None if free)
            self._initialized = True
    
    def reinit(self, *args, **kwargs):
        """Reinitialize pin mode (init)"""
        self.pin.init(*args, **kwargs)

class SafePin:
    """
    Wrapper class for machine.Pin.
    - Controls access to a singleton PinCore.
    - Manages write permissions via owner_key.
    """
    
    def __init__(self, id, owner_key, mode=-1, pull=-1, *, value=None, drive=None, alt=None):
        """
        :param id: GPIO pin number
        :param owner_key: Unique key to identify the current module (e.g., self, 'module_name')
        :param args, kwargs: machine.Pin initialization parameters
        """
        self._core = _PinCore(id, mode, pull, value=value, drive=drive, alt=alt)
        self._my_key = owner_key

    # Additional pin number return method
    def id(self):
        return self._core.id

    # Mutex-like methods for pin control
    def acquire(self):
        """
        Acquire control of the pin.
        Raises RuntimeError if it is already locked by another key.
        """
        if self._core.owner_key is not None and self._core.owner_key != self._my_key:
            raise RuntimeError(f"Pin {self._core.id} is locked by {self._core.owner_key}")
        
        self._core.owner_key = self._my_key
        return True

    def release(self):
        """
        Release control of the pin.
        Only allowed if the current owner holds the lock.
        """
        if self._core.owner_key == self._my_key:
            self._core.owner_key = None

    def is_mine(self):
        """Check if the current instance holds control or if the pin is free."""
        # Returns True if not locked or locked by this instance's key
        return self._core.owner_key is None or self._core.owner_key == self._my_key

    def _check_permission(self):
        """Check write permission before performing write operations."""
        if self._core.owner_key is not None and self._core.owner_key != self._my_key:
            raise PermissionError(f"Pin {self._core.id} write access denied. Owned by {self._core.owner_key}")

    # Wrapping machine.Pin interface (read allowed, write restricted)
    
    def value(self, *args):
        """
        If no args (read): perform without restriction
        If args (write): check permission before performing
        """
        if len(args) == 0:
            return self._core.pin.value()
        else:
            self._check_permission()
            return self._core.pin.value(args[0])

    def on(self):
        self._check_permission()
        return self._core.pin.on()

    def off(self):
        self._check_permission()
        return self._core.pin.off()
    
    def toggle(self):
        self._check_permission()
        return self._core.pin.toggle()

    def init(self, *args, **kwargs):
        self._check_permission()
        # Reinitialize the pin state of the singleton Core
        return self._core.reinit(*args, **kwargs)

    def irq(self, *args, **kwargs):
        self._check_permission()
        return self._core.pin.irq(*args, **kwargs)

    # Context Manager support (automatic acquire/release when using with statement)
    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()