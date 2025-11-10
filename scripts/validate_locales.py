#!/usr/bin/env python3
"""Validate JSON translation files under `locales/*/*.json`.

Usage: from repo root run `python3 scripts/validate_locales.py`
Exit code: 0 if all JSON files parse successfully. Non-zero otherwise.
"""
import json
import sys
from pathlib import Path


def find_locale_files(root: Path):
    locales = root / 'locales'
    if not locales.exists():
        print('No locales directory found at', locales)
        return []

    files = list(locales.rglob('*.json'))
    return files


def validate_file(path: Path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            json.load(f)
        return True, None
    except Exception as e:
        return False, str(e)


def main():
    repo_root = Path(__file__).parent.parent
    files = find_locale_files(repo_root)
    if not files:
        print('No locale json files found.')
        return 1

    failed = []
    for f in sorted(files):
        ok, err = validate_file(f)
        if ok:
            print('OK    ', f)
        else:
            print('ERROR ', f, '->', err)
            failed.append((f, err))

    if failed:
        print('\nFound', len(failed), 'invalid JSON files')
        return 2

    print('\nAll', len(files), 'locale JSON files are valid')
    return 0


if __name__ == '__main__':
    sys.exit(main())
