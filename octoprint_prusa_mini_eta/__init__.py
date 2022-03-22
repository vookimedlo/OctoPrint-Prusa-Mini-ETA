# coding=utf-8

#    Octoprint plugin for retrieving the estimated time of printing using the Prusa Mini.
#    Copyright (C) 2020 Michal Duda - github@vookimedlo.cz
#    https://github.com/vookimedlo/OctoPrint-Prusa-Mini-ETA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

# pylint: disable=line-too-long

from __future__ import absolute_import
from distutils.log import debug

from typing import Pattern

import octoprint.plugin
from octoprint_prusa_mini_eta.initialestimation import PrusaMiniGcodeAnalysisQueue
from octoprint_prusa_mini_eta.liveestimation import PrusaMiniPrintTimeEstimator


class PrusaMiniETAPlugin(octoprint.plugin.SettingsPlugin,
                         octoprint.plugin.AssetPlugin,
                         octoprint.plugin.TemplatePlugin,
                         octoprint.plugin.StartupPlugin):
    """The Octoprint plugin for retrieving estimated time of printing using the Prusa Mini."""
    _print_time_estimator = PrusaMiniPrintTimeEstimator
    logger = None

    def on_after_startup(self):
        self.logger = self._logger

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            silent_mode_enabled=False
        )

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

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
                user="egguy",
                repo="OctoPrint-Prusa-Mini-ETA",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/egguy/OctoPrint-Prusa-Mini-ETA/archive/{target_version}.zip"
            )
        )

    def custom_gcode_analysis_queue(self, *_, **__):
        return dict(gcode=lambda finished_callback: PrusaMiniGcodeAnalysisQueue(finished_callback, self))

    def create_estimator_factory(self, *_, **__):
        return self._print_time_estimator

    def update_estimation(self, comm_instance, phase, cmd, cmd_type, gcode, *_, **__):
        if gcode != "M73":
            return

        is_silent = self._settings.get_boolean(["silent_mode_enabled"])

        cmd_args = cmd.split()
        for cmd_arg in cmd_args[1:]: # Skip M73
            if cmd_arg and cmd_arg[0] == "R":
                # ETA needs to be in seconds
                self._print_time_estimator.remaining_time = int(cmd_arg[1:]) * 60
                self._logger.info("New ETA: " + str(self._print_time_estimator.remaining_time))
            if cmd_arg and cmd_arg[0] == "S" and is_silent:
                # ETA needs to be in seconds
                self._print_time_estimator.remaining_time = int(cmd_arg[1:]) * 60
                self._logger.info("New silent ETA: " + str(self._print_time_estimator.remaining_time))



__plugin_name__ = "Prusa Mini ETA Plugin"
__plugin_pythoncompat__ = ">=3,<4"  # only python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PrusaMiniETAPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.sent": __plugin_implementation__.update_estimation,
        "octoprint.filemanager.analysis.factory": __plugin_implementation__.custom_gcode_analysis_queue,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.printer.estimation.factory": __plugin_implementation__.create_estimator_factory,
    }
