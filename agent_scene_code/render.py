"""Draw ops -> SVG. Deterministic: same project + time = same bytes."""

import math
from xml.sax.saxutils import escape

from . import model


def _n(value):
    """Format a number short and stable (2 decimals max, no -0)."""
    text = "%.2f" % float(value)
    text = text.rstrip("0").rstrip(".")
    if text in ("", "-0"):
        return "0"
    return text


def _arrow_head(x1, y1, x2, y2, size=14.0):
    """A filled triangle at (x2, y2) pointing back along the arrow."""
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length == 0:
        return ""
    ux, uy = dx / length, dy / length
    # Two base corners, perpendicular to the arrow direction.
    bx, by = x2 - ux * size, y2 - uy * size
    px, py = -uy * size * 0.55, ux * size * 0.55
    return '<polygon points="%s,%s %s,%s %s,%s" fill="%s" />' % (
        _n(x2), _n(y2), _n(bx + px), _n(by + py), _n(bx - px), _n(by - py),
        "currentColor")


def op_to_svg(op):
    """One draw op -> one SVG element string."""
    kind = op.get("kind")
    opacity = op.get("opacity", 1.0)
    if opacity <= 0:
        return ""
    if kind == "rect":
        return (
            '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" '
            'fill-opacity="%s" />' % (
                _n(op["x"]), _n(op["y"]), _n(op["w"]), _n(op["h"]),
                _n(op.get("rx", 0)), escape(str(op.get("fill", "#888888"))),
                _n(opacity)))
    if kind == "circle":
        fill = op.get("fill")
        stroke = op.get("stroke")
        if fill is None and stroke is not None:
            return (
                '<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" '
                'stroke-width="%s" opacity="%s" />' % (
                    _n(op["cx"]), _n(op["cy"]), _n(op["r"]),
                    escape(str(stroke)), _n(op.get("width", 4)), _n(opacity)))
        return (
            '<circle cx="%s" cy="%s" r="%s" fill="%s" opacity="%s" />' % (
                _n(op["cx"]), _n(op["cy"]), _n(op["r"]),
                escape(str(fill or "#888888")), _n(opacity)))
    if kind in ("line", "arrow"):
        stroke = escape(str(op.get("stroke", "#111111")))
        line = (
            '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" '
            'stroke-width="%s" stroke-linecap="round" opacity="%s" />' % (
                _n(op["x1"]), _n(op["y1"]), _n(op["x2"]), _n(op["y2"]),
                stroke, _n(op.get("width", 4)), _n(opacity)))
        if kind == "arrow":
            head = _arrow_head(op["x1"], op["y1"], op["x2"], op["y2"])
            head = head.replace("currentColor", stroke)
            return line + head
        return line
    if kind == "text":
        anchor = op.get("anchor", "start")
        return (
            '<text x="%s" y="%s" font-size="%s" fill="%s" '
            'text-anchor="%s" font-family="sans-serif" opacity="%s">%s</text>'
            % (_n(op["x"]), _n(op["y"]), _n(op.get("size", 32)),
               escape(str(op.get("fill", "#111111"))), anchor,
               _n(opacity), escape(str(op.get("text", "")))))
    return ""


def render_frame(project, t):
    """The full SVG document for the project at time t."""
    width = project["width"]
    height = project["height"]
    background = project.get("background", "#FFFFFF")
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" '
        'viewBox="0 0 %s %s">' % (width, height, width, height),
        '<rect x="0" y="0" width="%s" height="%s" fill="%s" />'
        % (width, height, escape(str(background))),
    ]
    for op in model.sample(project, t):
        svg = op_to_svg(op)
        if svg:
            parts.append(svg)
    parts.append("</svg>")
    return "".join(parts)
