# iOS / Swift 平台接入

> 前提：已读取 `.l10n/profile.yaml`。以下路径均指 profile 中的配置项。

## 1. Localizable.xcstrings

- 为每个 `strings` entry 的 `localizations` 添加目标 BCP-47
- **不要**修改 `sourceLanguage`（除非项目明确要求迁移）
- 占位符必须与 source locale 完全一致
- 空 key / 符号 key（`N`、`S`、`%lld`）通常保持原样

## 2. InfoPlist.strings

在 `{ios.info_plist_strings_dir}/{bcp47}.lproj/InfoPlist.strings` 创建文件。

至少翻译 profile `ios.info_plist_keys` 列出的 key；默认：

- `CFBundleDisplayName` / `CFBundleName`
- 所有 `NS*UsageDescription`（从现有 `en.lproj` 或 `Base.lproj` 对照）

## 3. 语言枚举（AppLanguage 模式）

典型项目有 `enum AppLanguage` + `AppSettings.resolvedLocale`。新增 locale 需改：

```swift
case korean  // 示例

// titleKey → settings_language_korean
// fixedLocaleIdentifier → "ko"
// settingsOrder 追加（顺序见 profile ios.language_settings_order）
```

`AppSettings` / `resolvedLocale` switch 同步追加 case。

**变体**：若项目用 `Locale` 数组而非 enum，按现有模式扩展，不要强行改成 enum。

## 4. Xcode project.pbxproj

在 `knownRegions` 追加 BCP-47（如 `ko`、`fr`、`zh-Hans`）。

Folder-based sync 工程通常自动识别新 `.lproj`；若未识别，手动加入 file reference。

## 5. 测试

扩展 `*LanguageTests*`（路径见 profile）：

- case 持久化（UserDefaults / @AppStorage key 见 profile）
- `resolvedLocale.identifier`
- `AppLocalization.string` 或等价 API 抽样 2–3 个 key

运行 profile `verification.test_command`。

## 6. settings_language_* 同步

1. 新建 `settings_language_{case}` entry
2. 在所有**已有** locale 的 catalog 中补该 key 的翻译（语言自称）
3. 在新 locale 中补全**所有** `settings_language_*` key

labels JSON 示例：

```json
{
  "en": "Korean",
  "zh-Hans": "韩语",
  "zh-Hant": "韓語",
  "ja": "韓国語",
  "ko": "한국어"
}
```

## 7. 常见工程布局

| 布局 | 识别特征 |
|------|----------|
| String Catalog | `Localizable.xcstrings` |
| legacy strings | `*.lproj/Localizable.strings` — 需按 key 文件逐条追加 |
| SwiftUI + enum | `AppLanguage` + `LocalizedStringKey` |
| 仅系统语言 | 无 in-app 切换 — 跳过 §3、§9，仅 catalog + knownRegions |

legacy `.strings` 项目：用 `genstrings` 或 Xcode Export 流程，本 skill 脚本仅直接支持 xcstrings（v1）。

## 8. 验证清单

- [ ] 设置页出现新语言且名称正确
- [ ] 切换后 Tab / 核心流程文案为目标语言
- [ ] 权限弹窗（InfoPlist.strings）为目标语言
- [ ] **切换语言后 navigationTitle / Tab 标签立即更新（无需重启）**
- [ ] **UserDefaults / 默认种子数据随语言切换显示正确翻译（非旧 locale 文案）**
- [ ] **冷启动 + 应用内切换语言各测一次**
- [ ] 单元测试通过
- [ ] `audit_catalog.py` 无 missing locale
- [ ] `audit_runtime_l10n.py` 无 WARN（或已列入交付文档待修复项）

## 9. SwiftUI 应用内语言切换

> **何时必查**：`ios.has_in_app_language_switch: true`，或项目有 `AppLanguage` / 语言设置页 / 非系统 `resolvedLocale`。

catalog 有翻译，但 UI 仍显示旧语言，通常是 **消费链** 问题，不是 catalog 问题。

### 反模式

| 反模式 | 后果 |
|--------|------|
| 默认习惯/分类数组存 `["阅读", "运动"]` | 切换语言后仍显示中文 |
| `UserDefaults` 写入已翻译展示文案 | 持久化层绑定某一 locale |
| `.navigationTitle("app.name")` 仅传 key | SwiftUI 切换语言后标题可能不刷新 |
| `Text(savedDisplayString)` 直接显示持久化字符串 | 不随 locale 变化 |
| 只改 catalog，根视图未注入 `\.locale` | 部分组件仍用系统语言 |

### 推荐模式

**1. 持久化层只存 key 或 stable id**

```swift
// ❌ 反模式
let defaultHabits = ["阅读", "运动", "冥想", "早睡"]

// ✅ 推荐
let defaultHabitKeys = ["habit.reading", "habit.exercise", "habit.meditation", "habit.early_sleep"]

// 展示时解析
func displayName(for key: String, locale: Locale) -> String {
    String(localized: String.LocalizationValue(key), locale: locale)
}
```

**2. 旧数据一次性迁移**

若已有用户数据存的是某 locale 的展示文案，提供 migration（启动时或版本升级）：

```swift
// 旧中文 → catalog key 映射；映射表仅用于 migration，不进 skill 正文
let legacyNameToKey = ["阅读": "habit.reading", "运动": "habit.exercise", ...]
```

skill 职责：**检测**需迁移的字段并给出映射建议；**不** silent 改写用户数据。

**3. 显式 locale 取串 + 强制刷新视图树**

```swift
// 显式按当前 app 语言取标题
.navigationTitle(
    String(localized: String.LocalizationValue("app.name"), locale: settings.resolvedLocale)
)

// 语言变更时强制重建视图（挂在 NavigationStack / TabView 根节点）
.id(settings.appLanguage)

// 根节点注入 locale
.environment(\.locale, settings.resolvedLocale)
```

**4. 优先复用项目已有 L10n 封装**

若已有 `AppLocalization.string(_:)` 或等价 API，扩展它而非新建平行体系。

### 审计命令

```bash
python3 <skill-root>/scripts/audit_runtime_l10n.py --source-dir <ios.source_dir>
```

详见 [reference.md § 持久化数据本地化](../reference.md#持久化数据本地化)。
