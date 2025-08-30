.PHONY: venv install extract validate lint er test
venv:
	python3.11 -m venv .venv && . .venv/bin/activate && pip install -U pip
install: venv
	. .venv/bin/activate && pip install -r requirements.txt
extract:
	. .venv/bin/activate && python tools/req_extract.py samples/requirements_sample.md --out samples/requirements.yaml
validate:
	. .venv/bin/activate && python tools/req_validate.py samples/requirements.yaml
lint:
	. .venv/bin/activate && python tools/req_lint.py samples/requirements.yaml || true
er:
	. .venv/bin/activate && python tools/generate_mermaid_er.py samples/requirements.yaml --out docs/er.mmd
test:
	. .venv/bin/activate && pytest -q
