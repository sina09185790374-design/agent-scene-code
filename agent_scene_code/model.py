"""Scene model: a scene is a pure function of time.

A project is JSON: title, width, height, fps, duration, background,
elements[]. Every element has base props plus optional keyframes that
override numeric props over time. ``sample(project, t)`` returns the
list of draw ops visible at time ``t`` — the same function the renderer,
the viewer and the check gate all use, so preview, stills and checks
can never disagree about a frame.

Element kinds: rect, circle, line, arrow, text, stick (a stick figure
whose limbs are keyframed joint angles, drawn from a ground point).
"""

import json
import math

EASINGS = ("linear", "ease-in-out", "hold")
KINDS = ("rect", "circle", "line", "arrow", "text", "stick")

# Numeric props a keyframe may animate.
NUMERIC_PROPS = (
    "x", "y", "w", "h", "r", "opacity", "size", "scale",
    "x1", "y1", "x2", "y2", "arm_l", "arm_r", "leg_l", "leg_r",
)


def lerp(a, b, u):
    """Linear interpolation between a and b."""
    return a + (b - a) * u


def ease_in_out(u):
    """Smoothstep easing."""
    return u * u * (3.0 - 2.0 * u)


def _apply_ease(name, u):
    if name == "ease-in-out":
        return ease_in_out(u)
    if name == "hold":
        return 0.0
    return u


def interpolate(keyframes, t, base):
    """Merge keyframed numeric props at time t over base props.

    The ease of a segment is read from the keyframe that ends it.
    ``hold`` keeps the previous value until the next keyframe time.
    """
    props = dict(base)
    if not keyframes:
        return props
    ordered = sorted(keyframes, key=lambda k: k["t"])
    keys = set()
    for kf in ordered:
        keys |= {k for k in kf if k not in ("t", "ease")}
    for key in keys:
        pts = [(kf["t"], kf[key]) for kf in ordered if key in kf]
        if not pts:
            continue
        if t <= pts[0][0]:
            props[key] = pts[0][1]
            continue
        if t >= pts[-1][0]:
            props[key] = pts[-1][1]
            continue
        for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
            if t0 <= t <= t1:
                if t1 == t0:
                    u = 1.0
                else:
                    u = (t - t0) / (t1 - t0)
                ease = "linear"
                for kf in ordered:
                    if kf["t"] == t1 and "ease" in kf:
                        ease = kf["ease"]
                props[key] = lerp(v0, v1, _apply_ease(ease, u))
                break
    return props


def _stick_ops(props):
    """A stick figure drawn from a ground point (x, y = feet).

    Angles are degrees from straight down; positive swings toward +x.
    """
    x = props.get("x", 0.0)
    y = props.get("y", 0.0)
    s = props.get("scale", 1.0)
    color = props.get("color", "#111111")
    opacity = props.get("opacity", 1.0)
    width = 6.0 * s
    ops = []

    def line(x1, y1, x2, y2):
        ops.append({
            "kind": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "stroke": color, "width": width, "opacity": opacity,
        })

    def limb(px, py, angle_deg, length):
        a = math.radians(angle_deg)
        return (px + length * math.sin(a), py + length * math.cos(a))

    head_cy = y - 150.0 * s
    shoulder = (x, y - 120.0 * s)
    hip = (x, y - 66.0 * s)
    ops.append({
        "kind": "circle", "cx": x, "cy": head_cy, "r": 18.0 * s,
        "fill": "none", "stroke": color, "width": width,
        "opacity": opacity,
    })
    line(x, y - 132.0 * s, x, y - 66.0 * s)  # torso
    for key, px, py, length in (
        ("arm_l", shoulder[0], shoulder[1], 56.0 * s),
        ("arm_r", shoulder[0], shoulder[1], 56.0 * s),
        ("leg_l", hip[0], hip[1], 70.0 * s),
        ("leg_r", hip[0], hip[1], 70.0 * s),
    ):
        angle = props.get(key, 0.0)
        if key in ("arm_l", "leg_l"):
            angle = -angle
        ex, ey = limb(px, py, angle, length)
        line(px, py, ex, ey)
    return ops


def sample_element(element, t):
    """Draw ops for one element at time t."""
    props = interpolate(element.get("keyframes", []), t, element)
    kind = element.get("kind")
    if kind == "stick":
        return _stick_ops(props)
    op = dict(props)
    op["kind"] = kind
    return [op]


