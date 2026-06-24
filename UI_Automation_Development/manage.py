#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    # Ensure repository root is on sys.path so imports like `FastAPI_MongoDB...` work.
    repo_root = Path(__file__).resolve().parents[1]  # -> d:/Manju/Django_UI
    sys.path.insert(0, str(repo_root))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'UI_Automation_Development.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

