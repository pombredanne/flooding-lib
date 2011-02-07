#!c:/python25/python.exe
# -*- coding: utf-8 -*-
#***********************************************************************
# This file is part of the nens library.
#
# the nens library is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# the nens library is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with the nens libraray.  If not, see
# <http://www.gnu.org/licenses/>.
#
# Copyright 2008, 2009 Nelen & Schuurmans
#*
#***********************************************************************
#* Library    : <if this is a module, what is its name>
#* Purpose    :
#* Function   : main
#* Usage      : calculaterisespeed.py --help
#*
#* Project    : K0115
#*
#* $Id: calculaterisespeed_132.py 9992 2010-03-15 10:13:14Z Mario $
#*
#* initial programmer :  Mario Frasca
#* initial date       :  20081210
#**********************************************************************

__revision__ = "$Rev: 9992 $"[6:-2]

"""this script computes the water level rise speed needed by the
module HISSSM.  please refer to Ticket:1092.
"""

import logging
log = logging.getLogger('nens')

import nens.asc

if __name__ == '__main__':
    sys.path.append('..')
    
    from django.core.management import setup_environ
    import lizard.settings
    setup_environ(lizard.settings)

from django.db import transaction
from zipfile import ZipFile, ZIP_DEFLATED
from lizard.flooding.models import Scenario, Result, ResultType
from lizard.base.models import Setting
from numpy import nan


