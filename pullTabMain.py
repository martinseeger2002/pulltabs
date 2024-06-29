import subprocess
import time
import itertools
import sys

# List of scripts to run in sequence
scripts = [
    "TXlistnerRPCmod.py",
    "send_tabsMod.py",
    "tabCheckerMod.py",
    "sendReturnedMod.py"
]

spinner = itertools.cycle(['|', '/', '-', '\\'])

while True:
    for script in scripts:
        try:
            result = subprocess.run(["python", "-Xfrozen_modules=off", script], check=True)
        except subprocess.CalledProcessError as e:
            pass  # Ignore errors, continue with the loop
        for _ in range(10):  # Adjust this range to control how long the spinner shows
            sys.stdout.write(next(spinner))  # Write the next character
            sys.stdout.flush()  # Flush the output
            time.sleep(0.1)  # Wait a little bit
            sys.stdout.write('\b')  # Erase the last character written
