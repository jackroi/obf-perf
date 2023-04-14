import os
import bz2


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