"""Core module of the obf-perf tool.

This module contains the core functions of the obf-perf tool.
The main function is `perform_analysis`, which performs the analysis on the
given source code file, using the given obfuscation configs.

Typical usage example:
    import obf_perf_core as opc

    # load the obfuscation configs
    obf_configs = opc.load_obfuscation_configs(["config1.txt", "config2.txt"])

    # perform the analysis
    results = opc.perform_analysis("source_code.c",
                                   obf_configs,
                                   runs=10,
                                   warmup=3,
                                   optimization_level=3)
"""


import os
import shlex
import tempfile
from typing import List, Tuple, Optional, Callable

import obf_perf.resource_monitor as rm
import obf_perf.result_container as rc
import obf_perf.metrics as metrics


# identity tigress config (no obfuscation)
__NORMAL_CONFIG = (str("00-normal"), [ "tigress",
                                       "--Environment=x86_64:Linux:Gcc:4.6",
                                       "--Transform=Ident" ])


def load_obfuscation_configs(obf_config_path_list: List[str]
                             ) -> List[Tuple[str, List[str]]]:
    """Loads the obfuscation configs from the given list of paths.

    Args:
        obf_config_path_list: List of paths to the obfuscation configs.

    Returns:
        List of tuples containing the config name and the
        list of config params.

    Raises:
        OSError: If one of the files at the given paths cannot be read.
    """

    # list of obfuscation configs
    # always include the identity config
    # list[pair[conf_name,list[conf_params]]]
    loaded_configs: List[Tuple[str, List[str]]] = [ __NORMAL_CONFIG ]

    # load the given obfuscation configs
    for obf_config_path in obf_config_path_list:
        # read the config file
        with open(obf_config_path) as f:
            config_content = f.read()

        # split the config file content into a list of params
        params = shlex.split(config_content)
        # remove newlines
        params = list(filter(lambda x: x != '\n', params))
        # add the config to the list
        loaded_configs.append((obf_config_path, params))

    return loaded_configs


