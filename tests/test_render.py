"""Tests for the SVG renderer. Stdlib unittest, no network."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_scene_code import model, render  # noqa: E402

EXAMPLE = os.path.join(os.path.dirname(__file__), "..",
                       "examples", "yaml-to-json.json")


def _project():
    return model.load_project(EXAMPLE)


class RenderTest(unittest.TestCase):
    def test_frame_is_svg_with_background(self):
        svg = render.render_frame(_project(), 0.0)
        self.assertTrue(svg.startswith("<svg "))
        self.assertIn('fill="#0D1220"', svg)
        self.assertTrue(svg.endswith("</svg>"))

    def test_deterministic(self):
        project = _project()
        self.assertEqual(render.render_frame(project, 1.0),
                         render.render_frame(project, 1.0))

    def test_frames_differ_over_time(self):
        project = _project()
        self.assertNotEqual(render.render_frame(project, 0.0),
                            render.render_frame(project, 5.9))

    def test_text_is_escaped(self):
        op = {"kind": "text", "x": 10, "y": 20, "text": "a < b & c",
              "size": 32}
        svg = render.op_to_svg(op)
        self.assertIn("a &lt; b &amp; c", svg)
        self.assertNotIn("a < b", svg)

    def test_opacity_zero_renders_nothing(self):
        op = {"kind": "rect", "x": 0, "y": 0, "w": 10, "h": 10,
              "opacity": 0}
        self.assertEqual(render.op_to_svg(op), "")

    def test_arrow_has_a_head(self):
        op = {"kind": "arrow", "x1": 0, "y1": 0, "x2": 0, "y2": 100,
              "stroke": "#000000"}
        svg = render.op_to_svg(op)
        self.assertIn("<line ", svg)
        self.assertIn("<polygon ", svg)

    def test_stick_renders_as_lines_and_circle(self):
        project = _project()
        svg = render.render_frame(project, 3.0)
        self.assertIn("<circle ", svg)
        self.assertIn("<line ", svg)


if __name__ == "__main__":
    unittest.main()
