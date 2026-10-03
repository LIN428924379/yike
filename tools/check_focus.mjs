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

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import vm from "node:vm";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const html = readFileSync(join(root, "focus", "index.html"), "utf8");

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

check("界面里不该再出现「导出 / 导入」（这两个功能已经删掉）", () => {
  for (const word of ["导出", "导入", "file-input", 'id="export"', 'id="import"']) {
    if (html.includes(word)) throw new Error("还残留着：" + word);
  }
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

check("到点震动 + 默认跟随系统", () => {
  if (!script.includes("function vibrate")) throw new Error("缺少震动功能");
  if (!script.includes("navigator.vibrate")) throw new Error("没有调用系统震动");
  if (!script.includes("vibrate(finished")) throw new Error("一段结束时没有触发震动");
  if (!script.includes('theme: "auto"')) throw new Error("默认主题不是跟随系统");
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

check("后台提醒：通道不能传 sound，必须有权限检查", () => {
  // "default" 会被插件当成 res/raw/default 去找音频文件，找不到就变成静音通道
  if (/sound:\s*"default"/.test(script)) throw new Error('还传着 sound: "default"，会让通道静音');
  if (!script.includes("deleteChannel")) throw new Error("没有重建通道，旧的静音通道改不掉");
  if (!script.includes("function alarmPermissionGranted")) throw new Error("没有检查通知权限");
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
} = sandbox;

// 注意：顶层 const 声明进的是「全局词法环境」，不是沙箱对象的属性，
// 所以不能写 sandbox.DEFAULT_SETTINGS，得再跑一次取出来。
const DEFAULT_SETTINGS = vm.runInContext("DEFAULT_SETTINGS", sandbox);

check("纯逻辑函数都导出了", () => {
  for (const [name, fn] of Object.entries({
    formatClock, formatDuration, dayKey, lastNDays, phaseSeconds,
    nextPhase, byTask, byDay, daySeconds, dayCount, readBackup, buildBackup,
  })) {
    if (typeof fn !== "function") throw new Error(`${name} 不是函数`);
  }
  equal(DEFAULT_SETTINGS.focus, 25, "默认专注时长");
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
  equal(nextPhase("focus", 1, settings), "short");
  equal(nextPhase("focus", 3, settings), "short");
  equal(nextPhase("focus", 4, settings), "long", "第 4 轮后要长休息");
  equal(nextPhase("short", 1, settings), "focus");
  equal(nextPhase("long", 4, settings), "focus");
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
