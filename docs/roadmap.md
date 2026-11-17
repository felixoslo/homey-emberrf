# EmberRF alpha to Homey App Store roadmap

## Available in public alpha v0.2.0

- Tested G6R-H4T2 RF encoding and separate standard/AUX end-pulse profiles, On/Off, Broad, Narrow, Flame Up and Flame Down (Flame Up RF needs physical validation).
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

- Physically validate EmberRF Flame Up RF 1101 (HA only has an unrelated IR packet under that name). Confirm effective press/repetition duration. Flame Down RF 1110 is supported by HA Broadlink and passive handset captures.


## v0.3.0 alpha implementation and outstanding verification

- Model-specific G6R RF masks 1101 (Flame Up) and 1110 (Flame Down) implemented with repeatable time factor 1–10 in Homey Flow. Radio timing unchanged.
- Dashboard widget supports press and hold with release, browser-hide and focus-loss STOP, backend heartbeat timeout and eight-second hold limit.
- Physical testing pending: confirm Flame Up actually raises flame (HA had an IR rather than RF capture), whether 10 repeated packets yield the intended step, hold response time, and the behavior of RF Bridge vs Pro. Test release timing on Android and iOS.
- Do not confuse virtual On/Off state, RF acknowledgment or transmission factor with measured burner operation or gas safety.
