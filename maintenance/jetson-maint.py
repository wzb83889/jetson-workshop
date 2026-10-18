#!/usr/bin/env python3
"""Jetson maintenance assistant v1.0; Python standard library only."""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

SERVICES = ['NetworkManager', 'systemd-resolved', 'nv-l4t-usb-device-mode.service',
            'nv-l4t-usb-device-mode-runtime.service']
PROTECTED = re.compile(r'^(nvidia|cuda|libcuda|libcud|cudnn|tensorrt|libnvinfer|python3-libnvinfer|'
                       r'libnv|vpi|libnvvpi|nsight|linux-|initramfs|flash-|grub|shim|'
                       r'firmware|systemd|udev|libsystemd|libudev|network-manager|netplan|'
                       r'isc-dhcp|dnsmasq|docker|containerd|runc|libc6|libc-bin|python3|libpython3|'
                       r'ubuntu-release-upgrader|update-manager|libegl|libgl|libgbm|mesa)')

def protected(name):
    return bool(PROTECTED.match(name.split(':')[0]))

def changes(output):
    return [(m.group(1), m.group(2)) for line in output.splitlines()
            if (m := re.match(r'^(Inst|Remv) (\S+)', line))]

def gate(output):
    bad = [(action, name) for action, name in changes(output)
           if action == 'Remv' or protected(name)]
    if bad:
        raise RuntimeError('需专项审查，拒绝常规安装：' + repr(bad))

def read(path):
    p = Path(path)
    return p.read_text(errors='replace') if p.exists() else ''

