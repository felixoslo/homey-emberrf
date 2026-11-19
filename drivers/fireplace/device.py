import asyncio
import math
from typing import Any
from homey.device import Device

# A flow factor controls the duration of a *repeated RF command*, not
# a known percentage of physical flame height.
BASE_REPETITIONS = 10
MAX_FLOW_FACTOR = 10
DEFAULT_FLAME_TAP_REPETITIONS = 50  # One contiguous TX call; approximately 5x former 10-frame tap

def repetitions_for_factor(factor: int | float) -> int:
    if isinstance(factor, bool) or not isinstance(factor, (int, float)):
        raise ValueError("Factor must be a number from 1 to 10")
    if not math.isfinite(factor) or factor != int(factor) or not 1 <= factor <= MAX_FLOW_FACTOR:
        raise ValueError("Factor must be an integer from 1 to 10")
    return int(factor) * BASE_REPETITIONS


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
    "flame_up": ("Flamme opp", 0b1101, STANDARD_SIGNAL_ID, DEFAULT_FLAME_TAP_REPETITIONS),
    "flame_down": ("Flamme ned", 0b1110, STANDARD_SIGNAL_ID, DEFAULT_FLAME_TAP_REPETITIONS),
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

        if not self.has_capability("emberrf_flame_mode"):
            await self.add_capability("emberrf_flame_mode")
            await self.set_capability_value("emberrf_flame_mode", "unknown")
            self.log("EMBERRF MIGRATE: flame mode state installed, initially unknown; no RF sent")
        # Homey manages Satellite Mode. Expose the SDK-reported value without
        # overriding the routing; the RF stack selects the antenna from device=self.
        if not self.has_capability("emberrf_antenna"):
            await self.add_capability("emberrf_antenna")
        await self._refresh_antenna_readback()
        if self.has_capability("emberrf_antenna_control"):
            # v0.4.2 experimental picker did not change Homey's native RF
            # antenna and was never referenced by any user Flow. Remove it.
            await self.remove_capability("emberrf_antenna_control")
            self.log("EMBERRF MIGRATE: removed misleading antenna picker; no RF sent")
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

    def _antenna_setting(self) -> tuple[str | None, str]:
        # Homey may expose its built-in satellite field via get_settings()
        # without exposing it via get_setting(). Do not infer a route.
        try:
            settings = self.get_settings()
            if "satellite_mode_antenna" in settings:
                value = settings["satellite_mode_antenna"]
                if isinstance(value, str) and value:
                    return value, "get_settings"
        except (AttributeError, KeyError, TypeError):
            pass
        try:
            value = self.get_setting("satellite_mode_antenna")
            if isinstance(value, str) and value:
                return value, "get_setting"
        except (AttributeError, KeyError, TypeError):
            pass
        return None, "not_exposed"

    @staticmethod
    def _antenna_state(value: str | None) -> str:
        if value == "self":
            return "pro"
        if isinstance(value, str) and value:
            return "bridge"
        return "unknown"

    def _antenna_name(self) -> str:
        state = self._antenna_state(self._antenna_setting()[0])
        if state == "unknown":
            # The reserved field may not be exposed on app restart;
            # use only a previously observed native setting, never guess.
            try:
                last = self.get_capability_value("emberrf_antenna")
            except (AttributeError, KeyError, TypeError):
                last = None
            if last == "pro":
                return "Homey Pro (last observed)"
            if last == "bridge":
                return "Homey Bridge (last observed)"
            return "not exposed by Homey app SDK"
        return {"pro": "Homey Pro", "bridge": "Homey Bridge"}[state]

    async def _refresh_antenna_readback(self, new_settings: dict | None = None) -> None:
        # Note: this shows the configuration exposed to this app, not proof
        # of which hardware actually transmitted a radio frame.
        if new_settings is not None and "satellite_mode_antenna" in new_settings:
            value = new_settings.get("satellite_mode_antenna")
            source = "on_settings"
        else:
            value, source = self._antenna_setting()
        state = self._antenna_state(value)
        if state == "unknown":
            try:
                last = self.get_capability_value("emberrf_antenna")
            except (AttributeError, KeyError, TypeError):
                last = None
            if last in ("pro", "bridge"):
                state, source = last, "last_observed_in_Homey"
        if self.has_capability("emberrf_antenna"):
            await self.set_capability_value("emberrf_antenna", state)
        self.log(f"EMBERRF ANTENNE STATUS: {state}; source={source}; RF routing=Homey Satellite Mode (device=self)")

    async def on_settings(self, old_settings: dict, new_settings: dict, changed_keys: tuple[str, ...]) -> str | None:
        if "satellite_mode_antenna" in changed_keys:
            await self._refresh_antenna_readback(new_settings)
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

    repetitions_for_factor = staticmethod(repetitions_for_factor)

    async def send_command(
        self, action: str, *, source: str = "ukjent",
        repetitions: int | None = None, emit_result: bool = True,
    ) -> None:
        title, command, profile, repeats = COMMANDS[action]
        if repetitions is not None:
            if isinstance(repetitions, bool) or not isinstance(repetitions, int) or not 1 <= repetitions <= 255:
                raise ValueError("Repetitions must be an integer from 1 to 255")
            repeats = repetitions
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
                if emit_result:
                    await self._trigger_result("rf_failed", {"kommando": title, "antenne": antenna, "feil": str(exc)[:240]})
                raise
            if action in ("narrow", "broad", "off", "on"):
                # This is last requested mode only: no RF feedback about burner status.
                mode={"narrow":"narrow","broad":"broad","on":"unknown","off":"unknown"}[action]
                if self.has_capability("emberrf_flame_mode"):
                    try:
                        await self.set_capability_value("emberrf_flame_mode",mode)
                        self.log(f"EMBERRF FLAMMEMODUS: anmodet={mode}; via={source}; ikke fysisk bekreftet")
                    except Exception as state_error:
                        self.error(f"EMBERRF MODE LOG ERROR: {state_error}")
            self.log(
                f"EMBERRF TX OK: kommando={title}; antenne={antenna}; "
                f"kilde={source}; RF akseptert av Homey; fysisk resultat ikke bekreftet"
            )
        if emit_result:
            await self._trigger_result("rf_accepted", {"kommando": title, "antenne": antenna, "kilde": source})


homey_export = PeisTestDevice
