# Pedal Mapper

This is a simple program for mapping the buttons on an Elgato Stream Deck Pedal
to keyboard inputs. 

## Dependencies

There aren't a lot of dependencies, but what you do need are:
- Python
- hidapi
- evdev

## How it works

Run the Python script with `sudo python3 pedal_mapper.py` and press your pedal. You can run it as a `systemd` unit
or equivalent to have it always running in the background.

You can find a list of all possible keycodes
[here](https://github.com/torvalds/linux/blob/master/include/uapi/linux/input-event-codes.h).


## Configuring

Configuring is done in the python code itself at the moment. This config will allow you to:

- double press the middle button to ALT+TAB to the next window
- single press the middle button to press ALT and automatically holds it. You can then press the right and left button to navigate windows. Press ALT again to select.
- double press the right button to send CTRL+W, which generally closes tabs

```

    pm = PedalMapper(
        left_keys=[KeyCombo(mods=[e.KEY_LEFTSHIFT, e.KEY_TAB])],
        middle_keys=[KeyCombo(mods=[e.KEY_LEFTALT], hold=True)], # press ALT and hold it so we can select the right screen
        right_keys=[KeyCombo(mods=[e.KEY_TAB])],
        #dbl_left_keys=[KeyCombo(mods=[e.KEY_LEFTCTRL], keys=[e.KEY_A])], # select all
        dbl_right_keys=[KeyCombo(mods=[e.KEY_LEFTCTRL], keys=[e.KEY_W])], # close window
        dbl_middle_keys=[KeyCombo(mods=[e.KEY_LEFTALT, e.KEY_TAB])], # press ALT and TAB to switch between screens immediately
    )
```

## Systemd

```
cat systemd/system/pedal.service 
[Unit]
Description=Pedal service
After=network.target

[Service]
StartLimitIntervalSec=0
Type=simple
Restart=always
RestartSec=1
User=root  
ExecStart=/usr/bin/python3 /home/matthiasvanwoensel/PedalMapper/pedal_mapper.py

[Install]
WantedBy=multi-user.target
```
