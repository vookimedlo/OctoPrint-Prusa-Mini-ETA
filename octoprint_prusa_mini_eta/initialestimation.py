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

import re
import time
from typing import Pattern

from octoprint.filemanager.analysis import AnalysisAborted
from octoprint.filemanager.analysis import GcodeAnalysisQueue


class PrusaMiniGcodeAnalysisQueue(GcodeAnalysisQueue):
    _remaining_time_pattern: Pattern[str] = re.compile(r'^\s*M73\s+P\d+\s+R(\d+)\s*\r?\n?$')

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

            with open(self._current.absolute_path, 'r') as f:
                for line in f:
                    remaining_time_pattern_result = self._remaining_time_pattern.search(line)
                    if remaining_time_pattern_result:
                        result["estimatedPrintTime"] = int(remaining_time_pattern_result.group(1)) * 60
                        self._eta_plugin.logger.info("New ETA from the upload: " + str(result["estimatedPrintTime"]))
                        break
                    if not high_priority:
                        throttle()
                    if self._aborted:
                        # If abortion is requested do not raise AnalysisAborted, but return already
                        # estimatedPrintTime from the base class.
                        return result

            return result
        except AnalysisAborted as e:
            raise

    def _do_abort(self, reenqueue=True):
        super(PrusaMiniGcodeAnalysisQueue, self)._do_abort(reenqueue)
