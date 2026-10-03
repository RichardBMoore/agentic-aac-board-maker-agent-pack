import { expect, test } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const python = existsSync(path.join(root, ".venv/bin/python")) ? path.join(root, ".venv/bin/python") : "python3";
const renderer = path.join(root, "skills/agentic-aac-board-maker/scripts/render_html.py");
const board = (relative) => path.join(root, "generated", relative);
const SHOPS = board("qcia-community-shops/qcia-community-shops.html");
const HERO = board("curriculum-sentence-builder/year7-hero-speech-sentence-builder.html");
const NEEDS = board("needs-repair-board/secondary-needs-repair-board.html");
const GAZE = board("gaze-choice-2x2/gaze-choice-class-activity.html");
const SCHEDULE = board("visual-schedule-expressive/morning-routine-expressive-schedule.html");

let scratch;
test.beforeAll(() => { scratch = mkdtempSync(path.join(tmpdir(), "aac-house-")); });
test.afterAll(() => rmSync(scratch, { recursive: true, force: true }));

function renderCandidate(source, edit) {
  const ir = JSON.parse(readFileSync(source));
  edit(ir);
  const input = path.join(scratch, "candidate.ir.json");
  const output = path.join(scratch, "candidate.html");
  writeFileSync(input, JSON.stringify(ir));
  execFileSync(python, [renderer, input, output]);
  return output;
}

// Speech that takes ~400 ms per word, like a real voice, so dwell timing matters.
async function open(page, file, { query = "", voices = null } = {}) {
  await page.addInitScript((voiceList) => {
    window.__spoken = [];
    window.__completed = [];
    window.__cancelled = [];
    window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
    let current = null;
    let timer = 0;
    Object.defineProperty(window, "speechSynthesis", {
      value: {
        getVoices: () => voiceList || [],
        cancel() { if (current) window.__cancelled.push(current.text); clearTimeout(timer); current = null; },
        speak(utterance) {
          current = utterance;
          window.__spoken.push({ text: utterance.text, voice: utterance.voice ? utterance.voice.name : null });
          setTimeout(() => utterance.onstart?.(), 5);
          timer = setTimeout(() => { window.__completed.push(utterance.text); current = null; utterance.onend?.(); }, 400 * utterance.text.split(/\s+/).length);
        },
      },
    });
  }, voices);
  await page.goto(pathToFileURL(file).href + query);
  await expect.poll(() => page.evaluate(() => Boolean(window.AACBoard))).toBe(true);
  await page.evaluate(() => window.AACBoard.start());
}

async function restGazeOn(page, locator, milliseconds) {
  const box = await locator.boundingBox();
  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;
  for (let elapsed = 0; elapsed < milliseconds; elapsed += 100) {
    await page.mouse.move(x + (elapsed % 3) - 1, y + (elapsed % 2));
    await page.waitForTimeout(100);
  }
}

test("a gaze user resting on a button hears the whole message once", async ({ page }) => {
  await open(page, SHOPS);
  await restGazeOn(page, page.locator('[data-button-id="btn-where"]'), 4500);
  const result = await page.evaluate(() => ({ spoken: window.__spoken.map((item) => item.text), completed: window.__completed, cancelled: window.__cancelled }));
  expect(result.spoken).toEqual(["Where is it?"]);
  expect(result.completed).toEqual(["Where is it?"]);
  expect(result.cancelled).toEqual([]);
});

test("after navigating, the button under the gaze waits for the pointer to leave", async ({ page }) => {
  await open(page, NEEDS);
  const forward = page.locator('[data-button-id="btn-to-repair"]');
  await restGazeOn(page, forward, 2600);
  await expect(page.locator('[data-page-id="page-repair"]')).toBeVisible();
  const nextForward = page.locator('[data-page-id="page-repair"] [data-button-id="nav-page-repair"]');
  await expect(nextForward).toBeVisible();
  await expect(page.locator('[data-page-id="page-repair"]')).toBeVisible();
  await page.mouse.move(5, 5);
  await page.waitForTimeout(150);
  await restGazeOn(page, nextForward, 1500);
  await expect(page.locator('[data-page-id="page-core-words"]')).toBeVisible();
});

