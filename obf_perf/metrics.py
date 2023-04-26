"""Metrics for obfuscation evaluation.

This module contains functions to compute metrics for obfuscation evaluation.
The metrics are:
    - file size
    - line count
    - normalized compression distance
    - Halstead difficulty metric

Typical usage example:
    import metrics

    orig_path = "original.c"
    obf_path = "obfuscated.c"

    obf_size = metrics.file_size(obf_path)
    obf_line_count = metrics.line_count(obf_path)
    ncd = metrics.normalized_compression_distance(orig_path, obf_path)
    halstead_difficulty = metrics.halstead_difficulty(orig_path, obf_path)
"""


import os
import bz2
import json
import subprocess


def file_size(path: str) -> int:
    """Returns the size of the file at the given path in bytes.

    Args:
        path: Path of the file to be measured.

    Returns:
        The size of the file in bytes.

    Raises:
        FileNotFoundError: If the file at the given path does not exist.
    """

    return os.path.getsize(path)


def line_count(path: str) -> int:
    """Returns the number of lines of the file at the given path.

    Args:
        path: Path of the file to be measured.

    Returns:
        The number of lines of the file.

    Raises:
        OSError: If the file at the given path cannot be read.
    """

    with open(path) as f:
        # count the number of lines in the file
        num_lines = sum(1 for _ in f)

    return num_lines


def normalized_compression_distance(orig_path: str, obf_path: str) -> float:
    """Returns the normalized compression distance between
    the two files at the given paths.

    The formula returns a value from from 0.0 (maximally similar)
    to 1.0 (maximally dissimilar).

    See http://phrack.org/issues/68/15.html

    Args:
        orig_path: Path of the original file.
        obf_path: Path of the obfuscated file.

    Returns:
        The normalized compression distance between the two files.

    Raises:
        OSError: If the file at the given path cannot be read.
    """

    # read files as bytes
    with open(orig_path, 'rb') as orig_f, open(obf_path, 'rb') as obf_f:
        bytes_orig = orig_f.read()
        bytes_obf = obf_f.read()

    # compute compressed sizes
    combined_compressed_size = len(bz2.compress(bytes_orig + bytes_obf))
    orig_compressed_size = len(bz2.compress(bytes_orig))
    obf_compressed_size = len(bz2.compress(bytes_obf))

    # compute normalized compression distance
    ncd = (combined_compressed_size \
          - min(orig_compressed_size, obf_compressed_size)) \
          / max(orig_compressed_size, obf_compressed_size)

    # clip to [0, 1] for floating point errors
    if ncd < 0.0:
        ncd = 0.0
    elif ncd > 1.0:
        ncd = 1.0

    return ncd


def halstead_difficulty(orig_path: str, obf_path: str) -> float:
    """Returns the Halstead difficulty metric of the obfuscated file.

    The Halstead difficulty metric is computed as the sum of the
    Halstead difficulty of some functions in the obfuscated file.
    In particular, the functions are the ones that were present in
    the original file, before obfuscation.
    This is done to keep the computation time reasonable.

    To compute the Halstead difficulty of a function, `tigress` is used.
    To extract the function names, `ctags` is used.

    See https://en.wikipedia.org/wiki/Halstead_complexity_measures

    Args:
        orig_path: Path of the original file.
        obf_path: Path of the obfuscated file.

    Returns:
        The Halstead difficulty metric of the obfuscated file.

    Raises:
        OSError: If the file at the given path cannot be read.
        CalledProcessError: If `ctags` or `tigress` fail.
    """

    # extract function names from original file using ctags
    ctags_call = [ "ctags", "-x", "--c-kinds=f", orig_path ]
    ctags = subprocess.run(ctags_call,
                           check=True,
                           text=True,
                           capture_output=True)

    # split output into lines
    ctags_output_lines = ctags.stdout.splitlines()
    # function names are the first word of each line
    functions = [ line.split()[0] for line in ctags_output_lines ]

    # compute difficulty
    difficulty = 0.0
    # for each function in the original file
    for function in functions:
        # compute difficulty of function using tigress
        tigress_call = [ "tigress",
                         "--Environment=x86_64:Linux:Gcc:4.6",
                         "--Transform=SoftwareMetrics",
                         f"--Functions={function}",
                         "--SoftwareMetricsKind=halstead",
                         "--SoftwareMetricsJsonFileName=metrics.json",
                         "--out=temp-metrics.c",
                         obf_path ]
        subprocess.run(tigress_call,
                       check=True,
                       text=True,
                       capture_output=True)

        # read json file containing Halstead metrics
        with open("metrics.json") as f:
            metrics = json.load(f)

        # add difficulty of function to total difficulty
        difficulty += metrics[0]["difficulty"]

    return difficulty
