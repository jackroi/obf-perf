import os
import sys
import shlex
import tempfile
import time
from typing import List, Callable, Optional, Tuple

import obf_perf.resource_monitor as rm
import obf_perf.result_container as rc
import obf_perf.metrics as metrics


# TODO: maybe use a real no-op config
__NORMAL_CONFIG = (str("00-normal"), [ "tigress",
                                       "--Environment=x86_64:Linux:Gcc:4.6",
                                       "--Transform=Ident" ])


def load_obfuscation_configs(obf_config_path_list: List[str]):
    # iterate through all the obf_configs, load them

    # list[pair[conf_name,list[conf_params]]]

    loaded_configs = [ __NORMAL_CONFIG ]

    for obf_config_path in obf_config_path_list:
        with open(obf_config_path) as f:
            config_content = f.read()
            params = shlex.split(config_content)
            params = list(filter(lambda x: x != '\n', params))

            # TODO: probably keep only filename (and not entire path) as config name

            loaded_configs.append((obf_config_path, params))

    return loaded_configs


def perform_analysis(source_code_path: str,
                     obf_configs: List,
                     runs: int,
                     warmup: int,
                     step_callback: Optional[Callable] = None):
    source_code_full_path = os.path.abspath(source_code_path)
    # get the filename without the path
    source_code_filename = os.path.basename(source_code_path)
    # get filename without extension
    source_code_filename_no_ext = os.path.splitext(source_code_filename)[0]

    results = rc.ResultContainer()

    old_cwd = os.getcwd()

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        # chdir to make the a.out file go in the temp directory
        os.chdir(tmp_dir_name)

        for obf_config in obf_configs:
            # get the filename without the path
            obf_config_filename = os.path.basename(obf_config[0])
            # get filename without extension
            obf_config_filename_no_ext = os.path.splitext(obf_config_filename)[0]

            # TODO: decide if reobfuscate when repeating the benchmark
            # for simplicity no, for better average maybe yes

            # generate new source code file with tigress headers
            # same filename, but stored in the temp directory
            new_source_code_path = source_code_filename
            __create_tigress_source_code(source_code_full_path,
                                         new_source_code_path,
                                         obf_config)

            # output obfuscated source code filename
            obf_file = f"{source_code_filename_no_ext}-{obf_config_filename_no_ext}.c"

            # obfuscate source code
            __obfuscate(new_source_code_path, obf_file, obf_config)

            # compute metrics
            ncd = metrics.normalized_compression_distance(source_code_full_path, obf_file)
            halstead_difficulty = metrics.halstead_difficulty(source_code_full_path,
                                                              obf_file)

            for _ in range(warmup):
                __obfuscate_compile_run(new_source_code_path, obf_file, obf_config)
                if step_callback: step_callback()

            for _ in range(runs):
                try:
                    obf_monitor, gcc1_monitor, gcc2_monitor, prg_monitor = __obfuscate_compile_run(new_source_code_path, obf_file, obf_config)

                    obf_wall_time = max(0, obf_monitor.wall_time() - gcc1_monitor.wall_time())
                    obf_user_time = max(0, obf_monitor.user_time() - gcc1_monitor.user_time())
                    obf_system_time = max(0, obf_monitor.system_time() - gcc1_monitor.system_time())

                    # TODO: handle errors
                    obf_code_size = metrics.file_size(obf_file)
                    bin_size = metrics.file_size("a.out")
                    line_count = metrics.line_count(obf_file)

                    # TODO: evenutually pass a dict: **args
                    result = rc.Result(
                        name=obf_config_filename_no_ext,
                        obfuscation_wall_time=obf_wall_time,
                        obfuscation_user_time=obf_user_time,
                        obfuscation_system_time=obf_system_time,
                        obfuscation_memory=obf_monitor.max_memory(),
                        compile_wall_time=gcc2_monitor.wall_time(),
                        compile_user_time=gcc2_monitor.user_time(),
                        compile_system_time=gcc2_monitor.system_time(),
                        source_code_size=obf_code_size,
                        executable_size=bin_size,
                        lines_of_code=line_count,
                        compression_metric=ncd,
                        halstead_difficulty=halstead_difficulty,
                        execution_wall_time=prg_monitor.wall_time(),
                        execution_user_time=prg_monitor.user_time(),
                        execution_system_time=prg_monitor.system_time(),
                        execution_memory=prg_monitor.max_memory(),
                        execution_minor_page_faults=prg_monitor.major_page_faults(),
                        execution_major_page_faults=prg_monitor.minor_page_faults(),
                        execution_total_page_faults=prg_monitor.page_faults(),
                        execution_voluntary_context_switches=prg_monitor.volountary_context_switches(),
                        execution_involuntary_context_switches=prg_monitor.involountary_context_switches(),
                        execution_total_context_switches=prg_monitor.context_switches()
                    )
                    results.addResult(result)

                except RuntimeError:
                    # TODO: catch correct error
                    # TODO something happened
                    pass

                finally:
                    if step_callback: step_callback()


        # chdir to initial cwd
        os.chdir(old_cwd)

    return results

