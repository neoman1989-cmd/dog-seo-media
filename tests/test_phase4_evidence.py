import json
from pathlib import Path
from hashlib import sha256
import unittest
class BusinessEvidenceTests(unittest.TestCase):
    def test_public_terms_are_bound_to_exact_captured_text(self):
        for name in ('affiliate-programs','hosting'):
            rows=json.loads(Path('data/phase4/'+name+'.json').read_text())
            for row in rows:
                for evidence in row['public']:
                    text=Path(evidence['text_file']).read_text()
                    self.assertEqual(sha256(text.encode()).hexdigest(),evidence['sha256'])
                    self.assertIn(evidence['quote'],text)
                    self.assertNotIn('\ufffd',evidence['quote'])
    def test_no_actual_affiliate_activation(self):
        config=json.loads(Path('config/monetization.example.json').read_text())
        self.assertIs(config['affiliate_enabled'],False)
        for p in json.loads(Path('data/research/products.json').read_text()):
            self.assertIsNone(p['affiliate']['url'])
    def test_competition_not_misrepresented_as_google_ranking(self):
        for row in json.loads(Path('data/phase4/competition.json').read_text()):
            self.assertFalse(row['eligible_for_google_competition']);self.assertIsNone(row['rank_claim'])
