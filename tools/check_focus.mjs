/**
 * 校验单文件番茄钟 focus/index.html 的计时与统计逻辑。
 *
 * 单文件没法像模块那样 import，所以把 PURE-LOGIC-START/END 之间的纯计算
 * 抽出来，放进 Node 沙箱跑断言。同时做几个静态检查：
 *   - 整个脚本没有语法错误
 *   - 代码里 $("xxx") 引用到的界面元素都真实存在
 *   - 每个按钮都接上了动作
 *   - 没有任何外部网络依赖
 *
 * 用法：node tools/check_focus.mjs
 */

import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const html = readFileSync(join(root, "focus", "index.html"), "utf8");
const readText = (rel) => readFileSync(join(root, rel), "utf8");
const exists = (rel) => existsSync(join(root, rel));
const SHELL_JAVA = "android-app/android/app/src/main/java/com/tomato/focus/ShellPlugin.java";

let passed = 0;
const failures = [];

function check(name, fn) {
  try {
    fn();
    passed += 1;
  } catch (err) {
    failures.push(`${name} -> ${err.message}`);
  }
}

function equal(actual, expected, what) {
  const a = JSON.stringify(actual);
  const b = JSON.stringify(expected);
  if (a !== b) throw new Error(`${what || "值"}不一致：得到 ${a}，期望 ${b}`);
}

function throws(fn, keyword) {
  try {
    fn();
  } catch (err) {
    if (keyword && !String(err.message).includes(keyword)) {
      throw new Error(`报错内容里没有「${keyword}」：${err.message}`);
    }
    return;
  }
  throw new Error("本应报错，却没有报错");
}

/* ---------- 1. 结构 ---------- */

function scriptBlocks() {
  const blocks = [];
  const re = /<script>([\s\S]*?)<\/script>/g;
  let match;
  while ((match = re.exec(html)) !== null) blocks.push(match[1]);
  return blocks;
}

check("每一段 <script> 都没有语法错误", () => {
  const blocks = scriptBlocks();
  if (!blocks.length) throw new Error("找不到 <script> 块");
  blocks.forEach((code, index) => {
    try {
      new Function(code);
    } catch (err) {
      throw new Error(`第 ${index + 1} 段：${err.message}`);
    }
  });
});

const script = scriptBlocks()[scriptBlocks().length - 1];   // 主逻辑在最后一段

