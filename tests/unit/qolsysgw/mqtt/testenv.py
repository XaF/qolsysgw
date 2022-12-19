import os
import sys

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
FIXTURES_DIR = os.path.join(CURRENT_DIR, 'fixtures')

TESTS_DIR = os.path.normpath(CURRENT_DIR)
ROOT_DIR = (TESTS_DIR, '')
while ROOT_DIR[1] != 'tests':
    TESTS_DIR = ROOT_DIR[0]
    ROOT_DIR = os.path.split(ROOT_DIR[0])
ROOT_DIR = ROOT_DIR[0]

# Load environment needed for the tests
sys.path.append(os.path.join(TESTS_DIR, 'mock_modules'))

# Load the sources of the project
sys.path.append(os.path.join(ROOT_DIR, 'apps', 'qolsysgw'))