class Maintenance:
    def __init__(self, state):
        self.state = Path(state)
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = (self.state / 'maintenance.lock').open('w')
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.run_dir = self.state / datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        self.run_dir.mkdir(mode=0o700)
        self.log = (self.run_dir / 'session.log').open('w')

    def say(self, msg):
        print(msg, flush=True)
        self.log.write(msg + '\n')
        self.log.flush()

    def cmd(self, args, required=False, timeout=120):
        self.say('\n$ ' + ' '.join(args))
        try:
            p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               env={**os.environ, 'LC_ALL': 'C', 'LANG': 'C'}, timeout=timeout)
            self.say(p.stdout.rstrip())
        except (OSError, subprocess.TimeoutExpired) as e:
            self.say(str(e))
            if required:
                raise RuntimeError('命令失败或超时') from e
            return 127, str(e)
        if required and p.returncode:
            raise RuntimeError('命令失败，已停止；请查看日志')
        return p.returncode, p.stdout

    def snapshot(self):
        _, pkgs = self.cmd(['dpkg-query', '-W', '-f=${binary:Package}\t${Version}\t${db:Status-Status}\n'], True)
        packages = dict((a[0], a[1]) for line in pkgs.splitlines()
                        if len(a := line.split('\t')) == 3 and a[2] == 'installed')
        _, failed = self.cmd(['systemctl', '--failed', '--plain', '--no-legend', '--no-pager'])
        active = {}
        for s in SERVICES:
            _, out = self.cmd(['systemctl', 'is-active', s])
            active[s] = out.strip()
        audit_rc, audit = self.cmd(['dpkg', '--audit'])
        data = dict(os=read('/etc/os-release'), l4t=read('/etc/nv_tegra_release'),
                    kernel=os.uname().release, boot_id=read('/proc/sys/kernel/random/boot_id').strip(),
                    packages=packages, failed=failed.splitlines(), services=active,
                    audit=audit, audit_rc=audit_rc)
        for cmd in [['nmcli', 'general', 'status'], ['ip', '-brief', 'address'],
                    ['timedatectl', 'status'], ['nvpmodel', '-q'], ['df', '-h', '/', '/boot'],
                    ['ss', '-lunp', '( sport = :67 )']]:
            self.cmd(cmd)
        (self.run_dir / 'snapshot.json').write_text(json.dumps(data, ensure_ascii=False, indent=2))
        return data

    def preflight(self):
        if not Path('/etc/nv_tegra_release').exists():
            raise RuntimeError('未检测到 Jetson L4T；不执行更新')
        if shutil.disk_usage('/').free < 3 * 1024**3:
            raise RuntimeError('根分区剩余空间不足 3 GiB，请先检查空间')
        rc, out = self.cmd(['dpkg', '--audit'], True)
        if out.strip():
            raise RuntimeError('软件包安装状态异常，需先人工处理')
        # Strict mode treats even a partial repository refresh failure as fatal.
        self.cmd(['apt-get', '-o', 'APT::Update::Error-Mode=any',
                  '-o', 'Acquire::Retries=1', '-o', 'Acquire::http::Timeout=30',
                  '-o', 'Acquire::https::Timeout=30', 'update'], True, timeout=900)
        self.cmd(['apt-get', 'check'], True)

    def plan(self):
        self.preflight()
        _, out = self.cmd(['apt-get', '-s', 'upgrade'], True)
        (self.run_dir / 'plan.txt').write_text(out)
        for action, name in changes(out):
            self.say(('专项审查' if action == 'Remv' or protected(name) else '普通候选') + ': ' + name)
        self.say('预览完成，未安装软件包。阶段更新保持默认；apply 必须显式指定包。')

    def apply(self, names):
        if not names or any(not re.fullmatch(r'[a-z0-9][a-z0-9+.-]*(?::arm64)?', n) for n in names):
            raise RuntimeError('请用 --packages 指定普通软件包名，不接受通配符、版本或选项')
        if any(protected(n) for n in names):
            raise RuntimeError('包含平台/关键组件；请按手册进行专项维护')
        self.preflight()
        before = self.snapshot()
        if before['failed']:
            raise RuntimeError('已有失败服务，先排查并建立正常基线，再执行安装')
        _, default_plan = self.cmd(['apt-get', '-s', 'upgrade'], True)
        eligible = {n.split(':')[0] for action, n in changes(default_plan) if action == 'Inst'}
        pins = []
        for n in names:
            _, status = self.cmd(['dpkg-query', '-W', '-f=${db:Status-Status}', n], True)
            if status.strip() != 'installed':
                raise RuntimeError('只允许升级已安装的软件包：' + n)
            _, p = self.cmd(['apt-cache', 'policy', n], True)
            m = re.search(r'^\s*Candidate:\s*(\S+)', p, re.M)
            if not m or m[1] == '(none)':
                raise RuntimeError('没有可用候选版本：' + n)
            installed = re.search(r'^\s*Installed:\s*(\S+)', p, re.M)
            if installed and installed[1] == m[1]:
                continue
            if n.split(':')[0] not in eligible:
                raise RuntimeError('默认 upgrade 未计划更新此包（可能处于阶段更新或被保留）：' + n)
            pins.append(n + '=' + m[1])
        if not pins:
            self.say('所选包均无可执行更新。')
            return
        args = ['apt-get', '--only-upgrade', '--no-remove', 'install', *pins]
        _, simulation = self.cmd([args[0], '-s', *args[1:]], True)
        gate(simulation)  # Includes dependencies, not just explicitly selected packages.
        if not changes(simulation):
            self.say('所选包没有可执行更新。')
            return
        self.say('这是配置和清单备份，不是可启动系统镜像；确认已保存工作。')
        if input('输入 APPLY 安装以上精确版本；其他输入取消：').strip() != 'APPLY':
            self.say('已取消')
            return
        _, simulation2 = self.cmd([args[0], '-s', *args[1:]], True)
        gate(simulation2)
        if simulation2 != simulation:
            raise RuntimeError('计划已变化，请重新运行 apply')
        shutil.copytree('/etc/apt', self.run_dir / 'apt-config', symlinks=True)
        (self.run_dir / 'before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2))
        (self.state / 'last-apply.json').write_text(json.dumps({'directory': str(self.run_dir)}))
        # Streaming preserves apt's normal Y/n confirmation and configuration-file questions.
        self.say('开始安装。APT 日志另见 /var/log/apt/history.log 和 term.log。')
        rc = subprocess.call(args, env={**os.environ, 'LC_ALL': 'C'})
        (self.run_dir / 'apply-result.json').write_text(json.dumps({'returncode': rc}))
        self.snapshot()
        if rc:
            raise RuntimeError('安装未正常完成；保留现场，勿直接重启或自动修复')
        self.say('安装命令成功。请保存工作后自行重启，再运行 verify。')

    def verify(self):
        current = self.snapshot()
        pointer = self.state / 'last-apply.json'
        if not pointer.exists():
            self.say('没有本脚本的升级前记录；本次仅建立检查记录，不能判定升级前后是否一致。')
            return
        directory = Path(json.loads(pointer.read_text())['directory'])
        before = json.loads((directory / 'before.json').read_text())
        issues = []
        for key in ('os', 'l4t', 'kernel'):
            if before[key] != current[key]:
                issues.append(key + ' 已变化，需审查')
        for n in sorted(before['packages'].keys() | current['packages'].keys()):
            a, b = before['packages'].get(n), current['packages'].get(n)
            if a != b:
                self.say(f'包变更: {n}: {a} -> {b}')
                if protected(n):
                    issues.append('关键包变化: ' + n)
        if before['boot_id'] == current['boot_id']:
            issues.append('尚未重启；不能视为重启后验证通过')
        if current['failed'] or current['audit'].strip() or current['audit_rc']:
            issues.append('存在失败服务或软件包状态异常')
        for s, state in before['services'].items():
            if state == 'active' and current['services'][s] != 'active':
                issues.append('原活动服务异常: ' + s)
        result = directory / 'apply-result.json'
        if not result.exists() or json.loads(result.read_text())['returncode']:
            issues.append('上次安装未确认成功')
        self.say('\n验证结果：' + ('；'.join(issues) if issues else '系统层检查通过；GPU/项目任务仍需实际测试'))
        (self.run_dir / 'verification.json').write_text(json.dumps({'issues': issues}, ensure_ascii=False))
        if issues:
            raise RuntimeError('验证尚未通过，请检查上述项目')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['check', 'plan', 'apply', 'verify'])
    p.add_argument('--packages', nargs='+', default=[])
    a = p.parse_args()
    if os.geteuid() != 0:
        p.error('请使用 sudo python3 jetson-maint.py ' + a.mode)
    os.umask(0o077)
    task = Maintenance('/var/log/jetson-maint')
    try:
        if a.mode == 'check':
            task.snapshot()
        elif a.mode == 'plan':
            task.snapshot()
            task.plan()
        elif a.mode == 'apply':
            task.apply(a.packages)
        else:
            task.verify()
    except (RuntimeError, KeyboardInterrupt) as e:
        task.say('停止：' + str(e))
        return 1
    finally:
        task.say('记录目录：' + str(task.run_dir))
    return 0

if __name__ == '__main__':
    sys.exit(main())
