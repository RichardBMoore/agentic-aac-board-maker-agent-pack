import { expect, test } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

// SCORM packages run inside an LMS player's frames, not from file:///.
// These tests build the packages fresh and mimic how Canvas/QLearn shows an
// imported SCORM page: the course page (one origin) frames the SCORM tool's
// player (another origin), which holds the SCORM 1.2 API and nests the content
// two frames down. They check the unchanged board still works, the bridge only
// opens/closes a session, and nothing is fetched from outside the package.

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const python = process.env.PYTHON || (existsSync(path.join(root, ".venv/bin/python")) ? path.join(root, ".venv/bin/python") : "python3");
const builder = path.join(root, "skills/qlearn-accessibility/scripts/build_scorm.py");
const board = path.join(root, "generated/gaze-choice-2x2/gaze-choice-class-activity.html");
const LMS = "https://lms.test";
const COURSE = "https://course.test";

// Roughly the content area a Canvas page leaves an embedded tool on a 1280-wide
// screen once the global and course navigation are showing.
const EMBED = { width: 960, height: 600 };

const packages = {};
test.beforeAll(() => {
  const workDir = mkdtempSync(path.join(os.tmpdir(), "aac-scorm-"));
  // A two-page activity (menu + activity) for the multi-page session test.
  const multiSource = path.join(workDir, "multi-source");
  const page = (title, other) => `<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${title}</title></head>` +
    `<body><h1>${title}</h1><a id="go" href="${other}">Next page</a></body></html>`;
  mkdirSync(path.join(multiSource, "sub"), { recursive: true });
  writeFileSync(path.join(multiSource, "index.html"), page("Menu", "sub/two.html"));
  writeFileSync(path.join(multiSource, "sub", "two.html"), page("Activity", "../index.html"));
  execFileSync(python, [builder, path.join(multiSource, "index.html"), path.join(workDir, "multi.zip"), "--page", "sub/two.html"], { stdio: "pipe" });
  execFileSync(python, ["-m", "zipfile", "-e", path.join(workDir, "multi.zip"), path.join(workDir, "multi")], { stdio: "pipe" });
  packages.multi = path.join(workDir, "multi");
  execFileSync(python, [builder, path.join(multiSource, "index.html"), path.join(workDir, "multi-toggle.zip"), "--page", "sub/two.html", "--fullscreen-toggle", "bottom-right"], { stdio: "pipe" });
  execFileSync(python, ["-m", "zipfile", "-e", path.join(workDir, "multi-toggle.zip"), path.join(workDir, "multi-toggle")], { stdio: "pipe" });
  packages.multiToggle = path.join(workDir, "multi-toggle");
  execFileSync(python, [builder, board, path.join(workDir, "split-toggle.zip"), "--layout", "split", "--fullscreen-toggle"], { stdio: "pipe" });
  execFileSync(python, ["-m", "zipfile", "-e", path.join(workDir, "split-toggle.zip"), path.join(workDir, "split-toggle")], { stdio: "pipe" });
  packages.splitToggle = path.join(workDir, "split-toggle");
  // An activity whose dwell/switch engine guards every click on the document (capture phase),
  // swallowing clicks on any button that is not one of its own.
  const guardSource = path.join(workDir, "guard-source");
  mkdirSync(guardSource, { recursive: true });
  writeFileSync(path.join(guardSource, "index.html"), `<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Guarded</title></head>` +
    `<body><h1>Guarded</h1><button id="own" type="button">Own button</button><script>window.__seen = [];` +
    `document.addEventListener("click", (e) => { const b = e.target.closest ? e.target.closest("button") : null; window.__seen.push(b ? (b.id || "other") : "none");` +
    ` if (b && b.id !== "own") { e.preventDefault(); e.stopImmediatePropagation(); } }, true);` +
    `document.addEventListener("keyup", (e) => { if (e.key === " " || e.key === "Enter") { e.preventDefault(); e.stopImmediatePropagation(); } }, true);</script></body></html>`);
  execFileSync(python, [builder, path.join(guardSource, "index.html"), path.join(workDir, "guarded.zip"), "--fullscreen-toggle", "middle-right"], { stdio: "pipe" });
  execFileSync(python, ["-m", "zipfile", "-e", path.join(workDir, "guarded.zip"), path.join(workDir, "guarded")], { stdio: "pipe" });
  packages.guarded = path.join(workDir, "guarded");
  for (const layout of ["inline", "split"]) {
    const zip = path.join(workDir, `${layout}.zip`);
    const unpacked = path.join(workDir, layout);
    execFileSync(python, [builder, board, zip, "--layout", layout], { stdio: "pipe" });
    execFileSync(python, ["-m", "zipfile", "-e", zip, unpacked], { stdio: "pipe" });
    packages[layout] = unpacked;
  }
});