# obfuscate source code
def __obfuscate(source_code_full_path, obf_file, obf_config):
    obf_call = list(obf_config[1])
    obf_call.extend([
        f'--out={obf_file}',
        source_code_full_path
    ])
    obf_monitor = rm.ResourceMonitor(obf_call)
    exit_status = obf_monitor.run()
    if exit_status != 0:
        print("TODO: some error happened running tigress", file=sys.stderr)
        print(obf_monitor.stderr(), file=sys.stderr)
        raise

    return obf_monitor


def __obfuscate_compile_run(source_code_full_path, obf_file, obf_config):
    # TODO probably split in 3 functions

    # obfuscate source code
    obf_monitor = __obfuscate(source_code_full_path, obf_file, obf_config)

    # compile obfuscated code (without optimizations)
    gcc1_call = ["gcc", obf_file]
    gcc1_monitor = rm.ResourceMonitor(gcc1_call)
    exit_status = gcc1_monitor.run()
    if exit_status != 0:
        print("TODO: some error happened running gcc", file=sys.stderr)
        print(gcc1_monitor.stderr(), file=sys.stderr)
        raise

    # compile obfuscated code (with optimizations)
    gcc2_call = ["gcc", "-O3", obf_file]
    gcc2_monitor = rm.ResourceMonitor(gcc2_call)
    exit_status = gcc2_monitor.run()
    if exit_status != 0:
        print("TODO: some error happened running gcc", file=sys.stderr)
        print(gcc2_monitor.stderr(), file=sys.stderr)
        raise

    # TODO: subtract from tigress time, the gcc time

    # run obfuscated program
    prg_call = ["./a.out"]
    prg_monitor = rm.ResourceMonitor(prg_call)
    exit_status = prg_monitor.run()
    if exit_status != 0:
        print("TODO: some error happened running the program", file=sys.stderr)
        print(prg_monitor.stderr(), file=sys.stderr)
        raise

    return obf_monitor, gcc1_monitor, gcc2_monitor, prg_monitor


# create a new source code file, that includes in the original source code file
# the required tigress header files, depending on the obfuscation configuration
def __create_tigress_source_code(source_code_path: str,
                                 new_source_code_path: str,
                                 obf_config: Tuple[str, List[str]]):
    headers = __get_tigress_headers(obf_config)
    header_lines = [ f'#include "{header}"\n' for header in headers ]

    # create a new source code file, that includes the required tigress headers
    with open(source_code_path, 'r') as src, \
         open(new_source_code_path, 'w') as dst:
        dst.writelines(header_lines)
        dst.write(src.read())


# get header files required by the obfuscation configuration
def __get_tigress_headers(obf_config: Tuple[str, List[str]]) -> List[str]:
    # get tigress installation path
    tigress_path = os.environ.get("TIGRESS_HOME")
    if not tigress_path:
        raise RuntimeError("Error: TIGRESS_HOME not set")

    TIGRESS_DEFAULT_HEADERS = [ "tigress.h" ]
    OTHER_DEFAULT_HEADERS = [ "pthread.h" ]
    JITTER_HEADER = "jitter-amd64.c"
    # table that maps tigress transformations to header files
    TRANSFORMATION_TO_HEADERS = {
        "jit": [ JITTER_HEADER ],
        "jitdynamic": [ JITTER_HEADER ]
    }

    # identify the required header files
    tigress_header_files = []
    for arg in obf_config[1]:
        if arg.startswith("--Transform="):
            transformation = arg.split("=")[1].lower()
            if transformation in TRANSFORMATION_TO_HEADERS:
                tigress_header_files.extend(TRANSFORMATION_TO_HEADERS[transformation])

    # add default headers
    tigress_header_files.extend(TIGRESS_DEFAULT_HEADERS)

    # prepend tigress path to tigress header files
    header_files = [ os.path.join(tigress_path, header)
                     for header in tigress_header_files ]

    # add other default headers
    header_files.extend(OTHER_DEFAULT_HEADERS)

    return header_files
