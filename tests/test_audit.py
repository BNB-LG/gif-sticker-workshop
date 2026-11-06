import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_gif.py"


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "tests")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, name="motion.gif", count=3, loop=0, duration=100):
        frames = []
        for index in range(count):
            frame = Image.new("RGB", (48, 40), "white")
            ImageDraw.Draw(frame).rectangle((4 + index * 8, 10, 12 + index * 8, 20), fill="red")
            frames.append(frame)
        options = {"save_all": True, "append_images": frames[1:], "duration": duration}
        if loop is not None:
            options["loop"] = loop
        path = self.root / name
        frames[0].save(path, format="GIF", **options)
        return path

    def run_audit(self, path, expected=0, out="qa"):
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "audit", str(path), "--out", str(self.root / out)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, expected, result.stderr + result.stdout)
        report_path = self.root / out / "audit.json"
        self.assertTrue(report_path.exists(), result.stderr)
        return json.loads(report_path.read_text()), result

    def test_true_multiframe_and_artifacts(self):
        path = self.fixture()
        report, _ = self.run_audit(path)
        self.assertEqual(report["actual_format"], "GIF")
        self.assertEqual(report["frame_count"], 3)
        self.assertEqual(report["distinct_frames"], 3)
        self.assertEqual(report["duration_ms"], 300)
        self.assertEqual(report["dimensions"], {"width": 48, "height": 40})
        self.assertEqual(report["loop"], {"raw": 0, "mode": "infinite"})
        self.assertEqual(report["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(report["size_bytes"], path.stat().st_size)
        self.assertEqual(report["technical_status"], "pass")
        self.assertEqual(report["platform"]["status"], "not_evaluated")
        self.assertFalse(report["submission_ready"])
        self.assertEqual(report["provenance"]["model_id"], None)
        html = (self.root / "qa" / "preview.html").read_text()
        encoded = re.search(r"data:image/gif;base64,([A-Za-z0-9+/=]+)", html).group(1)
        self.assertEqual(base64.b64decode(encoded), path.read_bytes())
        self.assertEqual(html.count("data:image/png;base64,"), 3)
        self.assertNotIn(str(self.root), html)
        self.assertEqual(len(list((self.root / "qa" / "frames").glob("*.png"))), 3)
        with Image.open(self.root / "qa" / "contact-sheet.png") as sheet:
            self.assertGreater(sheet.width, 0)

    def test_png_renamed_gif_fails(self):
        path = self.root / "fake.gif"
        Image.new("RGB", (24, 24), "blue").save(path, format="PNG")
        report, _ = self.run_audit(path, expected=1)
        self.assertEqual(report["actual_format"], "PNG")
        self.assertIn("not_gif", report["errors"])

    def test_single_frame_fails(self):
        report, _ = self.run_audit(self.fixture(count=1), expected=1)
        self.assertIn("single_frame", report["errors"])

    def test_corrupt_file_fails_with_report(self):
        path = self.root / "broken.gif"
        path.write_bytes(b"GIF89a\x01\x00")
        report, _ = self.run_audit(path, expected=1)
        self.assertIn("decode_error", report["errors"])
        self.assertTrue((self.root / "qa" / "preview.html").is_file())

    def test_missing_file_is_operational_error(self):
        report, _ = self.run_audit(self.root / "missing.gif", expected=2)
        self.assertIn("input_unreadable", report["errors"])

    def test_missing_loop_is_not_infinite(self):
        report, _ = self.run_audit(self.fixture(loop=None))
        self.assertEqual(report["loop"], {"raw": None, "mode": "unspecified"})
        self.assertIn("loop_not_infinite", report["warnings"])

    def test_finite_loop_preserved(self):
        report, _ = self.run_audit(self.fixture(loop=2))
        self.assertEqual(report["loop"], {"raw": 2, "mode": "finite"})

    def test_nonpositive_timing_fails(self):
        report, _ = self.run_audit(self.fixture(duration=0), expected=1)
        self.assertIn("invalid_frame_duration", report["errors"])

    def test_actual_format_not_extension(self):
        report, _ = self.run_audit(self.fixture(name="motion.bin"))
        self.assertEqual(report["actual_format"], "GIF")

    def test_source_unchanged_and_out_cannot_overwrite(self):
        path = self.fixture()
        before = path.read_bytes()
        self.run_audit(path)
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "audit", str(path), "--out", str(self.root / "qa")],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(path.read_bytes(), before)

    def test_duplicate_rendered_frames_fail(self):
        # Build two identical image records; Pillow's encoder normally merges them.
        path = self.fixture(count=1, loop=None)
        original = path.read_bytes()
        gce = original.index(b"\x21\xf9\x04")
        path.write_bytes(original[:-1] + original[gce:-1] + b";")
        with Image.open(path) as image:
            self.assertEqual(image.n_frames, 2)
        report, _ = self.run_audit(path, expected=1)
        self.assertEqual(report["distinct_frames"], 1)
        self.assertIn("no_visible_change", report["errors"])

    def test_html_escapes_filename(self):
        path = self.fixture(name="<unsafe&name>.gif")
        self.run_audit(path)
        html = (self.root / "qa" / "preview.html").read_text()
        self.assertNotIn("<unsafe&name>", html)
        self.assertIn("&lt;unsafe&amp;name&gt;", html)

    def test_truncated_payload_fails(self):
        path = self.fixture()
        path.write_bytes(path.read_bytes()[:50])
        report, _ = self.run_audit(path, expected=1)
        self.assertEqual(report["technical_status"], "fail")

    def test_resource_limit(self):
        self.assertTrue(SCRIPT.exists(), "audit CLI not implemented")
        spec = importlib.util.spec_from_file_location("audit_gif", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.MAX_FRAMES = 2
        report, frames, _ = module.inspect_gif(self.fixture())
        self.assertIn("frame_limit_exceeded", report["errors"])
        self.assertFalse(report["decode_complete"])
        self.assertLessEqual(len(frames), 2)


if __name__ == "__main__":
    unittest.main()
