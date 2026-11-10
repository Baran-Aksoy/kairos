#!/usr/bin/env python3
"""Guarantee that the Kairos Ansible content never changes a managed VM.

Rules:
- only collection modules are allowed (allow-list below, plus any ``*_info`` / ``*_facts``);
- ``command`` / ``shell`` / ``raw`` must declare ``changed_when: false``;
- no handlers (a handler implies a change to react to).

Usage: check_ansible_readonly.py [ANSIBLE_DIR]   (default: <repo>/ansible)
Exit code 1 and one line per violation if anything is wrong.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ALLOWED_MODULES = {
    "setup",
    "gather_facts",
    "package_facts",
    "service_facts",
    "command",
    "shell",
    "raw",
    "stat",
    "slurp",
    "find",
    "getent",
    "uri",
    "set_fact",
    "set_stats",
    "debug",
    "assert",
    "fail",
    "meta",
    "include_tasks",
    "import_tasks",
    "include_role",
    "import_role",
    "include_vars",
}
COMMAND_MODULES = {"command", "shell", "raw"}
BLOCK_KEYS = ("block", "rescue", "always")
TASK_KEYWORDS = {
    "name", "when", "register", "become", "become_user", "become_method", "vars", "tags",
    "loop", "loop_control", "with_items", "with_dict", "with_list", "with_fileglob",
    "changed_when", "failed_when", "ignore_errors", "ignore_unreachable", "delegate_to",
    "delegate_facts", "run_once", "check_mode", "diff", "environment", "no_log", "until",
    "retries", "delay", "args", "notify", "listen", "timeout", "throttle", "any_errors_fatal",
    "collections", "module_defaults", "debugger", "async", "poll", "connection",
    *BLOCK_KEYS,
}  # fmt: skip
PLAY_TASK_SECTIONS = ("pre_tasks", "tasks", "post_tasks")


class _AnsibleLoader(yaml.SafeLoader):
    """SafeLoader that tolerates Ansible tags such as !vault or !unsafe."""


_AnsibleLoader.add_multi_constructor("!", lambda loader, suffix, node: None)


def _short_name(module: str) -> str:
    return module.rsplit(".", 1)[-1]


def _module_of(task: dict) -> str | None:
    for key in task:
        if key not in TASK_KEYWORDS:
            return key
    return None


def _is_false(value: object) -> bool:
    return value is False or (isinstance(value, str) and value.strip().lower() == "false")


def _check_tasks(tasks: object, where: str, errors: list[str]) -> None:
    if not isinstance(tasks, list):
        return
    for task in tasks:
        if not isinstance(task, dict):
            continue
        label = f"{where}: task '{task.get('name', '<sans nom>')}'"
        if any(key in task for key in BLOCK_KEYS):
            for key in BLOCK_KEYS:
                _check_tasks(task.get(key), where, errors)
            continue
        if "notify" in task:
            errors.append(f"{label}: 'notify' interdit (implique une modification)")
        module = _module_of(task)
        if module is None:
            continue
        short = _short_name(module)
        if short in COMMAND_MODULES:
            if not _is_false(task.get("changed_when")):
                errors.append(f"{label}: '{module}' doit avoir 'changed_when: false'")
        elif short not in ALLOWED_MODULES and not short.endswith(("_info", "_facts")):
            errors.append(f"{label}: module '{module}' non autorisé (lecture seule)")


def _load(path: Path) -> object:
    with path.open(encoding="utf-8") as fh:
        return yaml.load(fh, Loader=_AnsibleLoader)  # noqa: S506 - SafeLoader subclass


def check(ansible_dir: Path) -> list[str]:
    errors: list[str] = []
    if not ansible_dir.is_dir():
        return errors

    for playbook in sorted(ansible_dir.glob("*.y*ml")):
        plays = _load(playbook)
        if not isinstance(plays, list):
            continue
        for play in plays:
            if not isinstance(play, dict):
                continue
            if play.get("handlers"):
                errors.append(f"{playbook.name}: handlers interdits")
            for section in PLAY_TASK_SECTIONS:
                _check_tasks(play.get(section), playbook.name, errors)

    roles_dir = ansible_dir / "roles"
    for role in sorted(p for p in roles_dir.glob("*") if p.is_dir()):
        handlers = [p for p in (role / "handlers").rglob("*.y*ml")]
        if handlers:
            errors.append(f"roles/{role.name}: handlers interdits")
        for task_file in sorted((role / "tasks").rglob("*.y*ml")):
            _check_tasks(_load(task_file), str(task_file.relative_to(ansible_dir)), errors)

    return errors


def main(argv: list[str]) -> int:
    default = Path(__file__).resolve().parent.parent / "ansible"
    ansible_dir = Path(argv[1]) if len(argv) > 1 else default
    errors = check(ansible_dir)
    for error in errors:
        print(error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
