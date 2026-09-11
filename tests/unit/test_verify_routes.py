"""Contract tests for explicitly selected product verification routes."""

from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from tests._support import SCAFFOLD_ROOT

pytestmark = pytest.mark.unit


def make_repo(
    tmp_path: Path, config: str, scripts: dict[str, str] | None = None
) -> Path:
    repo = tmp_path / "repo"
    (repo / ".harness").mkdir(parents=True)
    (repo / ".harness" / "verification.toml").write_text(config)
    (repo / "scripts").mkdir()
    shutil.copy2(
        SCAFFOLD_ROOT / "scripts" / "verify-routes", repo / "scripts" / "verify-routes"
    )
    (repo / "scripts" / "verify-routes").chmod(0o755)
    for name, body in (scripts or {}).items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\n" + body)
        path.chmod(0o755)
    return repo


CONFIG = """version = 1
[[routes]]
id = "api"
title = "Exercise the API journey"
script = "scripts/verify/api"
[[routes]]
id = "browser"
title = "Exercise the browser journey"
script = "scripts/verify/browser"
[[routes]]
id = "shared"
title = "Exercise shared behavior"
script = "scripts/verify/shared"
"""


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(repo / "scripts" / "verify-routes"), *args],
        cwd=repo,
        text=True,
        capture_output=True,
    )


def scripts() -> dict[str, str]:
    return {
        "scripts/verify/api": "echo api >> result",
        "scripts/verify/browser": "echo browser >> result",
        "scripts/verify/shared": "echo shared >> result",
    }


def test_list_describes_routes_without_running_them(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, CONFIG, scripts())
    result = run(repo, "--list")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "api\tExercise the API journey",
        "browser\tExercise the browser journey",
        "shared\tExercise shared behavior",
    ]
    assert not (repo / "result").exists()


def test_repeated_route_runs_only_named_routes_once(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, CONFIG, scripts())
    result = run(repo, "--route", "api", "--route", "api", "--route", "shared")
    assert result.returncode == 0, result.stderr
    assert (repo / "result").read_text().splitlines() == ["api", "shared"]
    assert "Verified 2 route(s)." in result.stdout


def test_all_runs_every_registered_route(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, CONFIG, scripts())
    result = run(repo, "--all")
    assert result.returncode == 0, result.stderr
    assert (repo / "result").read_text().splitlines() == ["api", "browser", "shared"]


def test_explicit_mode_is_required(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, CONFIG, scripts())
    result = run(repo)
    assert result.returncode != 0
    assert "one of the arguments --list --route --all is required" in result.stderr


def test_modes_are_mutually_exclusive(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, CONFIG, scripts())
    result = run(repo, "--all", "--route", "api")
    assert result.returncode != 0
    assert "not allowed with argument" in result.stderr


def test_unknown_route_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, CONFIG, scripts())
    result = run(repo, "--route", "missing")
    assert result.returncode != 0
    assert "unknown verification route(s): missing" in result.stderr


@pytest.mark.parametrize(
    "config, expected",
    [
        ("version = 2\n", "requires version = 1"),
        ("version = 1\nextra = true\n", "unsupported top-level fields"),
        (
            "version = 1\n[[routes]]\nid='x'\ntitle='X'\nscript='scripts/verify/x'\npaths=['src/**']\n",
            "unsupported fields: paths",
        ),
        (
            "version = 1\n[[routes]]\nid='x'\nscript='scripts/verify/x'\n",
            "requires a non-empty title",
        ),
        (
            "version = 1\n[[routes]]\nid='x'\ntitle='X'\nscript='scripts/verify/x'\n[[routes]]\nid='x'\ntitle='X2'\nscript='scripts/verify/x2'\n",
            "route IDs must be unique",
        ),
    ],
)
def test_routes_reject_invalid_registry(
    tmp_path: Path, config: str, expected: str
) -> None:
    repo = make_repo(tmp_path, config)
    result = run(repo, "--list")
    assert result.returncode != 0 and expected in result.stderr


def test_routes_reject_non_utf8_registry(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, "version = 1\n")
    (repo / ".harness" / "verification.toml").write_bytes(b"\xff\xfe")
    result = run(repo, "--list")
    assert result.returncode != 0
    assert "malformed verification config" in result.stderr


def test_unselected_broken_route_does_not_block_selected_route(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        CONFIG,
        {"scripts/verify/api": "exit 0"},
    )
    result = run(repo, "--route", "api")
    assert result.returncode == 0, result.stderr


def test_selected_missing_script_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, CONFIG, {"scripts/verify/api": "exit 0"})
    result = run(repo, "--route", "browser")
    assert result.returncode != 0
    assert "missing or not executable" in result.stderr


def test_all_validates_every_script(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, CONFIG, {"scripts/verify/api": "exit 0"})
    result = run(repo, "--all")
    assert result.returncode != 0
    assert "route 'browser' script is missing or not executable" in result.stderr


