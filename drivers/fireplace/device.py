import asyncio
from typing import Any
from homey.device import Device

ADDRESS_BITS = 18
STANDARD_SIGNAL_ID = "g6r_h4t_standard"
AUX_SIGNAL_ID = "g6r_h4t_aux"
# Initially derived from a working Broadlink capture and a G6R handset.
# Keep these transmission parameters unchanged in this UI/Flow update.
COMMANDS: dict[str, tuple[str, int, str, int]] = {
    "on": ("På / tenn", 0b1001, STANDARD_SIGNAL_ID, 10),
    "off": ("Av", 0b1011, STANDARD_SIGNAL_ID, 10),
    "broad": ("Bred flamme", 0b1001, AUX_SIGNAL_ID, 30),
    "narrow": ("Smal flamme", 0b1010, AUX_SIGNAL_ID, 30),
    "flame_up": ("Flamme opp", 0b1101, STANDARD_SIGNAL_ID, 10),
    "flame_down": ("Flamme ned", 0b1110, STANDARD_SIGNAL_ID, 10),
}


def frame_for(address: int, command: int) -> list[int]:
    if not 0 <= address < 2**ADDRESS_BITS:
        raise ValueError("Invalid 18-bit G6R handset address")
    if not 0 <= command < 16:
        raise ValueError("Invalid 4-bit G6R command")
    word = (address << 4) | command
    return [(word >> n) & 1 for n in range(21, -1, -1)]


class PeisTestDevice(Device):
    async def on_init(self) -> None:
        await super().on_init()
        self._address = int(self.get_data()["address"])
        self._tx_lock = asyncio.Lock()
        self._standard = self.homey.rf.get_signal_433(STANDARD_SIGNAL_ID)
        self._aux = self.homey.rf.get_signal_433(AUX_SIGNAL_ID)
        # Homey does not automatically add new capabilities to already paired devices.
        # Perform migration only when needed, without sending any RF command.
        if not self.has_capability("onoff"):
            await self.add_capability("onoff")
            await self.set_capability_value("onoff", False)
            self.log("EMBERRF MIGRATE: added onoff, initialized to OFF as an assumed command state; no RF sent")
        for obsolete in ("button.peis_pa", "button.peis_av"):
            if self.has_capability(obsolete):
                await self.remove_capability(obsolete)
                self.log(f"EMBERRF MIGRATE: removed obsolete {obsolete}; no RF sent")

        self.register_capability_listener("onoff", self.on_onoff)
        self.register_capability_listener("button.bred_flamme", self._on_broad)
        self.register_capability_listener("button.smal_flamme", self._on_narrow)
        self.register_capability_listener("button.flame_up", self._on_flame_up)
        self.register_capability_listener("button.flame_down", self._on_flame_down)
        self.log(
            f"EMBERRF READY: device=EmberRF address=0x{self._address:05X} "
            f"antenna={self._antenna_name()} capabilities=onoff,broad,narrow,flame_up,flame_down "
            "RF=433.92MHz status=commanded-only (no physical feedback)"
        )

    async def on_onoff(self, value: bool, **kwargs: Any) -> None:
        await self.send_command("on" if value else "off", source="På/Av-bryter (UI eller standard Flow)")

    async def _on_broad(self, value: bool, **kwargs: Any) -> None:
        await self.send_command("broad", source="Bred-knapp (Homey UI)")

    async def _on_narrow(self, value: bool, **kwargs: Any) -> None:
        await self.send_command("narrow", source="Smal-knapp (Homey UI)")

    async def _on_flame_up(self, value: bool, **kwargs: Any) -> None:
        await self.send_command("flame_up", source="Flamme opp (Homey UI)")

    async def _on_flame_down(self, value: bool, **kwargs: Any) -> None:
        await self.send_command("flame_down", source="Flamme ned (Homey UI)")

    def _antenna_name(self) -> str:
        try:
            value = self.get_setting("satellite_mode_antenna")
        except Exception:
            return "ukjent"
        if value == "self":
            return "Homey Pro"
        return "Homey Bridge" if value else "not selected"

    async def on_settings(self, old_settings: dict, new_settings: dict, changed_keys: tuple[str, ...]) -> str | None:
        if "satellite_mode_antenna" in changed_keys:
            self.log(
                f"EMBERRF ANTENNE: byttet fra {old_settings.get('satellite_mode_antenna')} "
                f"til {new_settings.get('satellite_mode_antenna')}; ingen RF sendt"
            )
        return None

    async def _trigger_result(self, action: str, tokens: dict[str, str]) -> None:
        # A Flow-card error must never cause us to retransmit an already-sent RF frame.
        try:
            if action == "rf_accepted":
                await self.driver.trigger_rf_accepted(self, tokens)
            else:
                await self.driver.trigger_rf_failed(self, tokens)
        except Exception as exc:
            self.error(f"EMBERRF LOG: could not trigger {action} Flow: {exc}")

    async def send_command(self, action: str, *, source: str = "ukjent") -> None:
        title, command, profile, repeats = COMMANDS[action]
        signal = self._aux if profile == AUX_SIGNAL_ID else self._standard
        bits = frame_for(self._address, command)
        antenna = self._antenna_name()
        async with self._tx_lock:
            self.log(
                f"EMBERRF TX START: kommando={title}; kilde={source}; antenne={antenna}; "
                f"adresse=0x{self._address:05X}; databits={''.join(map(str,bits))}; "
                f"profil={profile}; repetisjoner={repeats}"
            )
            try:
                await signal.tx(bits, repetitions=repeats, device=self)
            except Exception as exc:
                self.error(
                    f"EMBERRF TX FEIL: kommando={title}; antenne={antenna}; "
                    f"kilde={source}; feil={type(exc).__name__}: {exc}"
                )
                await self._trigger_result("rf_failed", {"kommando": title, "antenne": antenna, "feil": str(exc)[:240]})
                raise
            self.log(
                f"EMBERRF TX OK: kommando={title}; antenne={antenna}; "
                f"kilde={source}; RF akseptert av Homey; fysisk resultat ikke bekreftet"
            )
        await self._trigger_result("rf_accepted", {"kommando": title, "antenne": antenna, "kilde": source})


homey_export = PeisTestDevice
