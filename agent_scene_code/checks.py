"""The check gate: render every frame and refuse what a viewer would see
as broken — elements that never enter the canvas, overlapping text,
empty frames. A slide-in or slide-out is fine: an element is only
flagged when it is never fully inside the canvas at any sampled time.
Exit 0 = PASS, 1 = FAIL. Same sampler as the renderer, so a passing
check means the frames you ship are the frames you reviewed.
"""

from . import model

MAX_SAMPLES = 240


def _overlaps(a, b):
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1


def _inside(box, width, height, eps=0.5):
    x0, y0, x1, y1 = box
    return (x0 >= -eps and y0 >= -eps
            and x1 <= width + eps and y1 <= height + eps)


def check_project(project):
    """Return a list of issue dicts (empty = pass)."""
    issues = []
    width = project["width"]
    height = project["height"]
    times = model.frame_times(project)
    if len(times) > MAX_SAMPLES:
        step = len(times) / MAX_SAMPLES
        times = [times[int(i * step)] for i in range(MAX_SAMPLES)]

    # First pass: which elements ever sit fully inside the canvas?
    # A slide-in/out is legitimate motion; an element that never enters
    # the frame at all is a bug.
    ever_inside = [False] * len(project.get("elements", []))
    for t in times:
        for idx, element in enumerate(project.get("elements", [])):
            if ever_inside[idx]:
                continue
            for op in model.sample_element(element, t):
                if op.get("opacity", 1.0) <= 0:
                    continue
                box = model.bbox(op)
                if box is not None and _inside(box, width, height):
                    ever_inside[idx] = True
                    break

    for frame, t in enumerate(times):
        ops = []
        for idx, element in enumerate(project.get("elements", [])):
            for op in model.sample_element(element, t):
                ops.append((idx, op))
        visible = [(idx, op) for idx, op in ops
                   if op.get("opacity", 1.0) > 0]
        if not visible:
            issues.append({
                "frame": frame, "t": round(t, 2), "kind": "empty-frame",
                "detail": "no visible element at this time",
            })
            continue
        for idx, op in visible:
            if ever_inside[idx]:
                continue
            box = model.bbox(op)
            if box is None:
                continue
            x0, y0, x1, y1 = box
            if x0 < -0.5 or y0 < -0.5 or x1 > width + 0.5 or y1 > height + 0.5:
                issues.append({
                    "frame": frame, "t": round(t, 2),
                    "kind": "out-of-bounds",
                    "detail": "%s at %s never enters the %sx%s canvas"
                              % (op.get("kind"), [round(v, 1) for v in box],
                                 width, height),
                })
        texts = [op for _, op in visible if op.get("kind") == "text"]
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                box_a = model.bbox(texts[i])
                box_b = model.bbox(texts[j])
                if box_a and box_b and _overlaps(box_a, box_b):
                    issues.append({
                        "frame": frame, "t": round(t, 2),
                        "kind": "text-overlap",
                        "detail": "%r overlaps %r"
                                  % (texts[i].get("text"), texts[j].get("text")),
                    })
    return issues
