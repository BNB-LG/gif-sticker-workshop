#!/usr/bin/env python3
"""Offline GIF inspection. No network, generation, conversion, or platform claims."""

import argparse
import base64
import hashlib
import html
from io import BytesIO
import json
from pathlib import Path
import sys
import warnings

from PIL import Image, ImageDraw, UnidentifiedImageError

MAX_BYTES = 32 * 1024 * 1024
MAX_FRAMES = 256
MAX_FRAME_PIXELS = 4_000_000
MAX_TOTAL_PIXELS = 32_000_000


def inspect_gif(path):
    path = Path(path)
    report = {
        "schema_version": 1,
        "input_name": path.name,
        "actual_format": None,
        "signature": None,
        "size_bytes": None,
        "sha256": None,
        "dimensions": None,
        "frame_count": 0,
        "distinct_frames": 0,
        "duration_ms": 0,
        "loop": {"raw": None, "mode": "unspecified"},
        "frames": [],
        "decode_complete": False,
        "technical_status": "fail",
        "errors": [],
        "warnings": [],
        "platform": {"status": "not_evaluated", "profile": None, "compliant": None},
        "provenance": {"status": "not_inferred_from_pixels", "model_id": None},
        "visual_review": "pending_human_review",
        "submission_ready": False,
        "artifacts": {},
    }
    decoded = []
    raw = b""
    try:
        # Bound reads even if the file changes between stat and open.
        report["size_bytes"] = path.stat().st_size
        if report["size_bytes"] > MAX_BYTES:
            report["errors"].append("file_size_limit_exceeded")
            return report, decoded, raw
        with path.open("rb") as source:
            raw = source.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            report["errors"].append("file_size_limit_exceeded")
            return report, decoded, b""
    except OSError:
        report["errors"].append("input_unreadable")
        return report, decoded, raw
    report["size_bytes"] = len(raw)
    report["sha256"] = hashlib.sha256(raw).hexdigest()
    signature_ok = raw[:6] in (b"GIF87a", b"GIF89a")
    report["signature"] = raw[:6].decode("ascii") if signature_ok else raw[:6].hex()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as source:
                report["actual_format"] = source.format
                report["dimensions"] = {"width": source.width, "height": source.height}
                if source.format != "GIF" or not signature_ok:
                    report["errors"].append("not_gif")
                    return report, decoded, raw
                loop = source.info.get("loop")
                report["loop"] = {"raw": loop, "mode": "infinite" if loop == 0 else "finite" if loop is not None else "unspecified"}
                if loop != 0:
                    report["warnings"].append("loop_not_infinite")
                total_pixels = 0
                index = 0
                while True:
                    try:
                        source.seek(index)
                    except EOFError:
                        report["decode_complete"] = True
                        break
                    if index >= MAX_FRAMES:
                        report["errors"].append("frame_limit_exceeded")
                        break
                    pixels = source.width * source.height
                    total_pixels += pixels
                    if pixels > MAX_FRAME_PIXELS or total_pixels > MAX_TOTAL_PIXELS:
                        report["errors"].append("pixel_limit_exceeded")
                        break
                    # Pillow applies palette, frame offsets and disposal while seeking.
                    frame = source.convert("RGBA")
                    canonical = Image.new("RGBA", frame.size, (0, 0, 0, 0))
                    canonical.paste(frame, (0, 0), frame.getchannel("A"))
                    digest = hashlib.sha256(str(frame.size).encode("ascii") + canonical.tobytes()).hexdigest()
                    duration = source.info.get("duration", 0)
                    duration = duration if isinstance(duration, int) else 0
                    report["frames"].append({
                        "index": index, "duration_ms": duration, "sha256_rgba": digest,
                        "width": frame.width, "height": frame.height,
                        "disposal": getattr(source, "disposal_method", None),
                    })
                    decoded.append(frame)
                    index += 1
    except (OSError, ValueError, SyntaxError, EOFError, UnidentifiedImageError,
            Image.DecompressionBombError, Image.DecompressionBombWarning):
        report["errors"].append("decode_error")
    report["frame_count"] = len(decoded)
    report["distinct_frames"] = len({frame["sha256_rgba"] for frame in report["frames"]})
    report["duration_ms"] = sum(frame["duration_ms"] for frame in report["frames"])
    if report["decode_complete"]:
        if len(decoded) < 2:
            report["errors"].append("single_frame")
        if report["distinct_frames"] < 2:
            report["errors"].append("no_visible_change")
        if any(frame["duration_ms"] <= 0 for frame in report["frames"]):
            report["errors"].append("invalid_frame_duration")
        if report["distinct_frames"] < len(decoded):
            report["warnings"].append("repeated_frames_present")
    if not report["errors"] and report["decode_complete"]:
        report["technical_status"] = "pass"
    return report, decoded, raw


