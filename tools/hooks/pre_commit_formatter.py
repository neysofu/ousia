#!/usr/bin/env python

import os
import shutil
import subprocess
import sys

try:
    from yapf.yapflib.yapf_api import FormatFile
    YAPF = True
except ImportError:
    YAPF = False

PYTHON33 = sys.version_info >= (3, 3)
EXTENSIONS_CXX = (".c", ".h", ".cpp", ".cc", ".hpp")
EXTENSIONS_PY = (".py", )
EXTENSIONS = EXTENSIONS_CXX + EXTENSIONS_PY
NEEDS_FORMATTING = lambda x: x.endswith(EXTENSIONS)
HERE = os.path.realpath(__file__)
OUSIA_DIR = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
CLANG_FORMAT = "clang-format"


def print_formatting_notice(file_name):
    print("Formatting {}...".format(file_name))


def print_formatting_success(file_name):
    print("Formatting {} -- SUCCESS".format(file_name))


def print_formatting_fail(file_name):
    print("Formatting {} -- FAILED".format(file_name))


def format_python(file_name):
    if YAPF:
        print_formatting_notice(file_name)
        FormatFile(file_name, in_place=True)
        print_formatting_success(file_name)
    return YAPF


def format_cxx(file_name):
    # shutil.which is only available in Python 3.3+
    if PYTHON33 and shutil.which(CLANG_FORMAT) is not None or not PYTHON33:
        print_formatting_notice(file_name)
        try:
            subprocess.call([CLANG_FORMAT, "-i", file_name])
            print_formatting_success(file_name)
            return True
        except (subprocess.CalledProcessError, OSError,
                FileNotFoundError) as e:
            print_formatting_fail(file_name)
            return False


def format_sources(file_names):
    modified_file_names = []
    for file_name in file_names:
        if file_name.endswith(EXTENSIONS_CXX):
            success = format_cxx(file_name)
        elif file_name.endswith(EXTENSIONS_PY):
            success = format_python(file_name)
        if success:
            modified_file_names.append(file_name)
    return modified_file_names


def git_add_file_names(file_names):
    subprocess.check_output(
        ["git", "add"] + file_names, stderr=subprocess.STDOUT)


def git_status_file_names():
    git_status_params = [
        "git", "diff", "--name-only", "--cached", "--diff-filter=drc",
        "--no-renames"
    ]
    try:
        git_status = subprocess.check_output(
            git_status_params, stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, OSError) as e:
        return []
    lines = git_status.decode("utf-8").splitlines()
    return [os.path.join(OUSIA_DIR, l) for l in lines]


if __name__ == "__main__":
    file_names = [x for x in git_status_file_names() if NEEDS_FORMATTING(x)]
    git_add_file_names(format_sources(file_names))
    sys.exit(0)
