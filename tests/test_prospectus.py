import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.claude/skills/speaker-prospectus/fill_prospectus.py'
spec = importlib.util.spec_from_file_location('prospectus', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def template():
    paras=[]
    i=1
    for _,heading in m.ANCHORS:
        for text in [heading+'\n','〇〇\n']:
            paras.append((i,i+len(text),text)); i+=len(text)
    return paras


class ProspectusTests(unittest.TestCase):
    def test_missing_placeholder_cannot_consume_next_section(self):
        paras=template(); paras[1]=(paras[1][0],paras[1][1],'Filled\n')
        targets=m.find_targets(paras)
        self.assertNotIn('participants',targets)
        self.assertIn('challenges',targets)

    def test_reverse_order_and_preserve_final_newline(self):
        paras=template()
        with patch.object(m,'get_doc',return_value={}),patch.object(m,'paragraphs',return_value=paras),patch.object(m,'api_post',return_value={'replies':[]}) as post:
            m.fill_sections('synthetic-id',{k:'Replacement' for k,_ in m.ANCHORS},'synthetic-token')
            requests=json.loads(post.call_args.args[2])['requests']
        expected=sorted(m.find_targets(paras).values(),reverse=True)
        for i,(start,end) in enumerate(expected):
            self.assertEqual(requests[2*i]['deleteContentRange']['range'],{'startIndex':start,'endIndex':end-1})
            self.assertEqual(requests[2*i+1]['insertText']['location']['index'],start)

    def test_missing_section_fails_before_api_write(self):
        with patch.object(m,'get_doc',return_value={}),patch.object(m,'api_post') as post:
            with self.assertRaises(SystemExit): m.fill_sections('synthetic-id',{},'synthetic-token')
            post.assert_not_called()

    def test_bullet_deletion_runs_in_reverse_after_creation(self):
        paras=[(1,5,'・aa\n'),(5,9,'・bb\n'),(9,14,'plain')]
        with patch.object(m,'get_doc',return_value={}),patch.object(m,'paragraphs',return_value=paras),patch.object(m,'api_post',return_value={}) as post:
            m.apply_bullets('synthetic-id','synthetic-token')
        calls=[json.loads(c.args[2])['requests'] for c in post.call_args_list]
        self.assertIn('createParagraphBullets',calls[0][0])
        self.assertEqual([r['deleteContentRange']['range']['startIndex'] for r in calls[1]],[5,1])

    def test_preview_makes_no_token_or_api_calls(self):
        args=['fill_prospectus.py','--from-template','YOUR_TEMPLATE_DOC_ID','--company','Example','--name','Example',
              '--content',str(ROOT/'examples/prospectus-content.json')]
        with patch('sys.argv',args),patch.object(m,'token') as tok,patch.object(m,'api_post') as post:
            m.main(); tok.assert_not_called(); post.assert_not_called()

if __name__ == '__main__': unittest.main()
