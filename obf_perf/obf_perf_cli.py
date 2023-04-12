"""obf-perf command line interface.

TODO

Usage:

    TODO
"""


import argparse
import os
import sys
import enum
import shlex
import tempfile

import obf_perf.resource_monitor as rm


@enum.unique
class ExitCode(enum.Enum):
    """Type of match for the input ground truth images path.
    Possible values:
        - EMPTY
        - SINGLE_IMAGE
        - SINGLE_OBJECT
        - MULTIPLE_OBJECTS
    """

    NO_ERROR = 0
    """TODO"""

    SOURCE_CODE_NOT_FOUND = 1
    OBF_CONFIGS_NOT_FOUND = 2


def main():
    """Main: TODO."""

    # parse cli arguments using argparse
    args = parse_args()

    print(args)


    # Steps
    # 1. Check source code exists
    # 2. Eventually add needed tigerss headers
    # 3. Check configs exist
    # 4. Parse and load them into a list (preserving filenames)
    # 5. Enrich configs adding the missing args
        # tigress, output filename, input filename
    # 6. For each obfuscation
    # 7. Generate obfuscation
    # 8. Calculate static metrics
    # 9. Run program several times (gather dynamic metrics)
    # 10. Print resulting table
    # 11. Produce plots

    # TODO: maybe verbose mode


    # check source code file exists
    if not os.path.isfile(args.source_code):
        error(f"Error: '{args.source_code}' is not a file",
              ExitCode.SOURCE_CODE_NOT_FOUND)

    # check obfuscation configs exists
    obf_configs = []

    if len(args.obf_configs) == 1 and os.path.isdir(args.obf_configs[0]):
        # get filenames in dir
        filenames = next(os.walk(args.obf_configs[0]), (None, None, []))[2]
        obf_configs.extend(map(lambda filename: os.path.join(args.obf_configs[0], filename), filenames))

    else:
        # len(args.obf_configs) > 1 or args.obf_configs[0] is not a dir

        for path in args.obf_configs:
            if not os.path.isfile(path):
                error(f"Error: 'obf_configs' argument must be a"
                       " single directory or a sequence of files",
                      ExitCode.OBF_CONFIGS_NOT_FOUND)
            obf_configs.append(path)

        # remove duplicates preserving the order
        obf_configs = list(dict.fromkeys(obf_configs))


    print(obf_configs)


    obf_configs = load_obf_configs(obf_configs)

    print(obf_configs)

    source_code_full_path = os.path.abspath(args.source_code)
    # get the filename without the path
    source_code_filename = os.path.basename(args.source_code)
    # get filename without extension
    source_code_filename_no_ext = os.path.splitext(source_code_filename)[0]

    old_cwd = os.getcwd()

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        # chdir to make the a.out file go in the temp directory
        os.chdir(tmp_dir_name)

        # TODO: before running obfuscated versions, need to run non obfuscated one

        for obf_config in obf_configs:
            # get the filename without the path
            obf_config_filename = os.path.basename(obf_config[0])
            # get filename without extension
            obf_config_filename_no_ext = os.path.splitext(obf_config_filename)[0]

            # TODO: decide if reobfuscate when repeating the benchmark
            # for simplicity no, for better average maybe yes


            # output obfuscated source code filename
            obf_file = f"{source_code_filename_no_ext}-{obf_config_filename_no_ext}.c"
            obf_call = list(obf_config[1])
            obf_call.extend([
                f'--out={obf_file}',
                source_code_full_path
            ])
            print(obf_call)

            for i in range(args.runs):

                print(obf_config_filename_no_ext, i)

                # TODO: obfuscate
                obf_monitor = rm.ResourceMonitor(obf_call)
                exit_status = obf_monitor.run()
                if exit_status != 0:
                    print("TODO: some error happened running tigress")
                    continue
                print("TIGRESS")
                print(obf_monitor.wall_time())
                print(obf_monitor.user_time())
                print(obf_monitor.max_memory())
                # print(obf_monitor.stdout())
                # print(obf_monitor.stderr())

                # compile obfuscated code
                gcc_call = ["gcc", "-O3", obf_file]
                gcc_monitor = rm.ResourceMonitor(gcc_call)
                gcc_monitor.run()
                if exit_status != 0:
                    print("TODO: some error happened running gcc")
                    continue
                print("GCC")
                print(gcc_monitor.wall_time())
                print(gcc_monitor.user_time())
                print(gcc_monitor.max_memory())

                # TODO: subtract from tigress time, the gcc time

                # run obfuscated program
                prg_call = ["./a.out"]
                prg_monitor = rm.ResourceMonitor(prg_call)
                prg_monitor.run()
                if exit_status != 0:
                    print("TODO: some error happened running the program")
                    continue
                print("PROGRAM")
                print(prg_monitor.wall_time())
                print(prg_monitor.user_time())
                print(prg_monitor.max_memory())



        # chdir to initial cwd
        os.chdir(old_cwd)



    # TODO: remove
    # c = ["sleep", "1"]
    # mon = rm.ResourceMonitor(c)
    # status = mon.run()
    # print(status)
    # print(mon.wall_time())
    # print(mon.user_time())
    # print(mon.max_memory())

    # c = ["true"]
    # mon = rm.ResourceMonitor(c)
    # status = mon.run()
    # print(status)
    # print(mon.wall_time())
    # print(mon.user_time())
    # print(mon.max_memory())







def load_obf_configs(obf_configs):
    # iterate through all the obf_configs, load them

    # list[pair[conf_name,list[conf_params]]]

    loaded_configs = []

    for obf_config_path in obf_configs:
        try:
            with open(obf_config_path) as f:
                config_content = f.read()
                params = shlex.split(config_content)
                params = list(filter(lambda x: x != '\n', params))

                # TODO: probably keep only filename (and not entire path) as config name

                loaded_configs.append((obf_config_path, params))



        except:
            error(f"Error: cannot read '{obf_config_path}'",
                  ExitCode.OBF_CONFIGS_NOT_FOUND)

    return loaded_configs




def error(message, exit_code: ExitCode):
    print(message, file=sys.stderr)
    sys.exit(exit_code.value)










#    #exit_code = subprocess.call(args.source_code)

#    #print(exit_code)
#    print(shlex.split(
#"""--Verbosity=1 --Environment=x86_64:Linux:Gcc:4.6 --Seed=42 \
#   --Transform=EncodeData \
#      --Functions=* \
#      --LocalVariables='insertion_sort:i,j' \
#   --out=foo_out.c ./src/main.c
#"""
#))


def parse_args() -> argparse.Namespace:
    """Define the argparse parser for the cli arguments.

    TODO

    Returns:
        A dictionary-like with that maps argument name to argument value.
    """

    # create the top-level parser
    parser = argparse.ArgumentParser(
        description="A tool to compare obfuscation methods"
    )

    parser.add_argument(
        "source_code",
        help="the source code to obfuscate"
    )

    parser.add_argument(
        "obf_configs",
        nargs="+",
        help="list of obfuscation configurations, or a folder containing them"
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="output directory, default current working directory"
    )

    parser.add_argument(
        "-p",
        "--plot",
        default=False,
        action="store_true",
        help="plot the results"
    )

    parser.add_argument(
        "-r",
        "--runs",
        type=int,
        default=1,
        help="number of times the program is run, default 1"
    )

    # parse arguments
    return parser.parse_args()
