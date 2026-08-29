"""
Example showing how to use the capture feature.

Console output is a compact, colorized, streaming, xxd-flavored view:
one line per bus transaction, printed as soon as it closes.
"""

import sys
import csv

from i2cdriver import I2CDriver, START, STOP, BYTE

msg = """
Now capturing traffic to
    standard output (human-readable)
    log.csv
Hit CTRL-C to leave capture mode
"""

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
LGREEN = "\033[1;92m"
YELLOW = "\033[33m"
LYELLOW = "\033[1;93m"

# xxd -R's byte->color mapping, applied here to the ascii column: 0x00 white,
# printable green, tab/lf/cr yellow, other non-printable red, 0xff blue.
# All bold there too, as far as I could tell from xxd's changelog/docs (bold
# itself wasn't explicitly confirmed in what I found, just the color choice).
A_WHITE = "\033[1;37m"
A_GREEN = "\033[1;32m"
A_YELLOW = "\033[1;33m"
A_RED = "\033[1;31m"
A_BLUE = "\033[1;34m"

COLOR = sys.stdout.isatty()


def colorize(code, s):
    return f"{code}{s}{RESET}" if COLOR else s


def fmt_start(tok):
    addr = "[%s:%02x" % ("R" if tok.rw else "W", tok.addr)
    return colorize(RED, addr) if not tok.ack else colorize(BOLD, addr)


def fmt_byte(tok):
    hexval = "%02x" % tok.b
    if tok.rw:
        color = LGREEN if tok.ack else GREEN
    else:
        color = LYELLOW if tok.ack else YELLOW
    return colorize(color, hexval)


def ascii_color(b):
    if b == 0:
        return A_WHITE
    if b == 0xff:
        return A_BLUE
    if b in (9, 10, 13):
        return A_YELLOW
    if 32 <= b < 127:
        return A_GREEN
    return A_RED


def ascii_repr(raw):
    return "".join(
        colorize(ascii_color(b), chr(b) if 32 <= b < 127 else ".")
        for b in raw
    )


ROW_WIDTH = 16


class TransactionFormatter:
    """Turns a stream of START/BYTE/STOP tokens into xxd-style output,
    wrapped at ROW_WIDTH bytes per line, fed one token at a time so
    output can be printed as it arrives.

    The first row of a transaction is led by '[W:ab'/'[R:ab'; wrapped
    continuation rows are indented to align under the same column. A
    real STOP closes the final row with a plain ']'. A repeated START
    (no intervening STOP) or a capture abort mid-transaction closes the
    pending row with a red ']' instead, flagging the missing STOP.
    """

    def __init__(self):
        self._open = False
        self._first_row = True
        self._prefix = ""
        self._indent = ""
        self._row = []
        self._raw = []

    def feed(self, tok):
        """Feed one token. Returns a formatted line if one just closed,
        else None."""
        if isinstance(tok, START):
            out = self._emit(colorize(RED, "]")) if self._open else None
            plain_addr = "[%s:%02x" % ("R" if tok.rw else "W", tok.addr)
            self._prefix = fmt_start(tok)
            self._indent = " " * (len(plain_addr) + 1)
            self._first_row = True
            self._open = True
            self._row = []
            self._raw = []
            return out
        elif isinstance(tok, BYTE):
            self._row.append(fmt_byte(tok))
            self._raw.append(tok.b)
            if len(self._row) == ROW_WIDTH:
                return self._emit(None)
            return None
        elif isinstance(tok, STOP):
            if not self._open:
                return None
            self._open = False
            if not self._row and not self._first_row:
                return None  # data ended exactly on a row boundary
            return self._emit("]")

    def flush(self):
        """Force-close a pending row (e.g. on capture abort)."""
        if not self._open:
            return None
        self._open = False
        if not self._row and not self._first_row:
            return None
        return self._emit(colorize(RED, "]"))

    def _emit(self, closer):
        lead = self._prefix if self._first_row else self._indent
        n = len(self._row)
        if self._row:
            sep = " " if self._first_row else ""
            lead += sep + " ".join(self._row)
        if self._raw:
            max_hex_width = ROW_WIDTH * 3 - 1
            visible_hex_width = (n * 3 - 1) if n else 0
            lead += " " * (max_hex_width - visible_hex_width)
            lead += closer if closer else " "  # 1-char closer slot, always present
            lead += "  " + ascii_repr(self._raw)
        elif closer:
            lead += closer
        self._row = []
        self._raw = []
        self._first_row = False
        return lead


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage: capture.py <device> [speed]")
        exit(1)

    speed = int(sys.argv[2]) if len(sys.argv) > 2 else 400

    i2 = I2CDriver(sys.argv[1], reset="never")
    i2.setspeed(speed)

    cap = i2.capture_start()

    sys.stderr.write(msg)

    fmt = TransactionFormatter()

    with open('log.csv', 'w') as csvfile:
        logcsv = csv.writer(csvfile)
        try:
            for token in cap():
                token.dump(logcsv, "csv")
                csvfile.flush()
                line = fmt.feed(token)
                if line is not None:
                    print(line, flush=True)
        except KeyboardInterrupt:
            line = fmt.flush()
            if line is not None:
                print(line, flush=True)
            print("\nCapture finished")
    i2.capture_stop()
