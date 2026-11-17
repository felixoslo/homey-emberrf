from homey.app import App

class PeisTestApp(App):
    async def on_init(self):
        await super().on_init()
        self.log("EmberRF ready. No RF transmissions are initiated on app startup.")

homey_export = PeisTestApp
