import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/(name+".py"))
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

class ToolsTest(unittest.TestCase):
    def test_download_rejects_html_and_cleans_partial(self):
        m=module("download_samples")
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"sample.mp4"
            with self.assertRaises(ValueError):
                m.download("https://example.invalid",target,
                    opener=lambda *a,**k:io.BytesIO(b"<html>not a video</html>"))
            self.assertEqual(list(Path(d).iterdir()),[])
    def test_download_hash_and_no_overwrite(self):
        import hashlib
        m=module("download_samples")
        data=b"\x00\x00\x00\x18ftypmp42"+b"x"*100
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/"sample.mp4"
            self.assertEqual(m.download("url",target,opener=lambda *a,**k:io.BytesIO(data)),
                             hashlib.sha256(data).hexdigest())
            self.assertEqual(target.read_bytes(),data)
            with self.assertRaises(FileExistsError):
                m.download("url",target)
    def test_restore_preserves_existing(self):
        m=module("restore_nvidia_shortcuts")
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"src"; dst=Path(d)/"dst"
            src.write_text("source"); dst.write_text("mine")
            m.restore(src,dst)
            self.assertEqual(dst.read_text(),"mine")
    def test_session_rejects_path_traversal(self):
        m=module("new_session")
        for value in ("../escape","a/b","UPPER","a--b","x;rm"):
            with self.assertRaises(ValueError):
                m.session_name(value)
    def test_launcher_keeps_venv_interpreter_and_quotes(self):
        m=module("install_desktop_launcher")
        script=m.launch_script(Path("/tmp/my venv/bin/python"),
                               Path("/tmp/my app/gui.py"),Path("/tmp/my log.txt"))
        subprocess.run(["sh","-n"],input=script,text=True,check=True)
        self.assertIn("'/tmp/my venv/bin/python'",script)
        self.assertIn("'/tmp/my app/gui.py'",script)
    def test_launcher_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            result=subprocess.run([sys.executable,str(ROOT/"scripts/install_desktop_launcher.py"),
                "--home",d,"--desktop",str(Path(d)/"Desk"),"--dry-run"],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(list(Path(d).iterdir()),[])
    def test_all_python_entrypoints_help_without_gpu(self):
        for path in (ROOT/"scripts").glob("*.py"):
            result=subprocess.run([sys.executable,str(path),"--help"],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,(path.name,result.stderr))

if __name__=="__main__":
    unittest.main()
