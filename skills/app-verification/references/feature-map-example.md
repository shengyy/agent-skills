# 功能地图示例

下面是一个虚构的 shop-admin 应用的地图片段：一个索引，加一个功能文件。命令和 `verify-shop` 的子命令都是示例，生成时换成仓库里真实的东西。

## `features/README.md`

```markdown
# shop-admin 功能地图

| 功能 | 文件 | 入口 |
|---|---|---|
| 订单导出 | [export-orders.md](export-orders.md) | 订单列表「导出 CSV」按钮、`shop export` |
| 登录 | [login.md](login.md) | `/login` |
```

## `features/export-orders.md`

```markdown
# 订单导出

运营在后台把筛选后的订单导出成 CSV；财务脚本解析这个文件，所以列和格式不能变。

## 子功能

- `export-filtered`：按当前筛选条件导出。
- `export-cli`：命令行导出同样格式的文件。

## 用户怎么走到它

- 订单列表页右上角的「导出 CSV」按钮。
- 终端运行 `shop export --status shipped --out orders.csv`。

## 用 verify-shop 驱动

前提：

- `verify-shop doctor` 通过，指向 `http://127.0.0.1:5173` 和一次性数据目录。
- 已用 `scripts/seed.ts --orders 200` 灌入种子数据。

- **筛选**：把状态筛成「已发货」。`verify-shop browser select --label "状态" --value "已发货"`。列表计数显示「共 87 单」。
- **导出**：点「导出 CSV」。`verify-shop browser click --role button --name "导出 CSV"`。下载目录出现 `orders-*.csv`。
- **核对文件**：把下载目录里最新的 `orders-*.csv` 复制为 `artifacts/export/web.csv`，再跑 `verify-shop csv check artifacts/export/web.csv --rows 87 --header fixtures/orders-header.csv`。行数 87，表头与基准逐字节一致。
- **命令行入口**：`verify-shop cli -- shop export --status shipped --out artifacts/export/cli.csv`。退出码 0，`diff artifacts/export/web.csv artifacts/export/cli.csv` 为空。
- **证据**：`artifacts/export/` 下的两个 CSV，以及导出前后的截图。

## 坑

- 计数在筛选后异步刷新，等「共 N 单」变化后再点导出。
- 下载文件名带时间戳，按通配找，别写死。
- 只看到「导出成功」提示不算证据，要核对文件内容。
- 清理时删掉种子订单，保留 `artifacts/export/`。
```
