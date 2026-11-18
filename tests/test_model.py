"""Tests for agent-scene-code model. Stdlib unittest, no network."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_scene_code import model  # noqa: E402

EXAMPLE = os.path.join(os.path.dirname(__file__), "..",
                       "examples", "yaml-to-json.json")


class InterpolateTest(unittest.TestCase):
    def test_linear_midpoint(self):
        kfs = [{"t": 0.0, "x": 60}, {"t": 1.5, "x": 300}]
        self.assertAlmostEqual(model.interpolate(kfs, 0.75, {})["x"], 180.0)

    def test_clamps_before_first_and_after_last(self):
        kfs = [{"t": 1.0, "x": 10}, {"t": 2.0, "x": 20}]
        self.assertEqual(model.interpolate(kfs, 0.0, {})["x"], 10)
        self.assertEqual(model.interpolate(kfs, 5.0, {})["x"], 20)

    def test_ease_in_out_is_slow_at_the_start(self):
        kfs = [{"t": 0.0, "x": 60}, {"t": 1.5, "x": 300, "ease": "ease-in-out"}]
        # u=0.25 -> smoothstep 0.15625 -> 60 + 240*0.15625 = 97.5
        self.assertAlmostEqual(model.interpolate(kfs, 0.375, {})["x"], 97.5)

    def test_hold_keeps_previous_value(self):
        kfs = [{"t": 0.0, "x": 10}, {"t": 1.0, "x": 20, "ease": "hold"}]
        self.assertEqual(model.interpolate(kfs, 0.5, {})["x"], 10)
        self.assertEqual(model.interpolate(kfs, 1.0, {})["x"], 20)

    def test_no_keyframes_returns_base(self):
        self.assertEqual(model.interpolate([], 3.0, {"x": 7})["x"], 7)


class StickTest(unittest.TestCase):
    def test_six_parts_and_head_position(self):
        ops = model.sample_element(
            {"kind": "stick", "x": 100, "y": 200, "scale": 1.0}, 0.0)
        self.assertEqual(len(ops), 6)
        head = ops[0]
        self.assertEqual(head["kind"], "circle")
        self.assertEqual((head["cx"], head["cy"], head["r"]), (100, 50, 18))

    def test_arm_angle_swings_forward(self):
        ops = model.sample_element(
            {"kind": "stick", "x": 100, "y": 200, "scale": 1.0,
             "arm_r": 90}, 0.0)
        # arm_r is the 3rd op (head, torso, arm_l, arm_r, ...): shoulder
        # (100, 80), length 56, 90 degrees -> endpoint (156, 80).
        arm = ops[3]
        self.assertEqual(arm["kind"], "line")
        self.assertAlmostEqual(arm["x2"], 156.0)
        self.assertAlmostEqual(arm["y2"], 80.0)

    def test_left_limb_mirrors_right(self):
        ops = model.sample_element(
            {"kind": "stick", "x": 100, "y": 200, "scale": 1.0,
             "arm_l": 90, "arm_r": 90}, 0.0)
        self.assertAlmostEqual(ops[2]["x2"], 44.0)   # arm_l swings -x
        self.assertAlmostEqual(ops[3]["x2"], 156.0)  # arm_r swings +x


class ValidateTest(unittest.TestCase):
    def test_example_project_is_valid(self):
        project = model.load_project(EXAMPLE)
        self.assertEqual(model.validate_project(project), [])
        self.assertEqual(model.frame_count(project), 72)

    def test_missing_title(self):
        project = {"width": 100, "height": 100, "fps": 10, "duration": 1.0}
        self.assertIn("missing 'title'", model.validate_project(project))

    def test_unknown_kind(self):
        project = {"title": "t", "width": 100, "height": 100, "fps": 10,
                   "duration": 1.0,
                   "elements": [{"kind": "blob", "x": 1, "y": 2}]}
        errors = model.validate_project(project)
        self.assertTrue(any("unknown kind" in e for e in errors))

    def test_keyframe_outside_duration(self):
        project = {"title": "t", "width": 100, "height": 100, "fps": 10,
                   "duration": 1.0,
                   "elements": [{"kind": "rect", "x": 1, "y": 2, "w": 3,
                                 "h": 4,
                                 "keyframes": [{"t": 5.0, "x": 9}]}]}
        errors = model.validate_project(project)
        self.assertTrue(any("outside" in e for e in errors))

    def test_unknown_ease(self):
        project = {"title": "t", "width": 100, "height": 100, "fps": 10,
                   "duration": 1.0,
                   "elements": [{"kind": "rect", "x": 1, "y": 2, "w": 3,
                                 "h": 4,
                                 "keyframes": [{"t": 0.5, "x": 9,
                                               "ease": "bounce"}]}]}
        errors = model.validate_project(project)
        self.assertTrue(any("unknown ease" in e for e in errors))

    def test_text_width_estimate(self):
        self.assertAlmostEqual(model.estimate_text_width("ab", 10), 12.0)
        # CJK chars count a full em each.
        self.assertAlmostEqual(model.estimate_text_width("\u4e2d\u6587", 10), 20.0)


if __name__ == "__main__":
    unittest.main()
