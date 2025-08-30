#!/usr/bin/env python
import argparse, json, yaml, jsonschema, pathlib
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("yaml_file"); ap.add_argument("--schema", default="tools/req_schema.json")
    a=ap.parse_args()
    schema=json.loads(pathlib.Path(a.schema).read_text())
    data=yaml.safe_load(pathlib.Path(a.yaml_file).read_text())
    jsonschema.validate(data, schema)
    print("Schema validation: OK")
