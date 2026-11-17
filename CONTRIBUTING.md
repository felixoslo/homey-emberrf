# Contributing to EmberRF

Thanks for helping improve a safety-sensitive 433 MHz fireplace integration. Bugs and fixes are welcome, but **do not test gas ignition unattended**. Keep the original handset available and test beside the fireplace.

Run `python3 -m unittest discover -s tests -q`, `homey app build --path .`, and `homey app validate --path .` before opening a pull request. Include exact hardware type and Homey firmware, but **do not share your private handset address, RF capture, Wi-Fi details or credentials** in issues.

Important source files: `.homeycompose/signals/433/` (RX and two TX RF profiles); `drivers/fireplace/driver.py` (pairing + Flow registration); `drivers/fireplace/pair/learn_remote.html` (pairing UI); `drivers/fireplace/device.py` (RF command transmission); `tests/` (unit tests).

The project is licensed under MIT and credits Michael Dove's upstream Maxitrol project.


The v0.3.0 hold widget is safety-relevant. Changes must include tests for interrupted widget contacts, repeated/overlapping sessions, factor bounds and real-device response before claiming hardware support. Do not report accepted RF transmission as proven fire state.
