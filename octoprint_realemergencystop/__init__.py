# coding=utf-8
from __future__ import absolute_import
from xmlrpc.client import boolean

import octoprint.plugin
import re
from octoprint.events import Events
from time import sleep
from gpiozero import LED, Button
import click

class realemergencystopPlugin(octoprint.plugin.StartupPlugin,
                                       octoprint.plugin.EventHandlerPlugin,
                                       octoprint.plugin.TemplatePlugin,
                                       octoprint.plugin.SettingsPlugin,
                                       octoprint.plugin.AssetPlugin,
                                       octoprint.plugin.SimpleApiPlugin):

    #Init global variables
    def initialize(self):
        self.estop_sent = False
        self.button_pin_initialized = False
        self.led_pin_initialized = False
        self.button = None
        self.led = None

    #Gets settings from UI config file
    @property
    def button_pin(self):
        return int(self._settings.get(["button_pin"]))
    @property
    def led_pin(self):
        return int(self._settings.get(["led_pin"]))
    @property
    def switch(self):
        return int(self._settings.get(["switch"]))
    @property
    def emergencyGCODE(self):
        return str(self._settings.get(["emergencyGCODE"]))
    @property
    def resetGCODE(self):
        return str(self._settings.get(["resetGCODE"]))
    @property
    def physical_switch(self):
        return bool(self._settings.get(["physical_button"]))

    # AssetPlugin hook
    def get_assets(self):
        return dict(js=["js/realemergencystop.js"], css=["css/realemergencystop.css", "css/fontawesome.min.css"])

    # Template hooks
    def get_template_configs(self):
        return [dict(type="settings", custom_bindings=False)]

    # Settings hook
    def get_settings_defaults(self):
        return dict(
            button_pin=0,
			led_pin=0,
            switch=0,
            emergencyGCODE="M112",
            resetGCODE="FIRMWARE_RESTART",
			confirmationDialog=False,
			big_button=False
        )

    #Startup Function
    def on_after_startup(self):
        self._logger.info("Real Emergency Stop started")
        self._setup_button()
        self._setup_led()

    #Settings Saved Function
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self._setup_button()
        self._setup_led()

    def get_api_commands(self):
        return dict(
            emergencyStop=[],
            emergencyStopReset=[]
        )

    def on_api_command(self, command, data):
        if command == "emergencyStop":
            self.send_emergency_stop()
        elif command == "emergencyStopReset":
            self.estop_reset()

    def custom_stop_command(self, cli_group, pass_octoprint_ctx, *args, **kwargs):
        command = self
        @click.command("estop")
        def estop_command():
            """Printer E-STOP"""
            command.send_emergency_stop()
            click.echo("ESTOP ACTIVATED!")

        @click.command("estopreset")
        def estopreset_command():
            """Printer E-Stop Reset"""
            command.estop_reset()
            click.echo("ESTOP RESET!")

        return [estop_command, estopreset_command]

    #Button Setup Function
    def _setup_button(self):
        if self.button_enabled():
            self._logger.info("Setting up button.")
            self._logger.info(
                f"Emergency Stop button active on GPIO Pin [{self.button_pin}]"
            )
            if self.switch == 0:
                self.button = Button(self.button_pin, pull_up=True)
            else:
                self.button = Button(self.button_pin, pull_up=False)
            self.button.when_pressed = self.send_emergency_stop
            self.button.when_released = self.estop_reset
            self.button_pin_initialized = True

        else:
            self._logger.info("Button pin not configured, won't work unless configured!")

    #LED Setup Function
    def _setup_led(self):
        if self.button_enabled():
            self._logger.info("Setting up LED.")
            self._logger.info(
                f"Emergency Stop LED active on GPIO Pin [{self.led_pin}]"
            )
            self.led = LED(self.led_pin)
            self.led_pin_initialized = True
        else:
            self._logger.info("LED pin not configured, won't work unless configured!")

    def button_enabled(self):
        return self.physical_switch != False

    def send_emergency_stop(self):
        if self.estop_sent:
            return
        self._logger.info("Sending emergency stop GCODE")
        self._printer.commands(self.emergencyGCODE)
        self.estop_sent = True
        self.led.blink(on_time=1, off_time=1, n=None, background=True)


	#E-Stop Reset
    def estop_reset(self):
        self._logger.info("Emergency stop button was reset")
        self.led.blink(on_time=0.2, off_time=0.2, n=None, background=True)
        self._printer.connect()
        sleep(3)
        self._printer.commands(self.resetGCODE)
        self.led.off()
        self.estop_sent = False


	#extra UI Shit idk what this really does lmao
    def on_event(self, event, payload):
        if event is Events.CONNECTED:
            self.estop_sent = False
        elif event is Events.DISCONNECTED:
            self.estop_sent = True

        if not self.button_enabled():
            if event is Events.USER_LOGGED_IN:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="info", autoClose=True, msg="Don' forget to configure this plugin."))
            elif event is Events.PRINT_STARTED:
                self._plugin_manager.send_plugin_message(self._identifier, dict(type="info", autoClose=True, msg="You may have forgotten to configure this plugin."))


    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            realemergencystop=dict(
                displayName="Real Emergency stop",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="jonathanrobichaud4",
                repo="Octoprint-RealEmergencyStop",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/jonathanrobichaud4/Octoprint-RealEmergencyStop/archive/{target_version}.zip"
            )
        )

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
# __plugin_pythoncompat__ = ">=2.7,<3" # only python 2
# __plugin_pythoncompat__ = ">=3,<4" # only python 3
__plugin_pythoncompat__ = ">=2.7,<4"  # python 2 and 3

__plugin_name__ = "Real Emergency Stop"
__plugin_version__ = "0.1.7"

def __plugin_check__():
    try:
        from gpiozero import LED, Button
    except ImportError:
        return False
    return True

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = realemergencystopPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.cli.commands": __plugin_implementation__.custom_stop_command,
    }
