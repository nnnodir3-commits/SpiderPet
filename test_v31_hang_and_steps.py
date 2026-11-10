"""Regression checks: no shadowed hanging anchor and quicker stride."""
from pathlib import Path
import ast, math, unittest
from PIL import Image
from spider_hanging import hanging_anchor as locate_anchor,hanging_depth,hanging_position
from spider_combat import gait_cycle_distance

class V31Regression(unittest.TestCase):
    def setUp(self):
        self.folder=Path(__file__).resolve().parent
        self.source=(self.folder/'spiderpet.pyw').read_text(encoding='utf-8')
    def test_no_local_hanging_anchor_callable_collision(self):
        tree=ast.parse(self.source)
        imports=[node for node in ast.walk(tree) if isinstance(node,ast.ImportFrom) and node.module=='spider_hanging']
        self.assertTrue(any(n.name=='hanging_anchor' and n.asname=='calculate_hanging_anchor'
                            for imp in imports for n in imp.names))
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        prepare=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='start_hang_prepare')
        calls=[n for n in ast.walk(prepare) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
        self.assertIn('calculate_hanging_anchor',[n.func.id for n in calls])
        self.assertNotIn('hanging_anchor',[n.func.id for n in calls])
    def test_spider_actually_descends_200_pixels(self):
        a=locate_anchor(0,400,1920,1080)
        d=(a[0],hanging_depth(a[1],1080,75,57))
        positions=[hanging_position(a,d,k/20.) for k in range(21)]
        self.assertGreater(positions[-1][1]-positions[0][1],140)
        self.assertTrue(all(positions[k+1][1]>=positions[k][1] for k in range(20)))
    def test_gait_cycle_suited_to_15mm_spider(self):
        self.assertLess(gait_cycle_distance(57,60),50)
        self.assertLess(gait_cycle_distance(57,200,combat=True),53)
        self.assertGreater(gait_cycle_distance(57,60),39)
    def test_photoreal_frames_present_and_shaped(self):
        frames=sorted(self.folder.glob('walk_??.png'))
        self.assertEqual(len(frames),32)
        for path in frames:
            with Image.open(path) as im:
                self.assertEqual(im.size,(323,323))
                self.assertEqual(im.mode,'RGBA')
    def test_main_body_is_not_artificially_replaced(self):
        # Both abdomen and eyes retain opaque, textured pixels in every pose.
        for n in (0,8,16,24):
            with Image.open(self.folder/f'walk_{n:02d}.png') as im:
                self.assertGreater(im.getpixel((161,105))[3],240)
                self.assertGreater(im.getpixel((161,177))[3],240)

if __name__=='__main__':unittest.main()
