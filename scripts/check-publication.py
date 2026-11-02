#!/usr/bin/env python3
"""Scan candidate public files without printing matched private values."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    'credential': re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{24,}|xox[baprs]-[A-Za-z0-9-]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)'),
    'personal absolute path': re.compile(r'/(?:Users|home)/[A-Za-z0-9_.-]+/'),
    'private service link': re.compile(r'https://(?:[^/\s]+\.slack\.com/archives/|(?:www\.)?notion\.so/[^\s]+|docs\.google\.com/(?:document|spreadsheets|presentation)/d/[A-Za-z0-9_-]{20,})'),
    'email address': re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'),
}
ALLOWED_EMAIL_DOMAINS = {'example.com', 'example.org', 'example.net'}


def scan(root=ROOT):
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-co', '--exclude-standard', '-z']).decode().split('\0')
    problems = []
    count = 0
    for name in sorted(set(filter(None, names))):
        path = root / name
        if not path.exists():
            continue
        if path.is_symlink():
            problems.append((name, 0, 'symlink')); continue
        try:
            content = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            problems.append((name, 0, 'non-text file requires review')); continue
        count += 1
        for number, line in enumerate(content.splitlines(), 1):
            for kind, pattern in RULES.items():
                for match in pattern.finditer(line):
                    if kind == 'email address' and match.group().rsplit('@', 1)[1] in ALLOWED_EMAIL_DOMAINS:
                        continue
                    problems.append((name, number, kind))
    return count, problems


if __name__ == '__main__':
    count, problems = scan()
    for name, line, kind in problems:
        print(f'{name}:{line}: review {kind}')
    print(f'Checked {count} candidate files; {len(problems)} findings. Review is still required.')
    sys.exit(bool(problems))
