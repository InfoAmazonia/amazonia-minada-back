"""Retention boundaries and path safety; no Docker or production access."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('daily', Path(__file__).with_name('mongodb-daily-backup.py'))
daily = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily)


class RetentionTests(unittest.TestCase):
    def fixture(self, root, number, state, job=daily.JOB):
        name = f'202610{number:02d}T040000000000Z-' + f'{number:032x}'
        folder = root / name
        folder.mkdir()
        (folder / 'status.json').write_text(json.dumps({'job': job, 'run': name, 'state': state}))
        (folder / 'archive').write_text('fixture only')
        return folder

    def test_keep_latest_fourteen_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folders = [self.fixture(root, number, 'verified') for number in range(1, 17)]
            removed = daily.prune(root, 'verified', 14)
            self.assertEqual(set(removed), {folder.name for folder in folders[:2]})
            self.assertTrue(all(folder.exists() for folder in folders[2:]))

    def test_failure_cleanup_does_not_touch_verified_or_running(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            valid = self.fixture(root, 1, 'verified')
            running = self.fixture(root, 2, 'running')
            failed = [self.fixture(root, number, 'failed') for number in range(3, 8)]
            daily.prune(root, 'failed', 3)
            self.assertTrue(valid.exists() and running.exists())
            self.assertFalse(any(folder.exists() for folder in failed[:2]))
            self.assertTrue(all(folder.exists() for folder in failed[2:]))

    def test_unrelated_and_malformed_folders_are_untouched(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            unrelated = self.fixture(root, 1, 'verified', job='something-else')
            malformed = self.fixture(root, 2, 'verified')
            (malformed / 'status.json').write_text('{invalid json')
            good = self.fixture(root, 3, 'verified')
            self.assertEqual(daily.prune(root, 'verified', 1), [])
            self.assertTrue(all(folder.exists() for folder in [unrelated, malformed, good]))

    def test_directory_and_status_symlinks_are_not_followed(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as target:
            root = Path(temporary)
            outside = self.fixture(Path(target), 1, 'verified')
            (root / outside.name).symlink_to(outside, target_is_directory=True)
            other = self.fixture(root, 2, 'verified')
            (other / 'status.json').unlink()
            (other / 'status.json').symlink_to(outside / 'status.json')
            self.assertEqual(daily.prune(root, 'verified', 1), [])
            self.assertTrue((outside / 'archive').exists())
            self.assertTrue(other.exists())


if __name__ == '__main__':
    unittest.main()
