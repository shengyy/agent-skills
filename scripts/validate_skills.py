#!/usr/bin/env python3
"""Validate every skill under skills/.

Checks, for each skills/<name>/SKILL.md:
  1. frontmatter exists (delimited by --- ... ---)
  2. `name` and `description` are present and non-empty
  3. the folder name matches the `name` field
  4. SKILL.md has a body after the frontmatter
  5. frontmatter values are strict-YAML-safe (no unquoted ": ", which GitHub's
     frontmatter renderer and other strict parsers reject)

No third-party dependencies — runs on a bare python3 (CI and local alike).
Exit code 0 = all good, 1 = at least one problem.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"


def parse_frontmatter(text: str):
    """Return (frontmatter_dict, body) or (None, reason) on failure."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "缺少 frontmatter 起始分隔符 '---'"
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, "frontmatter 没有结束分隔符 '---'"
    fm = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            continue
        key, _, val = raw.partition(":")
        fm[key.strip()] = val.strip()
    body = "\n".join(lines[end + 1 :]).strip()
    return fm, body


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"✗ 找不到 skills/ 目录: {SKILLS_DIR}")
        return 1

    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        print("✗ skills/ 下没有任何 skill 目录")
        return 1

    errors: list[str] = []
    ok: list[str] = []

    for d in skill_dirs:
        rel = d.relative_to(ROOT)
        skill_md = d / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"{rel}/: 缺少 SKILL.md")
            continue

        fm, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if fm is None:
            errors.append(f"{rel}/SKILL.md: {body}")
            continue

        name = fm.get("name", "")
        desc = fm.get("description", "")
        if not name:
            errors.append(f"{rel}/SKILL.md: frontmatter 缺少非空的 `name`")
        if not desc:
            errors.append(f"{rel}/SKILL.md: frontmatter 缺少非空的 `description`")
        if name and name != d.name:
            errors.append(
                f"{rel}/SKILL.md: `name: {name}` 与目录名 `{d.name}` 不一致"
            )
        if not body:
            errors.append(f"{rel}/SKILL.md: frontmatter 之后没有正文内容")

        # strict-YAML safety: an unquoted scalar value containing ": " (colon-space) is parsed
        # as a nested mapping and breaks strict YAML parsers (e.g. GitHub's frontmatter renderer).
        yaml_ok = True
        for k, v in fm.items():
            quoted = len(v) >= 2 and ((v[0] == '"' and v[-1] == '"') or (v[0] == "'" and v[-1] == "'"))
            if ": " in v and not quoted:
                errors.append(
                    f"{rel}/SKILL.md: frontmatter `{k}` 的值含未加引号的 ': '（破坏严格 YAML，如 GitHub 渲染）"
                    "——去掉冒号后的空格，或给整个值加引号"
                )
                yaml_ok = False

        if name and desc and name == d.name and body and yaml_ok:
            ok.append(d.name)

    print(f"扫描 {len(skill_dirs)} 个 skill 目录\n")
    for name in ok:
        print(f"  ✓ {name}")
    if errors:
        print()
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\n校验失败：{len(errors)} 个问题。")
        return 1

    print(f"\n全部通过 ✓ （{len(ok)} 个 skill）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
