import unittest, math
from pathlib import Path
from spider_hanging import hanging_anchor, hanging_depth, hanging_position, can_begin_hanging
from spider_nest import max_web_span

class TrailingSilkTests(unittest.TestCase):
    def test_top_web_descends_and_rope_follows(self):
        m=max_web_span(1920,1080)
        for corner in (0,1):
            a=hanging_anchor(corner,m,1920,1080)
            top=(a[0],a[1]+57*.72)
            bottom=(a[0],hanging_depth(top[1],1080,75,57)+57*.10)
            positions=[hanging_position(top,bottom,i/24) for i in range(25)]
            self.assertGreater(positions[-1][1]-positions[0][1],170)
            self.assertTrue(all(positions[i][1]<=positions[i+1][1] for i in range(24)))
            self.assertTrue(can_begin_hanging(corner,m,m,True))
            self.assertGreater(positions[10][1]-57*.29,a[1])
    def test_lower_web_never_hangs(self):
        for corner in (2,3):
            self.assertFalse(can_begin_hanging(corner,700,700,True))
    def test_same_overlay_renders_spider_and_silk(self):
        code=(Path(__file__).parent/'spiderpet.pyw').read_text('utf-8')
        block=code[code.index('    def update_hanging_cord(photo):'):code.index('    def start_rage_leap(')]
        self.assertIn('cordcanvas.create_line(',block)
        self.assertIn('cordcanvas.create_image(body_local_x,body_local_y,image=photo',block)
        self.assertIn("canvas.itemconfigure(item,state='hidden')",block)
        self.assertLess(block.index('cordcanvas.create_line('),block.index('cordcanvas.create_image('))
        self.assertIn('update_hanging_cord(photo)',code)
        self.assertIn("canvas.itemconfigure(item,state='normal')",code)
    def test_no_warping_of_legs(self):
        from PIL import Image
        frames=sorted(Path(__file__).parent.glob('walk_??.png'))
        self.assertEqual(len(frames),32)
        with Image.open(frames[0]) as image:
            self.assertEqual(image.size,(323,323))

if __name__=='__main__':unittest.main()
