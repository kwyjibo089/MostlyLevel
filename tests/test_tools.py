"""Build, deploy, and screenshot scripts, run against a fake mpremote.

The fake records its arguments instead of talking to a board, so these
tests check the commands the scripts send, not the board's response.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

FAKE_MPREMOTE = """#!{python}
import json, os, shutil, sys
args = sys.argv[1:]
with open(os.environ["FAKE_MPREMOTE_LOG"], "a") as log:
    log.write(json.dumps(args) + "\\n")
# Emulate "fs cp :remote local" for the screenshot script.
for index, arg in enumerate(args[:-1]):
    nxt = args[index + 1]
    if arg.startswith(":") and arg.endswith(".bmp") and not nxt.startswith(":"):
        shutil.copy(os.environ["FAKE_BMP"], nxt)
"""

COMPILED = {"app", "ble_read", "compositor", "graphics", "ili9341", "screenshot", "touch"}


@pytest.fixture
def fake_mpremote(tmp_path):
    script = tmp_path / "mpremote"
    script.write_text(FAKE_MPREMOTE.format(python=sys.executable))
    script.chmod(0o755)
    log = tmp_path / "mpremote.log"
    return script, log


def run_tool(name, *args, env_extra=None, fake=None, check=True):
    env = dict(os.environ)
    if fake is not None:
        env["MPREMOTE"] = str(fake[0])
        env["FAKE_MPREMOTE_LOG"] = str(fake[1])
    env.update(env_extra or {})
    return subprocess.run(
        [str(TOOLS / name), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=check,
    )


def calls(fake):
    return [json.loads(line) for line in fake[1].read_text().splitlines()]


def exec_snippets(args):
    return [args[index + 1] for index, arg in enumerate(args) if arg == "exec"]


@pytest.fixture
def build_dir(tmp_path):
    return tmp_path / "build"


def test_build_bundle(build_dir):
    run_tool("build_mpy.sh", env_extra={"BUILD_DIR": str(build_dir)})
    names = sorted(path.name for path in build_dir.iterdir())
    assert names == sorted(["main.py", "config.py"] + [name + ".mpy" for name in COMPILED])
    assert (build_dir / "main.py").read_bytes() == (ROOT / "src" / "main.py").read_bytes()
    for name in COMPILED:
        header = (build_dir / (name + ".mpy")).read_bytes()[:3]
        # .mpy major version 6 matches the board's MicroPython 1.29 (_mpy 6.3);
        # flags 0 means bytecode only, loadable on any 6.x sub-version.
        assert header == b"M\x06\x00", name


def test_deploy_builds_checks_uploads_and_cleans(fake_mpremote, build_dir):
    run_tool("deploy.sh", env_extra={"BUILD_DIR": str(build_dir)}, fake=fake_mpremote)
    (args,) = calls(fake_mpremote)
    assert args[:3] == ["connect", "auto", "exec"]
    check, cleanup = exec_snippets(args)
    assert "!= 6" in check

    cp = args.index("cp")
    uploaded = args[cp + 1:args.index(":", cp)]
    assert sorted(pathlib.Path(path).name for path in uploaded) == sorted(
        path.name for path in build_dir.iterdir()
    )
    for name in COMPILED:
        assert "'%s.py'" % name in cleanup
    assert "'main.py'" not in cleanup and "'config.py'" not in cleanup
    assert args[-2:] == ["+", "reset"]
    for snippet in (check, cleanup):
        compile(snippet, "board", "exec")


def test_deploy_version_check_rejects_other_mpy_versions(fake_mpremote, build_dir):
    run_tool("deploy.sh", env_extra={"BUILD_DIR": str(build_dir)}, fake=fake_mpremote)
    check = exec_snippets(calls(fake_mpremote)[0])[0]

    class Implementation:
        _mpy = 0x2B06  # Reported by the board: .mpy 6.3, xtensawin.

    namespace = {}
    sys_module = type(sys)("sys")
    sys_module.implementation = Implementation
    exec(check.replace("import sys\n", ""), {"sys": sys_module}, namespace)

    Implementation._mpy = 0x2B05
    with pytest.raises(RuntimeError, match="version 5"):
        exec(check.replace("import sys\n", ""), {"sys": sys_module}, namespace)


def test_deploy_sources(fake_mpremote):
    run_tool("deploy.sh", "-s", "-p", "/dev/ttyACM0", fake=fake_mpremote)
    (args,) = calls(fake_mpremote)
    assert args[:4] == ["connect", "/dev/ttyACM0", "fs", "cp"]
    uploaded = [pathlib.Path(path).name for path in args[4:args.index(":")]]
    assert "ble_scan.py" not in uploaded and "app.py" in uploaded and "main.py" in uploaded
    (cleanup,) = exec_snippets(args)
    assert "'app.mpy'" in cleanup and "'main.mpy'" not in cleanup


def test_deploy_explicit_files_without_reset(fake_mpremote):
    run_tool("deploy.sh", "-n", "src/ble_scan.py", fake=fake_mpremote)
    assert calls(fake_mpremote) == [["connect", "auto", "fs", "cp", "src/ble_scan.py", ":"]]


def test_deploy_repl_option(fake_mpremote):
    run_tool("deploy.sh", "-r", "src/config.py", fake=fake_mpremote)
    assert calls(fake_mpremote)[0][-2:] == ["+", "repl"]


def test_deploy_rejects_missing_file(fake_mpremote):
    result = run_tool("deploy.sh", "nope.py", fake=fake_mpremote, check=False)
    assert result.returncode == 1
    assert not fake_mpremote[1].exists()


@pytest.fixture
def fake_bmp(tmp_path):
    import screenshot

    path = tmp_path / "fake.bmp"
    with open(path, "wb") as image_file:
        screenshot.write_bmp_header(image_file, 240, 320)
        screenshot.write_bmp_tile(image_file, bytearray(240 * 320 * 2), 240, 320)
    return path


@pytest.mark.skipif(shutil.which("magick") is None, reason="ImageMagick 'magick' not installed")
@pytest.mark.parametrize(
    "argument, board_name, png_name",
    [
        (None, "screenshot.bmp", "screenshot.png"),
        ("levelling", "levelling.bmp", "levelling.png"),
        ("corners.bmp", "corners.bmp", "corners.png"),
        ("wedges.png", "wedges.png.bmp", "wedges.png"),
    ],
)
def test_screenshot_names(fake_mpremote, fake_bmp, tmp_path, argument, board_name, png_name):
    assets = tmp_path / "assets"
    args = ["-n"] + ([argument] if argument else [])
    run_tool(
        "screenshot.sh",
        *args,
        fake=fake_mpremote,
        env_extra={"FAKE_BMP": str(fake_bmp), "ASSETS_DIR": str(assets)},
    )
    (call,) = calls(fake_mpremote)
    assert call[:4] == ["connect", "auto", "resume", "+"]
    assert exec_snippets(call) == ["save_screenshot('/%s')" % board_name]
    assert ":" + board_name in call
    assert [path.name for path in assets.iterdir()] == [png_name]
    assert (assets / png_name).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_screenshot_rejects_paths(fake_mpremote):
    result = run_tool("screenshot.sh", "../evil", fake=fake_mpremote, check=False)
    assert result.returncode == 2
    assert not fake_mpremote[1].exists()
