import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.claude/scripts'


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copytree(SCRIPTS, self.root / '.claude/scripts')
        (self.root / 'journal').mkdir()
        (self.root / 'bin').mkdir()
        fake = self.root / 'bin/claude'
        fake.write_text('''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
Path(os.environ['CAPTURE']).write_text(json.dumps({'args':sys.argv[1:],'stdin':sys.stdin.read()}))
if os.environ.get('FAIL_SUMMARY'): sys.exit(1)
print('SLUG: migration\\nTITLE: Synthetic migration\\nINDEX: synthetic\\n---\\n## 申し送り\\nReview migration evidence.')
''')
        fake.chmod(0o755)
        self.env = {**os.environ, 'PATH': str(self.root/'bin')+':'+os.environ['PATH'],
                    'CAPTURE':str(self.root/'capture.json'), 'CLAUDE_PROJECT_DIR':str(self.root),
                    'CONFERENCE_JOURNAL_ENABLED':'1'}
        self.transcript = self.root / 'session-001.jsonl'
        self.write_transcript(3)

    def write_transcript(self, count):
        rows = [{'type':'user','sessionId':'session-001','cwd':'synthetic-workspace','gitBranch':'main',
                 'message':{'content':f'Synthetic migration request {i}'}} for i in range(count)]
        rows += [{'type':'assistant','message':{'content':[{'type':'text','text':'Visible response'},
                  {'type':'thinking','thinking':'DO_NOT_COPY'}, {'type':'tool_use','input':'DO_NOT_COPY'}]}},
                 {'type':'user','isSidechain':True,'message':{'content':'DO_NOT_COPY'}},
                 {'type':'user','message':{'content':[{'type':'tool_result','content':'DO_NOT_COPY'}]}},
                 {'type':'user','message':{'content':'<system-reminder>DO_NOT_COPY'}}]
        self.transcript.write_text('bad json\n[]\n'+ '\n'.join(map(json.dumps, rows)))

    def worker(self):
        return subprocess.run(['bash',str(SCRIPTS/'journal-worker.sh'),'session-001',str(self.transcript),str(self.root)],
                              env=self.env, capture_output=True, text=True)

    def test_extract_filters_non_dialogue_and_malformed_records(self):
        result = subprocess.run(['python3',str(SCRIPTS/'journal-extract.py'),str(self.transcript)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0)
        self.assertIn('user_turns=3',result.stdout)
        self.assertIn('Visible response',result.stdout)
        self.assertNotIn('DO_NOT_COPY',result.stdout)

    def test_opt_out_does_not_call_model_or_create_index(self):
        self.env['CONFERENCE_JOURNAL_ENABLED']='0'
        self.worker()
        self.assertFalse((self.root/'capture.json').exists())
        self.assertFalse((self.root/'journal/INDEX.md').exists())

    def test_summary_index_recall_search_and_sequential_idempotency(self):
        self.assertEqual(self.worker().returncode,0)
        index=self.root/'journal/INDEX.md'
        first=index.read_text()
        self.assertIn('session-001',first)
        self.worker()
        self.assertEqual(index.read_text(),first)
        capture=json.loads((self.root/'capture.json').read_text())
        args=capture['args']
        self.assertEqual(args[args.index('--tools')+1],'')
        self.assertTrue(json.loads(args[args.index('--settings')+1])['disableAllHooks'])
        self.assertNotIn('DO_NOT_COPY',capture['stdin'])
        recall=subprocess.run(['bash',str(SCRIPTS/'journal-recall.sh')],env=self.env,capture_output=True,text=True)
        self.assertIn('Review migration evidence.',recall.stdout)
        search=subprocess.run(['bash',str(SCRIPTS/'journal-search.sh'),'migration'],env=self.env,capture_output=True,text=True)
        self.assertIn('Synthetic migration',search.stdout)

    def test_trivial_sessions_skip_model(self):
        self.write_transcript(2)
        self.worker()
        self.assertIn('(trivial, skipped)',(self.root/'journal/INDEX.md').read_text())
        self.assertFalse((self.root/'capture.json').exists())

    def test_failed_summary_not_indexed(self):
        self.env['FAIL_SUMMARY']='1'
        self.worker()
        self.assertFalse((self.root/'journal/INDEX.md').exists())

    def test_backfill_default_is_dry_run(self):
        self.env['CLAUDE_TRANSCRIPT_DIR']=str(self.root)
        result=subprocess.run(['bash',str(SCRIPTS/'journal-backfill.sh'),'--all'],env=self.env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0)
        self.assertIn('would-capture',result.stdout)
        self.assertFalse((self.root/'capture.json').exists())

if __name__ == '__main__': unittest.main()
