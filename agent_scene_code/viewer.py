"""Frame-by-frame review viewer: a self-contained HTML page.

The viewer embeds every rendered frame as inline SVG, steps through
them like motlab's viewer, and lists the notes from notes.json — a
note names a frame and a point, so the fix never has to be described
in chat. No network, no external assets.
"""

import json


def build_viewer(title, frames, fps, notes):
    """Return the viewer HTML string."""
    frames_json = json.dumps(frames, ensure_ascii=False)
    notes_json = json.dumps(notes, ensure_ascii=False)
    notes_rows = ""
    for note in notes:
        notes_rows += (
            '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
            % (note.get("frame", "?"), note.get("x", "?"),
               note.get("y", "?"),
               _html_escape(str(note.get("text", "")))))
    if not notes_rows:
        notes_rows = ('<tr><td colspan="4">No notes yet — add one with '
                      '<code>note --frame N --x X --y Y --text "..."</code>.'
                      '</td></tr>')
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>%s — scene review</title>
<style>
body { background:#0d1220; color:#e8ecf4; font-family:sans-serif; margin:0; padding:24px; }
h1 { font-size:20px; margin:0 0 12px; }
#stage { background:#fff; border-radius:8px; overflow:hidden; max-width:540px; margin:0 auto; }
#stage svg { display:block; width:100%%; height:auto; }
.controls { max-width:540px; margin:12px auto; display:flex; gap:8px; align-items:center; }
button { background:#1e293b; color:#e8ecf4; border:1px solid #334155; border-radius:6px; padding:8px 14px; cursor:pointer; }
button:hover { background:#334155; }
input[type=range] { flex:1; }
#label { font-variant-numeric:tabular-nums; min-width:130px; text-align:right; }
table { max-width:540px; margin:16px auto 0; border-collapse:collapse; width:100%%; font-size:14px; }
td, th { border:1px solid #334155; padding:6px 8px; text-align:left; }
th { background:#1e293b; }
</style>
</head>
<body>
<h1>%s — %d frames @ %s fps</h1>
<div id="stage"></div>
<div class="controls">
<button id="prev">&larr; Prev</button>
<button id="play">Play</button>
<button id="next">Next &rarr;</button>
<input id="scrub" type="range" min="0" max="%d" value="0">
<span id="label"></span>
</div>
<table>
<tr><th>Frame</th><th>x</th><th>y</th><th>Note</th></tr>
%s
</table>
<script>
const FRAMES = %s;
const NOTES = %s;
const FPS = %s;
let current = 0, timer = null;
const stage = document.getElementById('stage');
const label = document.getElementById('label');
const scrub = document.getElementById('scrub');
function show(i) {
  current = Math.max(0, Math.min(FRAMES.length - 1, i));
  stage.innerHTML = FRAMES[current];
  scrub.value = current;
  label.textContent = 'frame ' + current + '/' + (FRAMES.length - 1) +
    '  t=' + (current / FPS).toFixed(2) + 's';
}
document.getElementById('prev').onclick = () => { stop(); show(current - 1); };
document.getElementById('next').onclick = () => { stop(); show(current + 1); };
scrub.oninput = () => { stop(); show(parseInt(scrub.value, 10)); };
function stop() { if (timer) { clearInterval(timer); timer = null; document.getElementById('play').textContent = 'Play'; } }
document.getElementById('play').onclick = () => {
  if (timer) { stop(); return; }
  document.getElementById('play').textContent = 'Pause';
  timer = setInterval(() => { show(current + 1); if (current >= FRAMES.length - 1) stop(); }, 1000 / FPS);
};
show(0);
</script>
</body>
</html>
""" % (
        _html_escape(title), _html_escape(title), len(frames), fps,
        len(frames) - 1, notes_rows, frames_json, notes_json, fps,
    )


def _html_escape(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))
