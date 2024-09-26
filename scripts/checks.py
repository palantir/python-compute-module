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


import subprocess

SOURCE_DIR = "compute_modules"
TESTS_DIR = "tests"


def test() -> None:
    subprocess.run(["pytest", TESTS_DIR])


def check_format() -> None:
    subprocess.run(["black", "--check", "--diff", SOURCE_DIR, TESTS_DIR])
    subprocess.run(["ruff", "check", SOURCE_DIR, TESTS_DIR])
    subprocess.run(["isort", "--check", "--diff", SOURCE_DIR, TESTS_DIR])


def check_mypy() -> None:
    subprocess.run(["mypy", SOURCE_DIR, TESTS_DIR])


def format() -> None:
    subprocess.run(["black", SOURCE_DIR, TESTS_DIR])
    subprocess.run(["ruff", "--fix", SOURCE_DIR, TESTS_DIR])
    subprocess.run(["isort", SOURCE_DIR, TESTS_DIR])
