from collections import namedtuple
from enum import Enum
from evdev import UInput, ecodes as e
import hid
from collections import deque 
from threading import Timer

# Elgato Stream Deck Pedal Vendor / Product IDs
VENDOR_ID = 0x0FD9
PRODUCT_ID = 0x0086


# Represents a key combination of mods, which are held for the whole
# combination, and keys, which are pressed and released.
KeyCombo = namedtuple("KeyCombo", ["mods", "keys", "hold"], defaults=([], []))


# Simple enum that represents the three buttons.
class Button(Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2
    
sequences = deque([],maxlen=2) 
holds = []

class PedalMapper:
    def __init__(self, left_keys=[], middle_keys=[], right_keys=[], dbl_left_keys=[], dbl_middle_keys=[], dbl_right_keys=[], polling_rate=10):
        self.button_key_mappings = (left_keys, middle_keys, right_keys, dbl_left_keys, dbl_middle_keys, dbl_right_keys)
        self.button_state = [False, False, False]
        self.polling_rate = polling_rate
        self.dev = hid.device()
        self.dev.open(VENDOR_ID, PRODUCT_ID)
        self.dev.set_nonblocking(1)
        self.t = None

        # Register keys in UInput capabilities.
        reg_keys = set()
        for key_combos in self.button_key_mappings:
            for combo in key_combos:
                reg_keys.update(combo.mods)
                reg_keys.update(combo.keys)
        cap = {e.EV_KEY: reg_keys}
        self.ui = UInput(cap, name="Pedal Mapper Virtual Input")

    def clear_sequences_and_send_value(self, value):
        sequences.clear()
        self.btn_value_to_keys(value)

    def newTimer(self, value):
        self.t = Timer(0.4, self.clear_sequences_and_send_value, [value])

    def get_event(self):
        # We're non-blocking, so wait for a poll. This could just be changed to
        # blocking instead without issues, but it is non-blocking in case it's
        # actually needed in the future (e.g. handling multiple devices).
        read = self.dev.read(8, self.polling_rate)
        if not read:
            return
        button = None
        if read[4] != self.button_state[0]:
            button = Button.LEFT
        elif read[5] != self.button_state[1]:
            button = Button.MIDDLE
        elif read[6] != self.button_state[2]:
            button = Button.RIGHT
        else:
            return
        
        
        self.button_state[button.value] = not self.button_state[button.value]
        
        if self.button_state[button.value]: # when we let go of the pedal it will send back the button
            return button


    def handle_key(self, button):
        # keep a sequence of buttons (just to detect double press but I guess could be used to program sequences?)
        sequences.appendleft(button)
        if self.t:
            self.t.cancel()

        if len(sequences) > 1 and sequences[0] and sequences[0] == sequences[1]:
            # double pressed the same button
            self.clear_sequences_and_send_value(button.value + 3)
        else:
            # else: not a double press, we need to wait until the timer expires, which is 0.5 seconds
            self.newTimer(button.value)
            self.t.start()
        
                
    def btn_value_to_keys(self, value):
        # record which one is pressed
        key_combos = self.button_key_mappings[value]
        for combo in key_combos:
            # press            
            for mod in combo.mods:
                if combo.hold and mod in holds:
                    # if we already pressed the hold, release it
                    self.release(mod)
                    holds.remove(mod)
                else:
                    if combo.hold and mod not in holds:
                        holds.append(mod)
                    self.press(mod)
            
            for key in combo.keys:
                self.press(key)
                
            # release (only do if the combo is not a 'hold')
            if not combo.hold:
                for key in combo.keys:
                    self.release(key)
                for mod in combo.mods:
                    self.release(mod)

    def press(self, key):
        self.write_key(key, True)

    def release(self,  key):
        self.write_key(key, False)

    # Writes a key to uinput and then syncs.
    def write_key(self, key, state):
        self.ui.write(e.EV_KEY, key, state)
        self.ui.syn()


if __name__ == "__main__":
    # Create Pedal
    pm = PedalMapper(
        left_keys=[KeyCombo(mods=[e.KEY_LEFTSHIFT, e.KEY_TAB])],
        middle_keys=[KeyCombo(mods=[e.KEY_LEFTALT], hold=True)], # press ALT and hold it so we can select the right screen
        right_keys=[KeyCombo(mods=[e.KEY_TAB])],
        #dbl_left_keys=[KeyCombo(mods=[e.KEY_LEFTCTRL], keys=[e.KEY_A])], # select all
        dbl_middle_keys=[KeyCombo(mods=[e.KEY_LEFTCTRL], keys=[e.KEY_W])], # close window
        dbl_right_keys=[KeyCombo(mods=[e.KEY_LEFTALT, e.KEY_TAB])], # press ALT and TAB to switch between screens immediately
    )

    # Loop to get events and handle them accordingly.
    while True:
        ev = pm.get_event()
        if ev:
            pm.handle_key(ev)
