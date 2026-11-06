import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_all_json_parse(self):
        for path in ROOT.rglob("*.json"):
            if ".git" not in path.parts:
                with self.subTest(path=path.relative_to(ROOT)):
                    json.loads(path.read_text())

    def test_eight_actions_are_only_plans(self):
        manifest = json.loads((ROOT / "manifests/otter-actions.planning.json").read_text())
        self.assertFalse(manifest["generation_authorized"])
        self.assertEqual(manifest["generated_count"], 0)
        actions = manifest["actions"]
        self.assertEqual(len(actions), 8)
        self.assertEqual(len({action["id"] for action in actions}), 8)
        for action in actions:
            self.assertEqual(action["status"], "planned_not_generated")
            self.assertIsNone(action["output"])
            self.assertGreaterEqual(len(action["beats"]), 3)

    def test_platform_profile_cannot_certify(self):
        profile = json.loads((ROOT / "profiles/wechat.pending.json").read_text())
        self.assertFalse(profile["usable_for_compliance"])
        self.assertIsNone(profile["official_source_url"])
        self.assertIsNone(profile["limits"])
        self.assertFalse(profile["submission_ready"])

    def test_request_example_disabled(self):
        request = json.loads((ROOT / "examples/api-request.plan.json").read_text())
        self.assertFalse(request["execution_enabled"])
        self.assertIn(request["request_body_example"]["frame_count"], range(2, 17))

    def test_markdown_relative_links_exist(self):
        for path in ROOT.rglob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if "://" not in target and not target.startswith("#"):
                    with self.subTest(document=path.name, target=target):
                        self.assertTrue((path.parent / target.split("#")[0]).exists())

    def test_public_files_no_private_markers(self):
        pattern = re.compile(rb"(?:/Users/|/home/)[A-Za-z0-9_.-]+/|https?://(?:chatgpt\.com|chat\.openai\.com)/(?:c|share)/|sk-[A-Za-z0-9_-]{20,}")
        for path in ROOT.rglob("*"):
            if path.is_file() and not {".git", "__pycache__"}.intersection(path.parts):
                with self.subTest(path=path.relative_to(ROOT)):
                    self.assertIsNone(pattern.search(path.read_bytes()))


if __name__ == "__main__":
    unittest.main()
