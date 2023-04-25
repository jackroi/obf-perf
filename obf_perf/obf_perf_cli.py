"""obf-perf command line interface.

TODO

Usage:

    TODO
"""


import argparse
import os
import sys
import enum
import itertools
from dataclasses import asdict

from prettytable import PrettyTable
from alive_progress import alive_bar

import obf_perf.obf_perf_core as opcore
import obf_perf.plots as plots


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
    INVALID_CLI_PARAM = 3


# TODO: remove
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


def main():
    """Main: TODO."""

    # parse cli arguments using argparse
    args = parse_args()


    # TODO: maybe verbose mode

    if args.runs <= 0:
        error(f"Error: the parameter `runs` must be >= 1",
              ExitCode.INVALID_CLI_PARAM)

    if args.warmup < 0:
        error(f"Error: the parameter `warmup` must be >= 0",
              ExitCode.INVALID_CLI_PARAM)

    # check source code file exists
    if not os.path.isfile(args.source_code):
        error(f"Error: '{args.source_code}' is not a file",
              ExitCode.SOURCE_CODE_NOT_FOUND)

    # check obfuscation configs exists
    obf_config_path_list = []

    if len(args.obf_configs) == 1 and os.path.isdir(args.obf_configs[0]):
        # get filenames in dir
        filenames = next(os.walk(args.obf_configs[0]), (None, None, []))[2]
        filenames.sort()
        obf_config_path_list.extend(
            map(lambda filename: os.path.join(args.obf_configs[0], filename),
                filenames)
        )

    else:
        # len(args.obf_configs) > 1 or args.obf_configs[0] is not a dir

        for path in args.obf_configs:
            if not os.path.isfile(path):
                error(f"Error: 'obf_configs' argument must be a"
                       " single directory or a sequence of files",
                      ExitCode.OBF_CONFIGS_NOT_FOUND)
            obf_config_path_list.append(path)

        # remove duplicates preserving the order
        obf_config_path_list = list(dict.fromkeys(obf_config_path_list))


    try:
        obf_configs = opcore.load_obfuscation_configs(obf_config_path_list)
    except FileNotFoundError as e:
        error(f"Error: cannot read '{e.filename}'",
              ExitCode.OBF_CONFIGS_NOT_FOUND)


    # TODO: count also normal (non obfuscated) execution
    bar_step_count = len(obf_configs) * (args.warmup + args.runs)
    with alive_bar(bar_step_count, file=sys.stderr) as bar:
        results = opcore.perform_analysis(args.source_code,
                                          obf_configs,
                                          args.runs,
                                          args.warmup,
                                          lambda: bar())

    # print results using the specified format
    if args.format == "table":
        print_results_table(results)
    elif args.format == "table2":
        print_results_table(results, transposed=True)
    elif args.format == "json":
        print(results.to_json())
    else:
        # should not happen thanks to argparse
        error(f"Error: invalid output format '{args.format}'",
              ExitCode.INVALID_CLI_PARAM)

    if args.plot:
        # create the output directory (mkdir -p)
        os.makedirs(args.output_dir, exist_ok=True)

        exec_time_data_dict = results.metric_results("execution_wall_time")
        plots.violin_plot_with_avg(exec_time_data_dict,
                                   "Execution time by obfuscation type",
                                   os.path.join(args.output_dir, "execution_time.png"))

        exec_time_data_dict = results.metric_results("execution_memory")
        plots.violin_plot_with_avg(exec_time_data_dict,
                          "Execution memory by obfuscation type",
                          os.path.join(args.output_dir, "execution_memory.png"))

    # TODO: maybe loading bar for each batch of runs

    # TODO: cli flag for result to json
    #results.to_json()

def print_results_table(results, transposed=False):
    def mean_stdev_str(mean, stdev):
        mean = float(mean)
        stdev = float(stdev)
        # TODO maybe dynamic number instead of fixed 10
        return f"{mean:10.3f} \xb1 {stdev:7.3f}"

    # TODO: maybe use a user configurable config file
    METRICS_TO_PRINT = [ ("Time (s)", "execution_wall_time"),
                         ("Memory (KB)", "execution_memory"),
                         ("Page faults", "execution_total_page_faults"),
                         ("Context switches", "execution_total_context_switches"),
                         ("Obfuscation time (s)", "obfuscation_wall_time"),
                         ("Compilation time (s)", "compile_wall_time"),
                         ("Lines of code", "lines_of_code"),
                         ("Source code size (B)", "source_code_size"),
                         ("Norm compression dist", "compression_metric"),
                         ("Halstead difficulty", "halstead_difficulty") ]

    avg_results, std_results = results.getAverageResults()

    table = PrettyTable()

    table.add_column("Name", [ metric_name for metric_name, _ in METRICS_TO_PRINT ])

    # TODO
    # for all the obfuscation types
    for obf_name in avg_results:
        curr_avg_result = avg_results[obf_name]
        curr_std_result = std_results[obf_name]
        # build column
        column = [ mean_stdev_str(curr_avg_result[field_name],
                                  curr_std_result[field_name])
                   for _, field_name in METRICS_TO_PRINT ]
        table.add_column(obf_name, column)

    table = transpose_table(table) if transposed else table

    print_table(table)


# print the table split in subtables to fit the terminal width
def print_table(table):
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
def transpose_table(table: PrettyTable):
    # new table
    new_table = PrettyTable()
    fields = table.get_string(fields=["Name"], border=False).splitlines()
    # strip withespace from the fields
    fields = [ field.strip() for field in fields ]

    new_table.field_names = fields

    # get the column names
    column_names = table.field_names[1:]

    # add each column as a row
    for column_name in column_names:
        lines = table.get_string(fields=[column_name], border=False).splitlines()
        # strip "withespace" from the lines
        lines = [ line[1:len(line)-1] for line in lines ]
        new_table.add_row(lines)

    return new_table


def print_results_json(results):
    print(results.to_json())


def error(message, exit_code: ExitCode):
    print(message, file=sys.stderr)
    sys.exit(exit_code.value)



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

    # parse arguments
    return parser.parse_args()
