"""Regression checks for the stationary-cursor nest starvation fix.

The Xvfb graphical smoke test (see README) also verifies a shelter reaches
home=ready even with the pointer parked a few pixels from the spider.
"""
from pathlib import Path
import unittest

class NestWakefulnessRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(Path(__file__).parent/'spiderpet.pyw').read_text(encoding='utf-8')

    def test_mouse_must_move_to_reset_idle_timer(self):
        s=self.source
        self.assertIn('pointer_moved=pointer_step>=1.5',s)
        self.assertIn('if visible and pointer_active and state not in',s)
        self.assertIn('if pointer_moved:\n                last_interest=now',s)
        self.assertNotIn("if visible and state not in ('fight','fight_flee','fight_victory'):\n            last_interest=now",s)

    def test_pointer_stationary_does_not_abort_weave(self):
        s=self.source
        self.assertIn("if state in ('retreat_walk','weave'):",s)
        self.assertIn('if visible and pointer_active and state not in',s)

    def test_nest_grows_and_hang_begins_with_stationary_pointer(self):
        s=self.source
        self.assertIn('if visible and pointer_moved and dmouse < max(size*4.,230.):',s)
        self.assertIn('now>=hang_next_allowed and not pointer_active',s)
        self.assertIn("transition('hang_descend',hang_descend_seconds)",s)
        self.assertIn("transition('weave',5.5*(1.-silk_progress))",s)

if __name__=='__main__': unittest.main()
