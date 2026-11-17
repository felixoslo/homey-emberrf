EmberRF - experimental Maxitrol G6R-H4T2 / GV60 433.92 MHz fireplace control for Homey Pro / Homey Bridge.

On/Off switch, broad/narrow and flame up/down buttons, dedicated Homey Flow cards, RF logging,
and optional Homey Bridge antenna. All On/Off/Broad/Narrow/Flame Up/Flame Down codes are built in. Pair by learning ONLY the G6R-H4T2 handset address from RF
or entering the 18-bit hex address manually (generic pairing not physically verified).

SAFETY: The On/Off state indicates the LAST COMMAND, not physical fireplace state.
RF transmission acknowledgement cannot guarantee gas valve or flame status.
Keep the original remote; never rely on this alpha for unattended gas ignition.

Source, manual and testing: https://github.com/felixoslo/homey-emberrf


Alpha 0.3.0 adds Flame Up/Down scaling via Flow factor 1 to 10 (ten RF frames per
factor point). A dashboard widget provides actual press-and-hold through
repeated short radio bursts with automatic stop on release, lost heartbeat,
or the eight-second maximum. Native device buttons remain one-shot.
