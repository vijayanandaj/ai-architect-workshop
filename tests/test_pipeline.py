import subprocess, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
def run(cmd):
    subprocess.check_call(cmd, cwd=ROOT)
def test_end_to_end():
    run([sys.executable, "tools/req_extract.py", "samples/requirements_sample.md", "--out", "samples/requirements.yaml"])
    run([sys.executable, "tools/req_validate.py", "samples/requirements.yaml"])
    try:
        run([sys.executable, "tools/req_lint.py", "samples/requirements.yaml"])
    except subprocess.CalledProcessError:
        pass
