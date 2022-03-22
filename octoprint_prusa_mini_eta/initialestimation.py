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

import time
from typing import Pattern

from octoprint.filemanager.analysis import AnalysisAborted
from octoprint.filemanager.analysis import GcodeAnalysisQueue


class PrusaMiniGcodeAnalysisQueue(GcodeAnalysisQueue):
    """Initial estimation."""

    def __init__(self, finished_callback, eta_plugin):
        super(PrusaMiniGcodeAnalysisQueue, self).__init__(finished_callback)
        from octoprint_prusa_mini_eta import PrusaMiniETAPlugin
        assert isinstance(eta_plugin, PrusaMiniETAPlugin)
        self._eta_plugin = eta_plugin

    def _do_analysis(self, high_priority=False):
        try:
            def throttle():
                time.sleep(0.01)  # high_priority == False

            result = super(PrusaMiniGcodeAnalysisQueue, self)._do_analysis(high_priority)

            silent_mode_enabled = self._eta_plugin._settings.get_boolean(["silent_mode_enabled"])
            result["silent"] = silent_mode_enabled
            found_normal_eta = False
            found_silent_eta = not silent_mode_enabled  # Don't search if not enabled

            # Prusa slicer generate a GCODE in the form with the silent mode
            # M73 P0 R352  -- Normal Mode
            # M73 Q0 S352  -- Silent mode

            with open(self._current.absolute_path, 'r') as opened_file:
                for line in opened_file:
                    if found_normal_eta and found_silent_eta:
                        # Don't continue to parse the file
                        break

                    line = line.strip() # Prevent surprises
                    if line.startswith("M73"):
                        self._eta_plugin.logger.info("Found M73: %s", line)
                        splited = line.split()

                        for split_line in splited[1:]:  # Ignore already found M73
                            if split_line[0] == "R":
                                found_normal_eta = True
                                result["estimatedPrintTime"] = int(split_line[1:]) * 60
                                self._eta_plugin.logger.info("New ETA from the upload: %s seconds", result["estimatedPrintTime"])
                                break 
                            elif split_line[0] == "S":
                                found_silent_eta = True
                                result["estimatedPrintTime"] = int(split_line[1:]) * 60
                                self._eta_plugin.logger.info("New silent ETA from the upload: %s seconds", result["estimatedPrintTime"])
                                found_silent_eta = True
                                break
                        continue
                    
                    if found_normal_eta and not found_silent_eta:
                        self._eta_plugin.logger.debug("Only found normal ETA, don't continue parsing (is silent mode enable in the slicer profile ?)")
                        break

                    if not high_priority:
                        throttle()
                    if self._aborted:
                        # If abortion is requested do not raise AnalysisAborted, but return already
                        # estimatedPrintTime from the base class.
                        return result

            return result
        except AnalysisAborted as _:
            raise

    def _do_abort(self, reenqueue=True):
        super(PrusaMiniGcodeAnalysisQueue, self)._do_abort(reenqueue)
