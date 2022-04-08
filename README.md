# Real Emergency Stop

Takes **heavy** inspiration from [Emergency stop simplified](https://github.com/Mechazawa/Emergency_stop_simplified) which covers the physical button and [Simple Emergency Stop](https://github.com/Sebclem/OctoPrint-SimpleEmergencyStop) which covers the UI buttons

This plugin reacts to an E-top button and when triggered, it issues **M112** command to printer and blinks the light in the button. Also when the button is reset, it resets the printer. A UI E-Stop button also exists in which you can E-Stop and reset the printer which works almost interchangeably with the real button.

Let's check some features:
* Uses a real E-Stop button that can be found on industrial equipment
* Info pop-up when plugin hasn't been configured
* Virtual E-Stop and reset button in top bar
* User-friendly and easy to configure
* Runs on OctoPrint 1.3.0 and higher

## Setup

Install manually using this URL:

    https://github.com/jonathanrobichaud4/Octoprint-RealEmergencyStop

## Configuration

Configuration couldn't be simpler, you can configure all settings from the UI. For the button, you need to configure the listening board pin (board mode) and if the switch terminal is connected to ground or 3.3V.

Default pin is 0 (not configured) and ground (as it is safer, read below).

**WARNING! Never connect the switch input to 5V as it could fry the GPIO section of your Raspberry!**

#### Advice

Sometimes the button can be randomly triggered for some users. Turns out that if running button wires along motor wires, it was enough to interfere with button reading.

To solve this connect a shielded wire to your button and ground the shielding, ideally on both ends.

If you are unsure about your button being triggered, check [OctoPrint logs](https://community.octoprint.org/t/where-can-i-find-octoprints-and-octopis-log-files/299)
