# 贡献指南 / Contributing

本文写**人类贡献流程**：怎么加 skill、怎么本地试装、怎么发版。仓库的硬约束（目录与 frontmatter 规则、唯一 owner、门禁）由 [`AGENTS.md`](AGENTS.md) 拥有，这里不重复。

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
   description: 一句话说明这个 skill 做什么、什么时候该用它；把触发词写清楚
   ---
   ```

3. **写正文**——frontmatter 之后是给 agent 看的操作说明。建议：
   - 用祈使句、分步骤（`## Step 1` …），把判断分支和停下来问人的条件写明确；
   - 命令给可直接复制执行的形式；
   - 列清前置依赖（需要哪些外部 CLI、如何安装、如何验证）。

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