check("代码里引用的界面元素都真实存在", () => {
  const ids = new Set(Array.from(html.matchAll(/\bid="([^"]+)"/g), (m) => m[1]));
  const used = new Set(Array.from(script.matchAll(/\$\("([^"]+)"\)/g), (m) => m[1]));
  const missing = [...used].filter((id) => !ids.has(id));
  if (missing.length) throw new Error("这些 id 页面上不存在：" + missing.join(", "));
  if (used.size < 8) throw new Error("只找到 " + used.size + " 个引用，解析可能失效了");
});

check("每个按钮都接上了动作", () => {
  const buttons = Array.from(html.matchAll(/<button[^>]*id="([^"]+)"/g), (m) => m[1]);
  const wired = (id) =>
    script.includes(`$("${id}").addEventListener`) ||
    new RegExp(`bind\\w*\\(\\s*"${id}"`).test(script);
  const missing = buttons.filter((id) => !wired(id));
  if (missing.length) throw new Error("这些按钮没接动作：" + missing.join(", "));
  if (buttons.length < 6) throw new Error("只找到 " + buttons.length + " 个按钮");
});

check("没有任何外部网络依赖", () => {
  const external = html.match(/(?:src|href)\s*=\s*["'](https?:)?\/\//g);
  if (external) throw new Error("发现外部引用：" + external.join(", "));
  if (/<script[^>]+src=/i.test(html)) throw new Error("存在 <script src=...>");
});

check("备份：导出和导入必须成对出现", () => {
  // 只剩一个的话，用户要么导不出、要么导不回来 —— 都是死路
  for (const id of ["backup-export", "backup-import"]) {
    if (!html.includes(`id="${id}"`)) throw new Error(`界面上少了「${id}」按钮`);
  }
  // 导入要能"选文件"，不能只支持粘贴（备份文件本来就该能选）
  if (!html.includes('id="import-file"')) throw new Error("导入没有从文件读取的入口");
});

check("清空数据是两步确认，并且说清了后果", () => {
  if (!html.includes("再点一次确认清空")) throw new Error("找不到第二步确认的文案");
  const confirmBlock = html.slice(html.indexOf("最后确认："));
  if (!confirmBlock.includes("无法恢复")) throw new Error("确认文案里没说清「无法恢复」");
});

check("清空之前会先留一份可以恢复的数据", () => {
  const uses = (script.match(/snapshotBeforeClear\(\)/g) || []).length;
  if (uses < 2) throw new Error("snapshotBeforeClear 只出现 " + uses + " 次（定义 1 次 + 调用至少 1 次）");
  if (!script.includes("function readSnapshot")) throw new Error("缺少读取备份的函数");
  if (!html.includes("恢复上次清空前的数据")) throw new Error("界面上找不到恢复入口");
});

check("总结页有「今日 / 本周 / 总计」三个按钮，点哪看哪", () => {
  for (const mode of ["today", "week", "all"]) {
    if (!html.includes('data-mode="' + mode + '"')) throw new Error("找不到 data-mode=" + mode + " 的按钮");
  }
  if (!script.includes("function statsSessions")) throw new Error("缺少按模式取数据的函数");
  if (!/statMode === "week"/.test(script)) throw new Error("没有处理「本周」这个分支");
  if (!/statMode === "all"/.test(script)) throw new Error("没有处理「总计」这个分支");
  if (!/statMode === "day"/.test(script)) throw new Error("没有处理「某一天 / 今日」这个分支");
});

check("本周 / 总计展示的是扇形图，不是写死的文字数字", () => {
  if (!script.includes("const picked = statsSessions()")) throw new Error("扇形图没用上模式数据");
  if (!script.includes("byTask(sessions)")) throw new Error("扇形图没有按任务分块");
  if (/id="week-total"|id="all-total"/.test(html)) throw new Error("还留着旧的「只有数字」的卡片");
});

check("有浅色主题，并且能在设置里切换", () => {
  if (!html.includes('[data-theme="light"]')) throw new Error("找不到浅色主题的变量定义");
  for (const mode of ["dark", "light", "auto"]) {
    if (!html.includes('data-theme="' + mode + '"')) throw new Error("找不到主题按钮：" + mode);
  }
  if (!script.includes("function applyTheme")) throw new Error("缺少应用主题的函数");
  if (!script.includes("function resolvedTheme")) throw new Error("缺少解析「跟随系统」的函数");
  if (!script.includes("prefers-color-scheme")) throw new Error("没有跟随系统的判断");
});

check("打开时先定主题，避免浅色模式下闪一下深色", () => {
  const blocks = scriptBlocks();
  if (blocks.length < 2) throw new Error("头部应该有一段提前设置主题的脚本");
  if (!blocks[0].includes("dataset.theme")) throw new Error("头部那段脚本没有设置主题");
});

check("关键配色都走变量（浅色主题才不会花）", () => {
  const style = html.slice(html.indexOf("<style>"), html.indexOf("</style>"));
  const required = [
    "background: var(--bar-bg)",
    "background: var(--tabbar-bg)",
    "stroke: var(--track)",
    "fill: var(--ink)",
    "color: var(--toast-ink)",
    "background: var(--overlay)",
  ];
  for (const needle of required) {
    if (!style.includes(needle)) throw new Error("这一处没换成变量：" + needle);
  }
});

check("后台到点提醒：排原生闹钟、暂停/结束要取消", () => {
  if (!script.includes("function scheduleAlarm")) throw new Error("缺少排闹钟的函数");
  if (!script.includes("function cancelAlarm")) throw new Error("缺少取消闹钟的函数");
  if (!script.includes("LocalNotifications")) throw new Error("没有接安卓的原生通知插件");
  if (!script.includes("allowWhileIdle")) throw new Error("没设置休眠时也唤醒，锁屏会不准");
  for (const spot of ["scheduleAlarm(timer.phase, timer.remain)", "cancelAlarm()"]) {
    if (!script.includes(spot)) throw new Error("找不到调用：" + spot);
  }
});

check("打赏二维码真的嵌进去了", () => {
  if (!html.includes('id="tip-open"')) throw new Error("设置里没有打赏入口");
  if (!/id="tip-qr"[^>]*src="data:image\/png;base64,[A-Za-z0-9+/=]{500,}"/.test(html)) {
    throw new Error("收款码没嵌进去，或者数据不完整");
  }
  if (!script.includes('$("tip-open").addEventListener')) throw new Error("打赏按钮没接动作");
});

check("到点震动 + 固定开着的开关", () => {
  if (!script.includes("function vibrate")) throw new Error("缺少震动功能");
  if (!script.includes("navigator.vibrate")) throw new Error("没有调用系统震动");
  if (!script.includes("vibrate(finished")) throw new Error("一段结束时没有触发震动");
  // 开关撤掉了，这些行为固定用默认值 —— 默认值必须是"开着"
  for (const key of ["sound: true", "vibrate: true", "alarm: true"]) {
    if (!script.includes(key)) throw new Error("默认设置里少了：" + key);
  }
});

check("全屏：改窗口让网页铺满，系统栏区域自己让开", () => {
  if (!script.includes("function refineInsets")) throw new Error("缺少系统栏高度处理");
  if (!html.includes("--pad-top")) throw new Error("样式里没有状态栏让位变量");
  if (!html.includes("--pad-bottom")) throw new Error("样式里没有导航栏让位变量");
  // 键盘弹出时弹窗要能顶上去，否则改全屏会把输入框挡住
  if (!script.includes("visualViewport")) throw new Error("没有处理键盘遮挡");
});

check("兼容老手机：不用 2019 年之后才有的 CSS 特性", () => {
  // 先把注释剥掉 —— 注释里会提到这些名字，不能误伤
  const style = html
    .slice(html.indexOf("<style>"), html.indexOf("</style>"))
    .replace(/\/\*[\s\S]*?\*\//g, "");
  // 这两个在 2020~2021 年的内核上会让布局整个散架
  if (/(^|[\s;{])inset\s*:/.test(style)) throw new Error("样式里还有 inset（需要 Chrome 87+）");
  if (/aspect-ratio/.test(style)) throw new Error("样式里还有 aspect-ratio（需要 Chrome 88+）");
  // CSS 里的 min()/max()（Chrome 79+）—— JS 里的 Math.max 不算
  if (/[\s:(]max\(/.test(style)) throw new Error("样式里还有 max()（需要 Chrome 79+）");
  if (/[\s:(]min\(/.test(style)) throw new Error("样式里还有 min()（需要 Chrome 79+）");
  // flex 的 gap 要 Chrome 84+，只允许出现在 grid 容器里
  if (/display:\s*(inline-)?flex[^}]*gap\s*:/.test(style)) {
    throw new Error("flex 容器里还在用 gap（需要 Chrome 84+），应该改成外边距");
  }
  // inset 的老写法得在
  if (!style.includes("top: 0; right: 0; bottom: 0; left: 0")) {
    throw new Error("没找到 inset 的老写法替代");
  }
});

check("后台提醒：通道由原生建，必须检查权限", () => {
  // 通道不能交给通知插件建：它给不了自定义震动节奏，
  // 铃声也只能填 res/raw 文件名（填 "default" 会被当成真去找文件，找不到就静音）
  if (/sound:\s*"default"/.test(script)) throw new Error('还传着 sound: "default"，会让通道静音');
  if (!script.includes("function alarmPermissionGranted")) throw new Error("没有检查通知权限");
  if (!script.includes("prepareAlarm")) throw new Error("没让原生建通道（铃声和震动都靠它）");
  if (!script.includes('ALARM_CHANNEL = "focus-alarm-v2"')) {
    throw new Error("通道 id 不是 v2 —— 换过两次 v3，两次通知都不响了，别再动它");
  }
  if (!exists(SHELL_JAVA)) throw new Error("找不到原生插件 ShellPlugin.java");
});

check("铃声和震动要够长够响", () => {
  const java = readText(SHELL_JAVA);

  // 震动：拿自定义的长节奏，不是系统的默认两下
  if (!java.includes("setVibrationPattern")) throw new Error("原生那边没设置震动节奏");
  const pattern = java.match(/new long\[\]\{([^}]+)\}/);
  if (!pattern) throw new Error("震动模式是空的");
  const total = pattern[1].split(",")
    .map((part) => Number(part.trim()))
    .filter((n) => !Number.isNaN(n))
    .reduce((sum, n) => sum + n, 0);
  if (total < 4000) throw new Error(`震动总时长只有 ${total}ms，太短了`);

  // 铃声：用自己打包的文件，不是系统默认提示音
  if (!java.includes("pomodoro")) throw new Error("没有使用自定义铃声");
  if (!exists("android-app/android/app/src/main/res/raw/pomodoro.wav")) {
    throw new Error("铃声文件 pomodoro.wav 不存在（跑一下 tools/make_alarm_sound.py）");
  }
});

check("一段结束时不能取消原生闹钟（取消了通知就弹不出来）", () => {
  const start = script.indexOf("function completePhase");
  if (start === -1) throw new Error("找不到 completePhase");
  const rest = script.slice(start + 10);
  const next = rest.indexOf("\nfunction ");
  const body = next === -1 ? rest : rest.slice(0, next);
  if (body.includes("cancelAlarm()")) throw new Error("completePhase 里还在取消闹钟，系统通知会被掐掉");
  if (!body.includes("alarmArmed")) throw new Error("completePhase 没判断原生闹钟是否已排上，会响两遍");
  if (!script.includes("function alarmIdFor")) throw new Error("专注/休息没有用不同的通知 id");
});

check("任务能改名字、能删除（加错了不用干瞪眼）", () => {
  if (!script.includes("function openSheet")) throw new Error("缺少任务操作面板");
  if (!script.includes("function openRename")) throw new Error("缺少改名功能");
  if (!script.includes('classList.toggle("open"') && !script.includes('classList.add("open")')) {
    throw new Error("面板没有被打开的逻辑");
  }
  if (!html.includes('id="sheet-rename"')) throw new Error("面板里没有「改名字」");
  if (!html.includes('id="sheet-delete"')) throw new Error("面板里没有「删除」");
  // 删除任务时不能把历史专注记录一起删掉
  if (!script.includes("已经专注过的记录会留在总结里")) throw new Error("删除时没有说明历史记录会保留");
  // 改名要连带更新历史记录里的名字，否则统计里会出现两个名字
  if (!script.includes("item.task = name")) throw new Error("改名没有同步历史记录");
});

/* ---------- 2. 抽出纯逻辑 ---------- */

const start = html.indexOf("PURE-LOGIC-START");
const end = html.indexOf("PURE-LOGIC-END");
if (start === -1 || end === -1) throw new Error("缺少 PURE-LOGIC 标记");
const logic = html.slice(html.indexOf("*/", start) + 2, html.lastIndexOf("/*", end));

const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(logic, sandbox, { filename: "focus/index.html#pure-logic" });

const {
  formatClock, formatDuration, dayKey, lastNDays,
  phaseSeconds, nextPhase, byTask, byDay, daySeconds, dayCount,
  readBackup, buildBackup, filterByDay, taskSecondsOn, totalSeconds,
  rangeStart, filterByRange, firstDay,
  dayNumber, daysUntil, pickQuote, formatCnDate, countdownLabel, byDateThenId,
  barRows, roundsFor, readTaskPer,
} = sandbox;

// 注意：顶层 const 声明进的是「全局词法环境」，不是沙箱对象的属性，
// 所以不能写 sandbox.DEFAULT_SETTINGS，得再跑一次取出来。
const DEFAULT_SETTINGS = vm.runInContext("DEFAULT_SETTINGS", sandbox);
const CD_QUOTES = vm.runInContext("CD_QUOTES", sandbox);

check("纯逻辑函数都导出了", () => {
  for (const [name, fn] of Object.entries({
    formatClock, formatDuration, dayKey, lastNDays, phaseSeconds,
    nextPhase, byTask, byDay, daySeconds, dayCount, readBackup, buildBackup,
  })) {
    if (typeof fn !== "function") throw new Error(`${name} 不是函数`);
  }
  equal(DEFAULT_SETTINGS.focus, 25, "默认专注时长");
});

/* ---------- 2.5 倒计时（考研倒计时那种） ---------- */

check("倒计时：距目标日期算得对", () => {
  const noon = (y, m, d) => new Date(y, m - 1, d, 12).getTime();
  equal(daysUntil("2026-10-05", noon(2026, 10, 5)), 0, "就是今天");
  equal(daysUntil("2026-10-06", noon(2026, 10, 5)), 1, "明天");
  equal(daysUntil("2026-10-04", noon(2026, 10, 5)), -1, "昨天");
  equal(daysUntil("2026-10-05", new Date(2026, 9, 5, 23, 59).getTime()), 0, "当天最后一分钟");
  equal(daysUntil("2027-01-01", new Date(2026, 11, 31, 12).getTime()), 1, "跨年");
  equal(daysUntil("2026-12-20", noon(2026, 10, 5)), 76, "两个多月");
});

check("倒计时：文案池质量", () => {
  if (CD_QUOTES.length < 40) throw new Error(`自带文案只有 ${CD_QUOTES.length} 句，太少了`);
  if (new Set(CD_QUOTES).size !== CD_QUOTES.length) throw new Error("文案池里有重复的句子");
  for (const quote of CD_QUOTES) {
    if (typeof quote !== "string" || !quote.trim()) throw new Error("文案池里有空句子");
    if (quote.length > 20) throw new Error(`文案太长，会换行：「${quote}」`);
  }
});

check("倒计时：每天一句，不重样", () => {
  // 用本地时间中午做基准，避免时区/夏令时把日期算偏
  const base = new Date(2026, 0, 1, 12).getTime();
  const used = [];
  for (let i = 0; i < CD_QUOTES.length; i += 1) {
    used.push(pickQuote("", dayKey(base + i * 86400000)));
  }
  if (new Set(used).size !== CD_QUOTES.length) {
    throw new Error("连续几天出现了重复文案，轮换逻辑不对");
  }
  // 走完一整轮应该回到第一句 —— 说明它是按天循环的
  equal(pickQuote("", dayKey(base + CD_QUOTES.length * 86400000)), used[0], "一轮之后回到第一句");
  // 同一天必须稳定（刷新页面不能变）
  equal(pickQuote("", "2026-03-08"), pickQuote("", "2026-03-08"), "同一天要稳定");
});

check("倒计时：自己写了文案就用自己的", () => {
  equal(pickQuote("  我要上岸  ", "2026-03-08"), "我要上岸", "前后空格要去掉");
  equal(pickQuote("", "2026-03-08"), pickQuote(null, "2026-03-08"), "空值当作没写");
  equal(pickQuote("今天也要加油", "2026-03-08"), "今天也要加油");
});

check("倒计时：大数字上显示什么", () => {
  equal(countdownLabel(87).text, "87");
  equal(countdownLabel(87).unit, "天");
  equal(countdownLabel(87).small, false);
  equal(countdownLabel(0).text, "就是今天");
  equal(countdownLabel(-3).text, "已过去 3");
  equal(formatCnDate("2026-12-20"), "2026年12月20日");
  equal(formatCnDate("2026-01-05"), "2026年1月5日", "月份不补零");
  equal(formatCnDate("坏数据"), "");
});

check("倒计时：列表按日期从近到远排", () => {
  const list = [
    { id: "b", date: "2027-06-07", name: "高考" },
    { id: "a", date: "2026-12-20", name: "考研" },
    { id: "c", date: "2026-12-20", name: "四六级" },
  ];
  const sorted = list.slice().sort(byDateThenId).map((x) => x.name);
  // 同一天的按 id 排，保证顺序稳定（刷新页面不会跳来跳去）
  equal(sorted.join(","), "考研,四六级,高考", "近的在前，同一天顺序稳定");
});

check("倒计时：背景图必须先压缩再存", () => {
  // 手机照片 2~5MB，而本地存储总共才 5MB 左右 —— 不压缩存一张就爆
  if (!script.includes("CD_IMG_MAX")) throw new Error("没有设置图片尺寸上限");
  if (!script.includes('toDataURL("image/jpeg"')) throw new Error("没有把图片转成压缩过的 JPEG");
  if (!script.includes("focus.cd.img.")) {
    throw new Error("背景图应该单独存一个键，不能塞进主存档（否则每次保存都要写几百 KB）");
  }
  if (!script.includes("QuotaExceededError") && !script.includes("存不下了")) {
    throw new Error("本地存储写满时要有提示，不能默默失败");
  }
});

check("倒计时：底部是三个 tab", () => {
  const tabs = Array.from(html.matchAll(/data-screen="([a-z]+)"/g)).map((m) => m[1]);
  for (const name of ["tasks", "countdown", "stats"]) {
    if (!tabs.includes(name)) throw new Error(`缺少「${name}」这个 tab`);
  }
  if (tabs.length !== 3) throw new Error(`tab 有 ${tabs.length} 个，应该是 3 个`);
  const order = Array.from(html.matchAll(/data-screen="([a-z]+)"/g)).map((m) => m[1]).join(",");
  equal(order, "tasks,countdown,stats", "倒计时应该夹在中间");
});

check("倒计时：卡片底色必须是固定深色", () => {
  // 卡片上的字永远是白的。底色要是跟着主题走，浅色主题下就变成
  // "白字压浅底"，完全看不见 —— 这个 bug 真出现过。
  const card = html.match(/\.cd-card\s*\{[^}]*\}/);
  if (!card) throw new Error("找不到 .cd-card 的样式");
  const background = card[0].match(/background\s*:[^;]*;/);
  if (!background) throw new Error(".cd-card 没有设置底色");
  if (/var\(--/.test(background[0])) {
    throw new Error(".cd-card 的底色用了主题变量 —— 浅色主题下白字会看不见");
  }
});

check("总结：条形图的长度算得对", () => {
  const rows = barRows([
    { name: "背单词", seconds: 3600 },
    { name: "写周报", seconds: 1800 },
    { name: "看书", seconds: 600 },
  ], 6000, 400);
  equal(rows.length, 3, "几行");
  equal(rows[0].width, 240, "占一半就是一半长");
  equal(rows[1].width, 120, "占三成");
  equal(rows[2].width, 40, "占一成");
  equal(rows[0].name, "背单词", "名字要留着");
  equal(Math.round(rows[1].share * 100), 30, "百分比");
  equal(barRows([], 100, 400).length, 0, "没有数据就是空数组");
  equal(barRows([{ name: "空的", seconds: 0 }], 0, 400)[0].width, 0, "总和为 0 不该算出 NaN");
});

check("总结：扇形 / 条形可以切换，且能记住", () => {
  if (!html.includes('data-chart="pie"') || !html.includes('data-chart="bar"')) {
    throw new Error("没有扇形 / 条形的切换按钮");
  }
  if (!script.includes("drawBars")) throw new Error("没有画条形图的代码");
  equal(DEFAULT_SETTINGS.chart, "pie", "默认是扇形图");
  equal(readBackup({ version: 1, settings: { chart: "bar" } }).settings.chart, "bar", "选过条形要记住");
  equal(readBackup({ version: 1, settings: { chart: "折线图" } }).settings.chart, "pie", "值不对就回到默认");
});

check("主题：深浅两套必须定义同一批变量", () => {
  // 少定义一个变量，浅色主题下那块就会"继承"深色的值，出现莫名其妙的黑块
  const grab = (pattern, name) => {
    const m = html.match(pattern);
    if (!m) throw new Error(`找不到${name}主题的变量定义`);
    return new Set(Array.from(m[1].matchAll(/(--[a-z0-9-]+)\s*:/g)).map((x) => x[1]));
  };
  const dark = grab(/:root\s*\{([^}]*)\}/, "深色");
  const light = grab(/\[data-theme="light"\]\s*\{([^}]*)\}/, "浅色");
  // 这两个是布局常量（圆角半径、底栏高度），本来就不分主题，共用是对的
  const shared = new Set(["--radius", "--tabbar"]);
  const missing = Array.from(dark).filter((name) => !light.has(name) && !shared.has(name));
  if (missing.length) throw new Error(`浅色主题缺了：${missing.join("、")}`);

  // 实心按钮上的白字要有足够对比度：主色可以亮，按钮底色得深一点
  if (!dark.has("--focus-solid")) throw new Error("深色主题缺少 --focus-solid（实心按钮专用色）");
  equal(DEFAULT_SETTINGS.theme, "light", "默认主题应该是浅色");
});

check("背景图：卡片必须变半透明，否则等于没设", () => {
  // 卡片要还是不透明，图只能在卡片之间的缝里露一点点，用户会以为没生效
  if (!/\[data-bg="on"\]/.test(html)) throw new Error("缺少 data-bg 的样式开关");
  const block = html.match(/\[data-bg="on"\]\s*\{([^}]*)\}/);
  if (!block) throw new Error("找不到 [data-bg=on] 的样式");
  if (!/--surface:\s*rgba/.test(block[1])) throw new Error("卡片底色没有变半透明");
  if (!/--bg-veil:/.test(block[1])) throw new Error("没有压暗层，亮照片上文字会看不清");
  // 浅色主题下也要有一套
  const lightBlock = html.match(/\[data-theme="light"\]\[data-bg="on"\]\s*\{([^}]*)\}/);
  if (!lightBlock || !/--surface:\s*rgba/.test(lightBlock[1])) {
    throw new Error("浅色主题下没有对应处理");
  }
  if (!script.includes("focus.bg.image")) throw new Error("背景图没有单独存一个键");
  if (!script.includes("applyAppBg")) throw new Error("没有把背景图状态同步到界面");
});

check("备份：导出的东西必须能原样导回来", () => {
  // 这是备份功能的命根子 —— 导得出、导不回，等于白做
  const before = {
    version: 1,
    settings: Object.assign({}, DEFAULT_SETTINGS, { focus: 30, chart: "bar", theme: "dark" }),
    tasks: [{ id: "t1", name: "写周报", done: true, pomodoros: 3, createdAt: 1728000000000, day: "2026-10-05" }],
    sessions: [{ id: "s1", task: "写周报", start: 1728000000000, seconds: 1500 }],
    countdowns: [{ id: "cd1", name: "考研上岸", date: "2026-12-20", quote: "今天也要加油" }],
  };
  const after = readBackup(JSON.parse(buildBackup(before)));
  equal(after.settings.focus, 30, "专注时长");
  equal(after.settings.chart, "bar", "图表选择");
  equal(after.settings.theme, "dark", "主题");
  equal(after.tasks.length, 1, "任务条数");
  equal(after.tasks[0].name, "写周报", "任务名");
  equal(after.tasks[0].pomodoros, 3, "番茄数");
  equal(after.tasks[0].day, "2026-10-05", "任务归属哪一天");
  equal(after.sessions.length, 1, "记录条数");
  equal(after.sessions[0].seconds, 1500, "记录时长");
  equal(after.countdowns.length, 1, "倒计时条数");
  equal(after.countdowns[0].name, "考研上岸", "倒计时名字");
  equal(after.countdowns[0].date, "2026-12-20", "倒计时日期");
  equal(after.countdowns[0].quote, "今天也要加油", "倒计时文案");
});

check("备份：导出和导入用的是同一套格式和校验", () => {
  // 用同一个 buildBackup / readBackup，才不会出现"导出的东西自己导不回来"
  if (!script.includes("buildBackup(state)")) throw new Error("导出没有用本地存档格式");
  if (!script.includes("readBackup(JSON.parse(text))")) throw new Error("导入没有走校验");
  if (!script.includes("focus.bg.image")) throw new Error("背景图相关代码不见了");
  // 背景图不在备份里，导出时必须说明，不然用户会以为丢了
  if (!script.includes("背景图不在里面")) throw new Error("导出时没有提示背景图不含在内");
  // 覆盖数据要有二次确认
  if (!script.includes("再点一次恢复")) throw new Error("导入没有二次确认");
});

check("安卓：系统备份要带上 WebView 数据，并排除缓存", () => {
  const manifest = readText("android-app/android/app/src/main/AndroidManifest.xml");
  if (!/android:allowBackup="true"/.test(manifest)) throw new Error("没有开启系统备份");
  if (!manifest.includes("backup_rules")) throw new Error("没有指定备份规则");
  if (!manifest.includes("data_extraction_rules")) throw new Error("没有指定 Android 12+ 的备份规则");

  for (const rel of [
    "android-app/android/app/src/main/res/xml/backup_rules.xml",
    "android-app/android/app/src/main/res/xml/data_extraction_rules.xml",
  ]) {
    if (!exists(rel)) throw new Error(`找不到 ${rel}`);
    const rules = readText(rel);
    // 数据全在 WebView 的 localStorage 里，不带上这个目录等于没备份
    if (!rules.includes("app_webview")) throw new Error(`${rel} 没带上 WebView 数据`);
    // 备份有 25MB 配额，超了会静默失败、整份不备 —— 缓存必须排掉
    if (!rules.includes("Cache")) throw new Error(`${rel} 没有排除缓存，可能撑爆配额`);
  }
});

check("弹窗：从设置里打开的备份弹窗要能盖在设置上面", () => {
  // 同级弹窗谁在上由 DOM 顺序决定。之前就因为这个，
  // 导出备份弹窗被设置弹窗盖住了，得先关掉设置才看得见。
  if (!script.includes("function showModal")) throw new Error("缺少 showModal 辅助函数");
  if (!script.includes("document.body.appendChild(el)")) {
    throw new Error("打开弹窗时没有挪到 body 末尾，会被已打开的弹窗盖住");
  }
  if (!/showModal\(\$\("modal-export"\)\)/.test(script)) throw new Error("导出弹窗没用 showModal");
  if (!/showModal\(\$\("modal-import"\)\)/.test(script)) throw new Error("导入弹窗没用 showModal");
});

check("通知图标：矢量的那个先别用（它让通知不弹了）", () => {
  // v2.6 给通知指定了一个"矢量小图标"，结果通知干脆不弹了 —— 已退回用 App 图标。
  // 图标文件留着，以后换成 PNG 再启用。
  const config = readText("android-app/capacitor.config.json");
  if (config.includes("smallIcon")) {
    throw new Error("插件配置里又指定了通知小图标 —— 上次就是它让通知不弹的");
  }
  if (config.includes("iconColor")) {
    throw new Error("插件配置里又指定了通知图标颜色，一起退回去了");
  }
  if (!exists("android-app/android/app/src/main/res/drawable/ic_stat_timer.xml")) {
    throw new Error("单色图标文件丢了 —— 以后换成 PNG 还要用");
  }
});

check("计时：退出再点开不能重新计时", () => {
  // 之前 enterTimer 无条件 setPhase("focus")，于是"退出去再点开就重头开始"。
  // 这个 bug 只有真机上手点才发现，所以静态钉一下。
  const fn = script.match(/function enterTimer\(task\)\s*\{[\s\S]*?\n\}/);
  if (!fn) throw new Error("找不到 enterTimer");
  if (!fn[0].includes("sameTask")) {
    throw new Error("enterTimer 又是无条件重置了 —— 退出再点开会重新计时");
  }
  // 只有"同一个任务 + 计时正在跑"才接着用。
  // 条件写成 !sameTask 就太宽了 —— 上一轮结束后再点进来还停在旧状态，按开始也不动。
  if (!/if\s*\(!sameTask\s*\|\|\s*!timer\.running\)/.test(fn[0])) {
    throw new Error("重置条件不对 —— 必须是「换了任务 或者 计时没在跑」才重置");
  }
  if (!script.includes("visibilitychange")) {
    throw new Error("回到前台没有主动刷新 —— 画面会停在离开时那一秒");
  }
  // 到点之后就按设置走（自动开始下一段）。之前加过"后台到点就不自动开始"，
  // 那是自作聪明 —— 正常番茄钟就该自己接着走。
  if (/autoNext && !wasHidden/.test(script)) {
    throw new Error("又加回「后台到点不自动开始」了 —— 用户要的是正常流程");
  }
});

check("提醒：通道必须建成功，失败要说出来", () => {
  // 通知发到一个不存在的通道，系统会【静默丢掉】—— 用户什么都看不到，
  // 而且完全查不出原因。所以：Java 那边要兜底 + 返回结果，网页这边要看住。
  const java = readText(SHELL_JAVA);
  if (!java.includes('out.put("ok"')) throw new Error("原生那边没有把'通道建成功没'返回给网页");
  if (!/if \(manager\.getNotificationChannel\(ALARM_CHANNEL_ID\) == null\) \{\s*try \{\s*NotificationChannel fallback/.test(java)) {
    throw new Error("缺少兜底通道 —— 设置自定义铃声失败时，通道就建不出来了");
  }
  if (!script.includes("res.ok === false")) throw new Error("网页没有检查通道是否建成功");
  if (!script.includes("闹钟没排上")) throw new Error("排闹钟失败时要提示用户，不能默默吞掉");
});

check("提醒：必须争取「精确闹钟」和「允许后台耗电」", () => {
  // 没精确闹钟授权 → 系统给的是【不精确】闹钟，可以随意推迟、合并 ——
  // 表现就是"手机醒着能响、一忙或一熄屏就不响"。
  if (!script.includes("checkExactNotificationSetting")) {
    throw new Error("没有检查「精确闹钟」授权状态");
  }
  // 安卓 12 起「闹钟和提醒」要单独授权
  if (!script.includes("changeExactNotificationSetting")) {
    throw new Error("没授权时没有引导用户去开");
  }
  // 小米这类系统不开"允许后台耗电"，App 被清掉后系统就不再叫醒它了
  if (!script.includes("requestBackgroundPower")) {
    throw new Error("没有请求「允许后台耗电」—— 小米这类系统不开它，后台到点就是不响");
  }
  const java = readText(SHELL_JAVA);
  if (!java.includes("ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS")) {
    throw new Error("原生那边没有弹系统的电池优化对话框，用户还得自己翻设置");
  }
  const manifest = readText("android-app/android/app/src/main/AndroidManifest.xml");
  if (!manifest.includes("REQUEST_IGNORE_BATTERY_OPTIMIZATIONS")) {
    throw new Error("清单里缺少 REQUEST_IGNORE_BATTERY_OPTIMIZATIONS 权限");
  }
  // 两个系统页面同时弹会互相顶掉，必须一次只弹一个
  if (!/if \(res && res\.opened\) \{[\s\S]{0,160}?return;/.test(script)) {
    throw new Error("两个系统授权页面没有排好顺序 —— 同时弹会互相顶掉");
  }
  if (!script.includes("batteryChecked") || !script.includes("exactAlarmChecked")) {
    throw new Error("没有防重复 —— 每次进计时页都弹系统页面会很烦");
  }
});

/* ---------- 3. 倒计时显示 ---------- */
check("倒计时格式", () => {
  equal(formatClock(1500), "25:00");
  equal(formatClock(299), "04:59");
  equal(formatClock(59), "00:59");
  equal(formatClock(0), "00:00");
  equal(formatClock(-5), "00:00", "负数要归零，不能显示负号");
});

check("时长的人话说法", () => {
  equal(formatDuration(0), "不到 1 分钟");
  equal(formatDuration(59), "不到 1 分钟");
  equal(formatDuration(60), "1 分钟");
  equal(formatDuration(1500), "25 分钟");
  equal(formatDuration(3600), "1 小时");
  equal(formatDuration(5400), "1 小时 30 分");
});

/* ---------- 4. 阶段与轮次 ---------- */

const settings = { focus: 25, short: 5, long: 15, rounds: 4 };

check("每个阶段多长", () => {
  equal(phaseSeconds("focus", settings), 1500);
  equal(phaseSeconds("short", settings), 300);
  equal(phaseSeconds("long", settings), 900);
});

check("下一阶段怎么走", () => {
  equal(nextPhase("focus", 1, 4), "short");
  equal(nextPhase("focus", 3, 4), "short");
  equal(nextPhase("focus", 4, 4), "long", "第 4 轮后要长休息");
  equal(nextPhase("short", 1, 4), "focus");
  equal(nextPhase("long", 4, 4), "focus");
  equal(nextPhase("focus", 6, 3), "long", "任务设成 3 轮也要生效");
});

check("每个任务可以有自己的时长", () => {
  const settings = Object.assign({}, DEFAULT_SETTINGS);
  const task = { per: { focus: 45, short: 8, long: 20, rounds: 3 } };

  // 设过就用任务的
  equal(phaseSeconds("focus", settings, task), 45 * 60, "任务的专注时长");
  equal(phaseSeconds("short", settings, task), 8 * 60, "任务的短休息");
  equal(phaseSeconds("long", settings, task), 20 * 60, "任务的长休息");
  equal(roundsFor(settings, task), 3, "任务的轮数");

  // 没设过（老任务）就用全局的 —— 老数据必须不受影响
  equal(phaseSeconds("focus", settings), 25 * 60, "没任务用全局");
  equal(phaseSeconds("focus", settings, {}), 25 * 60, "任务没有 per 就用全局");
  equal(phaseSeconds("focus", settings, { per: {} }), 25 * 60, "per 是空的也用全局");
  equal(roundsFor(settings, null), 4, "没任务用全局轮数");

  // 只设了一半，另一半也要能回落到全局
  const half = { per: { focus: 50 } };
  equal(phaseSeconds("focus", settings, half), 50 * 60, "设了的用任务的");
  equal(phaseSeconds("short", settings, half), 5 * 60, "没设的用全局");

  // 乱填的（0、负数、超大、文字）都要被挡掉，回到全局
  equal(phaseSeconds("focus", settings, { per: { focus: 0 } }), 25 * 60, "0 不算");
  equal(phaseSeconds("focus", settings, { per: { focus: -5 } }), 25 * 60, "负数不算");
  equal(phaseSeconds("focus", settings, { per: { focus: "abc" } }), 25 * 60, "文字不算");
});

check("任务时长：入库时会被清洗", () => {
  equal(readTaskPer(null), null, "没有就是 null");
  equal(readTaskPer({}), null, "空的也算没有");
  equal(readTaskPer({ focus: 0, short: -1 }), null, "全是废值就当没有");
  equal(readTaskPer({ focus: 45 }).focus, 45);
  equal(readTaskPer({ focus: 45, short: 0 }).short, undefined, "废值丢掉");
  equal(readTaskPer({ focus: 999 }).focus, 180, "超过上限要压回来");
  equal(readTaskPer({ focus: 45.6 }).focus, 46, "小数四舍五入");
});

check("任务时长：存在任务里，而且能跟着备份走", () => {
  const backup = {
    version: 1,
    tasks: [{ id: "t1", name: "背单词", day: "2026-10-05", createdAt: 1791000000000, per: { focus: 15, rounds: 2 } }],
  };
  const restored = readBackup(backup);
  equal(restored.tasks[0].per.focus, 15, "专注时长存下来了");
  equal(restored.tasks[0].per.rounds, 2, "轮数存下来了");
  // 没设时长的任务，不该被塞一个空的 per 进去
  const plain = readBackup({ version: 1, tasks: [{ id: "t2", name: "写周报", day: "2026-10-05" }] });
  equal(plain.tasks[0].per, undefined, "没设过就不该有 per 字段");
});

/* ---------- 5. 日期与统计 ---------- */

const day = (y, m, d, h) => new Date(y, m - 1, d, h || 12, 0, 0).getTime();

check("日期归属", () => {
  equal(dayKey(day(2026, 10, 3)), "2026-10-03");
  equal(dayKey(day(2026, 1, 9)), "2026-01-09", "月日要补零");
});

check("最近 7 天包含当天且在最后", () => {
  const days = lastNDays(7, day(2026, 10, 3));
  equal(days.length, 7);
  equal(days[6], "2026-10-03");
  equal(days[0], "2026-09-27");
});

const sessions = [
  { id: "s1", task: "写周报", start: day(2026, 10, 3, 9), seconds: 1500 },
  { id: "s2", task: "写周报", start: day(2026, 10, 3, 10), seconds: 1500 },
  { id: "s3", task: "看论文", start: day(2026, 10, 3, 14), seconds: 900 },
  { id: "s4", task: "看论文", start: day(2026, 10, 2, 15), seconds: 1200 },
  { id: "s5", task: "写周报", start: day(2026, 9, 30, 9), seconds: 600 },
];

check("按任务汇总", () => {
  const rows = byTask(sessions);
  equal(rows[0], { name: "写周报", seconds: 3600 });
  equal(rows[1], { name: "看论文", seconds: 2100 });
});

check("按天汇总", () => {
  const map = byDay(sessions);
  equal(map.get("2026-10-03"), 3900);
  equal(map.get("2026-10-02"), 1200);
});

check("某天的时长与番茄数", () => {
  equal(daySeconds(sessions, "2026-10-03"), 3900);
  equal(dayCount(sessions, "2026-10-03"), 3);
  equal(daySeconds(sessions, "2026-01-01"), 0, "没记录的日期是 0");
});

check("跨天不会串味", () => {
  equal(daySeconds(sessions, "2026-09-30"), 600);
  const map = byDay(sessions);
  equal(map.size, 3, "一共跨了 3 天");
});

/* ---------- 5b. 按日期看总结 ---------- */

check("按日期筛选记录", () => {
  const rows = [
    { id: "a", task: "甲", start: day(2026, 10, 3, 9), seconds: 600 },
    { id: "b", task: "甲", start: day(2026, 10, 2, 9), seconds: 600 },
    { id: "c", task: "乙", start: day(2026, 10, 3, 22), seconds: 600 },
    { id: "d", task: "乙", start: day(2026, 9, 30, 9), seconds: 600 },
  ];
  equal(filterByDay(rows, "2026-10-03").length, 2);
  equal(filterByDay(rows, "2026-10-02").length, 1);
  equal(filterByDay(rows, "2026-10-04").length, 0, "没记录的日期应该是空的");
});

check("选某一天时，别把别的日子算进来", () => {
  const rows = [
    { id: "a", task: "写周报", start: day(2026, 10, 3, 9), seconds: 1500 },
    { id: "b", task: "看论文", start: day(2026, 10, 3, 10), seconds: 900 },
    { id: "c", task: "写周报", start: day(2026, 10, 3, 14), seconds: 600 },
    { id: "d", task: "写周报", start: day(2026, 10, 2, 9), seconds: 9999 },
  ];
  const parts = byTask(filterByDay(rows, "2026-10-03"));
  equal(parts[0], { name: "写周报", seconds: 2100 }, "昨天的 9999 秒不能算进来");
  equal(parts[1], { name: "看论文", seconds: 900 });
});

check("总和 = 扇形图各块加起来", () => {
  const rows = [
    { id: "a", task: "甲", start: day(2026, 10, 3, 9), seconds: 1500 },
    { id: "b", task: "乙", start: day(2026, 10, 3, 10), seconds: 900 },
    { id: "c", task: "甲", start: day(2026, 10, 3, 14), seconds: 600 },
    { id: "d", task: "丙", start: day(2026, 10, 2, 14), seconds: 7777 },
  ];
  const picked = filterByDay(rows, "2026-10-03");
  const total = totalSeconds(picked);
  equal(total, 3000);
  const parts = byTask(picked);
  equal(parts.reduce((sum, p) => sum + p.seconds, 0), total, "各块之和要等于总数");
});

check("某天某任务的专注时长", () => {
  const rows = [
    { id: "a", task: "写周报", start: day(2026, 10, 3, 9), seconds: 1500 },
    { id: "b", task: "写周报", start: day(2026, 10, 2, 9), seconds: 600 },
    { id: "c", task: "看论文", start: day(2026, 10, 3, 10), seconds: 900 },
  ];
  equal(taskSecondsOn(rows, "写周报", "2026-10-03"), 1500, "不能把昨天的算进来");
  equal(taskSecondsOn(rows, "看论文", "2026-10-03"), 900);
  equal(taskSecondsOn(rows, "不存在", "2026-10-03"), 0);
});

/* ---------- 5c. 本周 / 全部的总专注 ---------- */

check("本周从周一零点开始", () => {
  const now = day(2026, 10, 3, 15);          // 2026-10-03 是周六
  equal(dayKey(rangeStart("today", now)), "2026-10-03");
  equal(dayKey(rangeStart("week", now)), "2026-09-28", "要退到本周一");
  equal(rangeStart("all", now), 0, "全部就从 0 开始");
});

check("本周总专注只算这周", () => {
  const now = day(2026, 10, 3, 15);
  const rows = [
    { id: "a", task: "甲", start: day(2026, 10, 3, 9), seconds: 1500 },   // 周六，算
    { id: "b", task: "甲", start: day(2026, 9, 28, 9), seconds: 600 },    // 周一，算
    { id: "c", task: "乙", start: day(2026, 9, 27, 9), seconds: 9999 },   // 上周日，不算
    { id: "d", task: "乙", start: day(2026, 10, 2, 9), seconds: 300 },    // 周五，算
  ];
  equal(totalSeconds(filterByRange(rows, "week", now)), 2400, "上周日那 9999 秒不能算进来");
  equal(totalSeconds(filterByRange(rows, "all", now)), 12399);
});

check("全部总专注 = 所有记录之和", () => {
  equal(totalSeconds(sessions), 5700);
});

check("最早的一天", () => {
  equal(firstDay(sessions), "2026-09-30");
  equal(firstDay([]), "", "没有记录时是空字符串");
  const rows = [
    { id: "a", task: "甲", start: day(2026, 10, 3, 9), seconds: 60 },
    { id: "b", task: "甲", start: day(2026, 9, 1, 9), seconds: 60 },
    { id: "c", task: "甲", start: day(2026, 10, 1, 9), seconds: 60 },
  ];
  equal(firstDay(rows), "2026-09-01");
});

/* ---------- 6. 存档文件读写 ---------- */

const state = {
  version: 1,
  settings: { focus: 50, short: 10, long: 20, rounds: 2, autoNext: false, sound: false, notify: true },
  tasks: [{ id: "t1", name: "写周报", done: true, pomodoros: 3, createdAt: day(2026, 10, 3), day: "2026-10-03" }],
  sessions: sessions,
};

check("导出再导入，内容不变", () => {
  const back = readBackup(JSON.parse(buildBackup(state)));
  equal(back.settings.focus, 50);
  equal(back.settings.autoNext, false);
  equal(back.tasks, state.tasks);
  equal(back.sessions, state.sessions);
});

check("缺设置时用默认值补齐", () => {
  const back = readBackup({ version: 1, tasks: [], sessions: [] });
  equal(back.settings, DEFAULT_SETTINGS);
});

check("任务归属的日期：没有 day 字段就按创建时间算", () => {
  const back = readBackup({
    version: 1,
    tasks: [{ id: "t1", name: "写周报", createdAt: day(2026, 10, 1, 9) }],
    sessions: [],
  });
  equal(back.tasks[0].day, "2026-10-01", "老数据要能自动补上日期");
});

check("任务归属的日期：有 day 字段就听它的", () => {
  const back = readBackup({
    version: 1,
    tasks: [{ id: "t1", name: "写周报", createdAt: day(2026, 10, 1, 9), day: "2026-09-20" }],
    sessions: [],
  });
  equal(back.tasks[0].day, "2026-09-20");
});

check("坏数据给出中文提示", () => {
  throws(() => readBackup(null), "数据文件");
  throws(() => readBackup([1, 2]), "数据文件");
  throws(() => readBackup({ version: 9 }), "版本");
  throws(() => readBackup({ version: 1, settings: { focus: 0 } }), "设置");
  throws(() => readBackup({ version: 1, settings: { focus: "abc" } }), "设置");
  throws(() => readBackup({ version: 1, tasks: ["坏"] }), "任务");
  throws(() => readBackup({ version: 1, sessions: [{ seconds: 0, start: 1 }] }), "时长");
  throws(() => readBackup({ version: 1, sessions: [{ seconds: 60, start: 0 }] }), "时间");
});

check("导出文件带版本号，方便以后升级", () => {
  equal(JSON.parse(buildBackup(state)).version, 1);
  equal(typeof JSON.parse(buildBackup(state)).savedAt, "string");
});

/* ---------- 汇总 ---------- */

if (failures.length) {
  console.error(`✗ ${failures.length} 项没通过，${passed} 项通过\n`);
  for (const line of failures) console.error("  - " + line);
  process.exit(1);
}
console.log(`✓ 番茄钟逻辑全部通过（${passed} 项）`);
