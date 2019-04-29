"""
Example showing how to use the capture feature.
"""

import sys
import csv

from i2cdriver import I2CDriver, START, STOP

msg = """
Now capturing traffic to
    standard output (human-readable)
    log.csv
Hit CTRL-C to leave capture mode
"""

if __name__ == '__main__':
    i2 = I2CDriver(sys.argv[1])

    c = i2.capture_start()

    sys.stderr.write(msg)

    f = sys.stdout
    with open('log.csv', 'w') as csvfile:
        logcsv = csv.writer(csvfile)
        try:
            for token in c():
                print(repr(token))          # Human readable to standard output
                token.dump(logcsv, "csv")   # write to CSV
        except KeyboardInterrupt:
            print("\nCapture finished")
    i2.capture_stop()
