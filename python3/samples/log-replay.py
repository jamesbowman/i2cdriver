"""
Replay a capture.py log.csv through the same colorized, xxd-flavored
formatter used for live captures.
"""

import sys
import csv

from i2cdriver import START, STOP, BYTE
from capture import TransactionFormatter


def load(path):
    with open(path, newline='') as f:
        for row in csv.reader(f):
            if not row:
                continue
            kind, rw, val, ack = row
            if kind == "START":
                yield START(int(val), rw == "READ", ack == "ACK")
            elif kind == "BYTE":
                yield BYTE(int(val), rw == "READ", ack == "ACK")
            elif kind == "STOP":
                yield STOP()
            else:
                assert False, f"unknown row kind: {kind!r}"


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} log.csv")

    fmt = TransactionFormatter()
    for tok in load(sys.argv[1]):
        line = fmt.feed(tok)
        if line is not None:
            print(line)
    line = fmt.flush()
    if line is not None:
        print(line)
