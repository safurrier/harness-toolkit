"""Contract tests for path-selective product verification routes."""

from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from tests._support import SCAFFOLD_ROOT, _generated_project_env

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
paths = ["src/api/**"]
script = "scripts/verify/api"
required = true
kind = "runtime"
[[routes]]
id = "browser"
paths = ["web/**"]
script = "scripts/verify/browser"
required = true
kind = "browser"
[[routes]]
id = "shared"
always = true
paths = []
script = "scripts/verify/shared"
required = true
kind = "runtime"
"""


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(repo / "scripts" / "verify-routes"), *args],
        cwd=repo,
        text=True,
        capture_output=True,
    )


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        env=_generated_project_env(),
    )


def test_routes_select_matching_and_always_paths(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        CONFIG,
        {
            "scripts/verify/api": "echo api >> result",
            "scripts/verify/browser": "echo browser >> result",
            "scripts/verify/shared": "echo shared >> result",
        },
    )
    result = run(repo, "--path", "src/api/server.py", "--path", "src/api/server.py")
    assert result.returncode == 0, result.stderr
    assert (repo / "result").read_text().splitlines() == ["api", "shared"]


def test_routes_without_selector_run_all_required(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        CONFIG,
        {
            "scripts/verify/api": "echo api >> result",
            "scripts/verify/browser": "echo browser >> result",
            "scripts/verify/shared": "echo shared >> result",
        },
    )
    assert run(repo).returncode == 0
    assert set((repo / "result").read_text().splitlines()) == {
        "api",
        "browser",
        "shared",
    }


def test_routes_select_paths_from_git_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_repo(
        tmp_path,
        CONFIG,
        {
            "scripts/verify/api": "echo api >> result",
            "scripts/verify/browser": "echo browser >> result",
            "scripts/verify/shared": "echo shared >> result",
        },
    )
    run_git(repo, "init")
    run_git(repo, "add", ".")
    run_git(
        repo,
        "-c",
        "user.name=test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "base",
    )
    (repo / "web" / "page.ts").parent.mkdir()
    (repo / "web" / "page.ts").write_text("changed")
    run_git(repo, "add", "web/page.ts")
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "hostile.git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "hostile-worktree"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "hostile.index"))
    result = run(repo, "--changed-from", "HEAD")
    assert result.returncode == 0, result.stderr
    assert (repo / "result").read_text().splitlines() == ["browser", "shared"]


def test_renamed_path_selects_routes_for_old_and_new_locations(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        CONFIG,
        {
            "scripts/verify/api": "echo api >> result",
            "scripts/verify/browser": "echo browser >> result",
            "scripts/verify/shared": "echo shared >> result",
        },
    )
    source = repo / "src" / "api" / "page.ts"
    source.parent.mkdir(parents=True)
    source.write_text("original")
    run_git(repo, "init")
    run_git(repo, "add", ".")
    run_git(
        repo,
        "-c",
        "user.name=test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "base",
    )
    destination = repo / "web" / "page.ts"
    destination.parent.mkdir()
    source.rename(destination)
    run_git(repo, "add", "-A")

    result = run(repo, "--changed-from", "HEAD")

    assert result.returncode == 0, result.stderr
    assert (repo / "result").read_text().splitlines() == ["api", "browser", "shared"]


def test_empty_changed_from_runs_only_always_routes(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        CONFIG,
        {
            "scripts/verify/api": "echo api >> result",
            "scripts/verify/browser": "echo browser >> result",
            "scripts/verify/shared": "echo shared >> result",
        },
    )
    run_git(repo, "init")
    run_git(repo, "add", ".")
    run_git(
        repo,
        "-c",
        "user.name=test",
        "-c",
        "user.email=test@example.com",
        "commit",
        "-m",
        "base",
    )

    result = run(repo, "--changed-from", "HEAD")

    assert result.returncode == 0, result.stderr
    assert (repo / "result").read_text().splitlines() == ["shared"]


@pytest.mark.parametrize(
    "config, expected",
    [
        (
            "version = 1\n[[routes]]\nid='x'\npaths=[]\nscript='scripts/verify/x'\nrequired=true\n",
            "needs paths or always = true",
        ),
        (
            "version = 1\n[[routes]]\nid='x'\npaths=['x']\nscript='scripts/verify/missing'\nrequired=true\n",
            "missing or not executable",
        ),
        (
            "version = 1\n[[routes]]\nid='x'\npaths=['x']\nscript='scripts/a'\nrequired=true\nkind='manual'\n",
            "manual route",
        ),
    ],
)
def test_routes_reject_invalid_automated_contracts(
    tmp_path: Path, config: str, expected: str
) -> None:
    repo = make_repo(tmp_path, config)
    result = run(repo)
    assert result.returncode != 0 and expected in result.stderr


def test_selector_rejects_unmatched_required_route_with_missing_script(
    tmp_path: Path,
) -> None:
    repo = make_repo(
        tmp_path,
        """version = 1
