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

from __future__ import absolute_import

import re
import time
from octoprint.filemanager.analysis import AnalysisAborted
from octoprint.filemanager.analysis import GcodeAnalysisQueue


class PrusaMiniGcodeAnalysisQueue(GcodeAnalysisQueue):
    remaining_time_pattern = re.compile(r'^\s*M73\s+P\d+\s+R(\d+)\s*\r?\n?$')

    def __init__(self, finished_callback):
        super(PrusaMiniGcodeAnalysisQueue, self).__init__(finished_callback)

    def _do_analysis(self, high_priority=False):
        try:
            def throttle():
                time.sleep(0.01)

            throttle_callback = throttle
            if high_priority:
                throttle_callback = None

            result = super(PrusaMiniGcodeAnalysisQueue, self)._do_analysis(high_priority)

            with open(self._current.absolute_path, 'r') as f:
                for line in f:
                    remaining_time_pattern_result = self.remaining_time_pattern.search(line)
                    if remaining_time_pattern_result:
                        result["estimatedPrintTime"] = int(remaining_time_pattern_result.group(1)) * 60
                        break
                    throttle()
                    if self._aborted:
                        # If abortion is requested we will not raise AnalysisAborted, but return already
                        # estimatedPrintTime from the base class.
                        return result

            return result
        except AnalysisAborted as e:
            raise

    def _do_abort(self):
        super(PrusaMiniGcodeAnalysisQueue, self)._do_abort()