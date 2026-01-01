import argparse
import logging
import sys
import unittest

from pathlib import Path

# Set log-level
logging.basicConfig(level=logging.INFO)
#logging.basicConfig(level=logging.DEBUG)

## Set path to include stanford/green:
# Add parent directory as a search path.
# 1. Path to the current script
current_file = Path(__file__).resolve()

# 2. Parent directory of the script
parent_dir = current_file.parent.parent

# 3. Add parent_dir to search path
sys.path.append(str(parent_dir))

#################################################################
def run_tests(start_dir: str):

    ## Discover tests in all subdirectories with filenames starting with "test"
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=start_dir, pattern='tests*.py')

    runner = unittest.TextTestRunner()
    runner.run(suite)


parser = argparse.ArgumentParser(description="Process the start directory.")
parser.add_argument(
    '--start-dir',
    default='.',
    help='The directory to start with (default: current directory)'
)
args = parser.parse_args()

run_tests(args.start_dir)
