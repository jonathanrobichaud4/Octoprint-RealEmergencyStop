$(function() {
    function emergencystopViewModel(parameters) {
        var self = this;
        //self.settingsViewModel = parameters[0];

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin !== "emergencystop") {
                console.log('Ignoring '+plugin);
                return;
            }

            new PNotify({
                title: 'Emergency stop',
                text: data.msg,
                type: data.type,
                hide: data.autoClose
            });

        }

        this.settings = undefined;
        this.allSettings = parameters[0];
        this.loginState = parameters[1];
        this.printerState = parameters[2];
        this.confirmation = undefined;

        this.onAfterBinding = function () {};
        this.onBeforeBinding = function () {
            this.confirmation = $("#confirmation");
            this.settings = this.allSettings.settings.plugins.emergencystop;
        };

        this.click = function () {
            if (!this.can_send_command())
                return;
            if (this.settings.confirmationDialog())
                this.confirmation.modal("show");
            else
                this.sendCommand();

        };

        this.sendCommand = function () {
            $.ajax({
                url: API_BASEURL + "plugin/emergencystop",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "emergencyStop"
                }),
                contentType: "application/json; charset=UTF-8",
                success: function (data, status) {}
            });
            this.confirmation.modal("hide");

        };

        this.hasControlPermition = function () {
            let user = this.loginState.currentUser();
            if(user.permissions !== undefined){
                return user.permissions.includes("control") || user.needs.role.includes("control");
            }
            else return true;

        }

        this.big_button_visible = function () {
            return this.loginState.isUser() && this.settings.big_button() && this.hasControlPermition();
        };

        this.little_button_visible = function () {
            return this.loginState.isUser() && !this.settings.big_button() && this.hasControlPermition();
        };

        this.can_send_command = function () {
            return this.loginState.isUser() && this.hasControlPermition() && this.printerState.isOperational() ;
        };

        this.little_button_css = function () {
            return (this.printerState.isOperational() ? "emergencystop_small" : "emergencystop_small_disabled");
        };
        this.big_button_css = function () {
            return (this.printerState.isOperational() ? "emergencystop_big" : "emergencystop_big emergencystop_big_disabled");
        };

        this.get_title = function () {
            return (this.printerState.isOperational() ? gettext('!!! Emergency Stop !!! ') : gettext('Printer disconnected'));
        };

    }

    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    //OCTOPRINT_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        //construct: emergencystopViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument
        //dependencies: ["settingsViewModel"],

        // Finally, this is the list of selectors for all elements we want this view model to be bound to.
        //elements: ["#settings_plugin_emergencystop_form"]
    //]);

    OCTOPRINT_VIEWMODELS.push({
        construct: emergencystopViewModel,
        dependencies: ["settingsViewModel", "loginStateViewModel", "printerStateViewModel"],
        elements: ["#settings_plugin_emergencystop_form", "#navbar_plugin_emergencystop"]
    });
});
