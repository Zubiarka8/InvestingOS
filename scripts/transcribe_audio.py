"""Run the shared transcribe command."""
import sys
from _import_entry import dispatch

if __name__ == "__main__":
    dispatch("transcribe", sys.argv[1:])
