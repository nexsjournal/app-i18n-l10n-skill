# app-i18n-l10n-skill

Agent Skill：为移动 App 端到端增加新语言版本——应用内字符串翻译与工程接入、App Store Connect / Google Play 元数据、宣传截图文案、字符限制校验。

当前 **v1 主攻 iOS（Swift + String Catalog / xcstrings）**；Android 等平台预留扩展点。

## 能做什么

用户一句话：**「帮我增加日语版本」**，Agent 将：

1. 读取项目 `l10n.profile.yaml`（或自动探测工程结构）
2. 审计全部待翻译字符串（xcstrings、InfoPlist、硬编码等）
3. 写入新 locale 翻译并接入语言切换 / Xcode 配置
4. 生成 App Store Connect 元数据文档（含 ASO 关键词规则）
5. 生成宣传截图文案
6. 运行脚本校验字符上限

## 快速开始

### 1. 安装 Skill

**Cursor / Claude Code（项目级）**

```bash
git clone https://github.com/nexsjournal/app-i18n-l10n-skill.git
cp -r app-i18n-l10n-skill/skill .cursor/skills/app-i18n-l10n
# 或 Claude Code:
cp -r app-i18n-l10n-skill/skill ~/.claude/skills/app-i18n-l10n
```

**Skills CLI（若已发布到 GitHub）**

```bash
npx skills add nexsjournal/app-i18n-l10n-skill -y
```

### 2. 在 App 项目中创建配置文件

复制模板并按项目修改：

```bash
mkdir -p .l10n
cp path/to/app-i18n-l10n-skill/skill/templates/l10n.profile.yaml .l10n/profile.yaml
```

必填：`app.name`、`ios.string_catalog`、`ios.language_enum`、`store.apple.privacy_policy_url` 等。

参考完整示例：[examples/altitudeshot/l10n.profile.yaml](examples/altitudeshot/l10n.profile.yaml)

### 3. 触发

在 Agent 对话中说：

> 使用 app-i18n-l10n skill，帮我增加韩语版本

## 仓库结构

```
app-i18n-l10n-skill/
├── README.md
├── LICENSE
├── skill/                      # Agent Skill 本体（复制此目录安装）
│   ├── SKILL.md
│   ├── reference.md
│   ├── platforms/ios-swift.md
│   └── templates/
│       ├── l10n.profile.yaml
│       └── app-store-metadata.md
├── scripts/                    # 可独立运行的 CLI 工具
│   ├── validate_metadata.py
│   ├── apply_locale_localizations.py
│   ├── audit_catalog.py
│   ├── audit_runtime_l10n.py
│   └── export_catalog_keys.py
└── examples/
    └── altitudeshot/           # 真实项目配置示例
```

## 脚本用法

```bash
# 校验 App Store 元数据字符限制
python3 scripts/validate_metadata.py --file docs/localization/ja-app-store-metadata.md

# 审计 xcstrings 各 locale 完整度
python3 scripts/audit_catalog.py --catalog path/to/Localizable.xcstrings

# 审计 SwiftUI 运行时本地化（持久化 key、标题刷新等）
python3 scripts/audit_runtime_l10n.py --source-dir path/to/MyApp

# 导出 key 清单（供翻译）
python3 scripts/export_catalog_keys.py --catalog path/to/Localizable.xcstrings -o keys.json

# 批量写入新 locale（translations 为 JSON：{ "key": "翻译" }）
python3 scripts/apply_locale_localizations.py \
  --catalog path/to/Localizable.xcstrings \
  --locale ja \
  --translations translations/ja.json \
  --settings-key settings_language_japanese \
  --labels translations/labels/settings_language_japanese.json
```

## 通用化设计

| 层级 | 职责 |
|------|------|
| **Skill（通用）** | 工作流、ASO 规则、交付物模板、平台无关检查清单 |
| **`l10n.profile.yaml`（每项目）** | 路径、Bundle ID、品牌术语、已有语言、截图结构 |
| **`platforms/ios-swift.md`** | iOS 特有：AppLanguage、knownRegions、InfoPlist.strings |
| **`examples/`** | 参考实现，不进入 Skill 正文 |

新增 App 时**只需维护 profile**，无需 fork Skill。

## 与单项目 Skill 的关系

若 App 有非常特殊的业务（如 AltitudeNow 的「山峰护照」ASO 词库），可在项目内保留薄层 overlay：

```
.agents/skills/myapp-l10n/SKILL.md   # 仅 20 行：加载 profile + 链接本 skill + 项目术语表
.l10n/profile.yaml
.l10n/glossary.yaml                  # 可选：品牌术语锁定
```

## License

MIT — 见 [LICENSE](LICENSE)
