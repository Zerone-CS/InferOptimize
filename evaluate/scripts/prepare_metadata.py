#!/usr/bin/env python3
"""Fingerprint user-supplied run inputs; never infer quality or effective config."""
import argparse
import hashlib
import json
import sys
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def load_object(path):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    obj = json.loads(raw, object_pairs_hook=pairs,
                     parse_constant=lambda value: (_ for _ in ()).throw(ValueError("non-finite JSON")))
    if not isinstance(obj, dict) or not obj:
        raise ValueError(str(path) + " must contain a nonempty JSON object")
    canonical(obj)  # Reject numeric overflow (e.g. 1e999) as well as NaN.
    return obj, {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}


def prepare(args):
    if not args.scenario.strip():
        raise ValueError("scenario must not be empty")
    data = {"scenario": args.scenario, "quality_status": "not_evaluated",
            "effective_config_verified": False,
            "profiler_enabled": args.profiler_enabled == "on",
            "run_purpose": args.run_purpose,
            "source_inputs": {}, "schema_version": 1}
    for name in ("config", "environment", "metric_contract"):
        obj, source = load_object(getattr(args, name))
        data[name + "_sha256"] = hashlib.sha256(canonical(obj)).hexdigest()
        data["source_inputs"][name] = source
    if args.quality_report:
        obj, source = load_object(args.quality_report)
        if obj.get("status") not in ("pass", "fail", "not_evaluated"):
            raise ValueError("quality report status must be pass/fail/not_evaluated")
        if not isinstance(obj.get("scope"), str) or not obj["scope"].strip():
            raise ValueError("quality report must state a nonempty scope")
        if not isinstance(obj.get("method"), str) or not obj["method"].strip():
            raise ValueError("quality report must state a nonempty method")
        data["quality_status"] = obj["status"]
        data["quality_scope"] = obj["scope"]
        data["quality_method"] = obj["method"]
        data["source_inputs"]["quality_report"] = source
    if args.config_evidence:
        obj, source = load_object(args.config_evidence)
        if type(obj.get("verified")) is not bool:
            raise ValueError("config evidence verified must be a JSON boolean")
        if not isinstance(obj.get("scope"), str) or not obj["scope"].strip():
            raise ValueError("config evidence must state a nonempty scope")
        if not isinstance(obj.get("evidence"), list) or not obj["evidence"]:
            raise ValueError("config evidence must list supporting artifact paths")
        artifacts = []
        for entry in obj["evidence"]:
            if not isinstance(entry, str) or not entry.strip():
                raise ValueError("config evidence paths must be nonempty strings")
            p = Path(entry)
            if not p.is_absolute():
                p = Path(args.config_evidence).resolve().parent / p
            p = p.resolve(strict=True)
            if not p.is_file():
                raise ValueError("config evidence artifact is not a file")
            artifacts.append({"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
        data["effective_config_verified"] = obj["verified"]
        data["config_verification_scope"] = obj["scope"]
        data["source_inputs"]["config_evidence"] = source
        data["config_evidence_artifacts"] = artifacts
    data["verification_note"] = (
        "Quality and effective-config states are supplied assertions with provenance. "
        "This tool checks files and field types, not the sufficiency or truth of their conclusions.")
    return data


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("scenario", "config", "environment", "metric-contract", "output"):
        ap.add_argument("--" + name, required=True)
    ap.add_argument("--profiler-enabled", required=True, choices=("on", "off"))
    ap.add_argument("--run-purpose", required=True, choices=("performance", "diagnostic"))
    ap.add_argument("--quality-report")
    ap.add_argument("--config-evidence")
    args = ap.parse_args(argv)
    try:
        output = Path(args.output)
        if output.exists() or output.is_symlink():
            raise ValueError("output already exists; use a new path")
        data = prepare(args)
        encoded = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        with output.open("x", encoding="utf-8") as stream:
            stream.write(encoded)
        print("Metadata saved: " + str(output))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print("metadata error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
