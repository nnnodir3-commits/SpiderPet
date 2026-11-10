"""Behavior and regression tests for v30 hanging silk (no GUI needed)."""
import math
import unittest
from spider_hanging import (can_begin_hanging,hanging_anchor,hanging_depth,
                            hanging_position,drop_position)
from spider_nest import (max_web_span, INITIAL_SPAN, triangle_screen,
                         point_in_triangle, silk_paths)


class HangingBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.max_span = max_web_span(1920,1080)
        self.mature = INITIAL_SPAN+(self.max_span-INITIAL_SPAN)*.91
    def test_top_left_and_top_right_hang_when_web_mature(self):
        for corner in (0,1):
            self.assertTrue(can_begin_hanging(corner,self.mature,self.max_span,True))
    def test_bottom_left_and_bottom_right_never_hang(self):
        for corner in (2,3):
            for complete in (False,True):
                self.assertFalse(can_begin_hanging(corner,self.max_span,self.max_span,complete,0.26))
    def test_partial_web_cannot_hang(self):
        for span in (INITIAL_SPAN, INITIAL_SPAN+(self.max_span-INITIAL_SPAN)*.5):
            self.assertFalse(can_begin_hanging(0,span,self.max_span,True))
    def test_incomplete_web_cannot_hang(self):
        self.assertFalse(can_begin_hanging(0,self.max_span,self.max_span,False))
    def test_anchor_inside_both_upper_nests(self):
        for corner,den in ((0,(87,87)),(1,(1920-87,87))):
            a=hanging_anchor(corner,self.mature,1920,1080)
            tri=triangle_screen(corner,self.mature,1920,1080)
            self.assertTrue(point_in_triangle(a,tri),a)
            self.assertGreater(math.dist(a,den),100)
    def test_hanging_body_will_be_outside_the_web(self):
        for corner in (0,1):
            a=hanging_anchor(corner,self.mature,1920,1080)
            target=(a[0],hanging_depth(a[1],1080,75,57))
            self.assertFalse(point_in_triangle(target,triangle_screen(corner,self.mature,1920,1080)))
    def test_bottom_anchor_is_disallowed(self):
        for corner in (2,3):
            with self.assertRaises(ValueError):
                hanging_anchor(corner,self.mature,1920,1080)
    def test_thread_starts_near_den_and_ends_below(self):
        a=hanging_anchor(0,self.mature,1920,1080)
        bottom=hanging_depth(a[1],1080,75,57)
        self.assertGreater(bottom-a[1],130)
        self.assertLess(bottom,1080-75)
    def test_descent_and_ascent_do_not_teleport(self):
        top=(87,87); bottom=(93,297)
        self.assertEqual(hanging_position(top,bottom,0),top)
        self.assertEqual(hanging_position(top,bottom,1),bottom)
        self.assertEqual(hanging_position(bottom,top,1),top)
        last=top[1]
        for k in range(1,101):
            q=hanging_position(top,bottom,k/100)
            self.assertGreaterEqual(q[1],last)
            last=q[1]
    def test_drop_is_downward_and_accelerating(self):
        p=(100,270)
        at=[drop_position(p,i/20.,45,5) for i in range(21)]
        self.assertEqual(at[0],p)
        self.assertEqual(at[-1],(105,315))
        d1=at[2][1]-at[1][1]; d2=at[16][1]-at[15][1]
        self.assertGreater(d2,d1)
    def test_nest_has_no_central_silk_pod_art(self):
        from pathlib import Path
        source=(Path(__file__).parent/'spiderpet.pyw').read_text(encoding='utf-8')
        a=source.index('    def draw_silk(progress):')
        b=source.index('    def draw_broken_silk(progress):')
        web_renderer=source[a:b]
        self.assertNotIn('create_oval',web_renderer)
        self.assertNotIn('create_arc',web_renderer)
        self.assertNotIn('for j in range(9)',web_renderer)
        self.assertIn('silk_paths(',web_renderer)
    def test_hanging_line_is_click_through_and_break_causes_drop(self):
        from pathlib import Path
        source=(Path(__file__).parent/'spiderpet.pyw').read_text(encoding='utf-8')
        self.assertIn('cstyle|0x20|0x80',source)
        self.assertIn("transition('hang_drop'",source)
        self.assertIn("transition('rage_scan'",source)
        self.assertIn("state=='hang_drop'",source)
    def test_original_web_geometry_both_levels(self):
        for corner in range(4):
            for span in (INITIAL_SPAN,self.max_span):
                self.assertGreater(len(silk_paths(corner,span)),100)

if __name__=='__main__': unittest.main()
