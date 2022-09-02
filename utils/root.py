import sys
from pathlib import Path


def get_project_root() -> str:
    """
    This fx is super important!
    Literally everything acts up if this isn't good.
    """
    if getattr(sys, 'frozen', False):
        compiled_path = Path(sys.executable).parent
        return compiled_path
    else:
        path = str(Path(__file__).parent.parent)
        path = path.replace("\\", '/')
        return fr'{path}'


if __name__ == "__main__":
    print(get_project_root())