def perform_analysis(source_code_path: str,
                     obf_configs: List,
                     runs: int,
                     warmup: int,
                     optimization_level: int,
                     step_callback: Optional[Callable] = None
                     ) -> rc.ResultContainer:
    """Performs the analysis on the given source code file, using the given
    obfuscation configs.

    For each obfuscation config, the obfuscation is performed, then the
    obfuscated source code is compiled and run, and finally the metrics are
    computed. The number of runs and warmup runs can be specified, in order to
    get a more stable estimate of the metrics. Of course, the warmup runs are
    not included in the final results.
    After each step (run or warmup run), the step_callback function is called.
    The optimization level can be specified for the compiler, it takes values
    from 0 to 3, where 0 is no optimization and 3 is the highest optimization.

    Args:
        source_code_path: Path to the source code file.
        obf_configs: List of obfuscation configs.
            Use the function `load_obfuscation_configs` to get the configs.
        runs: Number of runs for each obfuscation config.
        warmup: Number of warmup runs for each obfuscation config.
        optimization_level: Optimization level for the compiler.
            Takes values from 0 to 3, where 0 is no optimization and
            3 is the highest optimization.
        step_callback: Callback function to be called after each step
            (run or warmup run).

    Returns:
        ResultContainer containing the results of the analysis.

    Raises:
        OSError: If the source code file cannot be read.
        CalledProcessError: If a command fails.
    """

    # validate arguments
    if runs < 1:
        raise ValueError("`runs` must be >= 1")
    if warmup < 0:
        raise ValueError("`warmup` must be >= 0")
    if optimization_level < 0 or optimization_level > 3:
        raise ValueError("`optimization_level` must be between 0 and 3")
    if len(obf_configs) < 1:
        raise ValueError("`obf_configs` must contain at least one config")

    # get the absolute path of the source code file
    source_code_full_path = os.path.abspath(source_code_path)
    # get the source code filename without the path
    source_code_filename = os.path.basename(source_code_path)
    # get the sourcd code filename without the extension
    source_code_filename_no_ext = os.path.splitext(source_code_filename)[0]

    # create the result container
    results = rc.ResultContainer()

    # save the current working directory
    old_cwd = os.getcwd()

    # create a temporary directory in which to run the analysis
    # to avoid polluting the current working directory
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        # change the current working directory to the temp directory
        os.chdir(tmp_dir_name)

        # repeat the analysis for each obfuscation config
        for obf_config in obf_configs:
            # get the obfuscation config filename without the path
            obf_config_filename = os.path.basename(obf_config[0])
            # get the obfuscation config filename without the extension
            obf_config_filename_no_ext = \
                os.path.splitext(obf_config_filename)[0]

            # dynamically generate new source code file with the required
            # tigress headers, depending on the obfuscation config
            # (same filename, but stored in the temp directory)
            new_source_code_path = source_code_filename
            __create_tigress_source_code(source_code_full_path,
                                         new_source_code_path,
                                         obf_config)

            # output obfuscated source code filename
            obf_file = f"{source_code_filename_no_ext}" \
                       f"-{obf_config_filename_no_ext}.c"

            # obfuscate the source code to compute the static metrics
            # that do not change run after run
            __obfuscate(new_source_code_path, obf_file, obf_config)

            # compute static metrics that do not change run after run
            # in reality they might change, but we assume that the
            # variability is negligible and since they are expensive
            # to compute, we compute them only once
            ncd = metrics.normalized_compression_distance(source_code_full_path,
                                                          obf_file)
            halstead_difficulty = \
                metrics.halstead_difficulty(source_code_full_path, obf_file)

            # perform the warmup runs
            for _ in range(warmup):
                # run the analysis, but do not save the results
                __obfuscate_compile_run(new_source_code_path,
                                        obf_file,
                                        obf_config,
                                        optimization_level)
                # call the callback function
                if step_callback: step_callback()

            # perform the actual runs
            for _ in range(runs):
                # run the analysis
                obf_monitor, gcc1_monitor, gcc2_monitor, prg_monitor = \
                    __obfuscate_compile_run(new_source_code_path,
                                            obf_file,
                                            obf_config,
                                            optimization_level)

                # compute tigress obfuscation process related metrics;
                # need to subtract the gcc1 times, because they are
                # included in the obfuscation times, since the tigress
                # obfuscation process concludes with a call to gcc;
                # to avoid negative values, we take the max with 0
                obf_wall_time = max(0, obf_monitor.wall_time()
                                       - gcc1_monitor.wall_time())
                obf_user_time = max(0, obf_monitor.user_time()
                                       - gcc1_monitor.user_time())
                obf_system_time = max(0, obf_monitor.system_time()
                                         - gcc1_monitor.system_time())

                # compute some metrics
                # (bytes to kilobytes)
                obf_code_size = metrics.file_size(obf_file) / 1000
                bin_size = metrics.file_size("a.out") / 1000
                line_count = metrics.line_count(obf_file)

                # build the result by extracting the relevant data
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
                    norm_compression_distance=ncd,
                    halstead_difficulty=halstead_difficulty,
                    execution_wall_time=prg_monitor.wall_time(),
                    execution_user_time=prg_monitor.user_time(),
                    execution_system_time=prg_monitor.system_time(),
                    execution_memory=prg_monitor.max_memory(),
                    execution_minor_page_faults=
                        prg_monitor.major_page_faults(),
                    execution_major_page_faults=
                        prg_monitor.minor_page_faults(),
                    execution_total_page_faults=prg_monitor.page_faults(),
                    execution_voluntary_context_switches=
                        prg_monitor.volountary_context_switches(),
                    execution_involuntary_context_switches=
                        prg_monitor.involountary_context_switches(),
                    execution_total_context_switches=
                        prg_monitor.context_switches()
                )
                # add the result to the ResultContainer
                results.add_result(result)

                # call the callback function
                if step_callback: step_callback() # type: ignore

        # chdir to initial cwd
        os.chdir(old_cwd)

    return results


def __obfuscate(source_code_path: str,
                obf_file_name: str,
                obf_config: Tuple[str, List[str]]) -> rm.ResourceMonitor:
    """Obfuscates the source code using the given obfuscation config.

    Args:
        source_code_path: Path to the source code file.
        obf_file_name: Name of the (output) obfuscated source code file.
        obf_config: Obfuscation config.

    Returns:
        ResourceMonitor object associated with the obfuscation process.

    Raises:
        CalledProcessError: If the obfuscation process fails.
    """

    # arguments to call the obfuscator
    obf_call = list(obf_config[1])
    # add output and input files to the arguments
    obf_call.extend([
        f'--out={obf_file_name}',
        source_code_path
    ])
    # run the obfuscator
    obf_monitor = rm.ResourceMonitor(obf_call)
    obf_monitor.run()
    return obf_monitor


def __compile(obf_file_name: str,
              optimization_level: int) -> rm.ResourceMonitor:
    """Compiles the obfuscated source code.

    Args:
        obf_file_name: Name of the obfuscated source code file.
        optimization_level: Optimization level for the compiler.
            Takes values from 0 to 3, where 0 is no optimization and
            3 is the highest optimization.

    Returns:
        ResourceMonitor object associated with the compilation process.

    Raises:
        CalledProcessError: If the compilation process fails.
    """

    # validate optimization level
    if optimization_level < 0 or optimization_level > 3:
        raise ValueError("`optimization_level` must be between 0 and 3")

    # arguments to call the compiler
    gcc_call = [ "gcc", f"-O{optimization_level}", obf_file_name ]
    # run the compiler
    gcc_monitor = rm.ResourceMonitor(gcc_call)
    gcc_monitor.run()
    return gcc_monitor