def sample(project, t):
    """All draw ops of the project at time t, in z order."""
    ops = []
    for element in project.get("elements", []):
        ops.extend(sample_element(element, t))
    return ops


def estimate_text_width(text, size):
    """Rough text width: 0.6em per Latin char, 1.0em per CJK char."""
    total = 0.0
    for ch in text:
        code = ord(ch)
        if 0x2E80 <= code <= 0x9FFF or 0xAC00 <= code <= 0xD7A3 \
                or 0xF900 <= code <= 0xFAFF:
            total += 1.0 * size
        else:
            total += 0.6 * size
    return total


def bbox(op):
    """Bounding box (x0, y0, x1, y1) of a draw op, or None."""
    kind = op.get("kind")
    if kind == "rect":
        return (op["x"], op["y"], op["x"] + op["w"], op["y"] + op["h"])
    if kind == "circle":
        return (op["cx"] - op["r"], op["cy"] - op["r"],
                op["cx"] + op["r"], op["cy"] + op["r"])
    if kind in ("line", "arrow"):
        return (min(op["x1"], op["x2"]), min(op["y1"], op["y2"]),
                max(op["x1"], op["x2"]), max(op["y1"], op["y2"]))
    if kind == "text":
        w = estimate_text_width(op.get("text", ""), op.get("size", 32))
        size = op.get("size", 32)
        anchor = op.get("anchor", "start")
        x = op["x"]
        if anchor == "middle":
            x0, x1 = x - w / 2.0, x + w / 2.0
        elif anchor == "end":
            x0, x1 = x - w, x
        else:
            x0, x1 = x, x + w
        return (x0, op["y"] - size, x1, op["y"] + size * 0.2)
    return None


def frame_times(project):
    """Sample times, one per frame, from 0 to duration (exclusive end)."""
    fps = project["fps"]
    count = int(project["duration"] * fps)
    return [i / fps for i in range(max(count, 1))]


def frame_count(project):
    return len(frame_times(project))


def load_project(path):
    """Load a project JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_project(project):
    """Return a list of error strings; empty means the project is valid."""
    errors = []
    if not isinstance(project, dict):
        return ["project must be a JSON object"]
    for key in ("title", "width", "height", "fps", "duration"):
        if key not in project:
            errors.append("missing %r" % key)
    if errors:
        return errors
    if not isinstance(project["width"], (int, float)) or project["width"] <= 0:
        errors.append("width must be a positive number")
    if not isinstance(project["height"], (int, float)) or project["height"] <= 0:
        errors.append("height must be a positive number")
    if not isinstance(project["fps"], (int, float)) or project["fps"] <= 0:
        errors.append("fps must be a positive number")
    if not isinstance(project["duration"], (int, float)) or project["duration"] <= 0:
        errors.append("duration must be a positive number")
    if project.get("duration", 0) * project.get("fps", 0) > 3600:
        errors.append("project has more than 3600 frames; shorten it")
    elements = project.get("elements", [])
    if not isinstance(elements, list):
        errors.append("elements must be a list")
        return errors
    for idx, el in enumerate(elements):
        if not isinstance(el, dict):
            errors.append("elements[%d] must be an object" % idx)
            continue
        kind = el.get("kind")
        if kind not in KINDS:
            errors.append("elements[%d] has unknown kind %r" % (idx, kind))
            continue
        if kind == "text" and "text" not in el:
            errors.append("elements[%d] (text) is missing 'text'" % idx)
        for kf in el.get("keyframes", []) or []:
            if not isinstance(kf, dict) or "t" not in kf:
                errors.append("elements[%d] has a keyframe without 't'" % idx)
                continue
            if kf["t"] < 0 or kf["t"] > project["duration"]:
                errors.append(
                    "elements[%d] keyframe t=%s is outside [0, %s]"
                    % (idx, kf["t"], project["duration"]))
            if kf.get("ease") not in (None,) + EASINGS:
                errors.append(
                    "elements[%d] keyframe has unknown ease %r" % (idx, kf.get("ease")))
            for key, value in kf.items():
                if key in ("t", "ease"):
                    continue
                if key not in NUMERIC_PROPS:
                    errors.append(
                        "elements[%d] keyframe animates unknown prop %r" % (idx, key))
                elif not isinstance(value, (int, float)):
                    errors.append(
                        "elements[%d] keyframe prop %r must be a number" % (idx, key))
    return errors
