[app]

# (str) 应用标题（手机上显示的名字）
title = 金属链板成本计算器

# (str) 包名（仅小写字母、数字、下划线；需全局唯一）
package.name = chainplatecost

# (str) 包域名（反向域名，用于唯一标识）
package.domain = org.chainplate

# (str) 源码目录
source.dir = .

# (list) 要打包的源文件扩展名
source.include_exts = py,kv,json,txt,atlas

# (str) 应用版本
version = 1.0.0

# (list) 应用依赖（python3 与 kivy 是必须的）
requirements = python3,kivy==2.3.0

# (str) 支持的屏幕方向: portrait / landscape / all
orientation = portrait

# (bool) 是否全屏（0 = 保留状态栏，手机上体验更好）
fullscreen = 0

# (list) 目标 CPU 架构。arm64-v8a 覆盖近些年所有手机，
# 加上 armeabi-v7a 兼容更老的 32 位机型（APK 会稍大）。
android.archs = arm64-v8a,armeabi-v7a

# (int) 编译所用的 Android SDK API 级别
android.accept_sdk_license = True
android.api = 33

# (int) 最低支持的 Android 版本 (API 21 = Android 5.0)
android.minapi = 21

# (bool) 是否允许系统备份应用数据
android.allow_backup = True

# (str) 应用图标（留空使用 Kivy 默认图标；可自行放一张 icon.png 并改成 %(source.dir)s/icon.png）
# icon.filename = %(source.dir)s/icon.png

# (str) 启动画面背景色（白）
android.presplash_color = #FFFFFF

# (str) 日志详细程度: 0=error, 1=warning, 2=info, 3=debug
log_level = 2

[buildozer]

# (int) 日志级别
log_level = 2

# (bool) 是否允许以 root 运行（GitHub Actions 容器内通常需要）
warn_on_root = 1