test("a new selection interrupts the current message instead of waiting", async ({ page }) => {
  await open(page, GAZE);
  await page.locator('[data-button-id="btn-read"]').click();
  await page.locator('[data-button-id="btn-music"]').click();
  await expect.poll(() => page.evaluate(() => window.__completed)).toEqual(["Music"]);
  expect(await page.evaluate(() => window.__cancelled)).toEqual(["Read"]);
});

test("ABC keyboard spells, adds a space and deletes letters", async ({ page }) => {
  await open(page, SHOPS);
  await page.getByRole("button", { name: "ABC", exact: true }).click();
  await expect(page.locator('[data-page-id="page-keyboard"]')).toBeVisible();
  await page.getByRole("button", { name: "h j k l ␣", exact: true }).click();
  await page.getByRole("button", { name: "h", exact: true }).click();
  await expect(page.locator('[data-page-id="page-keyboard"]')).toBeVisible();
  await page.getByRole("button", { name: "y u i o p", exact: true }).click();
  await page.getByRole("button", { name: "i", exact: true }).click();
  await expect(page.locator("#message-text")).toHaveText("hi");
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  await expect(page.locator("#message-text")).toHaveText("h");
  await page.getByRole("button", { name: "◀ Back", exact: true }).click();
  await expect(page.locator('[data-page-id="page-main"]')).toBeVisible();
});

test("core words and word endings build grammatical messages", async ({ page }) => {
  await open(page, HERO);
  await page.evaluate(() => window.AACBoard.navigate("page-core-words"));
  await page.locator('[data-button-id="core-i"]').click();
  await page.locator('[data-button-id="core-like"]').click();
  await page.evaluate(() => window.AACBoard.navigate("page-word-endings"));
  await page.locator('[data-button-id="end-s"]').click();
  await expect(page.locator("#message-text")).toHaveText("I likes");
  await page.locator('[data-button-id="end-undo"]').click();
  await expect(page.locator("#message-text")).toHaveText("I");
  const forms = await page.evaluate(() => ["go:ed", "like:s", "stop:ing", "make:ing", "try:ed", "run:ing", "visit:ed", "bus:s", "happy:er"].map((pair) => {
    const [word, ending] = pair.split(":");
    return window.AACBoard.inflect(word, ending);
  }));
  expect(forms).toEqual(["went", "likes", "stopping", "making", "tried", "running", "visited", "buses", "happier"]);
});

test("visual schedule shows now, next and done, and Finished moves it on", async ({ page }) => {
  await open(page, SCHEDULE);
  await expect(page.locator('[data-button-id="btn-arrive"] .schedule-badge')).toHaveText("Now ▶");
  await expect(page.locator('[data-button-id="btn-bag"] .schedule-badge')).toHaveText("Next");
  await page.locator('[data-button-id="btn-finished"]').click();
  await expect(page.locator('[data-button-id="btn-arrive"] .schedule-badge')).toHaveText("Done ✓");
  await expect(page.locator('[data-button-id="btn-arrive"]')).toHaveAttribute("aria-label", "Arrive, done");
  await expect(page.locator('[data-button-id="btn-bag"] .schedule-badge')).toHaveText("Now ▶");
  await expect(page.locator("#schedule-status")).toContainText("step 2 of 4");
});

