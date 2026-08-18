# 金属链板成本计算器 — Android 版

桌面版（tkinter）的计算器移植到手机上的版本。界面用 **Kivy** 重写，
计算内核 **完全复用** 桌面版的 `chainplate_calc.py`（纯 Python，无界面依赖），
因此计算结果与桌面版一致。

## 目录结构

```
.
├── main.py               # Kivy 手机界面 + 计算入口
├── chainplate_calc.py    # 计算引擎（与桌面版同一份）
├── settings.json         # 价格/常数配置（已放入你的实际价格，可在文件里改）
├── buildozer.spec        # buildozer 打包配置
├── .github/workflows/
│   └── build-apk.yml     # GitHub Actions 自动编译 APK
└── README.md
```

## 一、在 GitHub 上编译 APK（推荐，无需本地装环境）

1. 把本目录的所有文件上传到一个 **GitHub 仓库的根目录**（`main.py`、`buildozer.spec`、
   `chainplate_calc.py`、`settings.json`、`.github/` 都要在仓库根目录）。
2. 进入仓库页面 → **Actions** 标签。
3. 左侧选择 **Build Android APK** → 点 **Run workflow** → 再次确认 **Run workflow**。
4. 等待编译完成（首次约 10~20 分钟，需下载 Android SDK/NDK）。
5. 编译成功后，在该次运行页面底部 **Artifacts** 里下载 **chainplate-apk**（zip），
   解压得到 `chainplatecost-1.0.0-*.apk`。

> 首次推送代码到 `main` 分支也会自动触发编译（见 workflow 的 `push` 触发条件）。

## 二、安装到手机

1. 把 APK 传到手机（微信/QQ/数据线均可）。
2. 点击 APK 安装；若提示“未知来源/风险”，按提示允许“安装未知应用”即可
   （debug 版 APK 使用调试签名，属于正常现象）。
3. 打开「金属链板成本计算器」即可使用。

## 三、修改公式 / 价格 / 常数

- **计算公式**：在手机 App 主界面点右下角【**设置公式**】按钮，即可直接修改板价格、
  穿杆价格、切割/焊接/冲孔费、每米总价等全部公式（每条下方灰色小字列出可用变量）。
  修改后点【保存】，会校验公式合法性并保存到手机；之后计算立即按新公式生效。
  【恢复默认公式】可一键还原。
- **价格/常数**：修改本目录的 `settings.json`（已放入你的实际价格）后重新编译即可。
  `settings.json` 里缺的项会自动使用引擎内置默认值，所以只需改你要改的项。

## 四、本地编译（可选，需要 Linux 或 WSL）

```bash
pip install buildozer cython
buildozer android debug
```

生成的 APK 在 `bin/` 目录下。

## 五、手机版与桌面版的差异

| 项目 | 桌面版 | 手机版 |
|------|--------|--------|
| 界面框架 | tkinter | Kivy |
| 计算内核 | chainplate_calc.py | 同一份（未改动） |
| 材质/节距/尺寸/选配件 | 支持 | 支持 |
| 醒目总价显示 | 支持 | 支持（固定在底部） |
| 实时防抖重算 | 支持 | 支持 |
| 公式编辑 | 支持（设置窗口） | 支持（主界面【设置公式】按钮，保存到手机） |
| 价格/常数等其它设置 | 支持（设置窗口） | 暂不支持界面编辑（用 settings.json 修改） |
| 导出 CSV | 支持 | 暂不支持 |

## 六、常见问题

- **编译报错 `kivy` 依赖失败**：检查 `buildozer.spec` 里 `requirements = python3,kivy==2.3.0`；
  如仍失败可尝试 `requirements = python3,kivy`。
- **APK 太大**：把 `buildozer.spec` 里的 `android.archs` 改为只保留 `arm64-v8a`（减半）。
- **想要应用图标**：放一张 `icon.png`（512×512）到本目录，并取消 `buildozer.spec` 中
  `icon.filename` 那行的注释。
