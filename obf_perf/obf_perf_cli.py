"""obf-perf command line interface.

This module contains the command line interface of the obf-perf tool.
It measures the performance of a set of obfuscation techniques on a given
source code file. The results are printed on the standard output as a table
or as a JSON object.
It can also generate plots of the results.

Usage:

    obf-perf.py source_code obf_configs [obf_configs ...]
                [-r RUNS]
                [-w WARMUP]
                [-O {0,1,2,3}]
                [-f {table,table2,json}]
                [-p]
                [-o OUTPUT_DIR]
                [-h]

    To obtain more information about the usage of the tool, refer to the
    documentation or run the command with the '-h' option.
"""


import argparse
import os
import sys
import enum
import itertools
import signal
from typing import List, Union
from matplotlib import subprocess

from prettytable import PrettyTable
from alive_progress import alive_bar

import obf_perf.obf_perf_core as opcore
import obf_perf.result_container as rc
import obf_perf.plots as plots


@enum.unique
class ExitCode(enum.Enum):
    """Exit codes of the obf-perf command line interface.

    Possible values:
        NO_ERROR: No error occurred.
        SOURCE_CODE_NOT_FOUND: The source code file was not found.
        OBF_CONFIGS_NOT_FOUND: The obfuscation config file was not found.
        INVALID_CLI_PARAM: Invalid command line parameter.
    """

    NO_ERROR = 0
    """No error occurred."""

    SOURCE_CODE_NOT_FOUND = 1
    """The source code file was not found."""

    OBF_CONFIGS_NOT_FOUND = 2
    """The obfuscation config file was not found."""

    INVALID_CLI_PARAM = 3
    """Invalid command line parameter."""

    RUNTIME_ERROR = 4
    """An error occurred while running the analysis."""


# TODO: maybe verbose mode


def main():
    """Main function of the obf-perf command line interface."""

    # exit gracefully on keyboard interrupt
    signal.signal(signal.SIGINT, interrupt_handler)

    # parse cli arguments using argparse
    args = parse_args()

    # validate cli arguments and return a list of obfuscation configs
    obf_config_path_list = validate_args(args)

    # try to load the obfuscation configs
    try:
        obf_configs = opcore.load_obfuscation_configs(obf_config_path_list)
    except OSError as e:
        error(f"Error: cannot read '{e.filename}'",
              ExitCode.OBF_CONFIGS_NOT_FOUND)
        assert False    # unreachable (for pyright)

    # number of steps in the progress bar
    bar_step_count = len(obf_configs) * (args.warmup + args.runs)
    with alive_bar(bar_step_count, file=sys.stderr) as bar:
        try:
            # run the analysis
            results = opcore.perform_analysis(args.source_code,
                                              obf_configs,
                                              args.runs,
                                              args.warmup,
                                              args.optimization_level,
                                              lambda: bar())
        except OSError as e:
            # error while reading the source code
            error(f"Error: cannot read '{e.filename}'",
                  ExitCode.SOURCE_CODE_NOT_FOUND)
            assert False    # unreachable (for pyright)

        except subprocess.CalledProcessError as e:
            # error while running the analysis
            error(f"Error: an error happened while running the analysis\n"
                  f"{e}\n"
                  f"{e.stderr.decode('utf-8')}",
                  ExitCode.RUNTIME_ERROR)
            assert False    # unreachable (for pyright)

    # print the results in the specified format
    print_results(results, args.format)

    # plot the results
    if args.plot:
        plot_results(results, args.output_dir)


