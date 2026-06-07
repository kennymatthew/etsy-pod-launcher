#!/usr/bin/env python3
"""
create-project.py

Creates the standard folder structure for a new niche project.

Usage:
  python3 scripts/create-project.py --niche dog-mom
  python3 scripts/create-project.py --niche "nurse-humor"
"""

import argparse, sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

FOLDERS = [
    '01-research/scrapes',
    '02-design/print-files',
    '03-mockups',
    '04-listing',
    '05-performance',
    'scripts',
]

STUB_FILES = {
    '01-research/keywords.md': '# Keywords: {niche}\n\n## Niche Trend Keywords\n\n| Keyword | Search Volume | Competition | Trend |\n|---|---|---|---|\n| | | | |\n',
    '02-design/brief.md': '# Design Brief: {niche}\n\n## Lock block\n\nBlank: |  Blueprint ID:  |  Print Provider:  (ID: )\nAvg cost: $ |  List price: $ |  Margin: %\n\n## Design direction\n\n_Fill in after Phase 1 research._\n',
}


def main():
    parser = argparse.ArgumentParser(description='Create folder structure for a new niche project')
    parser.add_argument('--niche', required=True, help='Niche slug, e.g. dog-mom')
    args = parser.parse_args()

    niche = args.niche.strip().lower().replace(' ', '-')
    project_root = BASE_DIR / 'projects' / niche

    if project_root.exists():
        print(f'✗ Project already exists: {project_root}')
        sys.exit(1)

    created = []
    for folder in FOLDERS:
        path = project_root / folder
        path.mkdir(parents=True, exist_ok=True)
        created.append(str(path.relative_to(BASE_DIR)))

    for rel_path, content in STUB_FILES.items():
        path = project_root / rel_path
        path.write_text(content.replace('{niche}', niche))
        created.append(str(path.relative_to(BASE_DIR)))

    print(f'✓ Created project: projects/{niche}')
    for item in created:
        print(f'  {item}')

    print()
    print('Next steps:')
    print(f'  1. python3 scripts/research-autocomplete.py --niche {niche} --query "your broad keyword"')
    print(f'  2. python3 scripts/research-competitors.py --niche {niche} --query "your etsy search term"')
    print(f'  3. python3 scripts/extract-competitors.py --niche {niche}')
    print(f'  4. python3 scripts/generate-competitor-report.py --niche {niche}')


if __name__ == '__main__':
    main()
