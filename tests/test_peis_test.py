import asyncio
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest

APP = Path(__file__).resolve().parents[1]


class RFSignal:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    async def tx(self, bits, **kwargs):
        self.calls.append({"bits": list(bits), **kwargs})
        if self.fail:
            raise RuntimeError("test RF failure")


class RF:
    def __init__(self):
        self.signals = {"g6r_h4t_standard": RFSignal(), "g6r_h4t_aux": RFSignal()}

    def get_signal_433(self, id):
        return self.signals[id]


class StubDevice:
    def __init__(self):
        self.caps = {"button.peis_pa", "button.peis_av", "button.bred_flamme", "button.smal_flamme", "button.flame_up", "button.flame_down"}
        self.values = {}
        self.listeners = {}
        self.logs = []
        self.errors = []
        self.data = {"address": 0x12345}
        self.rf = RF()
        self.driver = SimpleNamespace(trigger_rf_accepted=self._on_sent, trigger_rf_failed=self._on_fail)
        self.triggers = []
        self.homey = SimpleNamespace(rf=self.rf)
        self.settings = {"satellite_mode_antenna": "test-homey-bridge-id"}

    async def on_init(self):
        pass

    def has_capability(self, cap):
        return cap in self.caps

    async def add_capability(self, cap):
        self.caps.add(cap)

    async def remove_capability(self, cap):
        self.caps.remove(cap)

    async def set_capability_value(self, cap, val):
        self.values[cap] = val

    def register_capability_listener(self, cap, fn):
        if cap not in self.caps:
            raise AssertionError(f"listener for absent capability {cap}")
        self.listeners[cap] = fn

    def get_data(self):
        return self.data

    def get_setting(self, name):
        return self.settings.get(name)

    def log(self, line):
        self.logs.append(line)

    def error(self, line):
        self.errors.append(line)

    async def _on_sent(self, device, tokens):
        self.triggers.append(("sent", tokens))

    async def _on_fail(self, device, tokens):
        self.triggers.append(("failed", tokens))


