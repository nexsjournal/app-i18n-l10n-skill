# AltitudeNow 示例

本目录展示如何将 [app-i18n-l10n-skill](../../README.md) 接入真实 iOS 项目。

对应仓库：[altitudeshot](https://github.com/nexsjournal/altitudeshot)（路径示例）

## 使用方式

1. 将 `l10n.profile.yaml` 复制到项目根目录 `.l10n/profile.yaml`
2. 可选：复制 `glossary.yaml` 到 `.l10n/glossary.yaml`
3. 安装通用 skill：`cp -r ../../skill ~/.cursor/skills/app-i18n-l10n`
4. 对 Agent 说：**「使用 app-i18n-l10n，帮我增加德语版本」**

## 本项目已产出

| Locale | 元数据文档 |
|--------|------------|
| ja | `docs/localization/ja-app-store-metadata.md` |
| ko | `docs/localization/ko-app-store-metadata.md` |
| fr | `docs/localization/fr-app-store-metadata.md` |

## 翻译数据存放

AltitudeNow 使用 Python 模块存放翻译（项目内 `scripts/*_translations_data.py`），也可用通用 JSON：

```bash
python3 path/to/app-i18n-l10n-skill/scripts/export_catalog_keys.py \
  --catalog altitudeshot/Resources/Localizable.xcstrings \
  -o .l10n/translations/_keys.json
```

写入新 locale：

```bash
python3 path/to/app-i18n-l10n-skill/scripts/apply_locale_localizations.py \
  --catalog altitudeshot/Resources/Localizable.xcstrings \
  --locale de \
  --translations .l10n/translations/de.json \
  --settings-key settings_language_german \
  --labels .l10n/translations/labels/settings_language_german.json
```
