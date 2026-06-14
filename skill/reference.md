# 参考文档

## 自动探测

无 `l10n.profile.yaml` 时，在 iOS/Swift 仓库中搜索：

```bash
find . -name 'Localizable.xcstrings' -o -name '*.xcstrings' | head -5
find . -name 'InfoPlist.strings' | head -5
rg -l 'enum AppLanguage|appLanguage' --glob '*.swift'
rg 'knownRegions' *.xcodeproj/project.pbxproj
```

取主 target 下的 catalog；若多个，优先 `Resources/` 或主 app module 名称匹配的路径。

---

## 语言映射表

| 用户说法 | BCP-47 | App Store Connect | 枚举 case 示例 | settings key 示例 |
|----------|--------|-------------------|----------------|-------------------|
| 日语 / 日本語 | `ja` | Japanese | `japanese` | `settings_language_japanese` |
| 韩语 / 한국어 | `ko` | Korean | `korean` | `settings_language_korean` |
| 法语 | `fr` | French | `french` | `settings_language_french` |
| 德语 | `de` | German | `german` | `settings_language_german` |
| 西班牙语 | `es` | Spanish (Spain) | `spanish` | `settings_language_spanish` |
| 葡语（巴西） | `pt-BR` | Portuguese (Brazil) | `portugueseBrazil` | `settings_language_portuguese_brazil` |
| 意大利语 | `it` | Italian | `italian` | `settings_language_italian` |
| 泰语 | `th` | Thai | `thai` | `settings_language_thai` |
| 越南语 | `vi` | Vietnamese | `vietnamese` | `settings_language_vietnamese` |
| 印尼语 | `id` | Indonesian | `indonesian` | `settings_language_indonesian` |
| 马来语 | `ms` | Malay | `malay` | `settings_language_malay` |
| 阿拉伯语 | `ar` | Arabic | `arabic` | `settings_language_arabic` |
| 俄语 | `ru` | Russian | `russian` | `settings_language_russian` |
| 简体中文 | `zh-Hans` | Chinese (Simplified) | `chinese` | `settings_language_chinese` |
| 繁体中文 | `zh-Hant` | Chinese (Traditional) | `traditionalChinese` | `settings_language_traditional_chinese` |
| English | `en` | English (U.S.) | `english` | `settings_language_english` |

**case 名与 key 名必须遵循项目已有命名风格**（camelCase / snake 后缀等）。

---

## App Store Connect 字符限制

| 字段 | 上限 |
|------|------|
| App 名称 | 30 |
| 副标题 | 30 |
| 推广文本 | 170 |
| 描述 | 4000 |
| 关键词 | 100 |
| 此版本的新增内容 | 4000 |

## Google Play（可选扩展）

| 字段 | 上限 |
|------|------|
| 标题 | 30 |
| 简短说明 | 80 |
| 完整说明 | 4000 |

---

## 元数据 Markdown 章节标题约定

供 `validate_metadata.py` 解析（中英均可）：

| 字段 | 推荐标题 |
|------|----------|
| App 名称 | `### 2.1 App 名称` 或 `### App Name` |
| 副标题 | `### 2.2 副标题` 或 `### Subtitle` |
| 推广文本 | `### 2.3 推广文本` 或 `### Promotional Text` |
| 描述 | `### 2.4 描述` 或 `### Description` |
| 关键词 | `### 2.5 关键词` 或 `### Keywords` |
| 此版本新增 | `### 2.6 此版本的新增内容` 或 `### What's New` |

字段内容放在紧随其后的 ` ```text ` 代码块中。

---

## 硬编码排查

```bash
# CJK 硬编码
rg '[\u4e00-\u9fff]' <source_dir> --glob '*.swift'

# SwiftUI 字面量
rg 'Text\("[^"]+"\)|Label\("[^"]+"\)' <source_dir> --glob '*.swift'

