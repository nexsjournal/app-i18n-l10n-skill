# {语言名}（{bcp47}）· App Store Connect 元数据与宣传文案

> 版本：{version} · {date}  
> App Store Connect 语言：**{app_store_language}**  
> BCP-47：`{bcp47}`

---

## 0. 本地化审计摘要

| 项目 | 值 |
|------|-----|
| 新增 locale | `{bcp47}` |
| String Catalog 翻译 key | {key_count} |
| InfoPlist.strings | `{info_plist_path}` |
| 硬编码 UI 字符串 | {hardcoded_summary} |
| 持久化数据风险 | {persisted_data_summary} |
| SwiftUI 运行时风险 | {swiftui_runtime_summary} |

---

## 1. App Store Connect 填写清单

| 字段 | 字符上限 | 章节 |
|------|----------|------|
| App 名称 | 30 | §2.1 |
| 副标题 | 30 | §2.2 |
| 推广文本 | 170 | §2.3 |
| 描述 | 4000 | §2.4 |
| 关键词 | 100 | §2.5 |
| 此版本的新增内容 | 4000 | §2.6 |

---

## 2. 元数据

### 2.1 App 名称

```text
{app_name}
```

> 字符数：{app_name_len} / 30

### 2.2 副标题

```text
{subtitle}
```

> 字符数：{subtitle_len} / 30

### 2.3 推广文本

```text
{promotional_text}
```

> 字符数：{promo_len} / 170

### 2.4 描述

```text
{description}
```

> 字符数：{desc_len} / 4000

### 2.5 关键词

```text
{keywords}
```

> 字符数：{keywords_len} / 100

### 2.6 此版本的新增内容

```text
{whats_new}
```

> 字符数：{whats_new_len} / 4000

---

## 3. 宣传截图文案

| # | 主标题 | 副标题 |
|---|--------|--------|
| 01 | **{headline_01}** | {subhead_01} |
| … | … | … |

**可复制清单：**

```text
01 {headline_01} · {subhead_01}
…
```

---

## 4. 字符数速查表

| 字段 | 字符数 | 上限 | 状态 |
|------|--------|------|------|
| App 名称 | | 30 | |
| 副标题 | | 30 | |
| 推广文本 | | 170 | |
| 描述 | | 4000 | |
| 关键词 | | 100 | |
| 此版本新增 | | 4000 | |

---

## 5. 工程变更清单

| 文件 | 变更 |
|------|------|
| | |

---

## 6. 运行时本地化（需人工验证）

> catalog 完整 ≠ UI 正确。有应用内语言切换时逐项确认。

| 检查项 | 状态 | 备注 |
|--------|------|------|
| 语言消费模式 | ☐ | `system_only` / `in_app_switch` |
| 设置页语言选项（跟随系统 + 各 locale） | ☐ | 仅 `in_app_switch` |
| L1：`AppleLanguages` 已写入 | ☐ | `Text("key")` / `Toggle` |
| L2：`AppLocalization` 覆盖动态 key | ☐ | 心情、习惯、导出等 |
| L3：关键子视图 `.id(appLanguage)` | ☐ | 首页、设置、列表 |
| 日期/数字格式化绑 `resolvedLocale` | ☐ | |
| 导航标题随语言刷新 | ☐ | |
| Tab / 核心流程文案随语言刷新 | ☐ | |
| 持久化数据用 key 非展示文案 | ☐ | 习惯、分类、标签等 |
| 旧数据 migration | ☐ | 旧 locale 文案 → catalog key |
| 权限弹窗（默认跟系统） | ☐ | 按需单独处理 InfoPlist |
| 冷启动 + 切换语言各测一次 | ☐ | 无需改系统语言 |