def perform_calculation(conn, tmp_location, scenario_id, year, timeout=0):

    import os
    
    log.debug("step 0a: get a cursor from the database connection")
    curs = conn.cursor()

    log.debug("step 0b: get the settings for scenario '%d' out of the database..." % scenario_id)
    log.debug("0b1: scenario_id, region_id, breach_id")
    scenario = Scenario.objects.get(pk=scenario_id)

    log.debug("0b2: destination_dir")    
    destination_dir = Setting.objects.get(key='DESTINATION_DIR').value
    output_dir_name = os.path.join(destination_dir, scenario.get_rel_destdir())

    log.debug("0c: resetting to forward-slash")
    location = tmp_location.replace("\\", "/")
    if not location.endswith("/"):
        location += "/"

    log.debug("0f: restore the files from the database.")
   

    for resulttype, names in [
            (15, ['fls_h.inc']),#"fls_import.zip"
            (18, ['fls_h.inc']),#"fls_import.zip"
            (1, ['dm1maxd0.asc']),          
        ]:
        try:
            resultloc = scenario.result_set.get(resulttype=ResultType.objects.get(pk=resulttype)).resultloc
            input_file = ZipFile(os.path.join(destination_dir, resultloc), "r")

            for name in names:
                try:
                    content = input_file.read(name)
                    temp = file(os.path.join(location, name.lower()), "wb")
                    temp.write(content)
                    temp.close()
                except KeyError:
                    log.debug('file %s not found in archive' % name)
        except Result.DoesNotExist, e:
            log.info('inputfile of resulttype %i not found'%resulttype)



    log.debug("0g: retrieve dm1maxd0 from gridmaxwaterdepth as to have a default shape.")
    def_grid = None
    def_name = 'dm1maxd0.asc'
    def_container = 'gridmaxwaterdepth.zip'
    log.debug("use %s as default grid (default shape) from %s" % (def_name,def_container))
    import stat
    if os.stat(os.path.join(output_dir_name, def_container))[stat.ST_SIZE] == 0:
        log.warning("input file '%s' is empty" % def_container)
    else:
        input_file = ZipFile(os.path.join(output_dir_name, def_container))
        def_grid = nens.asc.AscGrid(data=input_file, name=def_name)

    log.debug("step 3: use the fls_h.inc (sequence of water levels) into grid_dh.asc (maximum water raise speed)")

    input_name = "fls_h.inc"

    first_timestamps_generator = nens.asc.AscGrid.xlistFromStream(os.path.join(location , input_name), just_count=True, 
                                                                  default_grid=def_grid)
    first_timestamp, _ = first_timestamps_generator.next()
    second_timestamp, _ = first_timestamps_generator.next()
    delta_t = second_timestamp - first_timestamp

    arrival, arrival_value = nens.asc.AscGrid.firstTimestampWithValue(os.path.join(location, input_name), 
                                                                      default_grid=def_grid)
    temp = file(os.path.join(location, 'grid_ta.asc'), 'wb')
    arrival.writeToStream(temp)
    temp.close()

    deadly, deadly_value = nens.asc.AscGrid.firstTimestampWithValue(os.path.join(location, input_name), threshold=1.5, 
                                                                    default_grid=def_grid)
    temp = file(location + 'grid_td.asc', 'wb')
    deadly.writeToStream(temp)
    temp.close()

    time_difference = nens.asc.AscGrid.apply(lambda x, y: x - y, deadly, arrival)
    value_difference = nens.asc.AscGrid.apply(lambda x: x - 0.02, deadly_value)

    def speedFirstMetersFunction(x_value, y_value):

        if y_value == 0:
            return (x_value + 0.3) / delta_t
        else:
            return x_value / y_value
   
    def speedFirstMetersFunctionLoop(x, y):
        result = x.copy()
        
        for col in range(len(x)):
            for row in range(len(x[0])):
                x_value = x[col][row]
                y_value = y[col][row]
                
                try:
                    if y_value == 0:
                        result[col][row] = (x_value + 0.3) / delta_t
                    else:
                        result[col][row] = x_value / y_value
                except TypeError:
                    pass
        
        return result

    def fillInTheSpeedBlanks(speed, wet):
        "if water arrives but does not reach deadly level, return 0"

        result = speed.copy()
        
        for col in range(len(speed)):
            for row in range(len(speed[0])):
                speed_value = speed[col][row]
                wet_value = wet[col][row]
                try:
                    if wet_value > 0 and not speed_value > 0:
                        result[col][row] = 0.0
                    else:
                        result[col][row] = speed_value
                except TypeError:
                    pass   
        return result

    speedFirstMeters = nens.asc.AscGrid.apply(speedFirstMetersFunctionLoop, value_difference, time_difference)
    speedFirstMeters = nens.asc.AscGrid.apply(fillInTheSpeedBlanks, speedFirstMeters, arrival_value)
    temp = file(location + 'grid_dh.asc', 'wb')
    speedFirstMeters.writeToStream(temp)
    temp.close()

    def computeMaxSpeed(value_tsgrid):
        """compute maximum speed of water raise as of Ticket:1532

        'value_tsgrid' is an ordered list of pairs, associating the
        values from the .inc file to the grids holding the timestamps
        for which the value is first reached for the pixel.

        return value is a grid containing the maximum raise speed.
        """

        result = value_tsgrid[0][1].copy()
        for col in range(1, result.ncols+1):
            for row in range(1, result.nrows+1):
                if arrival[col, row] is not None:
                    for value, ts in value_tsgrid:
                        if value < 1.5: continue # below deadly
                        if ts[col, row] is None: continue # value not present for timestamp
                        speed = speedFirstMetersFunction(value, ts[col, row] - arrival[col, row]) # includes deadly at arrival case
                        result[col, row] = max(speed, result[col, row])
        return result

    value_tsgrid = nens.asc.AscGrid.firstTimestamp(location + input_name, threshold=True, 
                                                   default_grid=def_grid)
    maxWaterRaiseSpeed = computeMaxSpeed(value_tsgrid)
    temp = file(location + 'grid_ss.asc', 'wb')
    maxWaterRaiseSpeed.writeToStream(temp)
    temp.close()

    log.debug("step 5: store the output files and the fact that they exist")

    for dirname, filename, zipfilename, resulttype, unit, value in [
        ('.', 'grid_dh.asc', 'griddh.zip', 19, None, None),
        ('.', 'grid_ss.asc', 'gridss.zip', 23, None, None),
        ('.', 'grid_ta.asc', 'gridta.zip', 21, None, None),
        ('.', 'grid_td.asc', 'gridtd.zip', 22, None, None), ]:

        resultloc = os.path.join(scenario.get_rel_destdir(), zipfilename)
        
        content = file(os.path.join(location , dirname , filename), 'rb').read()
        output_file = ZipFile( os.path.join(destination_dir, resultloc), mode="w", compression=ZIP_DEFLATED)
        output_file.writestr(filename, content)
        output_file.close()
        
        result, new = scenario.result_set.get_or_create(resulttype=ResultType.objects.get(pk=resulttype))
        result.resultloc =  resultloc
        result.unit = unit
        result.value = value
        result.save()
        
    log.debug("tasks")
    return True

def main(options, args):
    """translates options to connection + scenario_id, then calls perform_calculation
    """

    log.setLevel(options.loglevel)

    from django.db import connection
    
    perform_calculation(connection, 'c:\\temp' , options.scenario, options.year, options.timeout)


if __name__ == '__main__':

    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s',)

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--hisssm-location', default='C:/Program Files/HIS-SSMv2.4/', help='the root of the his-ssm installation')

    parser.add_option('--scenario', help='the ID of the scenario to be computed', type='int')
    parser.add_option('--year', default=2008, help='the year of simulation data', type='int')

    parser.add_option('--timeout', default=3600, type='int', help='timeout in seconds before killing HISSSM executable')
    parser.add_option('--debug', help='be extremely verbose', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO)
    parser.add_option('--quiet', help='be extremely silent', action='store_const', dest='loglevel', const=logging.WARNING)

    (options, args) = parser.parse_args()
    main(options, args)
