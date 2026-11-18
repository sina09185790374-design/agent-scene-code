"""End-to-end CLI tests. Stdlib unittest, no network, subprocess only."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.join(os.path.dirname(__file__), "..")
EXAMPLE = os.path.join(REPO, "examples", "yaml-to-json.json")


def _run(args, cwd):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.abspath(REPO)
    return subprocess.run(
        [sys.executable, "-m", "agent_scene_code"] + args,
        cwd=cwd, env=env, capture_output=True, text=True, timeout=120)


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="scene-code-test-")

    def test_init_writes_example(self):
        result = _run(["init", "scene.json"], self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "scene.json")))

    def test_init_refuses_overwrite_without_force(self):
        _run(["init", "scene.json"], self.tmp)
        result = _run(["init", "scene.json"], self.tmp)
        self.assertEqual(result.returncode, 2)

    def test_demo_renders_72_frames_and_passes_check(self):
        result = _run(["demo", "--out", "demo-out"], self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        frames = os.listdir(os.path.join(self.tmp, "demo-out", "frames"))
        self.assertEqual(len(frames), 72)
        self.assertTrue(os.path.exists(
            os.path.join(self.tmp, "demo-out", "viewer.html")))
        check = _run(["check", EXAMPLE], self.tmp)
        self.assertEqual(check.returncode, 0, check.stdout)
        self.assertIn("PASS", check.stdout)

    def test_render_then_note_round_trip(self):
        result = _run(["render", EXAMPLE, "--out", "out"], self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = _run(["note", EXAMPLE, "--out", "out", "--frame", "23",
                       "--x", "790", "--y", "1010",
                       "--text", "label covers the box edge"], self.tmp)
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(os.path.join(self.tmp, "out", "notes.json"),
                  encoding="utf-8") as fh:
            notes = json.load(fh)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["frame"], 23)
        # Re-render keeps the note and shows it in the viewer.
        _run(["render", EXAMPLE, "--out", "out"], self.tmp)
        with open(os.path.join(self.tmp, "out", "viewer.html"),
                  encoding="utf-8") as fh:
            html = fh.read()
        self.assertIn("label covers the box edge", html)
        self.assertIn("frame-0023.svg",
                      os.listdir(os.path.join(self.tmp, "out", "frames")))

    def test_check_fails_on_broken_scene(self):
        broken = os.path.join(self.tmp, "broken.json")
        with open(broken, "w", encoding="utf-8") as fh:
            json.dump({"title": "broken", "width": 400, "height": 400,
                       "fps": 2, "duration": 1.0,
                       "elements": [{"kind": "rect", "x": -50, "y": 10,
                                     "w": 60, "h": 60}]}, fh)
        result = _run(["check", broken], self.tmp)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL", result.stdout)
        self.assertIn("out-of-bounds", result.stdout)

    def test_note_rejects_frame_out_of_range(self):
        result = _run(["note", EXAMPLE, "--out", "out", "--frame", "72",
                       "--x", "1", "--y", "1", "--text", "x"], self.tmp)
        self.assertEqual(result.returncode, 2)

    def test_bad_project_is_rejected(self):
        bad = os.path.join(self.tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        result = _run(["check", bad], self.tmp)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
