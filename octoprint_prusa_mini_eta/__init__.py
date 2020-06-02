# coding=utf-8

from __future__ import absolute_import
import re

import octoprint.plugin
from octoprint.printer.estimation import PrintTimeEstimator


class PrusaMiniPrintTimeEstimator(PrintTimeEstimator):
    def __init__(self, job_type):
        self.remaining_time = None

    @property
    def remaining_time(self):
        return int(self.__remaining_time)

    @remaining_time.setter
    def remaining_time(self, value):
        self.__remaining_time = value

    def estimate(self, progress, printTime, cleanedPrintTime, statisticalTotalPrintTime, statisticalTotalPrintTimeType):
        if self.remaining_time is None:
            return super(PrusaMiniPrintTimeEstimator, self).estimate(progress, printTime, cleanedPrintTime, statisticalTotalPrintTime, statisticalTotalPrintTimeType)
        else:
            return self.remaining_time, "estimate"


class PrusaMiniETAPlugin(octoprint.plugin.SettingsPlugin,
                         octoprint.plugin.AssetPlugin,
                         octoprint.plugin.TemplatePlugin):

    remaining_time_pattern = re.compile(r'R(\d+)$')
    remaining_time = 0
    print_time_estimator = PrusaMiniPrintTimeEstimator

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
        )

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/prusa-mini-eta.js"],
            css=["css/prusa-mini-eta.css"],
            less=["less/prusa-mini-eta.less"]
        )

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            prusa_mini_eta=dict(
                displayName="Prusa Mini ETA Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="vookimedlo",
                repo="OctoPrint-Prusa-Mini-ETA",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/vookimedlo/OctoPrint-Prusa-Mini-ETA/archive/{target_version}.zip"
            )
        )

    def create_estimator_factory(self, *args, **kwargs):
        return self.print_time_estimator

    def update_estimation(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if gcode != "M73":
            return

        remaining_time_result = self.remaining_time_pattern.search(cmd)
        if remaining_time_result:
            # ETA needs to be in seconds
            #
            self.print_time_estimator.remaining_time = int(remaining_time_result.group(1)) * 60
            self._logger.info("New ETA: " + str(self.print_time_estimator.remaining_time))


__plugin_name__ = "Prusa Mini ETA Plugin"
__plugin_pythoncompat__ = ">=3,<4"  # only python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PrusaMiniETAPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.update_estimation,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.printer.estimation.factory": __plugin_implementation__.create_estimator_factory,
    }
