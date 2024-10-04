#  Copyright 2024 Palantir Technologies, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import shutil
import subprocess
import sys
from itertools import chain
from os import unlink
from pathlib import Path
from typing import Iterator, List, Tuple

SOURCE_DIR = "compute_modules"
TESTS_DIR = "tests"
SCRIPTS_DIR = "scripts"
LICENSE_FILE = "LICENSE"
FILES_WITH_LICENSE_NEEDED_GLOB_EXPR = "*.py"


def test() -> None:
    """Runs pytest on all tests in the tests/ directory"""
    result = subprocess.run(["pytest", TESTS_DIR])
    sys.exit(result.returncode)


def check_format() -> None:
    """Runs linter 'checks'. Raises exception if any linting exceptions exist"""
    black_result = subprocess.run(["black", "--check", "--diff", SOURCE_DIR, TESTS_DIR, SCRIPTS_DIR])
    ruff_result = subprocess.run(["ruff", "check", SOURCE_DIR, TESTS_DIR, SCRIPTS_DIR])
    isort_result = subprocess.run(["isort", "--check", "--diff", SOURCE_DIR, TESTS_DIR, SCRIPTS_DIR])
    exit_code = 1 if black_result.returncode or ruff_result.returncode or isort_result.returncode else 0
    sys.exit(exit_code)


def check_mypy() -> None:
    """Runs mypy checks. Raises exception if any mypy exceptions exist"""
    result = subprocess.run(["mypy", SOURCE_DIR, TESTS_DIR, SCRIPTS_DIR])
    sys.exit(result.returncode)


def format() -> None:
    """Formats all files to fix any linter issues that can be automatically fixed"""
    subprocess.run(["black", SOURCE_DIR, TESTS_DIR, SCRIPTS_DIR])
    subprocess.run(["ruff", "--fix", SOURCE_DIR, TESTS_DIR, SCRIPTS_DIR])
    subprocess.run(["isort", SOURCE_DIR, TESTS_DIR, SCRIPTS_DIR])


def _get_license_content() -> Tuple[str, int]:
    with open(LICENSE_FILE, "r") as f:
        lines = []
        for line in f.readlines():
            # Empty lines should not have whitespace appended
            if line == "\n":
                lines.append("#\n")
            else:
                lines.append(f"#  {line}")
        content = "".join(lines)
    return content, len(lines)


def _get_n_lines_of_file(filename: str, num_lines: int) -> str:
    with open(filename, "r") as f:
        head = [next(f) for _ in range(num_lines)]
    return "".join(head)


def _iterate_licensed_files(num_lines: int) -> Iterator[Tuple[str, str]]:
    source_files = list(Path(SOURCE_DIR).rglob(FILES_WITH_LICENSE_NEEDED_GLOB_EXPR))
    test_files = list(Path(TESTS_DIR).rglob(FILES_WITH_LICENSE_NEEDED_GLOB_EXPR))
    script_files = list(Path(SCRIPTS_DIR).rglob(FILES_WITH_LICENSE_NEEDED_GLOB_EXPR))
    for path in chain(source_files, test_files, script_files):
        filename = str(path)
        file_head = _get_n_lines_of_file(filename=filename, num_lines=num_lines)
        yield filename, file_head


def _get_files_list_str(files_list: List[str]) -> str:
    return "\n".join([f"\t{filename}" for filename in files_list])


def check_license() -> None:
    """Raises an exception if there are any files with no license present at the top of the file"""
    expected_license_content, num_lines = _get_license_content()
    failed_files = []
    for filename, file_head in _iterate_licensed_files(num_lines=num_lines):
        if not file_head.startswith(expected_license_content):
            failed_files.append(filename)
    if failed_files:
        print(
            "Some files did not have the license header included!\n\n"
            + _get_files_list_str(failed_files)
            + "\n\nRun `poetry run license` and commit to fix the issue"
        )
    else:
        print(f"All {FILES_WITH_LICENSE_NEEDED_GLOB_EXPR} have license header")
    sys.exit(len(failed_files))


def _add_license_to_file(filepath: str, license_content: str) -> None:
    """Adds license header to top of a file"""
    with open(filepath, "r") as old:
        unlink(filepath)
        with open(filepath, "w") as new:
            new.write(license_content + "\n\n\n")
            shutil.copyfileobj(old, new)


def license() -> None:
    """Adds license header to any files that are missing it"""
    expected_license_content, num_lines = _get_license_content()
    updated_files = []
    for filename, file_head in _iterate_licensed_files(num_lines=num_lines):
        if not file_head.startswith(expected_license_content):
            _add_license_to_file(filepath=filename, license_content=expected_license_content)
            updated_files.append(filename)
    if updated_files:
        print(f"Added license to the following files:\n\n{_get_files_list_str(updated_files)}")
    else:
        print(f"All {FILES_WITH_LICENSE_NEEDED_GLOB_EXPR} have license header")
