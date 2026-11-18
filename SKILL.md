# agent-scene-code — skill

Use this when an agent needs a short animated explainer scene that shows
what a product does — a tiny video-as-code scene, no AI image or video
model, no browser, no GPU.

## The loop

1. **Brief.** One sentence: what the scene shows (e.g. "our CLI turns a
   YAML file into JSON"). Three beats max: setup → action → payoff.
2. **Write the scene.** A project JSON (`init` copies the example):
   title, width/height, fps, duration, background, elements. Kinds:
   `rect`, `circle`, `line`, `arrow`, `text`, `stick` (a stick figure
   whose `arm_l`/`arm_r`/`leg_l`/`leg_r` are keyframed joint angles in
   degrees from straight down). Animate numeric props with `keyframes`
   (`linear`, `ease-in-out`, `hold`); opacity 0 hides an element.
3. **Render.** `python3 -m agent_scene_code render scene.json --out out`
   writes `frames/frame-NNNN.svg` + `viewer.html` + `notes.json`.
4. **Review frame by frame.** Open `viewer.html`, step through the
   frames. Do not describe a problem in chat — leave a note on the
   frame: `note scene.json --out out --frame 23 --x 790 --y 1010
   --text "the label covers the box edge"`. Notes live in `notes.json`
   and are listed in the viewer.
5. **Fix from the notes, re-render, re-check.** `check scene.json`
   is the CI gate: elements that never enter the canvas, overlapping
   text, empty frames (a slide-in/out is legitimate motion and passes).
   Exit 0 = PASS.

## Rules

- A scene is a pure function of time: the same project + time always
  renders the same frame. Never hand-edit a rendered frame; fix the
  scene and re-render.
- Keep it small: one scene, ≤ 3 beats, ≤ 10 seconds, ≤ 12 elements.
- Text stays inside the canvas — the check gate enforces it, and the
  viewer is the proof.
- No network, no keys, no model calls: the tool never reads `.env`.
