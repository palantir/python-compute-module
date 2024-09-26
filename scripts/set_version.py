import subprocess

VERSION_FILE_PATH = "compute_modules/_version.py"


def _get_current_tag() -> str:
    return subprocess.check_output("git describe --tags --abbrev=0".split()).decode().strip()


def main() -> None:
    gitversion = _get_current_tag()
    print(f"Setting {VERSION_FILE_PATH} to {gitversion}...")

    with open(VERSION_FILE_PATH, "r") as f:
        content = f.read()

    content = content.replace('__version__ = "0.0.0"', f'__version__ = "{gitversion}"')

    with open(VERSION_FILE_PATH, "w") as f:
        f.write(content)

    subprocess.run(["poetry", "version", gitversion])
    print("Done!")
