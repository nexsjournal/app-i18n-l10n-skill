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

## 3. 语言模式：系统语言 vs 应用内切换

完成 catalog 翻译后，必须确认项目采用哪种 **消费模式**（见 profile `ios.localization_strategy`）：

| 模式 | profile 值 | 行为 | skill 交付 |
|------|------------|------|------------|
| 仅系统语言 | `system_only` | 用户改 iOS 系统语言后界面变化 | catalog + InfoPlist + knownRegions |
| 应用内切换 | `in_app_switch` | 设置页可选「跟随系统 / English / …」，**无需改系统语言** | 上列 + §3.1 脚手架 + §9 三层消费链 |

**探测**：若 profile 未配置但用户期望「设置里选语言」，或 `existing_locales` ≥ 2 且无 `AppLanguage` → **建议** `in_app_switch` 并实现 §3.1。

仅写 catalog **不等于** 应用内可切换；未实现 §3.1 时，交付文档须写明「当前仅跟随系统语言」。

### 3.1 应用内切换脚手架（`in_app_switch` 时默认交付）

无现有 `AppLanguage` 时，按项目结构新建（路径写入 profile）：

| 组件 | 职责 |
|------|------|
| `AppLanguage` enum | `followSystem` + 各固定 locale case；持久化到 `UserDefaults`（key 见 `ios.user_defaults_language_key`） |
| `AppSettings.resolvedLocale` | `followSystem` → 系统 Locale；固定 case → 对应 BCP-47 |
| `AppLocalization` | 统一取串（动态 key、模型标签、导出格式）；见 §9.2 |
| 设置页「语言」区块 | `跟随系统` + 各 `settings_language_*`；选项变更立即生效 |
| `ContentView` 根节点 | `.environment(\.locale, resolvedLocale)` + `.id(appLanguage)` |

设置页顺序见 `ios.language_settings_order`（默认 `follow_system_first`）。

新增 locale 时同步：enum case、`settings_language_*` catalog 条目、设置页选项、`AppLocalization` 测试。

**变体**：若项目已有 `AppLanguage` / 语言设置页，**扩展**而非重写。

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
| SwiftUI + enum | `AppLanguage` + 设置页语言区块 |
| 仅系统语言 | `localization_strategy: system_only` — 跳过 §3.1、§9 |

legacy `.strings` 项目：用 `genstrings` 或 Xcode Export 流程，本 skill 脚本仅直接支持 xcstrings（v1）。

## 8. 验证清单

- [ ] **设置页有语言选项**（`in_app_switch` 时：跟随系统 + 各 locale）
- [ ] 设置页出现新语言且名称正确
- [ ] 切换后 Tab / 核心流程文案为目标语言
- [ ] **模型/枚举展示名**（心情、习惯、导出格式等）随语言变化
- [ ] **日期 / 数字格式化**绑定 `resolvedLocale`（非 `Locale.current` 写死）
- [ ] 权限弹窗（InfoPlist.strings）为目标语言（或交付文档注明仍跟系统）
- [ ] **应用内切换语言后全文案刷新（无需重启、无需改系统语言）**
- [ ] **切换语言后 navigationTitle / Tab 标签立即更新**
- [ ] **UserDefaults / 默认种子数据随语言切换显示正确翻译（非旧 locale 文案）**
- [ ] **关键子视图**（首页、设置、列表项）有 `.id(appLanguage)` 或等价刷新
- [ ] **冷启动 + 应用内切换语言各测一次**
- [ ] 单元测试通过
- [ ] `audit_catalog.py` 无 missing locale
- [ ] `audit_runtime_l10n.py` 无 WARN（或已列入交付文档待修复项）

## 9. SwiftUI 应用内语言切换

> **何时必做**：`ios.localization_strategy: in_app_switch`，或 `has_in_app_language_switch: true`，或已有 `AppLanguage` / 语言设置页。

catalog 有翻译但 UI 仍不对，通常是 **消费链** 未接好——不是 catalog 问题。需按 **三层** 处理，单层不够。

### 9.0 三层消费链（缺一不可）

| 层级 | 解决什么 | 典型 API / 手段 |
|------|----------|-----------------|
| **L1 Bundle** | `Text("tab.home")`、`Toggle("settings.xxx")` 等 `LocalizedStringKey` **不跟** `.environment(\.locale)` | 切换语言时写 `AppleLanguages`；见 §9.1 |
| **L2 AppLocalization** | 动态 key、模型 `displayName`、导出模板、`String(localized:locale:)` 读 catalog 不稳 | 统一 `AppLocalization.string(_:)`，从 locale 对应 Bundle / `.lproj` 取串；见 §9.2 |
| **L3 视图刷新** | 部分子树不重建、日期仍用系统格式 | 根 + **关键子视图** `.id(appLanguage)`；`DateFormatter` / `formatted()` 显式传 `resolvedLocale`；见 §9.3 |