@pytest.mark.parametrize(
    "script, expected",
    [
        ("/tmp/route", "must be relative"),
        ("../outside", "must resolve beneath scripts/verify"),
    ],
)
def test_routes_reject_script_paths_outside_owned_directory(
    tmp_path: Path, script: str, expected: str
) -> None:
    repo = make_repo(
        tmp_path,
        f"""version = 1
[[routes]]
id = "x"
title = "X"
script = "{script}"
""",
    )
    result = run(repo, "--route", "x")
    assert result.returncode != 0
    assert expected in result.stderr


def test_routes_reject_symlink_escape(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        """version = 1
[[routes]]
id = "x"
title = "X"
script = "scripts/verify/escape"
""",
    )
    outside = tmp_path / "outside"
    outside.write_text("#!/bin/sh\nexit 0\n")
    outside.chmod(0o755)
    (repo / "scripts" / "verify").mkdir(parents=True)
    (repo / "scripts" / "verify" / "escape").symlink_to(outside)
    result = run(repo, "--route", "x")
    assert result.returncode != 0
    assert "must resolve beneath scripts/verify" in result.stderr


def test_routes_reject_symlinked_config_directory(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, CONFIG, scripts())
    external = tmp_path / "outside-config"
    (repo / ".harness").rename(external)
    (repo / ".harness").symlink_to(external)
    result = run(repo, "--list")
    assert result.returncode != 0
    assert "repository-owned regular file" in result.stderr


def test_routes_reject_symlinked_verification_directory(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, CONFIG)
    outside = tmp_path / "outside-routes"
    outside.mkdir()
    (repo / "scripts" / "verify").symlink_to(outside)
    result = run(repo, "--route", "api")
    assert result.returncode != 0
    assert "repository-owned directory, not a symlink" in result.stderr


def test_routes_reject_symlinked_scripts_directory(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, CONFIG, scripts())
    external = tmp_path / "outside-scripts"
    (repo / "scripts").rename(external)
    (repo / "scripts").symlink_to(external)
    result = run(repo, "--route", "api")
    assert result.returncode != 0
    assert "repository-owned directory, not a symlink" in result.stderr


def test_route_failure_propagates(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, CONFIG, {"scripts/verify/api": "exit 7"})
    assert run(repo, "--route", "api").returncode == 7


def test_runtime_route_exercises_server_side_effect_and_cleanup(tmp_path: Path) -> None:
    """A generated route must prove a public request and persisted effect."""
    repo = make_repo(
        tmp_path,
        """version = 1
[[routes]]
id = "record-journey"
title = "Create and retrieve a record"
script = "scripts/verify/record-journey"
""",
    )
    route = repo / "scripts" / "verify" / "record-journey"
    route.parent.mkdir(parents=True)
    route.write_text(
        "#!/usr/bin/env python3\n"
        + textwrap.dedent(
            """\
            import http.server
            import json
            import tempfile
            import threading
            import urllib.error
            import urllib.request
            from pathlib import Path

            state = Path(tempfile.mkdtemp(prefix="verification-route-")) / "record.json"
            class Handler(http.server.BaseHTTPRequestHandler):
                def do_GET(self):
                    if self.path == "/ready":
                        self.send_response(200); self.end_headers(); return
                    if self.path == "/record" and state.exists():
                        self.send_response(200); self.end_headers(); self.wfile.write(state.read_bytes()); return
                    self.send_response(404); self.end_headers()
                def do_POST(self):
                    if self.path != "/record":
                        self.send_response(404); self.end_headers(); return
                    state.write_bytes(self.rfile.read(int(self.headers["Content-Length"])))
                    self.send_response(201); self.end_headers()
                def log_message(self, *_): pass
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                assert urllib.request.urlopen(base + "/ready").status == 200
                try:
                    urllib.request.urlopen(base + "/record")
                except urllib.error.HTTPError as error:
                    assert error.code == 404
                else:
                    raise AssertionError("negative control unexpectedly found a record")
                request = urllib.request.Request(base + "/record", data=b'{"name":"Ada"}', method="POST")
                assert urllib.request.urlopen(request).status == 201
                observed = json.loads(urllib.request.urlopen(base + "/record").read())
                assert observed == {"name": "Ada"}
                output = Path("test-results/verification/record-journey/observed.json")
                output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(observed))
            finally:
                server.shutdown(); thread.join(); server.server_close()
                state.unlink(missing_ok=True); state.parent.rmdir()
            """
        )
    )
    route.chmod(0o755)

    result = run(repo, "--route", "record-journey")
    assert result.returncode == 0, result.stderr
    assert (
        repo / "test-results/verification/record-journey/observed.json"
    ).read_text() == '{"name": "Ada"}'
    assert not list(repo.glob("verification-route-*"))
