/**
 * 从 App 源码生成公开的网页版。
 *
 * 为什么要生成而不是手抄一份：
 *   App 版里有打赏入口（内嵌了作者收款码），公开的网页版不该有。
 *   如果维护两份文件，改一处忘一处，早晚会不一致。
 *   所以这里只认 focus/index.html 这一个源，把 TIP-START ~ TIP-END
 *   之间的内容删掉，输出到 docs/index.html（GitHub Pages 直接从 docs 发布）。
 *
 * 用法：
 *     node tools/make_web_version.mjs
 */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const SRC = join(ROOT, "focus", "index.html");
const OUT_DIR = join(ROOT, "docs");
const OUT = join(OUT_DIR, "index.html");

const BANNER = `<!--
  这个文件是自动生成的，请不要直接改它。
  改 focus/index.html，然后运行：node tools/make_web_version.mjs
-->
`;

let html = readFileSync(SRC, "utf8");
const sizeBefore = Buffer.byteLength(html, "utf8");

// 三种注释形式：HTML 用 <!-- -->，CSS 和 JS 用 /* */
const blocks = [
  { name: "HTML 块", re: /<!--\s*TIP-START[\s\S]*?TIP-END\s*-->/g },
  { name: "CSS / JS 块", re: /\/\*\s*TIP-START[\s\S]*?TIP-END\s*\*\//g },
];

let removed = 0;
for (const block of blocks) {
  html = html.replace(block.re, () => {
    removed++;
    return "";
  });
}

if (removed === 0) {
  console.error("✗ 一个 TIP 块都没找到 —— focus/index.html 里的标记是不是被删了？");
  process.exit(1);
}

// ---- 出厂检查：任何跟打赏有关的东西都不许留在公开版里 ----
const leftovers = [
  ["打赏入口按钮", /id="tip-open"/],
  ["打赏弹窗", /id="modal-tip"/],
  ["收款码图片", /id="tip-qr"/],
  ["打赏样式", /\.tip-card/],
  ["打赏按钮样式", /\.tip-btn/],
  ["打赏脚本", /\$\("tip-open"\)/],
];
for (const [name, re] of leftovers) {
  if (re.test(html)) {
    console.error(`✗ 公开版里还残留着「${name}」`);
    process.exit(1);
  }
}

// 收款码是 63 KB 的 base64，App 图标约 18 KB —— 超过 30 KB 的一律当成可疑图片
const fatImages = [...html.matchAll(/data:image\/png;base64,([A-Za-z0-9+/=]+)/g)]
  .filter((m) => m[1].length > 30000);
if (fatImages.length > 0) {
  console.error(`✗ 发现 ${fatImages.length} 张体积过大的内嵌图片（很可能是收款码）`);
  process.exit(1);
}

if (!html.includes("<!DOCTYPE html>")) {
  console.error("✗ 生成结果不像一个 HTML 文件");
  process.exit(1);
}

html = html.replace("<!DOCTYPE html>", `<!DOCTYPE html>\n${BANNER}`);

mkdirSync(OUT_DIR, { recursive: true });
writeFileSync(OUT, html, "utf8");

const sizeAfter = Buffer.byteLength(html, "utf8");
console.log(`✓ 删掉 ${removed} 段打赏相关内容`);
console.log(`✓ 生成 docs/index.html`);
console.log(`  ${(sizeBefore / 1024).toFixed(1)} KB  →  ${(sizeAfter / 1024).toFixed(1)} KB` +
            `（少了 ${((sizeBefore - sizeAfter) / 1024).toFixed(1)} KB）`);
console.log(`✓ 出厂检查通过：没有收款码、没有打赏入口`);
