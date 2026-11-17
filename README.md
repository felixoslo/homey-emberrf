# EmberRF 🔥

**Direct 433.92 MHz control for the Maxitrol G6R-H4T2 remote and compatible GV60 gas-fireplace receivers, using Homey Pro or Homey Bridge.**

![Status: experimental alpha](https://img.shields.io/badge/status-experimental%20alpha-orange) ![Homey SDK 3](https://img.shields.io/badge/Homey-SDK%203-0b7285) ![License: MIT](https://img.shields.io/badge/license-MIT-blue)

[Les på norsk](README.nb.md) · [RF protocol and findings](docs/rf-protocol.md) · [Roadmap](docs/roadmap.md)

## What it does

EmberRF is an open-source experimental Homey Python (SDK v3) app to control **Maxitrol G6R-H4T2 handsets and compatible GV60** fireplaces directly over RF, without Broadlink or Home Assistant in the command path.

| Control | Behavior |
|---|---|
| **On / Off** | Send ignition (`1001`, long ending pulse) or off (`1011`, long ending pulse) |
| **Broad flame** | Send AUX-on (`1001`, short ending pulse) |
| **Narrow flame** | Send AUX-off (`1010`, short ending pulse) |
| **Flame up** | RF command 1101, long ending pulse (alpha candidate, not physically verified) |
| **Flame down** | RF command 1110, long ending pulse (HA Broadlink and 88 handset frames) |

**No learning of individual commands required.** All six codes and their distinct pulse formats are preconfigured in the app. Pairing identifies only the **18-bit handset address** (like the original Maxitrol Homey app). This alpha targets the model above; other remotes/receivers have **not** been tested or claimed as compatible.

**Flame up / down:** Both commands are now included as dedicated buttons and Flow actions. Flame Down is confirmed as G6R RF command 1110 by HA Broadlink and 88 valid handset captures. The HA Broadlink entry called Flame Up is **IR, not RF**; EmberRF uses the original G6R Homey RF protocol command 1101 as a **still-untested RF candidate**, with the standard long end pulse. Both are sent with 10 repetitions initially; adjust only after physical validation.

**Important RF discovery:** ignition and broad flame transmit identical 22 data bits but **different final pulse lengths**. These are separate RF profiles in `.homeycompose/signals/433/`. The working behavior was confirmed on one G6R-H4T2 installation with Homey Bridge. Compatibility with other installations is **not yet established**.

## How to use

1. Install a compatible Homey Pro and the Homey CLI with SDK 3 / Python support.
2. Clone the repository, run `python3 -m unittest discover -s tests -q`, `homey app build --path .` and `homey app validate --path .`.
3. Use `homey app install --path .` to install this **separate** alpha app.
4. Add **EmberRF fireplace** through Homey. Pair only the 18-bit address by **listening for the original G6R-H4T2 remote**, preferably holding Flame Down for about two seconds, or manually entering the hexadecimal address. **No re-learning of On/Off/Broad/Narrow RF codes is necessary.** RF listening should be done within range of Homey's 433 MHz receiver. **The new generic pairing flow is experimental and has not yet been physically validated.**
5. Open the device's **Settings → Satellite Mode → Antenna**, and select **Homey Pro** or your available **Homey Bridge**.
6. Test On, Broad, Narrow, Flame Up, Flame Down and Off one by one while physically watching the fireplace. Keep the original remote immediately available.

> **Safety:** This is a gas-fireplace experiment, not a safety control. Sending RF is one-way. The On/Off switch reflects the *last requested command*, not the real flame, valve or gas state. A successful Homey API call only means it accepted the transmission. Do not rely on the app to confirm that a fireplace is off. Do not run unsupervised ignition automations.

## Flows

The app supports Homey's standard On/Off device Flows. Six repeatable action cards send `ON`, `OFF`, `Broad flame`, and `Narrow flame` regardless of current virtual On/Off state. Two trigger cards report an RF send **accepted by Homey** or a **send error**, with tokens for command, antenna, source and/or error. No automatic retransmission is performed after a failure.



## Flame Up / Down — continuous hold and Flow control (alpha v0.3.0)

Both commands use the model-specific G6R RF masks already defined in the original Maxitrol Homey app: **Flame Up = 1101**, **Flame Down = 1110**, using the standard long ending pulse. The previously tested On/Off and AUX/broad/narrow radio profiles have not been changed.

**Short press:** The standard Homey device buttons Flame Up and Flame Down each send 10 RF repetitions. A native Homey button does not provide reliable finger-release information, and cannot safely implement continuous holding.

**Real press-and-hold:** Add the **EmberRF flame hold** widget to a Homey dashboard. Select your EmberRF fireplace in widget settings. Touch and hold ▲ or ▼ to send consecutive 10-frame bursts. Release to stop. It also stops on pointer cancellation, dashboard hide and browser focus loss; the Homey backend enforces an approximately 1.2-second heartbeat timeout and an absolute eight-second maximum. An already-started short burst cannot be revoked. The dashboard widget is an alpha feature pending physical and mobile-device testing. Any other device or Flow command (especially OFF) interrupts an active hold before the next RF burst.

**Flow duration factor:** The explicit Increase Flame and Decrease Flame Flow action cards include a required **Factor** from 1 to 10. Factor 1 = 10 RF repetitions, factor 4 = 40 repetitions, factor 10 = 100 repetitions. This changes RF transmission length, **not a measured percentage or known flame height**. Start at factor 1 while watching the fireplace. Out-of-range or noninteger factors are rejected.

**Testing status:** Flame Down RF 1110 matches both HA Broadlink storage and 88 passive RF frames; the Flame Up RF mask 1101 is from the original Maxitrol driver. The HA Broadlink entry named Flame Up was saved as IR, not RF, and was not used. The new hold widget and Flow duration factors have passed offline tests but still require physical tuning and verification on the fireplace.

## Application logging

`EMBERRF TX START`, `EMBERRF TX OK`, `EMBERRF TX FEIL` (error), and `EMBERRF ANTENNE` provide action, source, selected antenna, signal profile and repetitions. Do not publish your actual handset address from the runtime logs.

## Development and support

This repository is an **alpha** and is **not yet listed in Homey App Store**. The RF data and device control were physically tested on one specific setup; generic pairing and other receivers still require validation. See [roadmap](docs/roadmap.md). Issues and improvement reports are welcome, but test on physical gas equipment only under supervision.

Created by EmberRF contributors, incorporating/deriving from the MIT-licensed work of [Michael Dove](https://github.com/michaeldove/homey-maxitrol-fireplace). Original copyright notice is retained in [LICENSE](LICENSE). Unaffiliated with Maxitrol, Athom or Broadlink.
