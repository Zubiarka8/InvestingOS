import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("youtube", ROOT / "scripts/youtube.py")
youtube = importlib.util.module_from_spec(spec)
spec.loader.exec_module(youtube)


class YouTubeTests(unittest.TestCase):
    def test_caption_command_uses_single_video_and_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            args = ["youtube.py", "captions", "https://youtu.be/example", temp]
            with patch("sys.argv", args), patch.object(youtube.shutil, "which", return_value="yt-dlp"), \
                    patch.object(youtube.subprocess, "call", return_value=0) as call:
                self.assertEqual(youtube.main(), 0)
            command = call.call_args.args[0]
            for value in ("--ignore-config", "--no-playlist", "--no-overwrites",
                          "--skip-download", "--write-auto-subs", temp):
                self.assertIn(value, command)
            self.assertEqual(command[-1], "https://youtu.be/example")

    def test_rejects_other_hosts_before_calling_tool(self):
        args = ["youtube.py", "video", "https://example.com/video", "."]
        with patch("sys.argv", args), patch.object(youtube.subprocess, "call") as call:
            with self.assertRaises(SystemExit) as failure:
                youtube.main()
            self.assertEqual(failure.exception.code, 2)
            call.assert_not_called()


    def test_invalid_port_is_reported_as_usage_error(self):
        from unittest.mock import patch
        with patch('sys.argv', ['youtube.py', 'video', 'https://youtube.com:invalid/watch?v=abc', '.']):
            with self.assertRaises(SystemExit) as result:
                youtube.main()
        self.assertEqual(result.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
