from textwrap import dedent

from conftest import ROOT


def _role(tmp_path, tasks: str):
    tasks_dir = tmp_path / "roles" / "demo" / "tasks"
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "main.yml").write_text(dedent(tasks))
    return tmp_path


def test_repository_ansible_is_read_only(ansible_checker):
    assert ansible_checker.check(ROOT / "ansible") == []


def test_collection_modules_are_allowed(ansible_checker, tmp_path):
    root = _role(
        tmp_path,
        """
        - name: Packages
          ansible.builtin.package_facts:
        - name: Docker
          community.docker.docker_host_info:
        - name: Redis version
          ansible.builtin.command: redis-server --version
          changed_when: false
        """,
    )
    assert ansible_checker.check(root) == []


def test_modifying_module_is_rejected(ansible_checker, tmp_path):
    root = _role(
        tmp_path,
        """
        - name: Upgrade everything
          ansible.builtin.apt:
            upgrade: dist
        """,
    )
    errors = ansible_checker.check(root)
    assert len(errors) == 1
    assert "ansible.builtin.apt" in errors[0]


def test_command_without_changed_when_false_is_rejected(ansible_checker, tmp_path):
    root = _role(
        tmp_path,
        """
        - name: Version
          ansible.builtin.shell: psql --version
        """,
    )
    assert "changed_when" in ansible_checker.check(root)[0]


def test_tasks_inside_blocks_are_checked(ansible_checker, tmp_path):
    root = _role(
        tmp_path,
        """
        - name: Group
          block:
            - name: Write a file
              ansible.builtin.copy:
                content: x
                dest: /tmp/x
        """,
    )
    assert "ansible.builtin.copy" in ansible_checker.check(root)[0]


def test_handlers_are_rejected(ansible_checker, tmp_path):
    root = _role(tmp_path, "- ansible.builtin.debug: {msg: hi}\n")
    handlers = root / "roles" / "demo" / "handlers"
    handlers.mkdir()
    (handlers / "main.yml").write_text("- name: Restart\n  ansible.builtin.service: {name: x}\n")
    assert any("handlers" in e for e in ansible_checker.check(root))