def __run(executable_name: str = "a.out") -> rm.ResourceMonitor:
    """Runs the executable.

    Args:
        executable_name: Name of the executable file.

    Returns:
        ResourceMonitor object associated with the execution process.

    Raises:
        CalledProcessError: If the execution process fails.
    """

    # validate executable name
    if not executable_name:
        raise ValueError("`executable_name` cannot be empty")

    # executable name that works even if it's not in PATH
    executable_name = os.path.join("./", executable_name)

    # arguments to call the executable
    run_call = [ executable_name ]
    run_monitor = rm.ResourceMonitor(run_call)
    run_monitor.run()
    return run_monitor


def __obfuscate_compile_run(source_code_path: str,
                            obf_file: str,
                            obf_config: Tuple[str, List[str]],
                            optimization_level: int
                            ) -> Tuple[rm.ResourceMonitor,
                                       rm.ResourceMonitor,
                                       rm.ResourceMonitor,
                                       rm.ResourceMonitor]:
    """Obfuscates, compiles and runs the source code.

    Args:
        source_code_path: Path to the source code file.
        obf_file: Name of the (output) obfuscated source code file.
        obf_config: Obfuscation config.
        optimization_level: Optimization level for the compiler.
            Takes values from 0 to 3, where 0 is no optimization and
            3 is the highest optimization.

    Returns:
        Tuple of four ResourceMonitor objects associated with the obfuscation,
        compilation (without optimization), compilation (with optimization),
        and execution processes.
        If `optimization_level` is 0, the third and fourth elements of the
        tuple are the same.

    Raises:
        CalledProcessError: If any of the processes fails.
    """

    # obfuscate source code
    obf_monitor = __obfuscate(source_code_path, obf_file, obf_config)

    # compile obfuscated code (without optimizations)
    gcc1_monitor = __compile(obf_file, optimization_level=0)

    # compile obfuscated code (with optimizations) if required
    if optimization_level > 0:
        gcc2_monitor = __compile(obf_file,
                                 optimization_level=optimization_level)
    else:
        # if no optimizations are required, use the same monitor
        # as for the compilation without optimizations
        gcc2_monitor = gcc1_monitor

    # run obfuscated program
    prg_monitor = __run("a.out")

    return obf_monitor, gcc1_monitor, gcc2_monitor, prg_monitor


def __create_tigress_source_code(source_code_path: str,
                                 new_source_code_path: str,
                                 obf_config: Tuple[str, List[str]]) -> None:
    """Creates a new source code file, with the required tigress headers.

    Creates a new source code file, that includes in the original
    source code file the required tigress header files, depending on the
    obfuscation configuration.

    Args:
        source_code_path: Path to the source code file.
        new_source_code_path: Path to the new source code file.
        obf_config: Obfuscation config.

    Raises:
        OSError: If the source code file cannot be opened.
    """

    # get tigress header files required by the obfuscation configuration
    headers = __get_tigress_headers(obf_config)
    # generate the include lines
    header_lines = [ f'#include "{header}"\n' for header in headers ]

    # create a new source code file, that includes the required tigress headers
    with open(source_code_path, 'r') as src, \
         open(new_source_code_path, 'w') as dst:
        # write the include lines
        dst.writelines(header_lines)
        # write the original source code
        dst.write(src.read())


# get header files required by the obfuscation configuration
def __get_tigress_headers(obf_config: Tuple[str, List[str]]) -> List[str]:
    """Gets the header files required by the obfuscation configuration.

    Args:
        obf_config: Obfuscation config.

    Returns:
        List of header files required by the obfuscation configuration.
    """

    # get tigress installation path
    tigress_path = os.environ.get("TIGRESS_HOME")
    if not tigress_path:
        # tigress not installed properly
        raise RuntimeError("Error: TIGRESS_HOME not set")

    # default header files required by tigress for all obfuscations
    TIGRESS_DEFAULT_HEADERS = [ "tigress.h" ]
    # default header files required by tigress for all obfuscations
    # but not included by tigress
    OTHER_DEFAULT_HEADERS = [ "pthread.h" ]
    # header file required by tigress for jitter obfuscation
    JITTER_HEADER = "jitter-amd64.c"
    # table that maps tigress transformations to header files
    TRANSFORMATION_TO_HEADERS = {
        "jit": [ JITTER_HEADER ],
        "jitdynamic": [ JITTER_HEADER ]
    }

    # identify the required header files
    tigress_header_files = []
    # go through the arguments of the obfuscation configuration
    for arg in obf_config[1]:
        # if the argument is a transformation
        if arg.startswith("--Transform="):
            # get the transformation name (lowercase)
            transformation = arg.split("=")[1].lower()
            # if the transformation requires header files
            if transformation in TRANSFORMATION_TO_HEADERS:
                # add the required header files
                tigress_header_files.\
                    extend(TRANSFORMATION_TO_HEADERS[transformation])

    # add default headers
    tigress_header_files.extend(TIGRESS_DEFAULT_HEADERS)

    # prepend tigress path to tigress header files
    header_files = [ os.path.join(tigress_path, header)
                     for header in tigress_header_files ]

    # add other default headers
    header_files.extend(OTHER_DEFAULT_HEADERS)

    return header_files
