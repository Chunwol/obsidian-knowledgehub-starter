import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

REPO = Path(__file__).resolve().parents[1]

class StarterTests(unittest.TestCase):
    def install(self, target, name='테스트 사용자'):
        return subprocess.run(['pwsh', '-NoProfile', '-File', str(REPO/'setup.ps1'), '-Destination', str(target), '-Name', name], capture_output=True, text=True, encoding='utf-8')

    def test_install_and_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'한글 보관함'
            result = self.install(target)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('테스트 사용자', (target/'20_Areas/나의 프로필.md').read_text(encoding='utf-8-sig'))
            for config in (target/'.obsidian').glob('*.json'):
                json.loads(config.read_text(encoding='utf-8-sig'))
            tool = target/'90_System/tools/knowledge.py'
            def run(*args):
                p = subprocess.run([sys.executable, str(tool), *args], capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(p.returncode, 0, p.stderr)
                return p.stdout
            self.assertIn('예시 프로젝트', run('search', '예시'))
            secret = target/'00_Inbox/비공개.md'
            secret.write_text('---\nprivacy: private\n---\nNEVER_EXPORT_THIS', encoding='utf-8')
            run('export')
            exported = (target/'90_System/Exports/새 채팅용 맥락.md').read_text(encoding='utf-8')
            self.assertNotIn('NEVER_EXPORT_THIS', exported)
            self.assertIn('예시 프로젝트', exported)
            archive = Path(tmp)/'backup.zip'
            run('backup', '--output', str(archive))
            with zipfile.ZipFile(archive) as z:
                self.assertIn('홈.md', z.namelist())
                self.assertIn('00_Inbox/비공개.md', z.namelist())
            original = archive.read_bytes()
            repeated = subprocess.run([sys.executable, str(tool), 'backup', '--output', str(archive)], capture_output=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(archive.read_bytes(), original)
            inside = subprocess.run([sys.executable, str(tool), 'backup', '--output', str(target/'backup.zip')], capture_output=True)
            self.assertNotEqual(inside.returncode, 0)
            self.assertFalse((target/'backup.zip').exists())

    def test_existing_folder_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'existing'
            target.mkdir()
            sentinel = target/'original.txt'
            sentinel.write_text('KEEP', encoding='utf-8')
            result = self.install(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_text(), 'KEEP')
            self.assertEqual(list(target.iterdir()), [sentinel])

    def test_name_is_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'vault'
            name = '가 "나" $(Get-Date)'
            result = self.install(target, name)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(name, (target/'20_Areas/나의 프로필.md').read_text(encoding='utf-8-sig'))

    def test_source_descendant_rejected(self):
        # WhatIf-style path check: target inside source must be rejected before creation.
        target = REPO/'vault'/'test-install-must-not-exist'
        result = self.install(target)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(target.exists())

if __name__ == '__main__':
    unittest.main()