def load_device():
    homey = ModuleType("homey")
    homey.__path__ = []
    device_mod = ModuleType("homey.device")
    device_mod.Device = StubDevice
    sys.modules["homey"] = homey
    sys.modules["homey.device"] = device_mod
    path = APP / "drivers/fireplace/device.py"
    spec = importlib.util.spec_from_file_location("peis_test_device_testmod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class PeisManifestTests(unittest.TestCase):
    def setUp(self):
        self.driver = json.loads((APP / "drivers/fireplace/driver.compose.json").read_text())
        self.standard = json.loads((APP / ".homeycompose/signals/433/g6r_h4t_standard.json").read_text())
        self.aux = json.loads((APP / ".homeycompose/signals/433/g6r_h4t_aux.json").read_text())
        self.flow = json.loads((APP / "drivers/fireplace/driver.flow.compose.json").read_text())

    def test_capabilities_switch_and_two_momentary_buttons(self):
        self.assertEqual(self.driver["capabilities"], ["onoff", "button.bred_flamme", "button.smal_flamme", "button.flame_up", "button.flame_down", "emberrf_flame_mode"])

    def test_bridge_or_pro_selectable(self):
        self.assertEqual(self.driver["rf433"], {"satelliteMode": True})

    def test_distinct_eof_with_unchanged_rf_parameters(self):
        self.assertEqual(self.standard["eof"], [690])
        self.assertEqual(self.aux["eof"], [361])
        self.assertEqual(self.standard["carrier"], 433920000)
        self.assertEqual(self.aux["words"], self.standard["words"])
        self.assertEqual(self.aux["interval"], 32760)
        self.assertTrue(self.aux["txOnly"])

    def test_four_flow_actions_and_two_result_triggers(self):
        self.assertEqual([x["id"] for x in self.flow["actions"]], ["send_on", "send_off", "send_broad", "send_narrow", "send_flame_up", "send_flame_down"])
        self.assertEqual([x["id"] for x in self.flow["triggers"]], ["rf_accepted", "rf_failed"])

    def test_unique_id(self):
        self.assertEqual(json.loads((APP / ".homeycompose/app.json").read_text())["id"], "com.emberrf.homey")

    def test_no_rf_transmit_during_init_or_pairing(self):
        self.assertNotIn(".tx(", (APP / "app.py").read_text())
        self.assertNotIn(".tx(", (APP / "drivers/fireplace/driver.py").read_text())
        self.assertIn("await signal.enable_rx()", (APP / "drivers/fireplace/driver.py").read_text())


    def test_embedded_rf_codes_and_model_description(self):
        manifest=json.loads((APP/".homeycompose/app.json").read_text())
        self.assertIn("G6R-H4T2",manifest["description"]["en"])
        self.assertIn("G6R-H4T2",manifest["description"]["no"])
        self.assertIn("Pair handset address only",manifest["description"]["en"])
        self.assertEqual(manifest["id"],"com.emberrf.homey")
        driver=(APP/"drivers/fireplace/device.py").read_text()
        self.assertIn('("På / tenn", 0b1001, STANDARD_SIGNAL_ID, 10)',driver)
        self.assertIn('("Av", 0b1011, STANDARD_SIGNAL_ID, 10)',driver)
        self.assertIn('("Bred flamme", 0b1001, AUX_SIGNAL_ID, 30)',driver)
        self.assertIn('("Smal flamme", 0b1010, AUX_SIGNAL_ID, 30)',driver)
        self.assertIn('("Flamme opp", 0b1101, STANDARD_SIGNAL_ID, DEFAULT_FLAME_TAP_REPETITIONS)',driver)
        self.assertIn('("Flamme ned", 0b1110, STANDARD_SIGNAL_ID, DEFAULT_FLAME_TAP_REPETITIONS)',driver)

    def test_pairing_recognizes_handset_address_only(self):
        import ast,re,typing
        filename=APP/"drivers/fireplace/driver.py"
        source=filename.read_text()
        tree=ast.parse(source)
        nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ("parse_handset_address","pairing_device")]
        ns={"Any":typing.Any,"re":re,"HEX_ADDRESS":re.compile(r"^(?:0[xX])?([0-9a-fA-F]{1,5})$")}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(filename),"exec"),ns)
        address=ns["parse_handset_address"]("0x12345")
        self.assertEqual(address,0x12345)
        device=ns["pairing_device"](address)
        self.assertEqual(device["data"]["address"],address)
        with self.assertRaises(ValueError):ns["parse_handset_address"]("0xFFFFF")
        with self.assertRaises(ValueError):ns["parse_handset_address"]("garbage")
        self.assertIn("g6r_h4t_rx",source)
        self.assertIn("REQUIRED_MATCHING_FRAMES = 3",source)
        self.assertIn("signal.on_payload(on_payload)",source)
        self.assertIn("manual_address",source)

    def test_flow_factor_arguments_and_hold_widget(self):
        flow=json.loads((APP/"drivers/fireplace/driver.flow.compose.json").read_text())
        for a in flow["actions"]:
            if a["id"] in ("send_flame_up","send_flame_down"):
                self.assertEqual(a["args"][0]["name"],"factor")
                self.assertEqual(a["args"][0]["type"],"number")
                self.assertEqual((a["args"][0]["min"],a["args"][0]["max"]),(1,10))
        widget=json.loads((APP/"widgets/flame_hold/widget.compose.json").read_text())
        self.assertEqual(widget["devices"]["type"],"app")
        self.assertTrue(widget["devices"]["singular"])
        self.assertEqual(len(widget["api"]),3)
        html=(APP/"widgets/flame_hold/public/index.html").read_text()
        for term in ("pointerdown","pointerup","pointercancel","visibilitychange","/hold/heartbeat"):
            self.assertIn(term,html)
        device=(APP/"drivers/fireplace/device.py").read_text()
        self.assertIn("HOLD_MAX_SECONDS = 8.0",device)
        self.assertIn("HOLD_HEARTBEAT_SECONDS = 1.2",device)
        self.assertIn("self._hold_stop.set()",device)

    def test_no_sdk_private_lock_collision(self):
        src = (APP / "drivers/fireplace/device.py").read_text()
        self.assertIn("self._tx_lock = asyncio.Lock()", src)
        self.assertNotIn("self._lock = ", src)


class PeisDeviceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mod = load_device()
        self.device = self.mod.PeisTestDevice()
        await self.device.on_init()

    async def test_migration_preserves_device_and_does_not_transmit(self):
        self.assertEqual(self.device.caps, {"onoff", "button.bred_flamme", "button.smal_flamme", "button.flame_up", "button.flame_down", "emberrf_flame_mode"})
        self.assertEqual(self.device.values["onoff"], False)
        self.assertEqual(set(self.device.listeners), self.device.caps - {"emberrf_flame_mode"})
        self.assertEqual(sum(len(x.calls) for x in self.device.rf.signals.values()), 0)
        await self.device.on_init()
        self.assertEqual(self.device.caps, {"onoff", "button.bred_flamme", "button.smal_flamme", "button.flame_up", "button.flame_down", "emberrf_flame_mode"})
        self.assertEqual(sum(len(x.calls) for x in self.device.rf.signals.values()), 0)

    async def test_onoff_switch_uses_long_eof_profile(self):
        await self.device.listeners["onoff"](True)
        await self.device.listeners["onoff"](False)
        calls = self.device.rf.signals["g6r_h4t_standard"].calls
        self.assertEqual(["".join(map(str, c["bits"])) for c in calls], ["0100100011010001011001", "0100100011010001011011"])
        self.assertEqual([c["repetitions"] for c in calls], [10, 10])
        self.assertEqual([ev[0] for ev in self.device.triggers], ["sent", "sent"])

    async def test_broad_and_narrow_keep_working_aux_profile(self):
        await self.device.listeners["button.bred_flamme"](True)
        await self.device.listeners["button.smal_flamme"](True)
        calls = self.device.rf.signals["g6r_h4t_aux"].calls
        self.assertEqual(["".join(map(str, c["bits"])) for c in calls], ["0100100011010001011001", "0100100011010001011010"])
        self.assertEqual([c["repetitions"] for c in calls], [30, 30])
        self.assertTrue(all("Homey Bridge" in x[1]["antenne"] for x in self.device.triggers))

    async def test_up_down_standard_rf_codes(self):
        await self.device.listeners["button.flame_up"](True)
        await self.device.listeners["button.flame_down"](True)
        calls = self.device.rf.signals["g6r_h4t_standard"].calls
        self.assertEqual(
            ["".join(map(str,c["bits"])) for c in calls],
            ["0100100011010001011101", "0100100011010001011110"]
        )
        self.assertEqual([c["repetitions"] for c in calls],[50,50])
        self.assertEqual([x[0] for x in self.device.triggers],["sent","sent"])

    async def test_flow_factor_sets_10_to_100_repetitions(self):
        compute=self.mod.repetitions_for_factor
        self.assertEqual(compute(1),10)
        self.assertEqual(compute(3),30)
        self.assertEqual(compute(10),100)
        for invalid in (0,11,1.5,True,False,None,"2",float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                compute(invalid)
        await self.device.send_command(
            "flame_up",source="Flow:flame_up factor=4",
            repetitions=compute(4),
        )
        self.assertEqual(self.device.rf.signals["g6r_h4t_standard"].calls[-1]["repetitions"],40)

    async def test_dashboard_hold_stops_after_release(self):
        signal=self.device.rf.signals["g6r_h4t_standard"]
        async def simulated_tx(bits,**kwargs):
            signal.calls.append({"bits":list(bits),**kwargs})
            await asyncio.sleep(0.025)
        signal.tx=simulated_tx
        key="unit-hold-unique-session"
        result=await self.device.start_hold("flame_up",key)
        self.assertTrue(result["active"])
        await asyncio.sleep(0.07)
        self.assertTrue((await self.device.heartbeat_hold(key))["active"])
        self.assertFalse((await self.device.stop_hold("wrong-session"))["stopped"])
        self.assertTrue((await self.device.stop_hold(key))["stopped"])
        n=len(signal.calls)
        self.assertGreater(n,0)
        await asyncio.sleep(0.07)
        self.assertEqual(len(signal.calls),n)
        self.assertTrue(all(x["repetitions"]==20 for x in signal.calls))

    async def test_hold_stops_when_heartbeat_is_stale(self):
        signal=self.device.rf.signals["g6r_h4t_standard"]
        async def simulated_tx(bits,**kwargs):
            signal.calls.append({"bits":list(bits),**kwargs})
            await asyncio.sleep(0.02)
        signal.tx=simulated_tx
        await self.device.start_hold("flame_down","heartbeat-test-session")
        self.device._hold_last_heartbeat-=10
        await asyncio.sleep(0.08)
        self.assertFalse((await self.device.heartbeat_hold("heartbeat-test-session"))["active"])
        n=len(signal.calls)
        await asyncio.sleep(0.05)
        self.assertEqual(len(signal.calls),n)
        self.assertLessEqual(n,1)

    async def test_off_command_interrupts_active_hold(self):
        signal=self.device.rf.signals["g6r_h4t_standard"]
        async def simulated_tx(bits,**kwargs):
            signal.calls.append({"bits":list(bits),**kwargs})
            await asyncio.sleep(0.02)
        signal.tx=simulated_tx
        await self.device.start_hold("flame_up","test-interrupt-session")
        await asyncio.sleep(0.035)
        await self.device.send_command("off",source="Flow:off")
        self.assertTrue(self.device._hold_stop.is_set())
        await self.device.stop_hold("test-interrupt-session")
        recorded=len(signal.calls)
        await asyncio.sleep(0.06)
        self.assertEqual(recorded,len(signal.calls))
        self.assertEqual("".join(map(str,signal.calls[-1]["bits"])),"0100100011010001011011")

    async def test_requested_flame_mode_migrates_and_logs(self):
        self.assertIn("emberrf_flame_mode",self.device.caps)
        self.assertEqual(self.device.values["emberrf_flame_mode"],"unknown")
        await self.device.send_command("narrow",source="unit")
        self.assertEqual(self.device.values["emberrf_flame_mode"],"narrow")
        await self.device.send_command("broad",source="unit")
        self.assertEqual(self.device.values["emberrf_flame_mode"],"broad")
        await self.device.send_command("off",source="unit")
        self.assertEqual(self.device.values["emberrf_flame_mode"],"unknown")
        self.assertTrue(any("EMBERRF FLAMMEMODUS" in l for l in self.device.logs))

    async def test_errors_logged_and_not_retried(self):
        self.device.rf.signals["g6r_h4t_aux"].fail = True
        with self.assertRaisesRegex(RuntimeError, "test RF failure"):
            await self.device.send_command("broad", source="unit test")
        self.assertEqual(len(self.device.rf.signals["g6r_h4t_aux"].calls), 1)
        self.assertTrue(any("TX FEIL" in log for log in self.device.errors))
        self.assertEqual(self.device.triggers[0][0], "failed")

    async def test_rf_failure_keeps_previous_mode(self):
        await self.device.send_command("broad",source="unit")
        self.device.rf.signals["g6r_h4t_aux"].fail=True
        with self.assertRaises(RuntimeError):
            await self.device.send_command("narrow",source="unit")
        self.assertEqual(self.device.values["emberrf_flame_mode"],"broad")

    async def test_antenna_change_does_not_transmit(self):
        await self.device.on_settings({"satellite_mode_antenna": "self"}, {"satellite_mode_antenna": "test-homey-bridge-id"}, ("satellite_mode_antenna",))
        self.assertTrue(any("ANTENNE" in log for log in self.device.logs))
        self.assertEqual(sum(len(x.calls) for x in self.device.rf.signals.values()), 0)


if __name__ == "__main__":
    unittest.main()
