# Finite State Machine Library
'''
    # Initialize Context
    hw_context = MyMachineContext()
    
    # Initialize FSM with context and logging
    # You can pass a custom logger here (e.g., logging.info)
    fsm = StateMachine(hw_context, log_func=print)
    
    # Register State Instances (Singleton Pattern)
    fsm.add_state(IdleState())
    fsm.add_state(RunState())
    
    # Start Machine
    fsm.start(IdleState)
    
    # Main Loop Simulation
    print("\n--- Starting Simulation Loop ---")
    for _ in range(15):
        fsm.run_cycle()
        time.sleep(0.5)
'''

__all__ = ['State', 'StateMachine']

class State:
    """
    Base interface for a State.
    State instances are stateless regarding the context data.
    They receive the context as an argument in methods.
    """
    def on_enter(self, ctx):
        """Executed once when entering this state."""
        pass

    def on_exit(self, ctx):
        """Executed once when exiting this state."""
        pass

    def update(self, ctx): 
        """
        Executed periodically.
        Returns:
            - The 'Class' of the next state to transition to.
            - None to stay in the current state.
        """
        return None

class StateMachine:
    """
    Generic controller handling state transitions.
    """
    def __init__(self, context, log_func=print):
        self.context = context       # User-defined hardware/data context
        self.current_state = None
        self.states = {}             # Storage for state instances
        self.log = log_func          # Logging function (default: print)

    def add_state(self, state_instance):
        """
        Registers a state instance.
        The key is automatically derived from the class name.
        """
        key = state_instance.__class__.__name__
        self.states[key] = state_instance

    def start(self, initial_state_cls):
        """Initializes the machine with the starting state class."""
        key = initial_state_cls.__name__
        
        if key in self.states:
            self.current_state = self.states[key]
            self.log(f"[FSM] System Started. Initial State: {key}")
            self.current_state.on_enter(self.context)
        else:
            self.log(f"[FSM] Error: Initial state '{key}' not registered.")

    def run_cycle(self):
        """
        Should be called in the main loop.
        Executes the current state's logic and handles transitions.
        """
        if not self.current_state:
            return

        # Inject context into the update method
        next_state_cls = self.current_state.update(self.context)

        if next_state_cls is not None:
            self._transition(next_state_cls)

    def _transition(self, next_state_cls):
        key = next_state_cls.__name__
        
        if key not in self.states:
            self.log(f"[FSM] Error: Target state '{key}' not registered.")
            return

        prev_state = self.current_state
        next_state = self.states[key]

        # 1. Log the transition
        self.log(f"[FSM] Transition: {prev_state.__class__.__name__} -> {key}")

        # 2. Exit current state
        prev_state.on_exit(self.context)
        
        # 3. Switch state
        self.current_state = next_state
        
        # 4. Enter new state
        self.current_state.on_enter(self.context)
