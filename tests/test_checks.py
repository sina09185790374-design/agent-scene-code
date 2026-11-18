"""Tests for the check gate. Stdlib unittest, no network."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_scene_code import checks, model  # noqa: E402

EXAMPLE = os.path.join(os.path.dirname(__file__), "..",
                       "examples", "yaml-to-json.json")


def _base(**overrides):
    project = {"title": "t", "width": 400, "height": 400, "fps": 2,
               "duration": 1.0, "elements": []}
    project.update(overrides)
    return project


class CheckTest(unittest.TestCase):
    def test_demo_project_passes(self):
        project = model.load_project(EXAMPLE)
        self.assertEqual(checks.check_project(project), [])

    def test_out_of_bounds_rect_is_flagged(self):
        project = _base(elements=[
            {"kind": "rect", "x": -50, "y": 10, "w": 60, "h": 60}])
        issues = checks.check_project(project)
        self.assertTrue(any(i["kind"] == "out-of-bounds" for i in issues))

    def test_overlapping_text_is_flagged(self):
        project = _base(elements=[
            {"kind": "text", "x": 100, "y": 100, "text": "hello",
             "size": 40},
            {"kind": "text", "x": 110, "y": 110, "text": "world",
             "size": 40},
        ])
        issues = checks.check_project(project)
        self.assertTrue(any(i["kind"] == "text-overlap" for i in issues))

    def test_non_overlapping_text_passes(self):
        project = _base(elements=[
            {"kind": "text", "x": 10, "y": 100, "text": "hello",
             "size": 40},
            {"kind": "text", "x": 10, "y": 300, "text": "world",
             "size": 40},
        ])
        self.assertEqual(checks.check_project(project), [])

    def test_empty_frame_is_flagged(self):
        # Text only fades in at t=1.0; frame 0 (t=0) is empty.
        project = _base(elements=[
            {"kind": "text", "x": 10, "y": 100, "text": "late",
             "size": 40, "opacity": 0,
             "keyframes": [{"t": 0.0, "opacity": 0},
                           {"t": 1.0, "opacity": 1}]},
        ])
        issues = checks.check_project(project)
        self.assertTrue(any(i["kind"] == "empty-frame" for i in issues))
        self.assertEqual(issues[0]["frame"], 0)


if __name__ == "__main__":
    unittest.main()
