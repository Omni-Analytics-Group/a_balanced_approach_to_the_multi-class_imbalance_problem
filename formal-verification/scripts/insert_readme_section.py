#!/usr/bin/env python3
"""Insert or update the formal verification section in the original README.

Runs locally only. Creates README.md.bak before modifying the file.
Usage from the repository root:
    python formal-verification/scripts/insert_readme_section.py --readme README.md --dry-run
    python formal-verification/scripts/insert_readme_section.py --readme README.md
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil

TITLE = '## Formal verification of Class Balance Accuracy with Lean 4'
OLD_TITLE = '## Formal verification: checking CBA with Lean 4'
ANCHOR = '- [Formal verification of Class Balance Accuracy with Lean 4](#formal-verification-of-class-balance-accuracy-with-lean-4)'
OLD_ANCHOR = '- [Formal verification: checking CBA with Lean 4](#formal-verification-checking-cba-with-lean-4)'
MARKER = '## What else is in the dissertation'
TOC_TARGET = '- [Class Balance Accuracy](#class-balance-accuracy)'


def insert(root: Path, readme_path: Path, dry_run: bool):
    snippet = (root / 'README_SECTION.md').read_text(encoding='utf-8').rstrip() + '\n\n'
    source = readme_path.read_text(encoding='utf-8')
    if MARKER not in source:
        raise SystemExit(f'Could not find insertion marker {MARKER!r} in {readme_path}')
    if TITLE in source:
        start = source.index(TITLE)
        end = source.index(MARKER, start)
        if source[start:end] == snippet and ANCHOR in source:
            print('Section is already up to date; no changes needed')
            return
        updated = source[:start] + snippet + source[end:]
        action = 'Update existing verified section'
    elif OLD_TITLE in source:
        start = source.index(OLD_TITLE)
        end = source.index(MARKER, start)
        updated = source[:start] + snippet + source[end:]
        action = 'Replace prior draft section'
    else:
        updated = source.replace(MARKER, snippet + MARKER, 1)
        action = 'Insert verification section'
    if OLD_ANCHOR in updated:
        updated = updated.replace(OLD_ANCHOR, ANCHOR, 1)
    elif ANCHOR not in updated:
        if TOC_TARGET not in updated:
            raise SystemExit(f'Could not find TOC anchor location {TOC_TARGET!r}')
        updated = updated.replace(TOC_TARGET, TOC_TARGET + '\n' + ANCHOR, 1)
    if dry_run:
        print('DRY RUN:', action)
        print('Original chars:', len(source), 'Revised chars:', len(updated))
        return
    backup = readme_path.with_name(readme_path.name + '.bak')
    shutil.copy2(readme_path, backup)
    readme_path.write_text(updated, encoding='utf-8')
    print(action + ':', readme_path)
    print('Backup:', backup)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--readme', type=Path, default=Path('README.md'))
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    insert(root, args.readme, args.dry_run)


if __name__ == '__main__':
    main()
