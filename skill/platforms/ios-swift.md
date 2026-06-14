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
| 仅系统语言 | 无 in-app 切换 — 跳过 §3，仅 catalog + knownRegions |

legacy `.strings` 项目：用 `genstrings` 或 Xcode Export 流程，本 skill 脚本仅直接支持 xcstrings（v1）。

## 8. 验证清单

- [ ] 设置页出现新语言且名称正确
- [ ] 切换后 Tab / 核心流程文案为目标语言
- [ ] 权限弹窗（InfoPlist.strings）为目标语言
- [ ] 单元测试通过
- [ ] `audit_catalog.py` 无 missing locale
