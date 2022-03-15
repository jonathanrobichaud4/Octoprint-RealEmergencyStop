# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import re
from octoprint.events import Events
from time import sleep
import RPi.GPIO as GPIO


class Emergency_stopPlugin(octoprint.plugin.StartupPlugin,
                                       octoprint.plugin.EventHandlerPlugin,
                                       octoprint.plugin.TemplatePlugin,
                                       octoprint.plugin.SettingsPlugin,
                                       octoprint.plugin.AssetPlugin):

    def initialize(self):
        GPIO.setwarnings(False)  # Disable GPIO warnings
        self.estop_sent = False
        self.button_pin_initialized = False
        self.led_pin_initialized = False

    @property
    def button_pin(self):
        return int(self._settings.get(["button_pin"]))
    @property
    def led_pin(self):
        return int(self._settings.get(["led_pin"]))


    @property
    def switch(self):
        return int(self._settings.get(["switch"]))

    # AssetPlugin hook
    def get_assets(self):
        return dict(js=["js/emergencystop.js"], css=["css/emergencystop.css"])

    # Template hooks
    def get_template_configs(self):
        return [dict(type="settings", custom_bindings=True)]

    # Settings hook
    def get_settings_defaults(self):
        return dict(
            button_pin=-1,  # Default is -1
			led_pin=-1,
            switch=0
        )

    def on_after_startup(self):
        self._logger.info("Emergency Stop started")
        self._setup_button()
        self._setup_led()

    def on_settings_save(self, data):
        if self.button_enabled() and self.button_pin_initialized:
            GPIO.remove_event_detect(self.button_pin)
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self._setup_button()
        self._setup_led()

    def _setup_button(self):
        if self.button_enabled():
            self._logger.info("Setting up button.")
            self._logger.info("Using Board Mode")
            GPIO.setmode(GPIO.BCM)
            self._logger.info("Emergency Stop button active on GPIO Pin [%s]" % self.button_pin)
            if self.switch is 0:
                GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            else:
                GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

            GPIO.remove_event_detect(self.button_pin)
            GPIO.add_event_detect(
                self.button_pin, GPIO.FALLING,
                callback=self.button_callback,
                bouncetime=1
            )
            self.button_pin_initialized = True
        else:
            self._logger.info("Pin not configured, won't work unless configured!")

    def _setup_led(self):
        if self.button_enabled():
            self._logger.info("Setting up LED.")
            self._logger.info("Using Board Mode")
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.led_pin, GPIO.OUT, initial=GPIO.LOW)
            self.led_pin_initialized = True
        else:
            self._logger.info("Pin not configured, won't work unless configured!")

    def sending_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
        if self.emergency_stop_triggered():
            self.send_emergency_stop()


    def button_enabled(self):
        return self.button_pin != -1

    def emergency_stop_triggered(self):
        return self.button_pin_initialized and self.button_enabled() and GPIO.input(self.button_pin) != self.switch

    def emergency_stop_reset(self):
        self.led_interupt()

    def activate_led(self):
        try:
            while True:
                GPIO.output(self.led_pin, GPIO.HIGH) # Turn on
                sleep(1)                  # Sleep for 1 second
                GPIO.output(self.led_pin, GPIO.LOW)  # Turn off
                sleep(1)
        except self.led_interupt():
               print("LED Off")

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

    def button_callback(self, _):
        self._logger.info("Emergency stop button was triggered")
        if self.emergency_stop_triggered():
            self.send_emergency_stop()
        else:
            self.estop_sent = False
            self.emergency_stop_reset()

    def send_emergency_stop(self):
        if self.estop_sent:
            return

        self._logger.info("Sending emergency stop GCODE")
        self._printer.commands("M112")
        self.activate_led()
        self.estop_sent = True



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

#GPIO.cleanup()
# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
# __plugin_pythoncompat__ = ">=2.7,<3" # only python 2
# __plugin_pythoncompat__ = ">=3,<4" # only python 3
__plugin_pythoncompat__ = ">=2.7,<4"  # python 2 and 3

__plugin_name__ = "Emergency Stop"
__plugin_version__ = "0.0.2"

def __plugin_check__():
    try:
        import RPi.GPIO as GPIO
        if GPIO.VERSION < "0.6":  # Need at least 0.6 for edge detection
            return False
    except ImportError:
        return False
    return True

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Emergency_stopPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.sending": __plugin_implementation__.sending_gcode
    }
