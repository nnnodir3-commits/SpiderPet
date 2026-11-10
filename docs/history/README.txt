SpiderPet v33 — RigidLegs

YANGI:
- Yuqori yoki pastki burchaklarda organik egri ipak uyasi to'qiladi.
- Markazdagi eski qalin ipak tuguni/uychasi OLIB TASHLANDI.
- Faqat YUQORI burchakdagi katta uyada turgan o'rgimchak
  bitta ipak ipida pastga osilib tushadi, sekin tebranadi va qaytib chiqadi.
- PASTKI burchakdagi uyada hech qachon osilish yo'q.
- O'rgimchak osilib turgan paytda sichqon kursori uyadagi
  iplarga tegsa, uya buziladi, ip uziladi, o'rgimchak 20-45 piksel
  pastga tushgandek harakat qiladi va himoya rejimiga o'tadi.
- Oddiy uya buzilishi, 5 daqiqa tashlab ketilgan uya 30 soniyada
  xiralashib yo'qolishi, ikki o'rgimchak janjali, kursor reaksiyalari
  va deraza chegaralarida yurish saqlandi.

START_PREVIEW.bat — oddiy rejim
START_TWO_SPIDERS.bat — ikkita o'rgimchak
TEST_HANGING.bat — YUQORI burchakdagi osilishni tezkor tekshirish
TEST_BOTTOM_NEST.bat — PASTKI burchakdagi uya (osilmaydi)
TEST_GROWTH.bat — uya kattalashishi
BUILD_ONE_EXE.bat — Windowsda yagona dist\SpiderPet.exe yig'ish
TEST_EXE.bat — EXE ishlashini tekshirish

Dasturni yopish: Ctrl + Shift + Q
Biologik izoh: bu katta naqsh salticidlar uchun dekorativ
modellashtirishdir; ular odatda yirik o'lja tutuvchi to'r to'qimaydi.


v31 TUZATISHLARI:
- Oldingi versiyada osilish nuqtasini hisoblovchi funksiya nomi koordinata
  nomi bilan to'qnashib, osilishdan oldin xatoga olib kelgan. Bu tuzatildi.
- O'rgimchak ipakdan 135–255 px atrofida pastga tushadi, tebranadi va qaytadi.
- Oyoq yurish sikli oldingidan qariyb 1.65 barobar tezroq; oyoq uchlari
  biroz kengroq siljiydi. Tana, ko'zlar va fotoreal tekstura saqlanadi.
- TEST_HANGING_TRACE.bat osilish holatini %LOCALAPPDATA%\SpiderPet\hanging_trace.txt
  ga yozadi (agar Windowsda muammo davom etsa, shu faylni yuboring).


v33 (2-NOYABR 2026): OLDINGI CHAP OYOQ DEFORMATSIYASI TUZATILDI.
- v31 dagi oyoq rasmlariga hududiy cho'zish/bukish (pixel remapping)
  qo'llangani uchun ayrim bo'g'imlar g'ayritabiiy ko'ringan.
- Barcha 32 ta realistik kadr asl deformatsiyasiz shakliga qaytarildi.
  Oyoqning uzunligi va bukilish shakli sun'iy o'zgartirilmaydi.
- 128 ta fazali yurish hisoblagichi va v31 dagi tezlashtirilgan
  qadam ritmi SAQLANDI. Faqat asl 32 ta aniq rasm namoyish etiladi.
- Ikki kadrni ustma-ust shaffof qo'shib yuborish ham olib tashlandi:
  bu oldingi oyoq atrofida soxta ikkilamchi oyoq paydo bo'lishini to'xtatadi.
- Osilish, uya, ikki o'rgimchak janjali va kursor reaksiyalari saqlandi.
- TEST_HANGING.bat — osilishni, START_PREVIEW.bat — yurishni tekshiring.
- BUILD_ONE_EXE.bat — Windowsda bitta mustaqil SpiderPet.exe yig'ish.