function coursePageHtml({ allowFullscreen }) {
  const allow = allowFullscreen ? ' allow="fullscreen" allowfullscreen' : "";
  return `<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><title>Pretend course page</title></head>
<body style="margin:0"><iframe id="tool" title="SCORM page" src="${LMS}/player.html" style="border:0;width:${EMBED.width}px;height:${EMBED.height}px"${allow}></iframe></body></html>`;
}

function playerHtml() {
  return `<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><title>Pretend LMS player</title></head>
<body style="margin:0;overflow:hidden">
<script>
  window.__scormCalls = [];
  let open = false; let finished = false; let lastError = "0";
  const record = (name, result) => (...args) => { window.__scormCalls.push([name, ...args]); return result; };
  window.API = {
    // Behaves like a strict SCORM 1.2 runtime: one session, no re-initialising, nothing after finish.
    LMSInitialize: (...args) => { window.__scormCalls.push(["LMSInitialize", ...args]); if (open || finished) { lastError = "101"; return "false"; } open = true; lastError = "0"; return "true"; },
    LMSFinish: (...args) => { window.__scormCalls.push(["LMSFinish", ...args]); if (!open) { lastError = "301"; return "false"; } open = false; finished = true; return "true"; },
    LMSGetValue: record("LMSGetValue", ""),
    LMSSetValue: record("LMSSetValue", "true"),
    LMSCommit: record("LMSCommit", "true"),
    LMSGetLastError: () => lastError,
    LMSGetErrorString: () => "",
    LMSGetDiagnostic: () => "",
  };
</script>
<iframe id="wrapper" title="Activity" src="${LMS}/wrapper.html" style="border:0;width:100%;height:100vh"></iframe>
</body></html>`;
}

function wrapperHtml() {
  return `<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><title>Wrapper</title></head>
<body style="margin:0"><iframe id="sco" title="SCORM activity" src="${LMS}/content/index.html" style="border:0;width:100%;height:100vh" allow="fullscreen"></iframe></body></html>`;
}

const CONTENT_TYPES = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".md": "text/markdown", ".xml": "application/xml" };

async function openInLms(page, layout, { csp = "", allowFullscreen = true } = {}) {
  const external = [];
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.context().route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.origin === COURSE && url.pathname === "/page.html") {
      return route.fulfill({ contentType: "text/html", body: coursePageHtml({ allowFullscreen }) });
    }
    if (url.origin !== LMS) {
      external.push(url.href);
      return route.abort();
    }
    if (url.pathname === "/player.html") return route.fulfill({ contentType: "text/html", body: playerHtml() });
    if (url.pathname === "/wrapper.html") return route.fulfill({ contentType: "text/html", body: wrapperHtml() });
    if (url.pathname.startsWith("/content/")) {
      const relative = decodeURIComponent(url.pathname.slice("/content/".length));
      const file = path.join(packages[layout], relative);
      if (!file.startsWith(packages[layout]) || !existsSync(file)) return route.fulfill({ status: 404, body: "not in package" });
      const headers = csp ? { "Content-Security-Policy": csp } : {};
      return route.fulfill({ body: readFileSync(file), contentType: CONTENT_TYPES[path.extname(file)] || "application/octet-stream", headers });
    }
    return route.fulfill({ status: 404, body: "unknown" });
  });
  await page.addInitScript(() => {
    const log = [];
    class FakeUtterance {
      constructor(text) { this.text = text; this.lang = ""; this.onstart = null; this.onend = null; this.onerror = null; }
    }
    Object.defineProperty(window, "SpeechSynthesisUtterance", { configurable: true, value: FakeUtterance });
    Object.defineProperty(window, "speechSynthesis", {
      configurable: true,
      value: { cancel() {}, getVoices() { return []; }, speak(utterance) { log.push(utterance.text); utterance.onstart?.(); } },
    });
    window.__speechLog = log;
  });
  await page.goto(`${COURSE}/page.html`);
  const content = page.frameLocator("#tool").frameLocator("#wrapper").frameLocator("#sco");
  await expect.poll(() => page.frames().some((frame) => frame.url().endsWith("/content/index.html"))).toBe(true);
  const frame = page.frames().find((candidate) => candidate.url().endsWith("/content/index.html"));
  const player = page.frames().find((candidate) => candidate.url() === `${LMS}/player.html`);
  await frame.waitForLoadState("load");
  return { content, frame, player, external, errors };
}

