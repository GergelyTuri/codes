import json
from datetime import datetime
import numpy as np
import cPickle as pickle
import os.path
import glob
import argparse
import re
import sys
import time

#from lab.classes import database

exts = ['.vr', '.tdml']

def parseTime(time_string):
    time_formats = ['%Y-%m-%d %H:%M:%S', '%d-%b-%Y %H:%M:%S', '%Y-%m-%d%H:%M:%S']
    for frmt in time_formats:
        try:
            return time.strptime(time_string, frmt)
        except ValueError:
            pass

def findFiles(directory, overwrite=False):
    paths = []
    pickled_paths = []
    for dirpath, dirnames, filenames in os.walk(directory):
        paths.extend(
            map(lambda f: os.path.join(dirpath, f),
            filter(lambda f: os.path.splitext(f)[1] in exts, filenames)))
        pickled_paths.extend(
            map(lambda f: os.path.join(dirpath, os.path.splitext(f)[0]),
            filter(lambda f: os.path.splitext(f)[1] == '.pkl', filenames)))
    
    if not overwrite:
        paths = filter(lambda f: os.path.splitext(f)[0] not in pickled_paths, paths)
        #paths = list(set(paths)-set(pickled_paths))

    #return map(lambda f: f+ext, paths)
    return paths
    

def loadSql(filename, trial_info, settings, experiment_group=None):
    """
    if database.fetchTrialId(filename) is not None:
        print "{} already in database".format(filename)
        return
    """
    database.updateTrial(filename, trial_info['mouse_name'], trial_info['start_time'],
        trial_info['stop_time'], experiment_group)
    trial_id = database.fetchTrialId(filename)
    print 'loading trial {}: {}'.format(trial_id, filename)

    for key in settings:
        if '_controller' in key:
            continue
        if type(settings[key]) == type({}):
            settings[key] = json.dumps(settings[key])
        database.updateTrialAttr(trial_id, key, settings[key])

    if 'laps' in trial_info.keys():
        database.updateTrialAttr(trial_id, 'laps', trial_info['laps'])