def contact_sheet(frames, metadata):
    columns = min(4, max(1, len(frames)))
    rows = max(1, (len(frames) + columns - 1) // columns)
    sheet = Image.new("RGB", (columns * 196, rows * 220), "#eeeeee")
    draw = ImageDraw.Draw(sheet)
    if not frames:
        draw.text((12, 20), "No decodable GIF frames", fill="black")
    for index, frame in enumerate(frames):
        left, top = (index % columns) * 196, (index // columns) * 220
        thumb = frame.copy()
        thumb.thumbnail((180, 180))
        sheet.paste(thumb, (left + 8, top + 8), thumb)
        draw.text((left + 8, top + 192), f"#{index:03d}  {metadata[index]['duration_ms']} ms", fill="black")
    return sheet


def write_artifacts(output, report, frames, raw):
    frame_dir = output / "frames"
    frame_dir.mkdir()
    png_data = []
    for index, frame in enumerate(frames):
        buffer = BytesIO()
        frame.save(buffer, format="PNG")
        data = buffer.getvalue()
        (frame_dir / f"frame-{index:03d}.png").write_bytes(data)
        png_data.append("data:image/png;base64," + base64.b64encode(data).decode("ascii"))
    contact_sheet(frames, report["frames"]).save(output / "contact-sheet.png")
    report["artifacts"] = {"json": "audit.json", "contact_sheet": "contact-sheet.png", "html": "preview.html", "frames": "frames/"}
    summary = json.dumps(report, ensure_ascii=False, indent=2)
    (output / "audit.json").write_text(summary + "\n", encoding="utf-8")
    original = ""
    if report["actual_format"] == "GIF" and report["decode_complete"]:
        original = '<img id="original" alt="原始 GIF 播放" src="data:image/gif;base64,' + base64.b64encode(raw).decode("ascii") + '">'
    frame_json = json.dumps(png_data)
    durations = json.dumps([item["duration_ms"] for item in report["frames"]])
    document = """<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>GIF 逐帧核验</title>
<style>
body{font:16px/1.6 system-ui,sans-serif;margin:24px auto;padding:0 16px;max-width:1000px;color:#202320;background:#fafafa;letter-spacing:0}
h1{font-size:24px}h2{font-size:20px}img{max-width:100%;object-fit:contain;background:#ddd}
.views{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:24px}
.stage{min-height:200px}button,input{font:inherit}button{margin:4px;padding:6px 10px;cursor:pointer}
input{max-width:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eee;padding:12px}
.notice{border-left:4px solid #b25525;padding-left:12px}#frame{max-height:500px}section{min-width:0}
</style>
<h1>GIF 逐帧核验</h1><p>文件：__NAME__</p>
<p class="notice">技术状态：__STATUS__。人工动作审查尚未完成；没有经过验证的平台规范 profile，不构成投稿包。</p>
<div class="views"><section><h2>原始 GIF</h2><div class="stage">__ORIGINAL__</div>
<p>此处直接播放原文件字节，未重新编码。实际速度以播放器为准。</p></section>
<section><h2>解码帧</h2><div class="stage"><img id="frame" alt="当前解码帧"></div>
<div><button id="prev" title="上一帧" aria-label="上一帧">&#9664;</button><button id="play">播放解码帧</button><button id="next" title="下一帧" aria-label="下一帧">&#9654;</button></div>
<input id="seek" type="range" min="0" value="0" aria-label="帧索引"><output id="label"></output>
<p>解码帧回放是检查工具，会重复播放；不代表原文件的 loop。原文件 loop 见下方 JSON。</p></section></div>
<h2>人工检查</h2><ul><li>五官、肢体和配件在相邻帧是否稳定。</li><li>动作是否有准备、执行、收尾，而非整张静态图平移或旋转。</li><li>首尾衔接是否突跳，是否有残影、裁切、文字跳动。</li></ul>
<h2>原始检测结果</h2><pre>__SUMMARY__</pre>
<script>
const frames=__FRAMES__, durations=__DURATIONS__;
const frame=document.getElementById('frame'), seek=document.getElementById('seek'), label=document.getElementById('label'), play=document.getElementById('play');
let index=0, timer=null;
function show(){if(!frames.length){label.textContent='没有可显示的 GIF 帧';return;}frame.src=frames[index];seek.value=index;label.textContent=` ${index+1}/${frames.length} | ${durations[index]} ms`;}
function stop(){clearTimeout(timer);timer=null;play.textContent='播放解码帧';}
function advance(){timer=setTimeout(()=>{index=(index+1)%frames.length;show();advance();},Math.max(20,durations[index]||100));}
seek.max=Math.max(0,frames.length-1);
document.getElementById('prev').onclick=()=>{stop();index=(index-1+frames.length)%frames.length;show();};
document.getElementById('next').onclick=()=>{stop();index=(index+1)%frames.length;show();};
seek.oninput=()=>{stop();index=Number(seek.value);show();};
play.onclick=()=>{if(timer!==null){stop();}else if(frames.length){play.textContent='暂停';advance();}};
if(!frames.length){for(const element of document.querySelectorAll('button,input'))element.disabled=true;frame.hidden=true;}
show();
</script></html>
"""
    # No untrusted filename or JSON is interpolated into executable JavaScript.
    values = {"NAME": html.escape(report["input_name"]), "STATUS": report["technical_status"],
              "ORIGINAL": original, "SUMMARY": html.escape(summary), "FRAMES": frame_json,
              "DURATIONS": durations}
    for key, value in values.items():
        document = document.replace("__" + key + "__", value)
    (output / "preview.html").write_text(document, encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline GIF audit; never certifies platform compliance.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit = subparsers.add_parser("audit", help="Inspect a GIF without modifying it")
    audit.add_argument("input", type=Path)
    audit.add_argument("--out", type=Path, required=True, help="New output directory; existing paths are refused")
    args = parser.parse_args(argv)
    try:
        args.out.mkdir(parents=True, exist_ok=False)
    except OSError:
        print("Output directory must be new and writable; no files overwritten.", file=sys.stderr)
        return 2
    report, frames, raw = inspect_gif(args.input)
    try:
        write_artifacts(args.out, report, frames, raw)
    except OSError:
        print("Could not write all artifacts; output is incomplete.", file=sys.stderr)
        return 2
    print(json.dumps({"technical_status": report["technical_status"], "frame_count": report["frame_count"],
                      "distinct_frames": report["distinct_frames"], "errors": report["errors"],
                      "platform_status": "not_evaluated", "submission_ready": False}))
    if "input_unreadable" in report["errors"]:
        return 2
    return 0 if report["technical_status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
