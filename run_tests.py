#!/usr/bin/env python3
"""
Main test runner for the XKCD comic finder project.

This script runs pytest with appropriate options, providing a convenient
way to run the entire test suite with coverage reporting.
"""
import sys
import os
import subprocess
import argparse
import tempfile

def main():
    """Run the test suite with appropriate options."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run XKCD Comic Finder tests')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Increase output verbosity')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Decrease output verbosity')
    parser.add_argument('--no-coverage', action='store_true',
                        help='Disable coverage reporting')
    parser.add_argument('-m', '--marker', type=str,
                        help='Only run tests with specific marker (parse, storage, error)')
    parser.add_argument('--save-coverage', action='store_true',
                        help='Save coverage report to permanent location (test_output/coverage_html)')

    args = parser.parse_args()

    # Build pytest command
    cmd = ['pytest']

    # Add verbosity
    if args.verbose:
        cmd.append('-vv')
    elif args.quiet:
        cmd.append('-q')
    else:
        cmd.append('-v')

    # Add marker if specified
    if args.marker:
        cmd.append(f'-m {args.marker}')

    # Add coverage if not disabled
    if not args.no_coverage:
        cmd.append('--cov=src')
        cmd.append('--cov-report=term')

        # Use temp directory for coverage reports unless --save-coverage is specified
        if args.save_coverage:
            html_dir = os.path.join('test_output', 'coverage_html')
            os.makedirs(html_dir, exist_ok=True)
            cmd.append(f'--cov-report=html:{html_dir}')
        else:
            # Create temporary directory for coverage reports
            temp_dir = tempfile.mkdtemp(prefix='xkcd_coverage_')
            cmd.append(f'--cov-report=html:{temp_dir}')
            print(f"Coverage report will be generated in temporary directory: {temp_dir}")
            print("This directory will be deleted when the process exits.")

    # Print the command being run
    print(f"Running: {' '.join(cmd)}")

    # Execute pytest
    result = subprocess.run(' '.join(cmd), shell=True)

    # Return non-zero exit code if tests failed
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()