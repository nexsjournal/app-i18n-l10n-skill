---
name: app-i18n-l10n
description: End-to-end mobile app localization — audit and translate in-app strings, wire up new locales in the project, and generate App Store Connect metadata (title, subtitle, promo text, description, keywords, what's new) plus screenshot marketing copy with ASO character limits. Use when the user asks to add a language version, localize the app, translate strings, i18n, l10n, or prepare store metadata for a new locale (e.g. "增加日语版本", "add Korean localization", "generate App Store metadata").
---

# App i18n / l10n

一句话触发：**「帮我增加 XX 语言版本」** → 应用内翻译 + 工程接入 + 商店元数据 + 截图文案 + 校验。

## 第一步：加载项目配置（必做）

按顺序查找并读取项目配置：

1. `.l10n/profile.yaml`（推荐）
2. `l10n.profile.yaml`（仓库根）
3. 若无配置文件 → 自动探测工程（见 [reference.md](reference.md#自动探测）），并**建议用户**补全 profile 模板

配置模板：[templates/l10n.profile.yaml](templates/l10n.profile.yaml)  
iOS 接入细节：[platforms/ios-swift.md](platforms/ios-swift.md)

若存在 `.l10n/glossary.yaml`，翻译时必须遵守其中的品牌术语。

---

## 工作流

```
- [ ] 0. 加载 l10n.profile.yaml
- [ ] 1. 解析目标语言（BCP-47 / 商店语言名 / 枚举 case）
- [ ] 2. 审计待翻译字符串
- [ ] 3. 应用内翻译与工程接入
- [ ] 4. 生成商店元数据（App Store Connect）
- [ ] 5. 生成宣传截图文案
- [ ] 6. 校验字符限制
- [ ] 7. 输出交付文档
- [ ] 8. 同步已有语言（语言列表、截图 #N 多语屏）
```

### 1. 解析目标语言

映射到（写入 profile / 平台文档）：

- **BCP-47** → xcstrings、`.lproj`
- **App Store Connect 语言名**
- **语言枚举 identifier**（iOS：`AppLanguage` case；命名遵循项目现有风格）
- **设置页 localization key**（如 `settings_language_japanese`）

常见映射见 [reference.md § 语言映射表](reference.md#语言映射表)。未指定语言时追问用户，不要猜测。

### 2. 审计

覆盖 profile 中 `audit.sources` 列出的全部来源。默认 iOS：

| 来源 | 典型路径 |
|------|----------|
| String Catalog | `*.xcstrings` |
| InfoPlist 字符串 | `{target}/{locale}.lproj/InfoPlist.strings` |
| 硬编码 | `Text("…")` / `Label("…")` / 中文正则 |
| 语言枚举 | `*Language*.swift` |
| 测试 | `*Language*Tests*` |
| Xcode | `project.pbxproj` → `knownRegions` |

运行（路径来自 profile 或探测结果）：

```bash
python3 <skill-root>/scripts/audit_catalog.py --catalog <xcstrings-path>
python3 <skill-root>/scripts/export_catalog_keys.py --catalog <xcstrings-path> -o /tmp/keys.json
```

交付文档 §0 写入：key 总数、缺失 locale 数、硬编码清单、待改文件列表。

### 3. 工程接入

**iOS** → 严格按 [platforms/ios-swift.md](platforms/ios-swift.md)。

通用原则：

- 保留所有格式占位符（`%@`、`%.0f`、`%lld`、`%1$d` 等）的位置与数量
- 翻译语气与现有 primary locale 一致；读 `profile.app.tone` 与 `glossary.yaml`
- 每个新 locale 同步添加 `settings_language_{locale}` 并在**所有已有 locale** 中补语言名

批量写入（推荐）：

```bash
python3 <skill-root>/scripts/apply_locale_localizations.py \
  --catalog <xcstrings> \
  --locale <bcp47> \
  --translations .l10n/translations/<bcp47>.json \
  --settings-key settings_language_<case> \
  --labels .l10n/translations/labels/settings_language_<case>.json
```

翻译 JSON 格式：`{ "key_name": "Translated value", ... }`

labels JSON 格式：`{ "en": "Japanese", "ja": "日本語", "zh-Hans": "日语", ... }`

完成后运行 profile 中 `verification.test_command`（若有）。

### 4. App Store Connect 元数据

字符上限（Apple 按字符计）：

| 字段 | 上限 |
|------|------|
| App 名称 | 30 |
| 副标题 | 30 |
| 推广文本 | 170 |
| 描述 | 4000 |
| 关键词 | 100 |
| 此版本的新增内容 | 4000 |

**ASO 关键词规则**：

- 英文逗号分隔，逗号后**不加空格**
- 不与 App 名称 / 副标题重复
- 字段内不重复（大小写不敏感）
- 从 profile `store.apple.aso_seed_terms` 与产品功能提炼，勿堆砌无关热词

**描述结构**（按 profile `store.apple.description_sections` 调整）：

1. 价值主张 1–2 句
2. 核心功能列表（条数见 profile，通常 4–8 条）
3. 目标用户（通常 3 条）
4. 隐私政策 + 用户协议 URL（来自 profile）

参考已有语言定稿：`profile.store.apple.metadata_reference`（若配置）。

### 5. 宣传截图文案

按 profile `store.apple.screenshots`：

- `count`：截图张数（默认 6）
- `themes`：每张主题（从现有 metadata 或产品文档提取，**勿硬编码业务词**）
- 最后一张通常为「多语界面」→ 副标题列出**全部已支持语言**（各语言自称）

### 6. 校验

```bash
python3 <skill-root>/scripts/validate_metadata.py \
  --file <profile.deliverables.metadata_dir>/{locale}-app-store-metadata.md
```

超限必须重写直至通过。

### 7. 交付文档

输出路径：`{profile.deliverables.metadata_dir}/{bcp47}-app-store-metadata.md`

结构见 [templates/app-store-metadata.md](templates/app-store-metadata.md)。

每个字段用 ` ```text ` 包裹，便于复制到 App Store Connect。

### 8. 同步已有语言

- 各 locale 的 `settings_language_*` 补新语言名
- 更新各语言 metadata 中截图「多语界面」列表
- 可选：更新 `profile.store.apple.metadata_reference` 主文档

---

## 翻译质量

- 术语一致：遵循 `glossary.yaml` 与 profile `app.brand_terms`
- 繁简 / 地区变体不可混用
- 无障碍 / VoiceOver 文案需自然可读
- 订阅、Pro 等品牌名：按 glossary 决定保留英文或官方译名

---

## 协作

- 截图**图片**生成：可配合 ASO screenshot skill；**文案以本 skill 产出为准**
- Google Play 元数据：复用工作流，字段上限见 reference（v1 可选）

---

## 示例

**用户**：帮我增加韩语版本

**Agent**：

1. 读 `.l10n/profile.yaml`
2. 映射 `ko` · App Store `Korean` · case `korean`
3. 审计 xcstrings + InfoPlist + 硬编码
4. 写入翻译、更新 AppLanguage / knownRegions / tests
5. 生成 `docs/localization/ko-app-store-metadata.md`
6. `validate_metadata.py` 通过 → 汇报变更清单