冒烟时 **三层都要测**：Tab/静态文案（L1）、心情/习惯/导出（L2）、首页日期（L3）。

### 反模式

| 反模式 | 后果 |
|--------|------|
| 只翻译 catalog，无设置页语言选项 | 只能改系统语言才生效 |
| 默认习惯/分类数组存 `["阅读", "运动"]` | 切换语言后仍显示中文 |
| `UserDefaults` 写入已翻译展示文案 | 持久化层绑定某一 locale |
| 以为 `.environment(\.locale)` 够用了 | `Text("key")` 仍显示旧语言 |
| 动态 key 仅用 `String(localized:locale:)` | 部分 key 从 String Catalog 解析失败 |
| 模型 `displayName` 返回硬编码或存好的文案 | 心情名、习惯名、导出句不随语言变 |
| `DateFormatter()` 未设 `locale` | 日期/星期仍跟系统语言 |
| 只在根视图 `.id(appLanguage)` | 嵌套列表/卡片不刷新 |

### 9.1 L1：AppleLanguages（LocalizedStringKey）

SwiftUI 的 `Text("settings.title")`、`Toggle("key")`、`Label("key", ...)` 使用 `LocalizedStringKey`，**不会**因 `.environment(\.locale)` 改变而切换语言。

在 `AppLanguage` 变更时（`followSystem` 时恢复系统列表）：

```swift
func applyLanguagePreference(_ language: AppLanguage) {
    switch language {
    case .followSystem:
        UserDefaults.standard.removeObject(forKey: "AppleLanguages")
    case .english:
        UserDefaults.standard.set(["en"], forKey: "AppleLanguages")
    case .chinese:
        UserDefaults.standard.set(["zh-Hans"], forKey: "AppleLanguages")
    // 每新增 case 追加对应 BCP-47
    }
}
```

仍建议在根视图保留 `.environment(\.locale, resolvedLocale)` + `.id(appLanguage)`，但 **不能替代** `AppleLanguages`。

### 9.2 L2：AppLocalization（动态 key / 模型 / 导出）

以下场景 **必须** 走 `AppLocalization`（或项目等价封装），不要依赖 `Text("key")` 或裸 `String(localized:locale:)`：

- 枚举/模型展示名：`Mood.displayName`、`HabitDefinition.title`
- 运行时拼出的 key：`"mood.\(rawValue)"`
- 导出/分享文案：`ExportService` 中的格式串
- `navigationTitle` 等需即时刷新的标题

推荐从 **locale 专用 Bundle** 取串（对 String Catalog 编译出的 `.lproj` 更稳）：

```swift
enum AppLocalization {
    static func string(_ key: String, locale: Locale) -> String {
        let id = locale.identifier.replacingOccurrences(of: "_", with: "-")
        guard let path = Bundle.main.path(forResource: id, ofType: "lproj"),
              let bundle = Bundle(path: path) else {
            return Bundle.main.localizedString(forKey: key, value: key, table: nil)
        }
        return bundle.localizedString(forKey: key, value: key, table: nil)
    }
}
```

持久化层只存 key（如 `habit.reading`），展示时 `AppLocalization.string(key, locale: settings.resolvedLocale)`。

旧数据 migration：旧展示文案 → catalog key 映射表（项目特有）；skill 只检测并建议，不 silent 改数据。

### 9.3 L3：视图刷新与日期格式化

```swift
// 根节点
.environment(\.locale, settings.resolvedLocale)
.id(settings.appLanguage)

// 易漏刷新的子视图（列表、卡片、设置区块）同样加 .id
HomeView().id(settings.appLanguage)

// 日期勿用 Locale.current
Text(date, format: .dateTime.weekday(.wide).month().day())
    .environment(\.locale, settings.resolvedLocale)
// 或 DateFormatter().locale = settings.resolvedLocale
```

### 9.4 InfoPlist 与系统对话框

`NS*UsageDescription`、Face ID 等系统权限弹窗读 **InfoPlist.strings**，默认跟 **系统语言**，不跟应用内 `AppleLanguages`。

交付文档须注明；若用户要求权限弹窗也跟应用语言，需单独评估（通常仍建议跟系统）。

### 审计命令

```bash
python3 <skill-root>/scripts/audit_runtime_l10n.py --source-dir <ios.source_dir>
```

详见 [reference.md § 持久化数据本地化](../reference.md#持久化数据本地化)、[§ SwiftUI 运行时本地化](../reference.md#swiftui-运行时本地化)。
