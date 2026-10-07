"""Local search, opt-in context export and full backup. Python 3.10+, no dependencies."""
import argparse
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def notes():
    for path in sorted(ROOT.rglob('*.md')):
        rel = path.relative_to(ROOT)
        if any(p.startswith('.') for p in rel.parts) or any(p in ('Exports', 'Private', '80_Templates', '65_Conversations') for p in rel.parts):
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            continue
        yield rel, path.read_text(encoding='utf-8-sig')

def shareable(text):
    if not text.startswith('---\n'):
        return False
    header = text.split('---', 2)[1]
    return bool(re.search(r'^privacy:\s*[\"\']?shareable[\"\']?\s*$', header, re.M))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search')
    search.add_argument('query')
    commands.add_parser('export')
    backup = commands.add_parser('backup')
    backup.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'search':
        for rel, text in notes():
            if args.query.casefold() in text.casefold() or args.query.casefold() in str(rel).casefold():
                print(rel.as_posix())
                for line in text.splitlines():
                    if args.query.casefold() in line.casefold():
                        print('  ' + line[:200])
    elif args.command == 'export':
        sections = ['# 새 채팅용 맥락\n\n첨부 전 내용을 검토하세요. 이 파일은 자동 업로드되지 않습니다.\n']
        for rel, text in notes():
            if shareable(text):
                sections.append(f'\n---\n\n## {rel.as_posix()}\n\n{text}')
        dest = ROOT/'90_System/Exports/새 채팅용 맥락.md'
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text('\n'.join(sections), encoding='utf-8')
        print(dest)
    else:
        dest = Path(args.output).expanduser().resolve()
        if dest.is_relative_to(ROOT):
            parser.error('Backup output must be outside the vault.')
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation preserves any existing backup.
        with zipfile.ZipFile(dest, 'x', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(ROOT.rglob('*')):
                if path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT) and '__pycache__' not in path.parts:
                    archive.write(path, path.relative_to(ROOT).as_posix())
        print(dest)

if __name__ == '__main__':
    main()
