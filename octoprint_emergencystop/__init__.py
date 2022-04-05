# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import re
from octoprint.events import Events
from time import sleep
from gpiozero import LED, Button

class Emergency_stopPlugin(octoprint.plugin.StartupPlugin,
                                       octoprint.plugin.EventHandlerPlugin,
                                       octoprint.plugin.TemplatePlugin,
                                       octoprint.plugin.SettingsPlugin,
                                       octoprint.plugin.AssetPlugin):

    #Init global variables
    def initialize(self):
        self.estop_sent = False
        self.button_pin_initialized = False
        self.led_pin_initialized = False
        self.button = None
        self.led = None
        self.emergencyGCODE = ""

    #Gets pin settings from UI config file
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
        return int(self._settings.get(["emergencyGCODE"]))

    # AssetPlugin hook
    def get_assets(self):
        return dict(js=["js/emergencystop.js"], css=["css/emergencystop.css", "css/fontawesome.all.min.css"])

    # Template hooks
    def get_template_configs(self):
        return [dict(type="settings", custom_bindings=False)]

    # Settings hook
    def get_settings_defaults(self):
        return dict(
            button_pin=-1,  # Default is -1
			led_pin=-1,
            switch=0,
            emergencyGCODE="M112",
			confirmationDialog=False,
			big_button=False
        )

    #Startup Function
    def on_after_startup(self):
        self._logger.info("Emergency Stop started")
        self._setup_button()
        self._setup_led()

    #Settings Saved Function
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self._setup_button()
        self._setup_led()

    def get_api_commands(self):
        return dict(
            emergencyStop=[]
        )

    def on_api_command(self, command, data):
		# check if there is a : in line
        find_this = ":"
        if find_this in str(self.emergencyGCODE):

			# if : found then, split, then for each:
            gcode_list = str(self.emergencyGCODE).split(':')
            for gcode in gcode_list:
                self._printer.commands(gcode)
        else:
            self._printer.commands(self.emergencyGCODE)


    #Button Setup Function
    def _setup_button(self):
        if self.button_enabled():
            self._logger.info("Setting up button.")
            self._logger.info(
                f"Emergency Stop button active on GPIO Pin [{self.button_pin}]"
            )
            if self.switch is 0:
                self.button = Button(self.button_pin, pull_up=True)
            else:
                self.button = Button(self.button_pin, pull_up=False)
            self.button.when_pressed = self._estop_activated
            self.button.when_released = self._estop_reset
            #self._printer.on_printer_add_message("M112") =
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

    def sending_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
        if self.emergency_stop_triggered():
            self.send_emergency_stop()

    def button_enabled(self):
        return self.button_pin != -1

    def emergency_stop_triggered(self):
        return self.button_pin_initialized and self.button_enabled() and self.button.is_pressed != self.switch

    def _estop_reset(self, _):
        self._logger.info("Emergency stop button was reset")
        self.led.blink(on_time=0.2, off_time=0.2, n=None, background=True)
        self._printer.connect()
        sleep(3)
        self._printer.commands("FIRMWARE_RESTART")
        self.led.off()
        self.estop_sent = False

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

    def _estop_activated(self, _):
        self._logger.info("Emergency stop button was triggered")
        if self.emergency_stop_triggered():
            self.send_emergency_stop()
        else:
            self.estop_sent = False

    def send_emergency_stop(self):
        if self.estop_sent:
            return
        self._logger.info("Sending emergency stop GCODE")
        self._printer.commands("M112")
        self.estop_sent = True
        self.led.blink(on_time=1, off_time=1, n=None, background=True)

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            emergencystop=dict(
                displayName="Emergency stop",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="jonathanrobichaud4",
                repo="Octoprint_Emergency_stop",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/jonathanrobichaud4/Octoprint_Emergency_stop/archive/{target_version}.zip"
            )
        )

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
# __plugin_pythoncompat__ = ">=2.7,<3" # only python 2
# __plugin_pythoncompat__ = ">=3,<4" # only python 3
__plugin_pythoncompat__ = ">=2.7,<4"  # python 2 and 3

__plugin_name__ = "Emergency Stop"
__plugin_version__ = "0.1.13"

def __plugin_check__():
    try:
        from gpiozero import LED, Button
    except ImportError:
        return False
    return True

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Emergency_stopPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.sending": __plugin_implementation__.sending_gcode,
    }
