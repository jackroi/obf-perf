import os
import shlex
import tempfile
from typing import List, Callable, Optional

import obf_perf.resource_monitor as rm
import obf_perf.result_container as rc
import obf_perf.metrics as metrics


def load_obfuscation_configs(obf_config_path_list: List[str]):
    # iterate through all the obf_configs, load them

    # list[pair[conf_name,list[conf_params]]]

    loaded_configs = []

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

            for i in range(runs):

                print(obf_config_filename_no_ext, i)

                # TODO: obfuscate
                obf_monitor = rm.ResourceMonitor(obf_call)
                exit_status = obf_monitor.run()
                if exit_status != 0:
                    print("TODO: some error happened running tigress")
                    continue

                # compile obfuscated code
                gcc_call = ["gcc", "-O3", obf_file]
                gcc_monitor = rm.ResourceMonitor(gcc_call)
                gcc_monitor.run()
                if exit_status != 0:
                    print("TODO: some error happened running gcc")
                    continue

                # TODO: subtract from tigress time, the gcc time

                # run obfuscated program
                prg_call = ["./a.out"]
                prg_monitor = rm.ResourceMonitor(prg_call)
                prg_monitor.run()
                if exit_status != 0:
                    print("TODO: some error happened running the program")
                    continue

                obf_wall_time = max(0, obf_monitor.wall_time() - gcc_monitor.wall_time())
                obf_user_time = max(0, obf_monitor.user_time() - gcc_monitor.user_time())
                obf_system_time = max(0, obf_monitor.system_time() - gcc_monitor.system_time())

                # TODO: handle errors
                obf_code_size = metrics.file_size(obf_file)
                bin_size = metrics.file_size("a.out")
                line_count = metrics.line_count(obf_file)
                ncd = metrics.normalized_compression_distance(source_code_full_path, obf_file)

                # TODO: evenutually pass a dict: **args
                result = rc.Result(
                    name=obf_config_filename_no_ext,
                    obfuscation_wall_time=obf_wall_time,
                    obfuscation_user_time=obf_user_time,
                    obfuscation_system_time=obf_system_time,
                    obfuscation_memory=obf_monitor.max_memory(),
                    compile_wall_time=gcc_monitor.wall_time(),
                    compile_user_time=gcc_monitor.user_time(),
                    compile_system_time=gcc_monitor.system_time(),
                    source_code_size=obf_code_size,
                    executable_size=bin_size,
                    lines_of_code=line_count,
                    compression_metric=ncd,
                    execution_wall_time=prg_monitor.wall_time(),
                    execution_user_time=prg_monitor.user_time(),
                    execution_system_time=prg_monitor.system_time(),
                    execution_memory=prg_monitor.max_memory(),
                    execution_minor_page_faults=prg_monitor.major_page_faults(),
                    execution_major_page_faults=prg_monitor.minor_page_faults(),
                    execution_total_page_faults=prg_monitor.page_faults(),
                    executable_voluntary_context_switches=prg_monitor.volountary_context_switches(),
                    executable_involuntary_context_switches=prg_monitor.involountary_context_switches(),
                    executable_total_context_switches=prg_monitor.context_switches()
                )
                results.addResult(result)

                if step_callback: step_callback()



        # chdir to initial cwd
        os.chdir(old_cwd)

    return results
