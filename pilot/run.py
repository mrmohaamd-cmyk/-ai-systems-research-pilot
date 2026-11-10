"""Version 0.2 command entry point; see README for the frozen-run interface."""
import sys
from .core import main

if __name__ == "__main__":
    main(["run"] + sys.argv[1:])
