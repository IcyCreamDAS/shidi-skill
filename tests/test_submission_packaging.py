"""Protect original evidence and fail closed when packaging untrusted paths."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

REPO = Path(__file__).resolve().parents[1]
PATH = REPO / "competitions/bohrium-reading-2026-10/build_submission.py"
spec = importlib.util.spec_from_file_location("build_reading_submission", PATH)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class SubmissionPackagingTests(unittest.TestCase):
    def test_manifest_preserves_duration_from_both_original_note_schemas(self):
        original_read = builder.read_json
        def fixture_read(path):
            if path.name == "manifest-with-bonus.json":
                return {"cases": []}
            return original_read(path)
        with patch.object(builder, "read_json", side_effect=fixture_read):
            manifest = builder.make_manifest(Path("unused-official-template-directory"))
        runs = {row["id"]: row for row in manifest["runs"]}
        self.assertEqual(runs["A-with-02"]["duration_seconds"], 610.134)
        self.assertEqual(runs["A-without-02"]["duration_seconds"], 469.749423)
        self.assertEqual(runs["B-with-02"]["duration_seconds"], 407.707281)
        self.assertIsNone(runs["C-with-02"]["duration_seconds"])
        self.assertFalse(manifest["submission_readiness"]["ready_to_submit"])

    def test_output_cannot_overwrite_evidence_or_source_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            existing = root / "existing"
            existing.mkdir()
            evidence = existing / "evidence.txt"
            evidence.write_bytes(b"original evidence\n")
            with self.assertRaises(FileExistsError):
                builder.reserve_output(existing, repo=repo)
            for unsafe in (repo, repo / "generated", root):
                with self.subTest(path=unsafe), self.assertRaises(ValueError):
                    builder.reserve_output(unsafe, repo=repo)
            self.assertEqual(evidence.read_bytes(), b"original evidence\n")
            self.assertFalse((repo / "generated").exists())

    def test_resource_tampering_stops_before_output_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resources = root / "resources"
            resources.mkdir()
            (resources / "check.py").write_bytes(b"altered")
            lock = {"files": [{"path": "check.py", "bytes": 7,
                              "sha256": hashlib.sha256(b"trusted").hexdigest()}]}
            with patch.object(builder, "read_json", return_value=lock):
                with self.assertRaisesRegex(ValueError, "hash/size mismatch"):
                    builder.build(resources, root / "output")
            self.assertFalse((root / "output").exists())

    def symlink_or_skip(self, link, target, target_is_directory=False):
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except OSError as error:
            if getattr(error, "winerror", None) != 1314:
                raise
            self.skipTest("Creating symbolic links requires additional Windows privilege")

    def test_source_paths_cannot_escape_through_traversal_or_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (root / "outside").write_bytes(b"private")
            self.symlink_or_skip(source / "link", root / "outside")
            self.symlink_or_skip(source / "directory-link", root, target_is_directory=True)
            for name in ("../outside", "/outside", "C:/outside", "a\\b", "a//b",
                         "./outside", "link", "directory-link/outside"):
                with self.subTest(path=name), self.assertRaises(ValueError):
                    builder.checked_file(source, name)

    def test_zip_preserves_original_bytes_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            original = "证据\r\n失败与重试\n".encode("utf-8")
            (source / "record.txt").write_bytes(original)
            (source / "original.bin").write_bytes(bytes(range(256)))
            first, second = root / "one.zip", root / "two.zip"
            builder.deterministic_zip(source, first)
            builder.deterministic_zip(source, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(archive.read("submission/record.txt"), original)
                self.assertEqual(archive.read("submission/original.bin"), bytes(range(256)))
            with self.assertRaises(FileExistsError):
                builder.deterministic_zip(source, first)

    def test_zip_does_not_accept_empty_files_or_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "empty").touch()
            with self.assertRaisesRegex(ValueError, "Empty artifact"):
                builder.deterministic_zip(source, root / "empty.zip")
            (source / "empty").unlink()
            (root / "target").write_bytes(b"outside")
            self.symlink_or_skip(source / "link", root / "target")
            with self.assertRaisesRegex(ValueError, "Symlinks"):
                builder.deterministic_zip(source, root / "link.zip")

    def test_selection_offsets_are_unicode_characters_with_byte_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = "前言\n" + "证据🧪" * 3000
            (root / "record.txt").write_text(original, encoding="utf-8")
            row = builder.source_selection(root, "record.txt", "source evidence",
                                           marker="证据", chars=10000)
            self.assertEqual(row["start"], 3)
            selected = original[row["start"]:row["end"]]
            self.assertLessEqual(len(selected.encode("utf-8")), 8192)
            self.assertEqual((root / "record.txt").read_text(encoding="utf-8"), original)

    def test_changed_frozen_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            base = repo / "contest"
            base.mkdir()
            original = b"frozen input"
            (base / "ready-freeze.json").write_text(json.dumps({"sha256": {
                "input.txt": hashlib.sha256(original).hexdigest()}}))
            (repo / "input.txt").write_bytes(b"changed input")
            with patch.object(builder, "REPO", repo), patch.object(builder, "BASE", base):
                with self.assertRaisesRegex(ValueError, "Frozen input/Skill/reference changed"):
                    builder.verify_artifacts()


if __name__ == "__main__":
    unittest.main()
