# SpiderPet 🕷️

**A little jumping spider living on your Windows desktop.**

SpiderPet v38 is a small, photorealistic desktop pet implemented with Python,
Tkinter and Pillow. The spider wanders around Windows, responds to cursor
movement, explores application-window edges, builds a corner silk retreat,
hangs from a trailing silk thread, and interacts with other spider instances.

> **Complete source package:** This repository bundle includes the **full 44 PNG animation set**
> required to run the graphical application. For upload instructions, see
> [START_HERE_GITHUB_UZ.md](START_HERE_GITHUB_UZ.md).
>
> **Licensing:** SpiderPet's **original code is MIT-licensed**. The 44 sprite PNGs
> have **separate, currently unverified redistribution rights**. They are **not
> MIT-licensed**. See [Image asset rights](ASSETS_LICENSE.md) and
> [Licensing details](docs/LICENSING.md). The complete image-containing package
> must not be publicly redistributed until the source rights are established.

## Features

- 32 photorealistic walking frames with direction-aware gait and jumps.
- Natural behavior: idle foreleg probing, careful looking around, subtle rest
  movements and startle/backstep reactions.
- Corner silk retreats that can grow, be disturbed, or fade when abandoned.
- A suspended spider that visibly descends and climbs **with its own silk**:
  the spider body and strand share a single transparent overlay (the working
  v36 fix).
- Two spiders perform raised-foreleg threat displays, then potentially fight;
  the loser retreats.
- Window-edge movement and cursor responses.
- No fly-hunting mode (the v37 experiment is not in v38).

## Requirements

- Windows 10/11 with a graphical desktop (Win32 API and Tk transparency).
- Python 3.10+ with Tkinter.
- [Pillow](https://pypi.org/project/Pillow/), installed using `requirements.txt`.
- For **running the graphic version**: 32 `walk_*.png` and 12 `threat_*.png`
  frames in the same directory as `spiderpet.pyw`.

## Run on Windows

```powershell
py -3 -m pip install -r requirements.txt
py -3 spiderpet.pyw
```

Or double-click `START_PREVIEW.bat`. Exit via **Ctrl+Shift+Q**.

`TEST_NATURAL_BEHAVIOR.bat`, `TEST_THREAT_DISPLAY.bat`, `TEST_HANGING.bat`
and `START_TWO_SPIDERS.bat` launch focused demonstrations.

**Note:** this source project is **not a pre-built `.exe`**. On Windows, run
`BUILD_ONE_EXE.bat` to build a one-file executable with PyInstaller, then test
it using `TEST_EXE.bat` before distributing it. GitHub Actions also provides a
manual **Build Windows EXE** workflow, which produces a downloadable build
artifact (not an automatically published Release).

## Development

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m unittest discover -p "test_*.py" -v
py -3 check_release_assets.py
```

64 unit tests passed in a non-Windows test environment during release
preparation. Those checks are not a substitute for real Windows GUI testing.
The original v38 graphics, body-and-silk hanging, and duel systems are
unchanged in this documentation/licensing release.

## Contributing

Issues, ideas and code improvements are welcome. Please read
[CONTRIBUTING.md](CONTRIBUTING.md) before submitting a Pull Request. Do not
commit copyrighted third-party resources without documented permissions.

## Rights and release status

- [MIT License — source code](LICENSE)
- [PNG animation image rights](ASSETS_LICENSE.md)
- [Image source/permission register](docs/ASSET_PROVENANCE.md)
- [Public release checklist](docs/PUBLISHING_CHECKLIST.md)
- [Uzbek-language README](README_UZ.md)

**Maintainer account:** [nnnodir3-commits](https://github.com/nnnodir3-commits).
This repository is designed for transparent, community-led development.
