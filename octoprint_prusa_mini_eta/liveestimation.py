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
            return super(PrusaMiniPrintTimeEstimator, self).estimate(progress, printTime, cleanedPrintTime,
                                                                     statisticalTotalPrintTime,
                                                                     statisticalTotalPrintTimeType)
        else:
            return self.remaining_time, "estimate"
