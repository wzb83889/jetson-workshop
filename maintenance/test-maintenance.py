"""Offline mocked tests: never invoke apt, change services, or install packages."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('maint', Path(__file__).with_name('jetson-maint.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Tests(unittest.TestCase):
    def task(self, directory):
        t = m.Maintenance(directory)
        self.addCleanup(t.log.close)
        self.addCleanup(t.lock.close)
        return t

    def test_transaction_guard(self):
        m.gate('Inst gnome-shell [1] (2 Ubuntu [arm64])\n')
        for s in ['Inst nvidia-l4t-core [1] (2)', 'Inst libnvinfer10 (2)',
                  'Inst linux-image-6.8-tegra (2)', 'Remv vim [1]',
                  'Inst gnome-shell (2)\nInst libc6:arm64 (3)']:
            with self.subTest(s=s), self.assertRaises(RuntimeError):
                m.gate(s)

    def test_partial_repository_failure_stops(self):
        with tempfile.TemporaryDirectory() as d:
            t = self.task(d)
            seen = []
            def fake(args, required=False, timeout=120):
                seen.append(args)
                if args[-1] == 'update':
                    self.assertIn('APT::Update::Error-Mode=any', args)
                    raise RuntimeError('partial refresh failed')
                return 0, ''
            t.cmd = fake
            with patch.object(m.Path, 'exists', return_value=True), self.assertRaises(RuntimeError):
                t.plan()
            self.assertFalse(any('-s' in cmd for cmd in seen))

    def test_failed_services_block_apply(self):
        with tempfile.TemporaryDirectory() as d:
            t = self.task(d)
            t.preflight = lambda: None
            t.snapshot = lambda: {'failed': ['dnsmasq failed']}
            with self.assertRaises(RuntimeError):
                t.apply(['gnome-shell'])

    def test_phased_package_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            t = self.task(d)
            t.preflight = lambda: None
            t.snapshot = lambda: {'failed': []}
            def fake(args, required=False, timeout=120):
                if args[:2] == ['dpkg-query', '-W']:
                    return 0, 'installed'
                if args[:2] == ['apt-cache', 'policy']:
                    return 0, '  Installed: 1\n  Candidate: 2\n'
                return 0, 'The following upgrades have been deferred due to phasing:\n snapd\n'
            t.cmd = fake
            with self.assertRaisesRegex(RuntimeError, '阶段更新'):
                t.apply(['snapd'])

    def test_verify_reboot_and_protected_drift(self):
        base = dict(os='noble', l4t='R39', kernel='tegra', boot_id='A',
                    packages={'nvidia-l4t-core': '39.2.1'}, failed=[], services={},
                    audit='', audit_rc=0)
        with tempfile.TemporaryDirectory() as d:
            t = self.task(d)
            (t.run_dir / 'before.json').write_text(json.dumps(base))
            (t.run_dir / 'apply-result.json').write_text('{"returncode":0}')
            (t.state / 'last-apply.json').write_text(json.dumps({'directory': str(t.run_dir)}))
            t.snapshot = lambda: base.copy()
            with self.assertRaises(RuntimeError):
                t.verify()
            t.snapshot = lambda: {**base, 'boot_id': 'B'}
            t.verify()
            t.snapshot = lambda: {**base, 'boot_id': 'B', 'packages': {'nvidia-l4t-core': '40'}}
            with self.assertRaises(RuntimeError):
                t.verify()

if __name__ == '__main__':
    unittest.main()