def validate_args(args: argparse.Namespace) -> List[str]:
    """Validates the command line arguments and extracts the
    obfuscation config paths.

    Args:
        args: The command line arguments.

    Returns:
        A list of obfuscation config paths extracted from the command line
        arguments.
    """

    # at least one run
    if args.runs <= 0:
        error(f"Error: the parameter `runs` must be >= 1",
              ExitCode.INVALID_CLI_PARAM)

    # no negative warmup value
    if args.warmup < 0:
        error(f"Error: the parameter `warmup` must be >= 0",
              ExitCode.INVALID_CLI_PARAM)

    # check source code file exists
    if not os.path.isfile(args.source_code):
        error(f"Error: '{args.source_code}' is not a file",
              ExitCode.SOURCE_CODE_NOT_FOUND)

    # check obfuscation configs exist and are valid
    # valid configs are either a single directory or a sequence of files
    # if a single directory is specified, all files in the directory are used
    # as obfuscation configs
    # if a sequence of files is specified, each file is used as an obfuscation
    # config

    if len(args.obf_configs) == 1 and os.path.isdir(args.obf_configs[0]):
        # user specified a single directory
        # use all files in the directory as obfuscation configs

        # get filenames in dir
        filenames = next(os.walk(args.obf_configs[0]), (None, None, []))[2]
        # sort filenames
        filenames.sort()
        # path to each file
        paths = map(lambda name: os.path.join(args.obf_configs[0], name),
                    filenames)
        # add paths to list
        obf_config_path_list = list(paths)

    else:
        # len(args.obf_configs) > 1 or args.obf_configs[0] is not a dir
        # user specified a sequence of files (no one can be a dir)
        # use each file as an obfuscation config

        obf_config_path_list = []

        # for each specified path
        for path in args.obf_configs:
            # verify it is a file (not a dir and exists)
            if not os.path.isfile(path):
                error(f"Error: 'obf_configs' argument must be a"
                       " single directory or a sequence of files",
                      ExitCode.OBF_CONFIGS_NOT_FOUND)
            # add path to list
            obf_config_path_list.append(path)

        # remove duplicates preserving the order
        obf_config_path_list = list(dict.fromkeys(obf_config_path_list))

    return obf_config_path_list


def print_results(results: rc.ResultContainer, format: str) -> None:
    """Prints the results to stdout in the specified format.

    Args:
        results: Results to print.
        format: Format to use. Valid values are "table", "table2" and "json".
    """

    # print results using the specified format
    if format == "table":
        # table
        print_results_table(results)
    elif format == "table2":
        # transposed table
        print_results_table(results, transposed=True)
    elif format == "json":
        # json
        print(results.to_json())
    else:
        # should not happen thanks to argparse
        error(f"Error: invalid output format '{format}'",
              ExitCode.INVALID_CLI_PARAM)


def print_results_table(results: rc.ResultContainer,
                        transposed: bool = False) -> None:
    """Prints the results to stdout in a table format.

    Args:
        results: Results to print.
        transposed: Whether to transpose the table.
    """

    def mean_stdev_str(mean: Union[int,float], stdev: Union[int,float]) -> str:
        """Returns a string containing the given mean and standard deviation
        values, with the plus/minus symbol.

        Args:
            mean: Mean value.
            stdev: Standard deviation value.

        Returns:
            A string containing the given mean and standard deviation values,
            with the plus/minus symbol.
        """

        # convert to float
        mean = float(mean)
        stdev = float(stdev)
        # TODO maybe dynamic number instead of fixed 10
        # mean plus/minus stdev
        return f"{mean:10.3f} \xb1 {stdev:7.3f}"

    # TODO: maybe use a user configurable config file
    # metrics to print
    # list of tuples (metric name, metric key)
    METRICS_TO_PRINT = [
        ("Time (s)", "execution_wall_time"),
        ("Memory (KB)", "execution_memory"),
        ("Page faults", "execution_total_page_faults"),
        ("Context switches", "execution_total_context_switches"),
        ("Obfuscation time (s)", "obfuscation_wall_time"),
        ("Compilation time (s)", "compile_wall_time"),
        ("Lines of code", "lines_of_code"),
        ("Source code size (KB)", "source_code_size"),
        ("Executable size (KB)", "executable_size"),
        ("Norm compression dist", "norm_compression_distance"),
        ("Halstead difficulty", "halstead_difficulty")
    ]

    # get average (stdev) results
    avg_results, std_results = results.get_average_results()

    # build table
    table = PrettyTable()
    # add first column: metric name
    table.add_column("Name",
                     [ metric_name for metric_name, _ in METRICS_TO_PRINT ])

    # add a column for all the obfuscation types
    for obf_name in avg_results:
        curr_avg_result = avg_results[obf_name]
        curr_std_result = std_results[obf_name]
        # build column
        column = [ mean_stdev_str(curr_avg_result[field_name], # type: ignore
                                  curr_std_result[field_name]) # type: ignore
                   for _, field_name in METRICS_TO_PRINT ]
        table.add_column(obf_name, column)

    # transpose table if requested
    table = transpose_table(table) if transposed else table

    # print table
    print_table_split(table)