for (const layout of ["inline", "split"]) {
  test(`${layout} package: unchanged board runs two frames inside an LMS with one SCORM session`, async ({ page }) => {
    const { content, frame, player, external, errors } = await openInLms(page, layout);
    await expect.poll(() => frame.evaluate(() => Boolean(window.AACBoard))).toBe(true);

    const status = await frame.evaluate(() => window.AACScorm.status());
    expect(status).toMatchObject({ mode: "lms", apiFound: true, initialised: true, finished: false, completionReported: false });
    expect(await player.evaluate(() => window.__scormCalls)).toEqual([["LMSInitialize", ""]]);

    await content.getByRole("button", { name: "Start board" }).click();
    const audit = await frame.evaluate(() => window.AACBoard.auditVisibleTargets());
    expect(audit.phase).toBe("board");
    expect(audit.ok, JSON.stringify(audit)).toBe(true);

    // Touch/click activation and eye-gaze dwell both work inside the player frames.
    await content.locator('[data-button-id="btn-art"]').click();
    await expect.poll(() => frame.evaluate(() => window.__speechLog.length)).toBe(1);
    await content.getByRole("button", { name: "Stop speech" }).click();
    await page.mouse.move(1, 1);
    await content.locator('[data-button-id="btn-music"]').hover();
    await expect.poll(() => frame.evaluate(() => window.__speechLog.length), { timeout: 5000 }).toBe(2);

    // Leaving the activity closes the session once and never writes progress or answers.
    await player.evaluate(() => { document.getElementById("wrapper").src = "about:blank"; });
    await expect.poll(() => player.evaluate(() => window.__scormCalls.map((call) => call[0]))).toEqual(["LMSInitialize", "LMSFinish"]);
    expect(external, "requests outside the package").toEqual([]);
    expect(errors).toEqual([]);
  });
}

test("multi-page activity keeps one SCORM session while moving between its pages", async ({ page }) => {
  const { content, player, external, errors } = await openInLms(page, "multi");
  await expect(content.locator("h1")).toHaveText("Menu");
  await content.locator("#go").click();
  await expect(content.locator("h1")).toHaveText("Activity");
  const frame = page.frames().find((candidate) => candidate.url().endsWith("/content/sub/two.html"));
  await expect.poll(() => frame.evaluate(() => window.AACScorm && window.AACScorm.status())).toMatchObject({ initialised: true, continued: true, finished: false });
  await content.locator("#go").click();
  await expect(content.locator("h1")).toHaveText("Menu");
  expect((await player.evaluate(() => window.__scormCalls)).filter((call) => call[0] === "LMSFinish")).toEqual([]);
  await player.evaluate(() => { document.getElementById("wrapper").src = "about:blank"; });
  await expect.poll(() => player.evaluate(() => window.__scormCalls.filter((call) => call[0] === "LMSFinish").length)).toBe(1);
  expect(external).toEqual([]);
  expect(errors).toEqual([]);
});

test("board fits the embedded player area at full target size", async ({ page }) => {
  const { content, frame, errors } = await openInLms(page, "inline");
  await expect.poll(() => frame.evaluate(() => Boolean(window.AACBoard))).toBe(true);
  await content.getByRole("button", { name: "Start board" }).click();
  const fit = await frame.evaluate(() => {
    const minimum = window.AACBoard.ir.access.minimumTargetSizePx;
    const targets = [...document.querySelectorAll("[data-page-id]:not([hidden]) [data-student-target]")].map((el) => {
      const rect = el.getBoundingClientRect();
      return { id: el.id, width: rect.width, height: rect.height, right: rect.right, bottom: rect.bottom };
    });
    return {
      minimum,
      targets,
      viewport: { width: window.innerWidth, height: window.innerHeight },
      horizontalOverflow: document.documentElement.scrollWidth - window.innerWidth,
    };
  });
  expect(fit.viewport).toEqual(EMBED);
  expect(fit.horizontalOverflow).toBeLessThanOrEqual(0);
  for (const target of fit.targets) {
    expect(target.width, `${target.id} width`).toBeGreaterThanOrEqual(fit.minimum);
    expect(target.height, `${target.id} height`).toBeGreaterThanOrEqual(fit.minimum);
    expect(target.right, `${target.id} on screen`).toBeLessThanOrEqual(EMBED.width);
  }
  expect(errors).toEqual([]);
});

