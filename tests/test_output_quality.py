import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/agentic-aac-board-maker/scripts'))
from render_html import render
from render_obf import render_boards
from validate_html_parity import validate
from fetch_arasaac_symbols import build_review_manifest,apply_review

class OutputQualityTests(unittest.TestCase):
 def setUp(self):
  self.ir=json.loads(next((ROOT/'generated/gaze-choice-2x2').glob('*.ir.json')).read_text())
 def test_switch_export_rejected(self):
  self.ir['access']['switchScanning']=True
  with self.assertRaisesRegex(ValueError,'does not implement switch scanning'):render(self.ir)
 def test_positions_preserved_across_exports(self):
  a,b=self.ir['pages'][0]['buttons'][:2];a['position'],b['position']=b['position'],a['position']
  self.assertEqual(b['id'],render_boards(self.ir)[0]['grid']['order'][0][0])
  self.assertEqual([],validate(self.ir,render(self.ir)))
 def test_overlap_rejected(self):
  self.ir['pages'][0]['buttons'][1]['position']=self.ir['pages'][0]['buttons'][0]['position']
  with self.assertRaisesRegex(ValueError,'overlaps'):render(self.ir)
 def test_stale_review_does_not_mutate_board(self):
  def no_network(url):raise OSError('offline')
  review=build_review_manifest(self.ir,fetcher=no_network)
  self.ir['pages'][0]['buttons'][0]['label']='Changed concept'
  previous=copy.deepcopy(self.ir)
  self.assertTrue(apply_review(self.ir,review)[0]['status'].startswith('error'))
  self.assertEqual(previous,self.ir)
 def test_download_failure_retains_approved_existing_symbol(self):
  def fetch(url):
   if '/search/' in url:return json.dumps([{'_id':123,'keywords':[]}]).encode()
   raise OSError('offline')
  button=self.ir['pages'][0]['buttons'][0];button['symbolId']=99;button['symbolSrc']='data:image/png;base64,b2xk'
  review=build_review_manifest(self.ir,fetcher=fetch);review['entries'][0]['approvedSymbolId']=123
  apply_review(self.ir,review,fetcher=fetch)
  self.assertEqual(99,button['symbolId']);self.assertEqual('data:image/png;base64,b2xk',button['symbolSrc'])
 def test_full_attribution_is_rendered(self):
  self.ir['attribution'][0]['attribution']='Specific author and owner attribution'
  self.assertIn('Specific author and owner attribution',render(self.ir))

 def test_visible_label_and_symbol_removal_break_parity(self):
  output=render(self.ir)
  changed=output.replace('class="label">Art</span>', 'class="label">Changed</span>')
  self.assertTrue(validate(self.ir,changed))
  example=json.loads(next((ROOT/'generated/symbol-shape-choice').glob('*.ir.json')).read_text())
  import re
  self.assertTrue(validate(example,re.sub(r'<img[^>]+>', '',render(example),count=1)))