# print the table split in subtables to fit the terminal width
def print_table_split(table: PrettyTable) -> None:
    """Prints the table split in subtables to fit the terminal width.

    Args:
        table: Table to print.
    """
    # directly print the table if we are not in a terminal
    if not sys.stdout.isatty():
        print(table)
        return

    # get terminal width
    terminal_width = os.get_terminal_size().columns
    # get table string
    table_str = table.get_string()
    # get table width
    table_width = len(table_str.splitlines()[0])
    # get the length of the "name" column
    name_column_width = len(table.get_string(fields=["Name"]).splitlines()[0])

    # repeat until the table fits in the terminal
    # and in the meanwhile print the subtables
    while table_width > terminal_width:
        # get the length of each column
        column_widths = [ len(table.get_string(fields=[column_name]).splitlines()[0])
                          for column_name in table.field_names[1:] ]
        # get the cumulative length of the columns
        cumulative_column_widths = list(itertools.accumulate(column_widths, initial=name_column_width))
        # get the index of the first column that exceeds the terminal width
        first_column_to_hide = next((i
                                     for i, cum_width in enumerate(cumulative_column_widths)
                                     if cum_width > terminal_width),
                                    len(column_widths))
        # names of the columns to show
        columns_to_show = list(table.field_names[1:first_column_to_hide])
        # print columns
        print(table.get_string(fields=["Name"] + columns_to_show))
        # remove columns
        for column_name in columns_to_show:
            table.del_column(column_name)
        # update table width
        table_width = len(table.get_string().splitlines()[0])

    # print the remaining columns
    print(table.get_string())


# transpose the PrettyTable table
def transpose_table(table: PrettyTable) -> PrettyTable:
    """Transposes the given PrettyTable table.

    Args:
        table: Table to transpose.

    Returns:
        The transposed table.
    """

    # new table
    new_table = PrettyTable()
    # get the field names (first column in the given table)
    fields = table.get_string(fields=["Name"], border=False).splitlines()
    # strip withespace from the field names
    fields = [ field.strip() for field in fields ]

    # set the field names in the new table
    new_table.field_names = fields

    # get the column names (first row in the given table)
    # excluding the first column ("names")
    column_names = table.field_names[1:]

    # add each column as a row
    for column_name in column_names:
        lines = table.get_string(fields=[column_name], border=False) \
                     .splitlines()
        # strip "withespaces" from the lines
        lines = [ line[1:len(line)-1] for line in lines ]
        new_table.add_row(lines)

    return new_table


def print_results_json(results: rc.ResultContainer) -> None:
    """Prints the results in JSON format."""

    print(results.to_json())


