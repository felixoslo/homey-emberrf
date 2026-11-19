# EmberRF alpha to Homey App Store roadmap

## Available in public alpha v0.2.0

- Tested G6R-H4T2 RF encoding and separate standard/AUX end-pulse profiles, On/Off, Broad, Narrow, Flame Up and Flame Down on one G6R-H4T2 installation.
- Homey Pro / Homey Bridge antenna selection via Satellite Mode.
- Six direct Flow actions, two send-status Flow triggers, local diagnostic logs, safety disclosure and MIT attribution.
- G6R-H4T2 handset-address pairing by RF capture or manual handset hex address. All six command codes are embedded; no individual RF command learning. **Implementation and unit-tested only; physical pairing is not yet verified.**

## Before an official release

1. **Pairing validation:** Verify the new generic pairing flow with real handsets and both radio receiver locations. Add user-friendly recovery for interference, wrong address and timeout.
2. **Cross-device testing:** Test different compatible G6R receivers, Homey versions, Homey Bridge and physical edge cases, including On, Off, narrow, broad, reboot, and radio transmission errors.
3. **Status model:** The Homey switch is currently a last-command estimate. Avoid displaying it as measured flame/gas state; consider clearer status language or optional physical feedback.
4. **UX and translations:** Review English and Norwegian pairing, help text, brand-neutral assets, logs, Flow card names, errors and accessibility.
5. **Release quality:** Add CI validation, robust SDK integration tests, support/contact details, release notes, issue templates and tags.
6. **App Store process:** Follow current [Homey guidelines](https://apps.developer.homey.app/app-store/guidelines) and [publishing process](https://apps.developer.homey.app/app-store/publishing); prepare a test listing, verify required metadata, then request official certification.

No claim of official certification or compatibility with untested fireplace models.

- Flame Up RF 1101 and Flame Down RF 1110 were both physically verified in the regular device buttons (50 repetitions per press, about three presses each way for full-range adjustment on the test fireplace). Broader compatibility remains unverified.


## Flame control (revised in v0.4.4)

- Model-specific G6R RF masks 1101 (Flame Up) and 1110 (Flame Down) implemented with repeatable time factor 1–10 in Homey Flow. Radio timing unchanged.
- Experimental dashboard hold widget and continuous-transmit backend were removed by request; native Flame Up/Down buttons are sufficient on the tested installation.
- On one fireplace, both Flame Up and Flame Down physically responded to 50-frame button presses. Remaining work includes pairing on additional handsets, both antenna locations, and cross-device reliability.
- Do not confuse virtual On/Off state, RF acknowledgment or transmission factor with measured burner operation or gas safety.
