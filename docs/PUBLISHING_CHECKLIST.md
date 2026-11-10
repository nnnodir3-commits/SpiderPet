# SpiderPet v38 — public-release checklist

## Completed in this preparation

- [x] Added active root `LICENSE` (MIT) for original source code and scripts.
- [x] Added explicit image-asset exclusion and provenance tracking documents.
- [x] Preserved the original 32 walking and 12 threat display PNGs unchanged.
- [x] Preserved v38 application and behavior source unchanged.
- [x] Ran 64 unit tests and verified all 44 PNG files are readable (Linux environment).
- [x] Prepared English/Uzbek documentation, CI and release notes.
- [x] Prepared a **code-only** public archive excluding images of unverified origin.

## REQUIRED before uploading the **complete** source archive as Public

- [ ] Establish and record permission for public redistribution of all 44 PNG
      frames derived from third-party visual sources, or replace them.
- [ ] Verify licence/copyright-holder text if contributions have other owners.
- [ ] Run SpiderPet v38 on Windows; check cursor, nest, body-and-silk overlay,
      duo threat-display/fight, DPI, exit shortcut.
- [ ] Optionally build and check an `.exe` on Windows. Do **not** describe a
      source-only archive as a ready-made Windows `.exe` installer.
- [ ] Confirm no personal data, API tokens or machine-specific paths are added.

## Publish

1. Use `GitHub Desktop` to clone `nnnodir3-commits/SpiderPet`.
2. Copy the repository files directly into the clone root (preserve `.git`).
3. Commit and push to `main`.
4. After asset clearance, switch **Settings -> General -> Danger Zone -> Change
   repository visibility -> Public**.
5. For a binary release: build and test `dist\SpiderPet.exe` on Windows, then
   upload it as an asset on a GitHub Release (`v38.0.0`).
6. Enable Issues, add a real-app screenshot and appropriately labelled demo.

Until PNG rights are confirmed, you can publish the source-only MIT package,
but the full graphical program will not run without its 44 animation PNGs.
