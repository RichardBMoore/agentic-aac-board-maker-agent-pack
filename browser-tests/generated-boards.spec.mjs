import { expect, test } from "@playwright/test";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const boards = [
  "generated/curriculum-sentence-builder/year7-hero-speech-sentence-builder.html",
  "generated/gaze-choice-2x2/gaze-choice-class-activity.html",
  "generated/needs-repair-board/secondary-needs-repair-board.html",
  "generated/partner-assisted-print/partner-assisted-scanning-print-board.html",
  "generated/qcia-community-shops/qcia-community-shops.html",
  "generated/visual-schedule-expressive/morning-routine-expressive-schedule.html",
];

async function openBoard(page, relativePath) {
  await page.addInitScript(() => {
    const log = [];
    class FakeUtterance {
      constructor(text) { this.text = text; this.lang = ""; this.onstart = null; this.onend = null; this.onerror = null; }
    }
    Object.defineProperty(window, "SpeechSynthesisUtterance", { configurable: true, value: FakeUtterance });
    Object.defineProperty(window, "speechSynthesis", {
      configurable: true,
      value: {
        cancel() {},
        speak(utterance) { log.push(utterance.text); utterance.onstart?.(); },
      },
    });
    window.__speechLog = log;
  });
  await page.goto(pathToFileURL(path.join(root, relativePath)).href);
  await expect.poll(() => page.evaluate(() => Boolean(window.AACBoard))).toBe(true);
}

for (const relativePath of boards) {
  test(`${relativePath} accounts for every active target and meets its target size`, async ({ page }) => {
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await openBoard(page, relativePath);

    const setupAudit = await page.evaluate(() => window.AACBoard.auditVisibleTargets());
    expect(setupAudit.ok).toBe(true);
    if (setupAudit.phase === "setup") {
      expect(setupAudit.count).toBeLessThanOrEqual(setupAudit.limit);
      await page.getByRole("button", { name: "Start board" }).click();
    }

    const audit = await page.evaluate(() => window.AACBoard.auditVisibleTargets());
    expect(audit.phase).toBe("board");
    expect(audit.ok, JSON.stringify(audit)).toBe(true);
    const targetSizes = await page.locator("[data-page-id]:not([hidden]) [data-student-target]").evaluateAll((targets) =>
      targets.map((target) => {
        const rect = target.getBoundingClientRect();
        return { id: target.id, width: rect.width, height: rect.height };
      })
    );
    const minimum = await page.evaluate(() => window.AACBoard.ir.access.minimumTargetSizePx);
    for (const size of targetSizes) {
      expect(size.width, `${size.id} width`).toBeGreaterThanOrEqual(minimum);
      expect(size.height, `${size.id} height`).toBeGreaterThanOrEqual(minimum);
    }
    const dwellEnabled = await page.locator("body").getAttribute("data-dwell-enabled");
    const activeDwellTargets = await page.locator("[data-page-id]:not([hidden]) [data-dwell]").count();
    if (dwellEnabled === "true") expect(activeDwellTargets).toBe(audit.count);
    else expect(activeDwellTargets).toBe(0);
    expect(errors).toEqual([]);
  });
}

test("dwell cancellation, dwell activation and exclusive Stop Speech work", async ({ page }) => {
  await openBoard(page, boards[1]);
  await page.getByRole("button", { name: "Start board" }).click();
  const target = page.locator('[data-button-id="btn-art"]');
  await target.hover();
  await page.waitForTimeout(250);
  await page.mouse.move(1, 1);
  await page.waitForTimeout(1100);
  expect(await page.evaluate(() => window.__speechLog.length)).toBe(0);

  await target.hover();
  await expect.poll(() => page.evaluate(() => window.__speechLog.length), { timeout: 5000 }).toBe(1);
  const speechAudit = await page.evaluate(() => window.AACBoard.auditVisibleTargets());
  expect(speechAudit).toMatchObject({ phase: "speech", count: 1, limit: 1, ok: true });
  await page.getByRole("button", { name: "Stop speech" }).click();
  const boardAudit = await page.evaluate(() => window.AACBoard.auditVisibleTargets());
  expect(boardAudit.phase).toBe("board");
  expect(boardAudit.ok).toBe(true);
});

test("sentence building and page navigation use the shared action runtime", async ({ page }) => {
  await openBoard(page, boards[0]);
  await page.getByRole("button", { name: "Start board" }).click();
  await page.locator('[data-button-id="btn-my-hero"]').click();
  await page.getByRole("button", { name: "Stop speech" }).click();
  await page.locator('[data-button-id="btn-because"]').click();
  await page.getByRole("button", { name: "Stop speech" }).click();
  await expect(page.locator("#message-text")).toContainText("My hero is");
  await expect(page.locator("#message-text")).toContainText("because");
  await page.locator('[data-button-id="btn-to-describe"]').click();
  await expect(page.locator('[data-page-id="page-describe"]')).toBeVisible();
  await page.locator('[data-button-id="btn-undo-2"]').click();
  await expect(page.locator("#message-text")).not.toContainText("because");
});

test("fullscreen rejection leaves a usable, announced setup state", async ({ page }) => {
  await openBoard(page, boards[1]);
  await page.evaluate(() => {
    document.documentElement.requestFullscreen = () => Promise.reject(new Error("blocked in test"));
  });
  await page.getByRole("button", { name: "Full screen" }).click();
  await expect(page.locator("#board-status")).toContainText("blocked");
  const audit = await page.evaluate(() => window.AACBoard.auditVisibleTargets());
  expect(audit.phase).toBe("setup");
  expect(audit.ok).toBe(true);
});

test("representative board has no serious or critical axe findings", async ({ page }) => {
  await openBoard(page, boards[1]);
  await page.getByRole("button", { name: "Start board" }).click();
  await page.addScriptTag({ path: path.join(root, "node_modules/axe-core/axe.min.js") });
  const results = await page.evaluate(async () => window.axe.run(document, {
    resultTypes: ["violations"],
    rules: { "color-contrast": { enabled: true } },
  }));
  const severe = results.violations.filter((violation) => ["serious", "critical"].includes(violation.impact));
  expect(severe, JSON.stringify(severe, null, 2)).toEqual([]);
});
