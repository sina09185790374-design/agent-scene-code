"""agent-scene-code: video as code, stdlib only.

Scenes are JSON: every element is keyframed over time, and the whole
scene is a pure function of time — renderAt(t) in motlab's sense, but
drawn by our own SVG renderer, so no browser, no GPU and no AI model
is needed. Render the frames, review them in the viewer, leave notes
on frames, fix, re-render.
"""

import argparse
import json
import os
import shutil
import sys

from . import checks, model, render, viewer

VERSION = "0.1.0"


def _here(*parts):
    return os.path.join(os.path.dirname(__file__), *parts)


def _example_path():
    return os.path.join(_here(os.pardir), "examples", "yaml-to-json.json")


def _load_or_die(path):
    try:
        project = model.load_project(path)
    except (OSError, ValueError) as exc:
        print("cannot load %s: %s" % (path, exc), file=sys.stderr)
        return None
    errors = model.validate_project(project)
    if errors:
        for error in errors:
            print("invalid project: %s" % error, file=sys.stderr)
        return None
    return project


def _read_notes(out_dir):
    path = os.path.join(out_dir, "notes.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            notes = json.load(fh)
        return notes if isinstance(notes, list) else []
    except (OSError, ValueError):
        return []


def cmd_init(args):
    dest = args.dest
    if os.path.exists(dest) and not args.force:
        print("refusing to overwrite %s (use --force)" % dest, file=sys.stderr)
        return 2
    shutil.copyfile(_example_path(), dest)
    print("wrote example scene to %s" % dest)
    return 0


def cmd_render(args):
    project = _load_or_die(args.project)
    if project is None:
        return 2
    frames_dir = os.path.join(args.out, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    frames = []
    for index, t in enumerate(model.frame_times(project)):
        svg = render.render_frame(project, t)
        frames.append(svg)
        with open(os.path.join(frames_dir, "frame-%04d.svg" % index),
                  "w", encoding="utf-8") as fh:
            fh.write(svg)
    notes = _read_notes(args.out)
    html = viewer.build_viewer(project["title"], frames, project["fps"], notes)
    with open(os.path.join(args.out, "viewer.html"), "w",
              encoding="utf-8") as fh:
        fh.write(html)
    if not os.path.exists(os.path.join(args.out, "notes.json")):
        with open(os.path.join(args.out, "notes.json"), "w",
                  encoding="utf-8") as fh:
            json.dump([], fh)
    print("rendered %d frames to %s (open %s)"
          % (len(frames), args.out,
             os.path.join(args.out, "viewer.html")))
    return 0


def cmd_check(args):
    project = _load_or_die(args.project)
    if project is None:
        return 2
    issues = checks.check_project(project)
    if not issues:
        print("PASS: %d frames, no issues"
              % model.frame_count(project))
        return 0
    print("FAIL: %d issue(s) in %d frames"
          % (len(issues), model.frame_count(project)))
    for issue in issues:
        print("  frame %(frame)d t=%(t)ss [%(kind)s] %(detail)s" % issue)
    return 1


def cmd_note(args):
    notes = _read_notes(args.out)
    project = _load_or_die(args.project)
    if project is None:
        return 2
    count = model.frame_count(project)
    if args.frame < 0 or args.frame >= count:
        print("frame must be in [0, %d)" % count, file=sys.stderr)
        return 2
    notes.append({"frame": args.frame, "x": args.x, "y": args.y,
                  "text": args.text})
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "notes.json"), "w",
              encoding="utf-8") as fh:
        json.dump(notes, fh, ensure_ascii=False, indent=2)
    print("note added on frame %d (%d note(s) total)"
          % (args.frame, len(notes)))
    return 0


def cmd_demo(args):
    project = _load_or_die(_example_path())
    if project is None:
        return 2
    args.project = _example_path()
    code = cmd_render(args)
    if code != 0:
        return code
    print("demo: %s — %d frames, %ss at %s fps"
          % (project["title"], model.frame_count(project),
             project["duration"], project["fps"]))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="agent-scene-code",
        description="Video as code: a scene is a pure function of time; "
                    "render it to SVG frames and review them frame by frame.")
    parser.add_argument("--version", action="version",
                        version="agent-scene-code %s" % VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="write the example scene to a file")
    p.add_argument("dest", nargs="?", default="scene.json")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("render", help="render frames + review viewer")
    p.add_argument("project")
    p.add_argument("--out", default="out")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("check", help="CI gate: bounds, overlap, empty frames")
    p.add_argument("project")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("note", help="leave a note on a frame")
    p.add_argument("project")
    p.add_argument("--out", default="out")
    p.add_argument("--frame", type=int, required=True)
    p.add_argument("--x", type=float, required=True)
    p.add_argument("--y", type=float, required=True)
    p.add_argument("--text", required=True)
    p.set_defaults(func=cmd_note)

    p = sub.add_parser("demo", help="render the bundled example scene")
    p.add_argument("--out", default="demo-out")
    p.set_defaults(func=cmd_demo)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
