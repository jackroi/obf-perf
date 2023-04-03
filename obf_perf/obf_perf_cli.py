"""obf-perf command line interface.

TODO

Usage:

    TODO
"""


import argparse


def main():
    """Main: TODO."""

    # parse cli arguments using argparse
    args = parse_args()

    print(args)


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