test("opt-in selection log separates student selections from partner models", async ({ page }) => {
  const file = renderCandidate(SHOPS.replace(".html", ".ir.json"), (ir) => {
    ir.evidenceLog = { enabled: true, consentNote: "Test: team and family agreed to log the shop routine." };
  });
  await open(page, file, { query: "?teacher=1" });
  await expect(page.locator("#teacher-panel")).toBeVisible();
  await page.getByRole("button", { name: "Record selections" }).click();
  await expect(page.locator("#recording-indicator")).toBeVisible();
  await page.locator('[data-button-id="btn-hello"]').click();
  await page.getByRole("button", { name: "Partner modelling" }).click();
  await page.getByRole("button", { name: "Close teacher panel" }).click();
  await expect(page.locator("#modelling-indicator")).toBeVisible();
  await page.locator('[data-button-id="btn-where"]').click();
  await page.keyboard.press("Control+Shift+T");
  await expect(page.locator("#teacher-panel")).toBeVisible();
  await expect(page.locator("#log-summary")).toContainText("Student selections: 1");
  await expect(page.locator("#log-summary")).toContainText("Partner models: 1");
  const waiting = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CSV" }).click();
  const csv = readFileSync(await (await waiting).path(), "utf8");
  expect(csv.split("\r\n")[0]).toBe("time,page,buttonId,label,message,function,role,wordClass,source,method");
  expect(csv).toContain('"btn-hello","Hello","Hello","initiate"');
  expect(csv).toContain('"partner-model"');
});

test("logging stays off unless the board enables it", async ({ page }) => {
  await open(page, GAZE, { query: "?teacher=1" });
  await expect(page.locator("#teacher-panel")).toContainText("Selection logging is switched off");
  await page.locator('[data-button-id="btn-read"]').click();
  expect(await page.evaluate(() => window.AACBoard.log())).toEqual([]);
});

test("speech prefers an installed en-AU voice over an online one", async ({ page }) => {
  const voices = [
    { name: "Microsoft Natasha Online (Natural) - English (Australia)", lang: "en-AU", localService: false },
    { name: "Microsoft Catherine", lang: "en-AU", localService: true },
    { name: "Google US English", lang: "en-US", localService: true },
  ];
  await open(page, GAZE, { voices });
  await page.locator('[data-button-id="btn-read"]').click();
  await expect.poll(() => page.evaluate(() => window.__spoken[0]?.voice)).toBe("Microsoft Catherine");
  expect(await page.evaluate(() => window.AACBoard.voice())).toMatchObject({ name: "Microsoft Catherine", local: true });
  await expect(page.locator("#voice-status")).toContainText("installed on this device");
});

test("a pinned voice is used even when it is online, and the panel warns", async ({ page }) => {
  const file = renderCandidate(GAZE.replace(".html", ".ir.json"), (ir) => { ir.speech.voiceName = "Natasha"; });
  await open(page, file, { voices: [
    { name: "Microsoft Natasha Online (Natural) - English (Australia)", lang: "en-AU", localService: false },
    { name: "Microsoft Catherine", lang: "en-AU", localService: true },
  ] });
  await page.locator('[data-button-id="btn-read"]').click();
  await expect.poll(() => page.evaluate(() => window.__spoken[0]?.voice)).toContain("Natasha");
  await expect(page.locator("#voice-status")).toContainText("needs internet");
});

test("CVI profile uses a dark background without colour coding", async ({ page }) => {
  const file = renderCandidate(GAZE.replace(".html", ".ir.json"), (ir) => { ir.display.visualProfile = "cvi"; ir.display.colourScheme = "none"; });
  await open(page, file);
  expect(await page.evaluate(() => getComputedStyle(document.body).backgroundColor)).toBe("rgb(0, 0, 0)");
  expect(await page.locator('[data-button-id="btn-art"]').evaluate((button) => getComputedStyle(button).backgroundColor)).toBe("rgb(0, 0, 0)");
});

test("a hidden (masked) cell keeps its place and is not a target", async ({ page }) => {
  const before = renderCandidate(GAZE.replace(".html", ".ir.json"), () => {});
  await open(page, before);
  const helpBefore = await page.locator('[data-button-id="btn-help"]').boundingBox();
  const file = renderCandidate(GAZE.replace(".html", ".ir.json"), (ir) => { ir.pages[0].buttons.find((button) => button.id === "btn-game").hidden = true; });
  await open(page, file);
  await expect(page.locator('[data-masked-id="btn-game"]')).toHaveCount(1);
  await expect(page.locator('[data-button-id="btn-game"]')).toHaveCount(0);
  expect(await page.evaluate(() => window.AACBoard.auditVisibleTargets().count)).toBe(5);
  expect(await page.locator('[data-button-id="btn-help"]').boundingBox()).toEqual(helpBefore);
});
