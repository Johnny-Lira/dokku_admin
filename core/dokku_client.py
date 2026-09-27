"""
dokku_client.py
Wrapper responsible for talking to the `dokku` CLI, either:
  - locally, via subprocess (use this when Streamlit runs ON the Dokku host)
  - remotely, via SSH/paramiko (use this when Streamlit runs on your laptop / another box)

Every dokku_client method returns a DokkuResult(ok, stdout, stderr).
"""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import paramiko
except ImportError:  # paramiko is optional if only local mode is used
    paramiko = None


PARAMIKO_INSTALL_HINT = (
    "paramiko nao esta instalado no Python atual. Ative o venv do projeto e rode: "
    "python -m pip install -r requirements.txt"
)


@dataclass
class DokkuResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    command: str = ""

    @property
    def lines(self) -> List[str]:
        return [l for l in self.stdout.splitlines() if l.strip()]


class DokkuClient:
    """Executes `dokku ...` commands locally or over SSH."""

    def __init__(
        self,
        mode: str = "local",           # "local" or "ssh"
        host: Optional[str] = None,
        port: int = 22,
        user: str = "root",
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        sudo: bool = False,            # prefix commands with sudo (needed if user != dokku/root)
    ):
        self.mode = mode
        self.host = host
        self.port = port
        self.user = user
        self.key_path = key_path
        self.password = password
        self.sudo = sudo
        self._ssh_client = None

    # ------------------------------------------------------------------ #
    # Connection handling
    # ------------------------------------------------------------------ #
    def test_connection(self) -> DokkuResult:
        return self.run(["version"])

    def _get_ssh(self):
        if paramiko is None:
            raise RuntimeError(PARAMIKO_INSTALL_HINT)
        if self._ssh_client is not None:
            return self._ssh_client
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        kwargs = dict(hostname=self.host, port=self.port, username=self.user, timeout=10)
        if self.key_path:
            kwargs["key_filename"] = self.key_path
        elif self.password:
            kwargs["password"] = self.password
        client.connect(**kwargs)
        self._ssh_client = client
        return client

    def close(self):
        if self._ssh_client is not None:
            self._ssh_client.close()
            self._ssh_client = None

    # ------------------------------------------------------------------ #
    # Core runner
    # ------------------------------------------------------------------ #
    def run(self, args: List[str], timeout: int = 90) -> DokkuResult:
        """args is the dokku subcommand split into tokens, e.g. ["apps:list"]
        or ["config:set", "--no-restart", "myapp", "KEY=VAL"]."""
        parts = ["dokku"] + args
        cmd = " ".join(shlex.quote(p) for p in parts)
        if self.sudo:
            cmd = "sudo " + cmd

        if self.mode == "local":
            return self._run_local(cmd, timeout)
        return self._run_ssh(cmd, timeout)

    def _run_local(self, cmd: str, timeout: int) -> DokkuResult:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return DokkuResult(
                ok=result.returncode == 0,
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip(),
                command=cmd,
            )
        except subprocess.TimeoutExpired:
            return DokkuResult(ok=False, stderr="Command timed out", command=cmd)
        except Exception as exc:  # noqa: BLE001
            return DokkuResult(ok=False, stderr=str(exc), command=cmd)

    def _run_ssh(self, cmd: str, timeout: int) -> DokkuResult:
        try:
            client = self._get_ssh()
            stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode(errors="replace")
            err = stderr.read().decode(errors="replace")
            code = stdout.channel.recv_exit_status()
            return DokkuResult(ok=code == 0, stdout=out.strip(), stderr=err.strip(), command=cmd)
        except Exception as exc:  # noqa: BLE001
            return DokkuResult(ok=False, stderr=str(exc), command=cmd)

    # ------------------------------------------------------------------ #
    # Apps
    # ------------------------------------------------------------------ #
    def apps_list(self) -> DokkuResult:
        r = self.run(["apps:list"])
        if r.ok:
            r.stdout = "\n".join(l for l in r.lines if not l.startswith("=====>"))
        return r

    def apps_create(self, name: str) -> DokkuResult:
        return self.run(["apps:create", name])

    def apps_destroy(self, name: str) -> DokkuResult:
        return self.run(["apps:destroy", name, "--force"])

    def apps_rename(self, old: str, new: str) -> DokkuResult:
        return self.run(["apps:rename", old, new])

    def apps_report(self, name: str) -> DokkuResult:
        return self.run(["apps:report", name])

    def apps_lock(self, name: str) -> DokkuResult:
        return self.run(["apps:lock", name])

    def apps_unlock(self, name: str) -> DokkuResult:
        return self.run(["apps:unlock", name])

    # ------------------------------------------------------------------ #
    # Config / env vars
    # ------------------------------------------------------------------ #
    def config_show(self, name: str) -> DokkuResult:
        return self.run(["config:show", name])

    def config_set(self, name: str, pairs: dict, no_restart: bool = False) -> DokkuResult:
        args = ["config:set"]
        if no_restart:
            args.append("--no-restart")
        args.append(name)
        args += [f"{k}={v}" for k, v in pairs.items()]
        return self.run(args)

    def config_unset(self, name: str, keys: List[str], no_restart: bool = False) -> DokkuResult:
        args = ["config:unset"]
        if no_restart:
            args.append("--no-restart")
        args.append(name)
        args += keys
        return self.run(args)

    # ------------------------------------------------------------------ #
    # Domains
    # ------------------------------------------------------------------ #
    def domains_report(self, name: str) -> DokkuResult:
        return self.run(["domains:report", name])

    def domains_add(self, name: str, domain: str) -> DokkuResult:
        return self.run(["domains:add", name, domain])

    def domains_remove(self, name: str, domain: str) -> DokkuResult:
        return self.run(["domains:remove", name, domain])

    def domains_set(self, name: str, domains: List[str]) -> DokkuResult:
        return self.run(["domains:set", name] + domains)

    def domains_clear(self, name: str) -> DokkuResult:
        return self.run(["domains:clear", name])

    def domains_enable(self, name: str) -> DokkuResult:
        return self.run(["domains:enable", name])

    def domains_disable(self, name: str) -> DokkuResult:
        return self.run(["domains:disable", name])

    # ------------------------------------------------------------------ #
    # Proxy / ports
    # ------------------------------------------------------------------ #
    def proxy_report(self, name: str) -> DokkuResult:
        return self.run(["proxy:report", name])

    def proxy_ports_add(self, name: str, mapping: str) -> DokkuResult:
        # mapping format: scheme:host_port:container_port  e.g. http:80:5000
        return self.run(["proxy:ports-add", name, mapping])

    def proxy_ports_remove(self, name: str, mapping: str) -> DokkuResult:
        return self.run(["proxy:ports-remove", name, mapping])

    def proxy_ports_set(self, name: str, mappings: List[str]) -> DokkuResult:
        return self.run(["proxy:ports-set", name] + mappings)

    def proxy_enable(self, name: str) -> DokkuResult:
        return self.run(["proxy:enable", name])

    def proxy_disable(self, name: str) -> DokkuResult:
        return self.run(["proxy:disable", name])

    # ------------------------------------------------------------------ #
    # SSL / Let's Encrypt (requires dokku-letsencrypt plugin)
    # ------------------------------------------------------------------ #
    def letsencrypt_list(self) -> DokkuResult:
        return self.run(["letsencrypt:list"])

    def letsencrypt_enable(self, name: str) -> DokkuResult:
        return self.run(["letsencrypt:enable", name])

    def letsencrypt_auto_renew(self, name: Optional[str] = None) -> DokkuResult:
        args = ["letsencrypt:auto-renew"]
        if name:
            args.append(name)
        return self.run(args)

    def certs_report(self, name: str) -> DokkuResult:
        return self.run(["certs:report", name])

    def certs_remove(self, name: str) -> DokkuResult:
        return self.run(["certs:remove", name])

    # ------------------------------------------------------------------ #
    # Process management
    # ------------------------------------------------------------------ #
    def ps_report(self, name: str) -> DokkuResult:
        return self.run(["ps:report", name])

    def ps_scale(self, name: str, proc_counts: dict) -> DokkuResult:
        args = ["ps:scale", name] + [f"{p}={c}" for p, c in proc_counts.items()]
        return self.run(args)

    def ps_restart(self, name: str) -> DokkuResult:
        return self.run(["ps:restart", name])

    def ps_stop(self, name: str) -> DokkuResult:
        return self.run(["ps:stop", name])

    def ps_start(self, name: str) -> DokkuResult:
        return self.run(["ps:start", name])

    def ps_rebuild(self, name: str) -> DokkuResult:
        return self.run(["ps:rebuild", name], timeout=600)

    # ------------------------------------------------------------------ #
    # Logs
    # ------------------------------------------------------------------ #
    def logs(self, name: str, num: int = 100, process: Optional[str] = None) -> DokkuResult:
        args = ["logs", name, "-n", str(num)]
        if process:
            args += ["-p", process]
        return self.run(args)

    # ------------------------------------------------------------------ #
    # Plugins
    # ------------------------------------------------------------------ #
    def plugin_list(self) -> DokkuResult:
        return self.run(["plugin:list"])

    def plugin_install(self, url: str, name: Optional[str] = None) -> DokkuResult:
        args = ["plugin:install", url]
        if name:
            args += ["--name", name]
        return self.run(args, timeout=600)

    def plugin_uninstall(self, name: str) -> DokkuResult:
        return self.run(["plugin:uninstall", name], timeout=600)

    # ------------------------------------------------------------------ #
    # Storage
    # ------------------------------------------------------------------ #
    def storage_list(self, name: str) -> DokkuResult:
        return self.run(["storage:list", name])

    def storage_mount(self, name: str, mapping: str) -> DokkuResult:
        # mapping format: /host/path:/container/path
        return self.run(["storage:mount", name, mapping])

    def storage_unmount(self, name: str, mapping: str) -> DokkuResult:
        return self.run(["storage:unmount", name, mapping])

    # ------------------------------------------------------------------ #
    # Datastore plugins (postgres / mysql / redis / mongo share the same verbs)
    # ------------------------------------------------------------------ #
    def service_list(self, service: str) -> DokkuResult:
        r = self.run([f"{service}:list"])
        if r.ok:
            r.stdout = "\n".join(l for l in r.lines if not l.startswith("=====>"))
        return r

    def service_create(self, service: str, db_name: str, extra_args: Optional[List[str]] = None) -> DokkuResult:
        args = [f"{service}:create", db_name] + (extra_args or [])
        return self.run(args, timeout=600)

    def service_destroy(self, service: str, db_name: str) -> DokkuResult:
        return self.run([f"{service}:destroy", db_name, "--force"])

    def service_info(self, service: str, db_name: str) -> DokkuResult:
        return self.run([f"{service}:info", db_name])

    def service_link(self, service: str, db_name: str, app_name: str) -> DokkuResult:
        return self.run([f"{service}:link", db_name, app_name])

    def service_unlink(self, service: str, db_name: str, app_name: str) -> DokkuResult:
        return self.run([f"{service}:unlink", db_name, app_name])

    def service_start(self, service: str, db_name: str) -> DokkuResult:
        return self.run([f"{service}:start", db_name])

    def service_stop(self, service: str, db_name: str) -> DokkuResult:
        return self.run([f"{service}:stop", db_name])

    def service_logs(self, service: str, db_name: str, num: int = 100) -> DokkuResult:
        return self.run([f"{service}:logs", db_name, "-n", str(num)])

    # ------------------------------------------------------------------ #
    # Misc
    # ------------------------------------------------------------------ #
    def version(self) -> DokkuResult:
        return self.run(["version"])

    def nginx_show_config(self, name: str) -> DokkuResult:
        return self.run(["nginx:show-config", name])

    def nginx_validate_config(self) -> DokkuResult:
        return self.run(["nginx:validate-config", "--clean"])
