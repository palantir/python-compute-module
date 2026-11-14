#  Copyright 2026 Palantir Technologies, Inc.
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

import ast
import re
from pathlib import Path

import pytest

README = Path(__file__).resolve().parents[1] / "README.md"
PYTHON_EXAMPLES = re.findall(r"```python\n(.*?)```", README.read_text(encoding="utf-8"), re.DOTALL)


@pytest.mark.parametrize("example", PYTHON_EXAMPLES, ids=[f"example-{i + 1}" for i in range(len(PYTHON_EXAMPLES))])
def test_readme_python_examples_have_valid_syntax(example: str) -> None:
    ast.parse(example)


def test_readme_contains_python_examples() -> None:
    assert PYTHON_EXAMPLES
