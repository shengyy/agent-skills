# 贡献指南 / Contributing

本文负责新增 skill、本地试装、贡献与发版流程；仓库约定见 [`AGENTS.md`](AGENTS.md)，结构校验以 [`scripts/validate_skills.py`](scripts/validate_skills.py) 为准，面向安装者的入口见 [`README.md`](README.md)。

## 加一个新 skill

1. **初始化骨架**（在仓库根目录）：

   ```bash
   npx skills init skills/<new-skill-name>
   ```

   会生成 `skills/<new-skill-name>/SKILL.md`。

2. **填好 frontmatter**——两个字段必填，写法见 [`AGENTS.md`](AGENTS.md)：

   ```yaml
   ---
   name: <new-skill-name>
   description: <一句话：做什么、什么时候用>
   ---
   ```

3. **写正文**——frontmatter 之后是给 agent 看的操作说明，写法见 [`AGENTS.md`](AGENTS.md)，样例见 [`codex-construction/SKILL.md`](skills/codex-construction/SKILL.md)；命令给可直接复制执行的形式，列清前置依赖。

4. **附带文件（可选）**：脚本、模板、参考资料放 `skills/<name>/` 下的子目录，会随 `skills add` 一起安装。

5. **本地校验**：

   ```bash
   python3 scripts/validate_skills.py
   ```

   CI（`.github/workflows/validate-skills.yml`）跑同一个脚本。

6. **更新文档**：两份 README 的 *Available Skills* 表各加一行；在 `CHANGELOG.md` 的 `Unreleased` 段记一笔。

7. **提交 PR**：提交信息用简洁的祈使句，一个 PR 聚焦一件事；CI 通过后合并。

## 本地试装

推送前想先验证安装效果，可以直接从本地目录装：

```bash
# 列出仓库里能识别到的 skill
npx skills add . -l

# 装到当前项目（不污染全局），用 --copy 避免软链到工作区
npx skills add . --skill <new-skill-name> --copy
```

## 发布新版本

版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。发布时一起做三件事，然后打 tag：

1. 把 `CHANGELOG.md` 的 `[Unreleased]` 内容归到新版本段（`## [X.Y.Z] - YYYY-MM-DD`），并补回一个空的 `[Unreleased]`。
2. 更新根目录 `VERSION` 文件为新版本号。
3. 提交后打 tag 并推送：`git tag vX.Y.Z && git push origin vX.Y.Z`。
