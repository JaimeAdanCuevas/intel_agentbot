#! /usr/bin/env python

import glob
import os
import shutil
import binascii
import sys
import getopt
import copy

iform_set = {}
global_set = {}
exe_results_set = {}
spec_loaded = 0


def insert_space(string, every=4):
    return ' '.join(string[i:i+every] for i in range(0, len(string), every))


def printplus(obj):
    """
    Pretty-prints the object passed in.
    """
    # Dict
    if isinstance(obj, dict):
        for k, v in sorted(obj.items()):
            print('{0}: {1}'.format(k, v))

    # List or tuple            
    elif isinstance(obj, list) or isinstance(obj, tuple):
        for x in obj:
            print(x)

    # Other
    else:
        print(obj)


def csv_ize(obj):
    row = ''
    if isinstance(obj, dict):
        for k, v in obj.items():
            row = row + (k) + ' , '
            row = row + (csv_ize(v))
    elif isinstance(obj, list) or isinstance(obj, tuple):
        row = row + obj + ' , '
    else:
        row = row + obj + ' , '
    return row


def listify(obj):
    row = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            row.append(k)
            row.append(listify(v))
    elif isinstance(obj, list) or isinstance(obj, tuple):
        row.append(obj)
    else:
        row.append(obj)
    return row


def pretty_ize(obj):
    row = ''
    if isinstance(obj, dict):
        row = row + '\n'
        for k, v in obj.items():
            row = row + (k) + ' = '
            row = row + (pretty_ize(v))
    elif isinstance(obj, list) or isinstance(obj, tuple):
        row = row + obj + '\n'
    else:
        row = row + str(obj) + '\n'
    return row


def print_report(exefile, result_set):
    filename = exefile.replace('.exe', '.csv')
    list_items = []
    list_keys = []
    row = 0
    count = 0
    if not isinstance(result_set, dict):
        print('result_set object is not a dictionary!\n')
        return 0
    with open(filename, 'w') as outfile:
        for k, v in result_set.items():
            for key, value in v.items():
                list_keys.append(str(key))
                list_items.append(str(value))
                if key == 'count':
                    count = int(value)
            list_keys.append('covered')
            if count == 0:
                list_items.append('No')
            else:
                list_items.append('Yes')
            if row == 0:
                outfile.write(' , '.join(list_keys) + '\n')
            outfile.write(' , '.join(list_items) + '\n')
            list_keys = []
            list_items = []
            row += 1
            count = 0


def process_sde_output(exefile, sde_output):
    global iform_set
    global spec_loaded
    global global_set
    global exe_results_set
    found_global_dynamic_stats = 0
    headers = []
    exe_results_set[exefile] = copy.deepcopy(iform_set)
    with open(sde_output, 'r') as inF:
        for line in inF:
            if not found_global_dynamic_stats and line.startswith('# EMIT_GLOBAL_DYNAMIC_STATS'):
                found_global_dynamic_stats = 1
            if found_global_dynamic_stats:
                if not line.startswith('#') and not line.startswith('*'):
                    # Load IFORM data and store it in a dictionary by IFORM name
                    tokens = line.split()
                    if len(tokens) > 0:
                        print(' , '.join(tokens) + '\n')
                        if tokens[0] in global_set:
                            print(tokens[0] + ' is in global set, adding count\n')
                            global_set[tokens[0]]['count'] = global_set[tokens[0]]['count'] + int(tokens[1])
                        else:
                            print(tokens[0] + ' is not in Global set!')
                        if tokens[0] in exe_results_set[exefile]:
                            print(tokens[0] + ' is in ' + exefile + ' set, adding count\n')
                            exe_results_set[exefile][tokens[0]]['count'] = exe_results_set[exefile][tokens[0]]['count'] + int(tokens[1])
                        else:
                            print(tokens[0] + ' is not in ' + exefile + ' set!')
    # Print the file results
    print_report(exefile, exe_results_set[exefile])


def execute_profiling(dir, exefile, params):
    sde_command = 'sde -mix -iform -- ' + exefile + ' ' + params
    sde_output_default = 'sde-mix-out.txt'
    sde_output_file = exefile.replace('.exe', '') + '-mix-out.txt'
    print('SDE command is : ' + sde_command)
    if os.path.exists(sde_output_file):
        print('Output file ' + sde_output_file + ' exists! Erasing it.')
        os.remove(sde_output_file)
    sde_result = os.popen(sde_command)
    std_out = sde_result.read()
    print("SDE result is ", std_out)

    if os.path.exists(sde_output_default):
        shutil.move(sde_output_default, sde_output_file)
        print(sde_output_file + ' generated! Processing it.')
        process_sde_output(exefile, sde_output_file)


# Loads the XED IFORM list (an ASCII table)
def process_spec(spec):
    global iform_set
    global spec_loaded
    headers = []
    with open(spec, 'r') as inF:
        for line in inF:
            if not line.startswith('#'):
                # Load IFORM data and store it in a dictionary by IFORM name
                tokens = line.split()
                iform_set[tokens[3]] = {}
                for i in range(0, len(tokens)):
                    iform_set[tokens[3]][headers[i]] = tokens[i]
                iform_set[tokens[3]]['count'] = 0
                # print(pretty_ize(iform_set[tokens[3]]) + '\n')
            else:
                # Load headers
                if line.startswith('#iclass'):
                    headers = line.replace('#', ' ').split()
                    print('Headers are : ' + ' , '.join(headers))
    spec_loaded = 1


def process_directory(dir):
    global spec_loaded
    params = ''
    os.chdir(dir)
    if not spec_loaded:
        print('Usage: iform_cov.py -s <XED IFORM list> -d <inputdirectory>')
        sys.exit()
    for file in glob.glob("*.exe"):
        print('Processing ' + file + '\n')
        params_file = file.replace('.exe', '.par')
        try:
            with open(params_file, 'r') as inF:
                for line in inF:
                    params = params + line
        except:
            print('No params for ' + file + '\n')
        os.chdir(dir)
        execute_profiling(dir, file, params) 
        params = ''


def main(argv):
    global global_set
    global iform_set
    inputdir = ''
    specfile = ''
    print('Starting')

    try:
        opts, args = getopt.getopt(argv, "h:s:d:", ["dir="])
    except getopt.GetoptError:
        print('iform_cov.py -s <XED IFORM list> -d <inputdirectory>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('iform_cov.py -s <XED IFORM list> -d <inputdirectory>')
            sys.exit()
        elif opt == '-s':
            specfile = arg
            process_spec(specfile)
        elif opt in ("-d", "--dir"):
            inputdir = arg
            global_set = copy.deepcopy(iform_set)
            process_directory(inputdir)
            # print(pretty_ize(global_set))
            print_report('global_result.exe', global_set)
    print('Input dir is ', inputdir)


if __name__ == "__main__":
    params = len(sys.argv)
    if params < 2:
        print('iform_cov.py -s <XED IFORM list> -d <inputdirectory>')
        quit()
    else:
        main(sys.argv[1:])
