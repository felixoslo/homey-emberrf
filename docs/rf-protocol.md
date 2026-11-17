# EmberRF — RF protocol observations (alpha)

Frequency **433.92 MHz**. Each frame carries an **18-bit handset address** (learned per device) and a **4-bit command**. The user's address is deliberately not included in the public source or captures.

| Command | Last four data bits | End pulse (tested candidate) | Repeat count |
|---|---|---|---|
| On / Ignite | `1001` | 690 µs | 10 |
| Off | `1011` | 690 µs | 10 |
| Broad flame / AUX on | `1001` | 361 µs | 30 |
| Narrow flame / AUX off | `1010` | 361 µs | 30 |

| Flame up (original Maxitrol RF protocol) | 1101 | 690 µs (candidate, physically unverified with EmberRF) | 10 |
| Flame down (Broadlink + handset confirmed) | 1110 | 690 µs | 10 |

The short/long ending pulse distinction was established by comparing a working Broadlink RM Pro+ signal library with passive handheld G6R captures (8/8 valid ignition frames with long end pulse, 85/85 broad and 120/120 narrow with short end pulse). The **signal files include two TX profiles** plus a separately tuned RX profile used only for pairing. The TX symbols currently use 361/690 µs with `interval=32760` µs, the closest supported approximation to Broadlink's longer pause. This parameterization is not guaranteed for every receiver.

All four RF command masks and transmit signal profiles are embedded in this repository; users only pair the 18-bit address. No per-command RF learning is required. Other handset or fireplace models are not established as compatible.

The RX capture profile is experimental. It accepts 22-bit candidate signals with recognized 4-bit commands and requires at least three repeated frames with matching handset address. Pairing can also be performed by manually entering an 18-bit hexadecimal address. Both mechanisms require validation on more Homey firmware and hardware versions.

**No safety acknowledgement:** an accepted TX call is not proof of actual fire state. Avoid unattended ignition automations and preserve manufacturer safety controls.

## HA Broadlink inspection – flame controls

The HA Broadlink code store is separate from Broadlink mobile app storage. The code saved as peis flamme ned is **RF** and decodes to G6R command 1110 with a long end pulse; 88 valid passive handset capture frames independently agree. The HA entry peis flamme opp is **IR**, not RF, and cannot be reused as a 433 MHz waveform. The original G6R-H4T2 Homey driver already defines FLAME_UP as RF 1101; EmberRF includes this **experimental unverified RF candidate** on the standard long-ending-pulse transmitter. Up/down commands may require different repetition durations after physical testing.
