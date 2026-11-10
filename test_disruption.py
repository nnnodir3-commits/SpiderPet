import unittest
from retreat_lifecycle import RetreatLifecycle
from retreat_disruption import cursor_in_retreat,DisruptionClock

class TestNestDisruption(unittest.TestCase):
    def test_pointer_over_central_silk(self):
        center=(100.,100.)
        self.assertTrue(cursor_in_retreat((100,100),center))
        self.assertTrue(cursor_in_retreat((160,100),center))
        self.assertTrue(cursor_in_retreat((100,150),center))
        self.assertFalse(cursor_in_retreat((190,100),center))
        self.assertFalse(cursor_in_retreat((160,150),center))
        self.assertFalse(cursor_in_retreat((100,100),None))

    def test_destroy_and_rebuild_after_cooldown(self):
        home=RetreatLifecycle()
        home.plan((100,100));home.start_build();home.finish(20)
        self.assertTrue(home.completed)
        timer=DisruptionClock()
        home.clear();timer.trigger(25,120)
        self.assertFalse(home.exists)
        self.assertFalse(timer.can_rebuild(144))
        self.assertTrue(timer.can_rebuild(145))
        home.plan((250,250))
        self.assertEqual(home.status,'planned')

    def test_expiry_not_triggered_by_nearby_cursor(self):
        timer=DisruptionClock()
        self.assertTrue(timer.can_rebuild(0))
        timer.trigger(100,110)
        timer.trigger(105,120)
        self.assertFalse(timer.can_rebuild(220))
        self.assertTrue(timer.can_rebuild(225))

if __name__=='__main__': unittest.main()
