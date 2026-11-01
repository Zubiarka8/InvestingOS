"""Run the shared search-youtube command."""
import sys
from _import_entry import dispatch

if __name__ == "__main__":
    dispatch("search-youtube", sys.argv[1:])
