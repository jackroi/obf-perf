import os
import bz2
import sys
import json
import subprocess


def file_size(path):
    return os.path.getsize(path)

def line_count(path):
    with open(path) as f:
        num_lines = sum(1 for _ in f)
    return num_lines


# TODO: decide if own file
def normalized_compression_distance(orig_path, obf_path):
    # see http://phrack.org/issues/68/15.html
    # The formula returns a value from returns a value from 0.0 (maximally similar)
    # to 1.0 (maximally dissimilar).

    # TODO handle error?
    with open(orig_path, 'rb') as orig, open(obf_path, 'rb') as obf:
        bytesX, bytesY = orig.read(), obf.read()

    ncBytesXY = len(bz2.compress(bytesX + bytesY))
    ncBytesX = len(bz2.compress(bytesX))
    ncBytesY = len(bz2.compress(bytesY))

    ncd = float(ncBytesXY - min(ncBytesX, ncBytesY)) / max(ncBytesX, ncBytesY)

    # TODO: capire se utile e in caso ritornare
    # kc = ncBytesY - ncBytesX
    # print("ΔK: " + str(kc))

    return ncd

# compute Halstead difficulty metric
def halstead_difficulty(orig_path: str, obf_path: str):
    # TODO: handle errors

    # extract function names
    CTAGS_CALL = [ "ctags", "-x", "--c-kinds=f", orig_path ]
    ctags_output = subprocess.run(CTAGS_CALL, check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    ctags_output = ctags_output.stdout.decode("utf-8")
    ctags_output_lines = ctags_output.splitlines()
    functions = [ line.split()[0] for line in ctags_output_lines ]

    difficulty = 0.0
    # run tigress metric tool, for each function, without printing output
    for function in functions:
        TIGRESS_CALL = [ "tigress",
                         "--Environment=x86_64:Linux:Gcc:4.6",
                         "--Transform=SoftwareMetrics",
                         f"--Functions={function}",
                         "--SoftwareMetricsKind=halstead",
                         "--SoftwareMetricsJsonFileName=metrics.json",
                         "--out=temp-metrics.c",
                         obf_path ]

        output = subprocess.run(TIGRESS_CALL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        stderr = output.stderr.decode("utf-8")
        if output.returncode != 0:
            print("tigress failed", file=sys.stderr)
            print("call", TIGRESS_CALL, file=sys.stderr)
            print(stderr, file=sys.stderr)
            raise RuntimeError("tigress failed")


        # read json file
        with open("metrics.json") as f:
            metrics = json.load(f)

        # compute difficulty
        difficulty += metrics[0]["difficulty"]

    return difficulty
