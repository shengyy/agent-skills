# 贡献指南 / Contributing

本仓库是一个 [Agent Skills](https://github.com/anthropics/skills) 合集，用 [`skills`](https://skills.sh/) CLI 一键分发。每个 skill 自成一个 `skills/<name>/` 目录，至少含一个 `SKILL.md`。

## 加一个新 skill

1. **初始化骨架**（在仓库根目录）：

   ```bash
   npx skills init skills/<new-skill-name>
   ```

   会生成 `skills/<new-skill-name>/SKILL.md`。

2. **填好 frontmatter**——两个字段必填：

   ```yaml
   ---
   name: <new-skill-name>          # 必须与目录名完全一致
   description: 一句话说明这个 skill 做什么、什么时候该用它；把触发词写清楚
   ---
   ```

   `description` 是 agent 决定「要不要用这个 skill」的唯一依据，务必写明**触发场景和触发词**，而不是泛泛而谈。

3. **写正文**——frontmatter 之后是给 agent 看的操作说明。建议：
   - 用祈使句、分步骤（`## Step 1` …），把判断分支和停下来问人的条件写明确；
   - 命令给可直接复制执行的形式；
   - 列清前置依赖（需要哪些外部 CLI、如何安装、如何验证）。

4. **附带文件（可选）**：需要脚本/模板/参考资料时，放进 `skills/<name>/` 下的 `scripts/`、`references/`、`assets/` 等子目录，并在 `SKILL.md` 里用相对路径引用——这些文件会随 `skills add` 一起安装。

5. **本地校验**：

   ```bash
   python3 scripts/validate_skills.py
   ```

   会检查每个 SKILL.md 的 frontmatter 完整性、目录名与 `name` 是否一致。CI 也跑同一个脚本。

6. **更新文档**：在 `README.md` 的 *Available Skills* 表格里加一行；在 `CHANGELOG.md` 的 `Unreleased` 段记一笔。

7. **提交 PR**：CI（`.github/workflows/validate-skills.yml`）通过后合并。

## 本地试装

推送前想先验证安装效果，可以直接从本地目录装：

```bash
# 列出仓库里能识别到的 skill
npx skills add . -l

# 装到当前项目（不污染全局），用 --copy 避免软链到工作区
npx skills add . --skill <new-skill-name> --copy
```

## 约定速查

- 一个 skill = 一个 `skills/<name>/` 目录，目录名即 skill 名，全小写、用 `-` 连字符。
- `SKILL.md` 的 `name` 必须等于目录名。
- 不要把机密、令牌、个人路径写进 SKILL.md（会被公开）。
- 提交信息遵循简洁的祈使句；一个 PR 聚焦一件事。

## 发布新版本

版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。发布时一起做三件事，然后打 tag：

1. 把 `CHANGELOG.md` 的 `[Unreleased]` 内容归到新版本段（如 `## [0.3.0] - YYYY-MM-DD`），并补回一个空的 `[Unreleased]`；更新底部的对比链接。
2. 更新根目录 `VERSION` 文件为新版本号。
3. 提交后打 tag 并推送：`git tag v0.3.0 && git push origin v0.3.0`。

README 顶部的版本徽章是动态读最新 git tag 的（`img.shields.io/github/v/tag`），打完 tag 会自动更新，无需手改。使用者用 `npx skills update -g` 即可拉到最新。
