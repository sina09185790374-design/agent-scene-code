# agent-scene-code

Video as code: a scene is a pure function of time. Write a short scene
as JSON, render it to SVG frames, and review it frame by frame in a
self-contained viewer — no browser, no GPU, no AI image or video model.
Stdlib only, no network, no keys. English + Persian.

**Pattern** (original code; pattern only, learned from today's radar):
staryone/motlab makes every scene a canvas page with one function,
`renderAt(t)`, that draws the frame at time `t` — so the preview, the
stills and the render can never disagree — and reviews the video in a
viewer where you step frame by frame and leave notes on the exact frame
(`selection.json`), which the agent then works through by number.
nilbuild/stick-scene adds the use case: a tiny dependency-free animated
scene that *shows* what a product does, instead of a screenshot. This
tool is that idea as a small local CLI: scenes are JSON, every element
is keyframed over time, frames render to SVG, the viewer steps through
them, notes land on frames, and a `check` gate refuses broken frames.

## How it works

1. **Scene.** A project JSON: title, width/height, fps, duration,
   background, elements. Kinds: `rect`, `circle`, `line`, `arrow`,
   `text`, `stick` (a stick figure whose limbs are keyframed joint
   angles, in degrees from straight down). Any numeric prop can be
   keyframed (`linear`, `ease-in-out`, `hold`); opacity 0 hides an
   element. The same project + time always renders the same frame.
2. **Render.** `render` writes `frames/frame-NNNN.svg` (one SVG per
   frame) plus a self-contained `viewer.html` and an empty `notes.json`.
3. **Review.** Open the viewer: step frame by frame, scrub the
   timeline, play at the project fps. A problem is never described in
   chat — it is left as a note on the frame (`note --frame N --x X
   --y Y --text "..."`), stored in `notes.json` and listed in the
   viewer. Fix the scene from the notes, re-render.
4. **Check.** CI gate: elements that never enter the canvas, overlapping text,
   empty frames. A slide-in/out is legitimate motion and passes. Exit 0 = PASS, 1 = FAIL.

## Usage

```bash
python3 -m agent_scene_code demo --out demo-out
python3 -m agent_scene_code init scene.json
python3 -m agent_scene_code render scene.json --out out
python3 -m agent_scene_code check scene.json
python3 -m agent_scene_code note scene.json --out out --frame 23 --x 790 --y 1010 --text "the label covers the box edge"
```

State lives in `--out` (default `out/`): `frames/`, `viewer.html`,
`notes.json`. Exit codes: 0 success, 1 `check` failed, 2 bad input.

## Example

Demo scene (verified run: `examples/demo-run.md`): a stick figure
turns a crank and a YAML file becomes JSON — 6 seconds, 72 frames at
12 fps, 1080×1920. `check` passes; the viewer steps through all 72
frames.

---

# agent-scene-code

ویدیو به‌مثابه کد: صحنه یک تابع خالص از زمان است. یک صحنه کوتاه را به‌صورت
JSON بنویسید، آن را به فریم‌های SVG رندر کنید و فریم‌به‌فریم در یک نمایشگر
بررسی کنید — بدون مرورگر، بدون GPU، بدون مدل تصویری یا ویدیویی هوش مصنوعی.
فقط کتابخانه استاندارد پایتون؛ بدون شبکه و بدون کلید.

**الگو** (کد اصلی؛ فقط الگو، برگرفته از رادار امروز): در motlab هر صحنه یک
صفحه کانوس با یک تابع `renderAt(t)` است که فریم زمان `t` را می‌کشد — پس
پیش‌نمایش، تصویر ثابت و رندر نهایی هرگز با هم اختلاف ندارند — و بازبینی در
نمایشگری انجام می‌شود که فریم‌به‌فریم جلو می‌رود و یادداشت‌ها روی همان فریم
ثبت می‌شوند (`selection.json`) تا ایجنت آن‌ها را یکی‌یکی رفع کند. stick-scene
هم کاربرد را اضافه می‌کند: یک صحنه متحرک کوچک و بدون وابستگی که *نشان می‌دهد*
محصول چه می‌کند، به‌جای اسکرین‌شات. این ابزار همان ایده است در قالب یک CLI
کوچک محلی: صحنه‌ها JSON هستند، هر عنصر در طول زمان کی‌فریم دارد، فریم‌ها SVG
می‌شوند، نمایشگر فریم‌به‌فریم جلو می‌رود، یادداشت‌ها روی فریم می‌نشینند و
دروازه `check` فریم‌های خراب را رد می‌کند.

## روش کار

۱. **صحنه.** یک فایل JSON: عنوان، عرض/ارتفاع، fps، مدت، پس‌زمینه، عناصر.
انواع: `rect` ،`circle` ،`line` ،`arrow` ،`text` ،`stick` (آدمک خطی که
مفصل‌هایش با کی‌فریم زاویه می‌گیرند، بر حسب درجه نسبت به راستای عمودی).
هر خاصیت عددی را می‌توان کی‌فریم کرد (`linear` ،`ease-in-out` ،`hold`)؛
شفافیت صفر یعنی عنصر پنهان است. یک پروژه + یک زمان همیشه یک فریم
می‌سازند.
۲. **رندر.** دستور `render` فریم‌ها را در `frames/frame-NNNN.svg`
می‌نویسد، به‌همراه `viewer.html` و `notes.json`.
۳. **بازبینی.** نمایشگر را باز کنید: فریم‌به‌فریم جلو بروید، تایم‌لاین را
بکشید، با fps پروژه پخش کنید. مشکل هرگز در چت توصیف نمی‌شود — به‌صورت
یادداشت روی همان فریم می‌نشیند (`note --frame N --x X --y Y --text "..."`)،
در `notes.json` ذخیره و در نمایشگر فهرست می‌شود. صحنه را از روی یادداشت‌ها
اصلاح کنید و دوباره رندر بگیرید.
۴. **بررسی.** دروازه CI: عناصری که هرگز وارد بوم نمی‌شوند، متن‌های هم‌پوشان، فریم‌های
خالی. ورود/خروج کشویی حرکت مشروع است و قبول می‌شود. خروج ۰ یعنی قبول، ۱ یعنی رد.

## نمونه

صحنه نمایشی (اجرای تأییدشده: `examples/demo-run.md`): یک آدمک خطی میل‌لنگ
را می‌چرخاند و یک فایل YAML به JSON تبدیل می‌شود — ۶ ثانیه، ۷۲ فریم با
۱۲ فریم‌برثانیه، ۱۰۸۰×۱۹۲۰. دستور `check` قبول می‌شود و نمایشگر هر ۷۲ فریم
را نشان می‌دهد.
