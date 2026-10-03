# 一刻

一个极简的番茄钟 App：**两个 Tab、三个按钮**，没有广告，不联网，数据只存在你自己的设备上。

> 「一刻」= 一刻钟，也 = 专注这一刻。

---

## 它有什么

- **任务清单**：加任务、改名字、删除；每天自动翻新，历史记录保留
- **番茄钟**：开始 / 暂停 / 结束任务，就三个按钮
- **到点提醒**：退到后台、甚至划掉 App，时间到了照样响铃 + 震动
- **统计**：今日 / 本周 / 总计的扇形图，还能按日期翻
- **深色 / 浅色 / 跟随系统** 三种主题
- **完全离线**：不联网、不收集任何个人信息、没有账号

## 怎么用

**安卓**：下载 Releases 里的 `一刻.apk`，直接安装。

**iPhone / 电脑**：直接打开网页版 ——
`https://<你的用户名>.github.io/<仓库名>/`
用 Safari 打开后点「添加到主屏幕」，看起来就和 App 一样。

> ⚠️ 网页版在 iPhone 上有个限制：**切到后台或锁屏后，时间到了不会响**。
> 因为 iOS 会冻结后台网页，而网页没法自己往系统里排闹钟。
> 安卓版没这个问题（我们写了原生插件）。

## 项目结构

```
focus/index.html        整个 App 的界面和逻辑（单文件，HTML + CSS + JS）
docs/index.html         公开的网页版（自动生成，别直接改）
tools/make_web_version  由 focus/index.html 生成 docs/index.html
tools/make_android_icons.py   生成安卓图标和启动画面
tools/check_focus.mjs   45 项自动检查，防止改坏
assets-src/             图标的原始图片
android-app/            安卓打包工程（Capacitor）
```

## 想自己改

改 `focus/index.html` 就能改掉所有界面和逻辑 —— 它是个单文件，浏览器直接打开就能看到效果。

```bash
# 改完之后跑一遍检查（45 项）
node tools/check_focus.mjs

# 重新生成公开的网页版
node tools/make_web_version.mjs

# 打包安卓（需要 Android SDK + JDK 21）
cd android-app
npm install
npx cap sync android
cd android && gradlew.bat assembleDebug
```

## 技术说明

- 界面用网页技术（HTML/CSS/JS），外壳用 **Capacitor** 套的安卓原生壳
- 为了让网页真正铺满全屏、并且能正确让开系统栏，写了一个原生插件
  （`android-app/android/app/src/main/java/com/tomato/focus/ShellPlugin.java`）
- 到点提醒用的是安卓原生闹钟，所以退到后台也能响
- CSS 刻意避开了 2019 年之后才有的特性，让 2017 年以后的老手机也能正常显示

## 声明

个人项目，未添加开源许可证（保留所有权利）。
