# Demo run — verified 2026-11-18

```bash
$ python3 -m agent_scene_code demo --out demo-out
rendered 72 frames to demo-out (open demo-out/viewer.html)
demo: yaml-to-json — 72 frames, 6.0s at 12 fps

$ python3 -m agent_scene_code check examples/yaml-to-json.json
PASS: 72 frames, no issues

$ python3 -m unittest discover -s tests
Ran 33 tests in 1.1s — OK
```

## Frame spot-checks (real renders)

- Frame 36 (t=3.0s): title + `config.yaml` visible, arrow with head
  present, `data.json` correctly still faded out (its fade starts at
  3.0s) — 1 circle, 6 lines, 2 texts.
- Frame 71 (t=5.9s): all four texts present (`YAML in, JSON out`,
  `config.yaml`, `data.json`, `Done.`) — 1 circle, 6 lines, 4 texts,
  3 rects (background + 2 boxes).
- `viewer.html` embeds all 72 frames and lists the (empty) notes table.

## What the tests caught before shipping

The first `check` run failed with 15 out-of-bounds issues: the YAML
box slides in from x=1120, off the 1080-wide canvas for its first
~1.2 seconds. The scene was right and the gate was too strict — so
the gate was refined instead of the scene: a slide-in/out is
legitimate motion, and an element is only flagged when it never sits
fully inside the canvas at any sampled time. After the fix the demo
passes and the gate still catches a rect stuck at x=-50 forever
(covered by `test_checks.py`).
