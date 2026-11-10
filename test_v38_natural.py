"""v38 regression: all v36 features unchanged while animations add behavior."""
import math,hashlib,unittest
from pathlib import Path
from PIL import Image,ImageChops
from spider_activity import (observe_rotation,probe_frame,threat_frame,
                             retreat_backstep,threat_display_motion)
from spider_combat import DUEL_DURATION,duel_phase

DIR=Path(__file__).resolve().parent
ORIGINAL_WALK_SHA256=('4a0f295bea351ebfa8257ace4b1b98621cd8060ab0ce96636435645809de39ad', '0bdf3a91b8eb0ee4c758caa15871f9828297ba95a2d632efec84737b7d2a7ba4', 'c86d3acc56aa4d488ce537bd7ff357c0db329edc323b784eb82806b47cbf9da6', 'fa74db036ee85ba3c407bc929bdab925204f1a0e854ca1c6bbe5c244eb08eacc', 'b4d89d3bf30aa18d721b9d461dfc40e498086222baf0802d3a94d7a94d9ecd2f', '7dbd478a05afb5beb5258f69fe5ebb4805da34ebe5f6ba6e183aa7a566e76a6e', 'e1e8c12a9121d1d12ea68afa10400afb88be3d834fd3e9ab22073b7fd79710a5', 'db34ff90a02eba763bfb41958067522b3131763a4df8b232b024e0aaffa5ef97', '7f7a048647f2454025eb6e952bd23b9524a4755eb8191fbf17abee967798d6c8', '52f15725a31a33068586ed627c2cc19f60c1079eb8c2aff9fd4592a934da2d9f', '21a36f6a2a7f435666824db33f9f8bfadd38d4a0eb777f46a0ac529197026a03', '246b0dbbc622035cf50cd2f20994e8ab21a848f6c1329c32e5b682b8e1234ef7', '7ac2c47a735a9a09a786861596f274d91a5a82c21f6d0ff1160a6385d30cc1df', '8f44793fb3970ef8410b693007895fc7edd46825659ad1595baf7620fbaf5eb7', '4f8762284addbaf9b63412e8e21226c9e982e69f5933c2fabd68355846a6ddf7', '7b0a131c6190e3e00d66407a28e295b6a26e31d3a75e58e16ff239f864b7e881', '4207f84d14a2db57e25d1cf9254e8e5ab54a04a44fb2d03dcfab52788ab7c2db', '7b24afbab04ab6793870757f81096692d2c33521c268a7affab2507cf29a6e2c', '092072876c7578b4e279075b01fb3b59dc0b297b2704ae8525005c514e37175e', '93071801aa8cd54c1ee2cf826aa53bc343482623faef8c3937a6385cfcb0aea2', '2fee5ec885c95d9f1849f01fb6b4f168e5e979889f31d8de0d493c30d6ebcc89', 'f74cf6d8ac91506ae6058f22e1683b664dc1614a4d4964e4933c33abd8d115c4', '21505e39fa1801ac4677705d4b1ffc846004c3f54c9b0ac73ba2afbd257233e0', '823081b5c06d1bf2a4544d5d9ca746aef8823f7629fa8a22650c90d9f43972c5', 'bdf7a33d070d2ac3c68b154156dfaae34bb4c4a02038478a2fd5c58166fe99b3', '51f49ea91b5c492b5f2f13db85a4d32dcfec952e3527312038aaea87ebb66e47', '4ad1bdf37cb04dd1afdefd60b3e9bdefe294900caaf022edef486b3d33df1c59', '0b94a00de92adfdf44936110e77f8e99971e387cb93f647a2ad58451e948be5c', '8f031eb04deb6c5ef0d8d2d51bda673c7c7b0ac935bd0f6bae6c595b124c6eee', 'f17aa5ff305d1fa706e86dc634770af66a20badde623095f03cabf3d2e9d8463', 'd37fea6a21c3863a4e6278be3e35f81d98b98aa8cd73a1aaf5315d2cc21cf59f', '287a032ab0913a2c461073d6c60b0c05a3db5643fb5247b9a1bc2145254b5eed')
ORIGINAL_HANG_CODE_SHA256='dd053f7f390fb1797e2ded1b670511c68768d75b6d1dbcaa8f172527610c3d62'