def plot_results(results: rc.ResultContainer, output_dir: str) -> None:
    """Plots the results and saves the plots in the output directory.

    Args:
        results: Results to plot.
        output_dir: Output directory where to save the plots.
            The directory will be created if it does not exist.
    """

    # create the output directory (mkdir -p)
    os.makedirs(output_dir, exist_ok=True)

    # list of (metric_name, measurement_unit, metric_key)
    # to plot using a violin plot
    violin_plot_metrics = [ ("Execution time", "s", "execution_wall_time"),
                            ("Execution memory", "KB", "execution_memory"),
                            ("Obfuscation time", "s", "obfuscation_wall_time"),
                            ("Compilation time", "s", "compile_wall_time") ]

    # violin plots
    for metric_name, unit, metric_key in violin_plot_metrics:
        # get the data dictionary
        data_dict = results.metric_results(metric_key)
        # produce the violin plot and save it
        plots.violin_plot_with_avg(data_dict,
                                   f"{metric_name} by obfuscation type",
                                   f"{metric_name} ({unit})",
                                   os.path.join(output_dir,
                                                f"{metric_key}.png"))

    # bar plots to produce
    # list[(title,y_label,filename,list[(metric_name, metric_key)])]
    grouped_bar_plot_configs = [
        ("Execution time by obfuscation type",
         "Average time (s)",
         "execution_time",
         [ ("Wall time", "execution_wall_time"),
           ("User time", "execution_user_time"),
           ("System time", "execution_system_time") ]),
        ("Execution memory and page faults by obfuscation type",
         "Average memory (KB) or page faults",
         "execution_memory_and_page_faults",
         [ ("Memory", "execution_memory"),
           ("Page faults", "execution_total_page_faults") ]),
        ("Source code size and executable size by obfuscation type",
         "Average size (KB)",
         "source_code_size_and_executable_size",
         [ ("Source code size", "source_code_size"),
           ("Executable size", "executable_size") ]),
    ]

    # grouped bar plots
    for title, y_label, filename_prefix, metrics in grouped_bar_plot_configs:
        # extract the metric result data dictionaries
        data_dicts = { metric_key: results.metric_results(metric_key)
                       for _, metric_key in metrics }
        # build data dictionary for the grouped bar plot
        data_dict_by_group = dict()
        # for each obfuscation type
        for obf_type in results.obfuscation_types():
            # build a dictionary with the data
            # inner_dict = dict()
            # for metric_name, metric_key in metrics:
            #     inner_dict[metric_name] = data_dicts[metric_key][obf_type]
            inner_dict = { metric_name: data_dicts[metric_key][obf_type]
                           for metric_name, metric_key in metrics }
            data_dict_by_group[obf_type] = inner_dict

        # produce the grouped bar plot and save it
        plots.grouped_bar_plot(data_dict_by_group,
                               title,
                               y_label,
                               os.path.join(output_dir,
                                            f"{filename_prefix}.png"))


def error(message: str, exit_code: ExitCode) -> None:
    """Prints an error message and exits with the given exit code.

    The message is printed to stderr.

    Args:
        message: The error message to print.
        exit_code: The exit code to use.
    """

    print(message, file=sys.stderr)
    sys.exit(exit_code.value)


import time
def interrupt_handler(signum: int, frame) -> None:
    """Handler for the SIGINT signal (CTRL-C).

    Args:
        signum: Signal number.
        frame: Current stack frame.
    """

    # print a message and exit
    print("CTRL-C: exiting...", file=sys.stderr)
    sys.exit(0)


def parse_args() -> argparse.Namespace:
    """Defines the argparse parser for the cli arguments, parses them and
    returns the parsed arguments.

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

    # add a format argument to specify the output format (table, table2, json)
    parser.add_argument(
        "-f",
        "--format",
        default="table",
        choices=["table", "table2", "json"],
        help="output format, default table"
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

    parser.add_argument(
        "-w",
        "--warmup",
        type=int,
        default=0,
        help="number of times the program is run before performing"
             " the actual analysis, default 0"
    )

    parser.add_argument(
        "-O",
        "--optimization-level",
        type=int,
        default=3,
        choices=[ 0, 1, 2, 3 ],
        help="compiler optimization level, 0: no optimization,"
             " 3: maximum optimization, default 3"
    )

    # parse arguments
    return parser.parse_args()