def main(argv):
    argParser = argparse.ArgumentParser()
    argParser.add_argument(
        '-o', '--overwrite', action='store_true', 
        help='overwirte existing .pkl file')
    argParser.add_argument(
        '-d', '--directory', type=str, 
        help='process all .vmn files beneath this directory')
    argParser.add_argument(
        '-f', '--file', action='store', type=str,
        help='process specifically this file')
    argParser.add_argument(
        '-s', '--load_sql', action='store_true',
        help='load trial info into sql database')
    argParser.add_argument(
        '-g', '--group', action='store', type=str,
        help='group this experiment belongs to')
    args = argParser.parse_args(argv)

    def _append(adict,key,val):
        try:
            adict[key].append(val)
        except KeyError:
            adict[key] = [val]

    if args.directory is not None:
        files = findFiles(args.directory, overwrite=args.overwrite)
    else:
        files = [args.file]

    sqltime_format = '%Y-%m-%d %H:%M:%S' 
    for fname in files:
        mdict = {}
        trial_info = {}
        inlick = False
        valve_start = -1
        starttime_offset = 0
        print 'pickling ' + fname

        with open(fname) as f:
            for line in f:
                data = json.loads(line)
                if 'settings' in  data.keys():
                    break

        settings = data['settings']
        behavior_address = str(settings['behavior_controller']['ip']) + ':' + \
            str(settings['behavior_controller']['receive_port'])   
        trial_info['reward_pin'] = settings['reward']['pin']
        trial_info['sync_pin'] = settings['sync_pin']
        
        behavior_address_valid = False
        with open(fname) as f:
            for line in f:
                data = json.loads(line)
                if behavior_address in data.keys():
                    behavior_address_valid = True 
                    break
        if not behavior_address_valid:
            behavior_address = str(settings['behavior_controller']['ip']) + ':' + \
            str(settings['behavior_controller']['send_port']) 
            print "received messages from send_port for file: " + fname

        with open(fname) as f:
            for line in f:
                data = json.loads(line)

                if 'mouse' in data.keys():
                    trial_info['mouse_name'] = data['mouse']

                if 'start' in data.keys():                   
                    start_time = parseTime(data['start'])
                    trial_info['start_time'] = time.strftime(sqltime_format,
                        start_time)
 
                if 'stop' in data.keys():
                    stop_time = parseTime(data['stop'])
                    trial_info['stop_time'] = time.strftime(sqltime_format,
                        stop_time)

                if 'lap' in data.keys():
                    _append(mdict, 'lap', data['time'])

                if 'y' in data.keys():
                    _append(mdict,'position_y',[data['time'],float(data['y'])])
                elif behavior_address in data.keys():
                    message = data[behavior_address]
                    if 'lick' in message.keys():
                        if message['lick']['action'] == 'start':
                            lick_start = data['time']
                            inlick = True
                        elif inlick and message['lick']['action'] == 'stop':
                            _append(mdict,'licking',[lick_start, data['time']])
                            inlick = False

                    elif str(trial_info.get('reward_pin', -1)) in message.get('valve', {}).keys():
                        if message['valve'][str(trial_info['reward_pin'])] == "open":
                            valve_start = data['time'] 
                        elif valve_start != -1 and \
                                message['valve'][str(trial_info['reward_pin'])] == "close":
                            _append(mdict,'water',[valve_start, data['time']])
                            valve_start = -1

                    elif str(trial_info.get('sync_pin', -1)) in message.get('valve', {}).keys():
                        if message['valve'][str(trial_info['sync_pin'])] == "open":
                            starttime_offset = data['time']
                    
                    elif 'valve' in message.keys():
                        if message['valve'].get('pin', -10) == trial_info.get('reward_pin', -1):
                            if message['valve'].get('action', '') == "open":
                                valve_start = data['time'] 
                            elif valve_start != -1 and \
                                    message['valve'].get('action','') == "close":
                                _append(mdict,'water',[valve_start, data['time']])
                                valve_start = -1
                        elif message['valve'].get('pin', -10) == trial_info.get('sync_pin', -1):
                            if message['valve'].get('action', 'close') == "open":
                                starttime_offset = data['time']

        if len(mdict.get('position_y', [])) < 2:
            continue

        if starttime_offset != 0:
            for key in mdict.keys():
                if key == 'position_y':
                    position_array = np.array(mdict[key])
                    position_array[:,0] -= starttime_offset
                    position_array = position_array[np.where(position_array[:,0] >= 0)]
                    mdict[key] = position_array.tolist()
                else:
                    mdict[key] = (np.array(mdict[key])-starttime_offset).tolist()

        try:
            mdict['recordingDuration'] = settings.get('trial_length',
                mdict['position_y'][-1][0])
        except IndexError:
            mdict['recordingDuration'] = 0
        else:
            mdict['treadmillPosition'] = np.array(mdict['position_y'])
            treadpos = mdict['treadmillPosition']
            treadpos[:,1] /= np.max(treadpos[:,1])
            treadpos[:,1] %= 1

            if treadpos[0,0] != 0:
                treadpos = np.vstack(([0,treadpos[0,1]], treadpos))
            mdict['treadmillPosition'] = treadpos

        trial_info['laps'] = len(mdict.get('lap',[]))
        if 'stop_time' not in trial_info.keys():
            time_format = '%Y-%m-%d %H:%M:%S'
            start_ti = time.mktime(
                time.strptime(trial_info['start_time'],time_format))
            trial_info['stop_time'] = datetime.fromtimestamp(
                start_ti + treadpos[-1,0]).strftime(time_format)

        for key in mdict.keys():
            mdict[key] = np.array(mdict[key])

        mdict['trackLength'] = float(settings['track_length'])
        mdict['recordingDuration'] = float(settings['trial_length'])

        pickle.dump(mdict,open(os.path.splitext(fname)[0] + '.pkl','w'))

        if args.load_sql:
            loadSql(fname, trial_info, settings, experiment_group=args.group)
            

if __name__ == '__main__':
    main(sys.argv[1:])