test("fullscreen blocked by the course page is announced and the board stays usable", async ({ page }) => {
  const { content, frame, errors } = await openInLms(page, "inline", { allowFullscreen: false });
  await expect.poll(() => frame.evaluate(() => Boolean(window.AACBoard))).toBe(true);
  await content.getByRole("button", { name: "Full screen" }).click();
  await expect(content.locator("#board-status")).toContainText("blocked");
  await content.getByRole("button", { name: "Start board" }).click();
  expect((await frame.evaluate(() => window.AACBoard.auditVisibleTargets())).ok).toBe(true);
  expect(errors).toEqual([]);
});

test("strict player CSP: inline layout cannot run, split layout still works", async ({ page, browser }) => {
  const csp = "default-src 'self' data: blob:; script-src 'self'; style-src 'self'";
  const inline = await openInLms(page, "inline", { csp });
  await page.waitForTimeout(500);
  expect(await inline.frame.evaluate(() => Boolean(window.AACBoard))).toBe(false);

  const context = await browser.newContext();
  const splitPage = await context.newPage();
  const split = await openInLms(splitPage, "split", { csp });
  await expect.poll(() => split.frame.evaluate(() => Boolean(window.AACBoard))).toBe(true);
  expect((await split.frame.evaluate(() => window.AACScorm.status())).initialised).toBe(true);
  await split.content.getByRole("button", { name: "Start board" }).click();
  expect((await split.frame.evaluate(() => window.AACBoard.auditVisibleTargets())).ok).toBe(true);
  await split.content.locator('[data-button-id="btn-art"]').click();
  await expect.poll(() => split.frame.evaluate(() => window.__speechLog.length)).toBe(1);
  expect(split.external).toEqual([]);
  expect(split.errors).toEqual([]);
  await context.close();
});

test("opened outside an LMS the packaged board behaves as the standalone file", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(pathToFileURL(path.join(packages.inline, "index.html")).href);
  await expect.poll(() => page.evaluate(() => Boolean(window.AACBoard))).toBe(true);
  expect(await page.evaluate(() => window.AACScorm.status().mode)).toBe("standalone");
  await page.getByRole("button", { name: "Start board" }).click();
  expect((await page.evaluate(() => window.AACBoard.auditVisibleTargets())).ok).toBe(true);
  expect(errors).toEqual([]);
});

test("full screen toggle fills the screen from inside the LMS frames, survives page changes and comes back", async ({ page }) => {
  const { content, frame, external, errors } = await openInLms(page, "multiToggle");
  const toggle = content.locator("[data-aac-fullscreen-toggle]");
  await expect(toggle).toBeVisible();
  await expect(toggle).toHaveAccessibleName("Full screen");
  const box = await toggle.boundingBox();
  expect(box.width).toBeGreaterThanOrEqual(48);
  expect(box.height).toBeGreaterThanOrEqual(48);
  // Compact at rest (icon only); the words appear while it is hovered or focused.
  const words = toggle.locator("span");
  await expect(words).toBeHidden();
  await toggle.hover();
  await expect(words).toBeVisible();
  await expect(words).toHaveText("Full screen");
  await page.mouse.move(1, 1);
  await expect(words).toBeHidden();
  expect(await frame.evaluate(() => window.AACFullscreenToggle.status())).toMatchObject({ shown: true, position: "bottom-right", target: "player frame", fullscreen: false });

  // A mouse/touch press goes full screen and hands focus back to what had it (so game keys keep working).
  await content.locator("#go").focus();
  await toggle.click();
  await expect.poll(() => page.evaluate(() => Boolean(document.fullscreenElement))).toBe(true);
  await expect(toggle).toHaveAccessibleName("Exit full screen");
  expect(await frame.evaluate(() => document.activeElement && document.activeElement.id)).toBe("go");
  await expect(content.locator("[data-aac-fullscreen-status]")).toContainText("Full screen on");

  // Moving to the activity's next page keeps full screen, and the new page's button knows it.
  await content.locator("#go").click();
  await expect(content.locator("h1")).toHaveText("Activity");
  expect(await page.evaluate(() => Boolean(document.fullscreenElement))).toBe(true);
  await expect(content.locator("[data-aac-fullscreen-toggle]")).toHaveAccessibleName("Exit full screen");

  // Keyboard: Tab to the button and press Enter to come back.
  const second = page.frames().find((candidate) => candidate.url().endsWith("/content/sub/two.html"));
  await second.focus("[data-aac-fullscreen-toggle]");
  await page.keyboard.press("Enter");
  await expect.poll(() => page.evaluate(() => Boolean(document.fullscreenElement))).toBe(false);
  await expect(content.locator("[data-aac-fullscreen-toggle]")).toHaveAccessibleName("Full screen");
  expect(external).toEqual([]);
  expect(errors).toEqual([]);
});