[[routes]]
id = "selected"
paths = ["src/**"]
script = "scripts/verify/selected"
required = true
kind = "runtime"
[[routes]]
id = "unmatched"
paths = ["web/**"]
script = "scripts/verify/missing"
required = true
kind = "browser"
""",
        {"scripts/verify/selected": "exit 0"},
    )

    result = run(repo, "--path", "src/app.py")

    assert result.returncode != 0
    assert "route 'unmatched' script is missing or not executable" in result.stderr


def test_selector_rejects_unmatched_required_route_with_non_executable_script(
    tmp_path: Path,
) -> None:
    repo = make_repo(
        tmp_path,
        """version = 1
[[routes]]
id = "selected"
paths = ["src/**"]
script = "scripts/verify/selected"
required = true
kind = "runtime"
[[routes]]
id = "unmatched"
paths = ["web/**"]
script = "scripts/verify/unmatched"
required = true
kind = "browser"
""",
        {
            "scripts/verify/selected": "exit 0",
            "scripts/verify/unmatched": "exit 0",
        },
    )
    (repo / "scripts" / "verify" / "unmatched").chmod(0o644)

    result = run(repo, "--path", "src/app.py")

    assert result.returncode != 0
    assert "route 'unmatched' script is missing or not executable" in result.stderr


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
paths = ["src/**"]
script = "{script}"
required = true
kind = "runtime"
""",
    )

    result = run(repo)

    assert result.returncode != 0
    assert expected in result.stderr


def test_routes_reject_symlink_escape(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        """version = 1
[[routes]]
id = "x"
paths = ["src/**"]
script = "scripts/verify/escape"
required = true
kind = "runtime"
""",
    )
    outside = tmp_path / "outside"
    outside.write_text("#!/bin/sh\nexit 0\n")
    outside.chmod(0o755)
    (repo / "scripts" / "verify").mkdir(parents=True)
    (repo / "scripts" / "verify" / "escape").symlink_to(outside)

    result = run(repo)

    assert result.returncode != 0
    assert "must resolve beneath scripts/verify" in result.stderr


def test_routes_reject_symlinked_config_directory(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        """version = 1
[[routes]]
id = "x"
paths = ["src/**"]
script = "scripts/verify/x"
required = true
kind = "runtime"
""",
        {"scripts/verify/x": "exit 0"},
    )
    external = tmp_path / "outside-config"
    (repo / ".harness").rename(external)
    (repo / ".harness").symlink_to(external)

    result = run(repo)

    assert result.returncode != 0
    assert "repository-owned regular file" in result.stderr


def test_routes_reject_symlinked_verification_directory(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        """version = 1
[[routes]]
id = "x"
paths = ["src/**"]
script = "scripts/verify/x"
required = true
kind = "runtime"
""",
    )
    outside = tmp_path / "outside-routes"
    outside.mkdir()
    script = outside / "x"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o755)
    (repo / "scripts" / "verify").symlink_to(outside)

    result = run(repo)

    assert result.returncode != 0
    assert "repository-owned directory, not a symlink" in result.stderr


def test_routes_reject_symlinked_scripts_directory(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        """version = 1
[[routes]]
id = "x"
paths = ["src/**"]
script = "scripts/verify/x"
required = true
kind = "runtime"
""",
        {"scripts/verify/x": "exit 0"},
    )
    external = tmp_path / "outside-scripts"
    (repo / "scripts").rename(external)
    (repo / "scripts").symlink_to(external)

    result = run(repo)

    assert result.returncode != 0
    assert "repository-owned directory, not a symlink" in result.stderr


def test_route_failure_propagates(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path,
        CONFIG,
        {
            "scripts/verify/api": "exit 7",
            "scripts/verify/browser": "exit 0",
            "scripts/verify/shared": "exit 0",
        },
    )
    assert run(repo, "--path", "src/api/x.py").returncode == 7


def test_runtime_route_exercises_server_side_effect_and_cleanup(tmp_path: Path) -> None:
    """A generated route must prove a public request and persisted effect."""
    repo = make_repo(
        tmp_path,
        """version = 1
[[routes]]
id = "record-journey"
paths = ["src/records/**"]
script = "scripts/verify/record-journey"
required = true
kind = "runtime"
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
                    assert error.code == 404  # negative control: absent record is not success
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
                state.unlink(missing_ok=True); state.parent.rmdir()  # cleanup only state this route owns
            """
        )
    )
    route.chmod(0o755)

    result = run(repo, "--path", "src/records/api.py")
    assert result.returncode == 0, result.stderr
    assert (
        repo / "test-results/verification/record-journey/observed.json"
    ).read_text() == '{"name": "Ada"}'
    assert not list(repo.glob("verification-route-*"))
