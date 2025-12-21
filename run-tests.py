from pathlib import Path
import sys
import unittest


## Set path to include stanford/green:
# Add parent directory as a search path.
# 1. Path to the current script
current_file = Path(__file__).resolve()

# 2. Parent directory of the script
parent_dir = current_file.parent.parent

# 3. Add parent_dir to search path
sys.path.append(str(parent_dir))

#################################################################
start_dir = parent_dir
start_dir = '.'

## Discover tests in all subdirectories with filenames starting with "test"
loader = unittest.TestLoader()
suite = loader.discover(start_dir=start_dir, pattern='tests*.py')

runner = unittest.TextTestRunner()
runner.run(suite)