# Android（预留）
rg 'android:text="[^@]' --glob '*.xml'
```

发现未本地化字符串：迁移到 catalog 并在所有 locale 补翻译。

---

## 持久化数据本地化

**原则**：持久化层（UserDefaults、`@AppStorage`、Core Data、JSON 文件、默认种子数组）只存 **stable id** 或 **localization key**，禁止存某一 locale 的展示文案。

### 典型反例

```swift
// ❌ 首次启动写入已翻译文案 — 切换语言后 UI 仍显示旧语言
UserDefaults.standard.set(["阅读", "运动", "冥想", "早睡"], forKey: "default_habits")
```

```swift
// ✅ 存 key，展示时再本地化
UserDefaults.standard.set(
    ["habit.reading", "habit.exercise", "habit.meditation", "habit.early_sleep"],
    forKey: "default_habits"
)
```

### 审计命令

```bash
# UserDefaults / AppStorage 附近字面量
rg 'UserDefaults|@AppStorage|\.set\(|\.string\(forKey' --glob '*.swift' <source_dir>

# 默认种子 / 初始数据里的 CJK 或硬编码数组
rg '\["[\u4e00-\u9fff]|defaultHabits|seedData|initialData|default.*=\s*\[' --glob '*.swift' <source_dir>

# 自动化审计（推荐）
python3 <skill-root>/scripts/audit_runtime_l10n.py --source-dir <source_dir>
```

### 旧数据迁移

若检测到已有用户数据存的是展示文案：

1. 建立 **旧文案 → catalog key** 映射表（项目特有，写在 app migration 代码里）
2. 启动或版本升级时一次性迁移
3. 交付文档 §6 标注迁移范围与状态

skill **只检测 + 给出修复模式**，不自动改写用户数据。

---

## SwiftUI 运行时本地化

**何时适用**：`ios.has_in_app_language_switch: true` 或存在应用内语言切换。

### 常见问题

| 现象 | 原因 | 修复方向 |
|------|------|----------|
| catalog 有 `app.name` 但标题不随语言变 | `.navigationTitle("app.name")` 不刷新 | `String(localized:locale:)` + `.id(appLanguage)` |
| 习惯/分类名切换语言不变 | 持久化层存了旧 locale 文案 | 改存 key + migration |
| 部分 Text 仍用系统语言 | 未注入 `\.locale` | 根视图 `.environment(\.locale, resolvedLocale)` |

### 审计命令

```bash
# navigationTitle / tabItem 直接用 key 字面量
rg 'navigationTitle\("|\.tabItem|Tab\("[^"]+"\)' --glob '*.swift' <source_dir>

# 是否注入 locale / 强制刷新
rg '\.environment\(\\\.locale|\.id\(.*[Ll]anguage' --glob '*.swift' <source_dir>

python3 <skill-root>/scripts/audit_runtime_l10n.py --source-dir <source_dir>
```

详见 [platforms/ios-swift.md §9](platforms/ios-swift.md#9-swiftui-应用内语言切换)。

---

## l10n.profile.yaml 字段说明

见 [templates/l10n.profile.yaml](templates/l10n.profile.yaml) 内注释。

关键字段：

| 字段 | 用途 |
|------|------|
| `platform` | `ios-swift`（v1） |
| `ios.string_catalog` | Localizable.xcstrings 路径 |
| `ios.language_enum` | AppLanguage.swift 路径 |
| `ios.has_in_app_language_switch` | 是否有应用内语言切换（触发 SwiftUI §9 检查） |
| `ios.user_defaults_keys` | 已知存用户数据的 UserDefaults key（可选，辅助审计） |
| `ios.info_plist_strings_dir` | `.lproj` 父目录 |
| `app.brand_terms` | ASO / 翻译术语 |
| `store.apple.*` | 元数据与截图配置 |
| `deliverables.metadata_dir` | 输出目录 |

---

## Skill 根目录定位

脚本路径 `<skill-root>/scripts/` 按安装位置解析：

- 项目内：`.cursor/skills/app-i18n-l10n/scripts/`
- 克隆仓库：`<clone-path>/scripts/`
- 若不确定，用 `find` 定位 `validate_metadata.py`

也可将 scripts 加入 PATH 或复制到项目 `scripts/l10n/`。
