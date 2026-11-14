import { expect, test } from "@playwright/test";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

// The screen-fit maths in display_fit.py (and check_accent_display.py) decides whether a board's
// bottom row, where Help, Different and Finished live, is cut off. These tests hold that maths
// to what a real browser lays out at the must-fit floor.
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const scripts = path.join(root, "skills/agentic-aac-board-maker/scripts");
const python = existsSync(path.join(root, ".venv/bin/python")) ? path.join(root, ".venv/bin/python") : "python3";
const FLOOR = { width: 1264, height: 600 };

function constant(name) {
  const match = readFileSync(path.join(scripts, "display_fit.py"), "utf8").match(new RegExp(`^${name} = (\\d+)`, "m"));
  if (!match) throw new Error(`display_fit.py has no ${name}`);
  return Number(match[1]);
}
const CHROME_PLAIN = constant("CHROME_PLAIN");
const CHROME_MESSAGE_BAR = constant("CHROME_MESSAGE_BAR");

const shipped = readdirSync(path.join(root, "generated"), { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .flatMap((entry) =>
    readdirSync(path.join(root, "generated", entry.name))
      .filter((name) => name.endsWith(".html") && name !== "partner-card.html")
      .map((name) => path.join("generated", entry.name, name)),
  );

async function openAtFloor(page, file) {
  await page.addInitScript(() => {
    class FakeUtterance {
      constructor(text) { this.text = text; this.onstart = null; this.onend = null; this.onerror = null; }
    }
    Object.defineProperty(window, "SpeechSynthesisUtterance", { configurable: true, value: FakeUtterance });
    Object.defineProperty(window, "speechSynthesis", { configurable: true, value: { cancel() {}, speak(utterance) { utterance.onstart?.(); } } });
  });
  await page.setViewportSize(FLOOR);
  await page.goto(pathToFileURL(path.isAbsolute(file) ? file : path.join(root, file)).href);
  const start = page.getByRole("button", { name: "Start board" });
  if (await start.isVisible().catch(() => false)) await start.click();
}

function measureGrid(page) {
  return page.evaluate(() => {
    const grid = [...document.querySelectorAll(".board-grid")].find((element) => element.offsetParent !== null);
    const boxes = [...grid.querySelectorAll("button")].filter((button) => button.offsetParent !== null).map((button) => button.getBoundingClientRect());
    const bar = document.querySelector(".message-bar");
    return {
      firstRowTop: Math.round(Math.min(...boxes.map((box) => box.top))),
      lowestBottom: Math.round(Math.max(...boxes.map((box) => box.bottom))),
      messageBar: Boolean(bar && bar.offsetParent !== null),
    };
  });
}

for (const file of shipped) {
  test(`${file} keeps its bottom row on a ${FLOOR.width}x${FLOOR.height} screen`, async ({ page }) => {
    await openAtFloor(page, file);
    const grid = await measureGrid(page);
    const allowance = grid.messageBar ? CHROME_MESSAGE_BAR : CHROME_PLAIN;
    expect(grid.firstRowTop, "space above the grid must stay within the allowance display_fit.py uses").toBeLessThanOrEqual(allowance);
    expect(grid.lowestBottom, "bottom row fully on screen").toBeLessThanOrEqual(FLOOR.height + 1);
  });
}

test.describe("build_board.py screen-fit verdict matches the browser", () => {
  let scratch;
  test.beforeAll(() => { scratch = mkdtempSync(path.join(tmpdir(), "aac-fit-")); });
  test.afterAll(() => rmSync(scratch, { recursive: true, force: true }));

  function build(name, target) {
    const source = {
      id: name, title: "Fit probe", purpose: "Screen-fit probe.", audience: { ageBand: "secondary" },
      access: { intended: ["eye-gaze-dwell", "keyboard"], profile: "eye-gaze-dwell", minimumTargetSizePx: target, dwellTimeMs: 1000 },
      communicationFunctions: ["comment", "repair", "regulate-rest"],
      pages: [{ id: "page-main", name: "Main", grid: { rows: 3, columns: 3 }, buttons: [
        { id: "btn-like", label: "I like it" }, { id: "btn-help", label: "Help" },
        { id: "btn-different", label: "Different" }, { id: "btn-finished", label: "Finished" },
      ] }],
    };
    const file = path.join(scratch, `${name}.source.json`);
    writeFileSync(file, JSON.stringify(source));
    const result = spawnSync(python, [path.join(scripts, "build_board.py"), file, "--quiet"], { encoding: "utf8" });
    return { status: result.status, output: result.stdout + result.stderr, html: path.join(scratch, `${name}.html`) };
  }

  test("the largest target the build accepts for three rows fits", async ({ page }) => {
    const built = build("fits", 132);
    expect(built.status, built.output).toBe(0);
    await openAtFloor(page, built.html);
    const grid = await measureGrid(page);
    expect(grid.messageBar).toBe(true);
    expect(grid.lowestBottom).toBeLessThanOrEqual(FLOOR.height + 1);
  });

  test("a board the build rejects really has Help cut off", async ({ page }) => {
    const built = build("clipped", 160);
    expect(built.status, built.output).toBe(1);
    expect(built.output).toContain("screen fit");
    await openAtFloor(page, built.html);
    const grid = await measureGrid(page);
    expect(grid.lowestBottom, "bottom row extends past the screen").toBeGreaterThan(FLOOR.height + 40);
    const help = await page.locator("#btn-help").boundingBox();
    expect(help.y + help.height, "Help is in the row that is cut off").toBeGreaterThan(FLOOR.height + 40);
    const scrollable = await page.evaluate(() => document.documentElement.scrollHeight - window.innerHeight);
    expect(scrollable, "the page does not scroll, so the row cannot be reached").toBeLessThanOrEqual(1);
  });
});
