# Contributing to SpiderPet

Contributions are welcome for the original MIT-licensed source code.

1. Open an Issue before significant changes, or explain your fix in a Pull
   Request. Fork the repository and make a topic branch.
2. Keep fixes small and testable. The confirmed v36 design draws the hanging
   spider and its silk in the **same transparent overlay**; preserve it.
3. Do not deform the 32 original walking poses or warp their leg geometry.
4. Preserve the threat-display sequence and the post-fight fleeing behavior.
5. Run `python -m unittest discover -p "test_*.py" -v` and, when possible,
   test the Windows desktop GUI. Describe your test environment.
6. Add no model, sprite, texture, sound or other third-party asset without a
   verifiable licence allowing inclusion, modification and redistribution.
7. Remove credentials, private paths and personal information from patches and
   logs; never upload diagnostic data that identifies another user.

By contributing, you affirm that you have the right to submit the work under
the licence applicable to the changed files. Project maintainers may request
changes or decline a PR.
