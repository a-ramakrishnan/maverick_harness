from collections.abc import Callable

from maverick_harness.tools.files import (
    edit_file,
    glob_files,
    grep_search,
    read_file,
    write_file,
)
from maverick_harness.tools.shell import run_bash

READ_ONLY_TOOLS: list[Callable] = [
    read_file,
    glob_files,
    grep_search,
]

ALL_TOOLS: list[Callable] = [
    *READ_ONLY_TOOLS,
    write_file,
    edit_file,
    run_bash,
]


def get_tools(*, read_only: bool = False) -> list[Callable]:
  
    return list(READ_ONLY_TOOLS if read_only else ALL_TOOLS)