class V38NaturalTests(unittest.TestCase):
    def test_original_photoreal_32_legs_are_unchanged(self):
        for i in range(32):
            a=(DIR/f'walk_{i:02d}.png').read_bytes()
            self.assertEqual(hashlib.sha256(a).hexdigest(),ORIGINAL_WALK_SHA256[i])
    def test_photo_threat_waves_are_real_and_leg_length_rigid(self):
        ims=[]
        for i in range(12):
            p=DIR/f'threat_{i:02d}.png'
            self.assertTrue(p.is_file(),p)
            with Image.open(p) as img:
                self.assertEqual(img.size,(323,323))
                self.assertEqual(img.mode,'RGBA')
                self.assertGreater(img.getpixel((161,100))[3],240)
                ims.append(img.copy())
        self.assertIsNotNone(ImageChops.difference(ims[0],ims[2]).getbbox())
        self.assertIsNotNone(ImageChops.difference(ims[2],ims[6]).getbbox())
        # Anatomical torso has not been warped or swapped while threatening.
        src=Image.open(DIR/'walk_00.png').convert('RGBA')
        for im in ims:
            self.assertEqual(im.crop((150,65,175,110)).tobytes(),
                             src.crop((150,65,175,110)).tobytes())
    def test_threat_symmetric_and_finishes_without_old_duel_changes(self):
        self.assertEqual(threat_frame(0),0)
        self.assertEqual(threat_frame(3.15),11)
        self.assertLess(threat_frame(1.2),threat_frame(2.1))
        self.assertEqual(duel_phase(.2,0,0)[0],'display')
        self.assertEqual(duel_phase(1.1,0,0)[0],'strike')
        self.assertAlmostEqual(DUEL_DURATION,7.25)
    def test_probe_and_look_are_in_place(self):
        self.assertEqual(probe_frame(0),0)
        self.assertTrue(any(probe_frame(i*.08)!=probe_frame(0) for i in range(30)))
        heading=1.45
        self.assertAlmostEqual(observe_rotation(heading,0.,2.),heading)
        self.assertAlmostEqual(observe_rotation(heading,2.,2.),heading)
        self.assertLess(observe_rotation(heading,1.5,2.),heading)
        self.assertGreater(observe_rotation(heading,.5,2.),heading)
    def test_backstep_moves_away_and_respects_edges(self):
        for start in ((240,350),(80,80),(1400,850)):
            danger=(start[0]+10,start[1]+2)
            end=retreat_backstep(start,danger,57,(1920,1080))
            self.assertGreaterEqual(math.dist(end,danger),math.dist(start,danger))
            self.assertGreater(math.dist(end,start),20)
            self.assertTrue(40<=end[0]<=1880)
            self.assertTrue(40<=end[1]<=1040)
    def test_display_no_contact_and_small_sway(self):
        a=(400,400);b=(520,400)
        positions=[threat_display_motion(a,b,57,0,i/100.) for i in range(101)]
        self.assertLess(max(math.dist(a,q) for q in positions),35.)
        self.assertLess(math.dist(a,positions[0]),.00001)
        self.assertLess(math.dist(a,positions[-1]),.00001)
        self.assertGreater(max(q[1] for q in positions)-min(q[1] for q in positions),1.5)
    def test_hanging_code_preserved_byte_for_byte(self):
        new=(DIR/'spiderpet.pyw').read_text('utf-8')
        s='    def update_hanging_cord(photo):'
        e='    def start_rage_leap(now,mx,my):'
        block=new[new.index(s):new.index(e)].encode()
        self.assertEqual(hashlib.sha256(block).hexdigest(),ORIGINAL_HANG_CODE_SHA256)
        self.assertIn("'threat_display'",new)
        self.assertNotIn('spawn_fly(',new)

if __name__=='__main__':unittest.main()