test("full screen toggle is not shown when the course page does not allow full screen", async ({ page }) => {
  const { content, frame, errors } = await openInLms(page, "multiToggle", { allowFullscreen: false });
  await expect(content.locator("h1")).toHaveText("Menu");
  await expect.poll(() => frame.evaluate(() => Boolean(window.AACFullscreenToggle))).toBe(true);
  expect(await frame.evaluate(() => window.AACFullscreenToggle.status())).toMatchObject({ shown: false, target: "none" });
  await expect(content.locator("[data-aac-fullscreen-toggle]")).toHaveCount(0);
  expect(errors).toEqual([]);
});

test("full screen toggle keeps its look under a strict player CSP (split layout)", async ({ page }) => {
  const csp = "default-src 'self' data: blob:; script-src 'self'; style-src 'self'";
  const { content, frame, errors } = await openInLms(page, "splitToggle", { csp });
  await expect.poll(() => frame.evaluate(() => Boolean(window.AACBoard))).toBe(true);
  const toggle = content.locator("[data-aac-fullscreen-toggle]");
  await expect(toggle).toBeVisible();
  const look = await toggle.evaluate((el) => { const s = getComputedStyle(el); return { position: s.position, background: s.backgroundColor, minHeight: s.minHeight }; });
  expect(look).toEqual({ position: "fixed", background: "rgb(19, 68, 81)", minHeight: "52px" });
  await toggle.click();
  await expect.poll(() => page.evaluate(() => Boolean(document.fullscreenElement))).toBe(true);
  await expect(toggle).toHaveAccessibleName("Exit full screen");
  await toggle.click();
  await expect.poll(() => page.evaluate(() => Boolean(document.fullscreenElement))).toBe(false);
  // The board's own controls still work alongside it.
  await content.getByRole("button", { name: "Start board" }).click();
  expect((await frame.evaluate(() => window.AACBoard.auditVisibleTargets())).ok).toBe(true);
  expect(errors).toEqual([]);
});

test("full screen toggle still works inside an activity that guards every click, and the activity never sees its presses", async ({ page }) => {
  const { content, frame, errors } = await openInLms(page, "guarded");
  const toggle = content.locator("[data-aac-fullscreen-toggle]");
  await expect(toggle).toBeVisible();
  await toggle.click();
  await expect.poll(() => page.evaluate(() => Boolean(document.fullscreenElement))).toBe(true);
  await expect(toggle).toHaveAccessibleName("Exit full screen");
  await toggle.click();
  await expect.poll(() => page.evaluate(() => Boolean(document.fullscreenElement))).toBe(false);
  // Keyboard Space, even though the activity cancels Space/Enter key-ups on the document.
  await frame.focus("[data-aac-fullscreen-toggle]");
  await page.keyboard.press(" ");
  await expect.poll(() => page.evaluate(() => Boolean(document.fullscreenElement))).toBe(true);
  await expect(toggle).toHaveAccessibleName("Exit full screen");
  await page.keyboard.press(" ");
  await expect.poll(() => page.evaluate(() => Boolean(document.fullscreenElement))).toBe(false);
  await content.locator("#own").click();
  expect(await frame.evaluate(() => window.__seen)).toEqual(["own"]);
  expect(errors).toEqual([]);
});
