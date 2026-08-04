import { expect, test } from "@playwright/test";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

// Real-device effective viewports for PRC-Saltillo Accent / EQ-managed Edge.
// See skills/accent-display-fit/references/accent-device-field-guide.md.
// mustFit profiles: no scroll at all, every visible student target >= 120px and on-screen.
// grace profiles: no horizontal scroll; setup targets still >= 120px and on-screen (content may paginate/scroll vertically).
const PROFILES = [
  { name: "accent-1400-150 (fullscreen, 150% scaling)", width: 1280, height: 720, mustFit: true },
  { name: "accent-1400-chrome (maximised Edge floor)", width: 1264, height: 600, mustFit: true },
  { name: "accent-1400-original (2013 hardware)", width: 1280, height: 800, mustFit: true },
  { name: "empower-browser (two toolbar rows)", width: 1280, height: 600, mustFit: true },
  { name: "nuvoice-keymode (half-screen grace floor)", width: 1180, height: 460, mustFit: false },
  { name: "published grace floor", width: 1024, height: 460, mustFit: false },
];

const MIN_TARGET = 120;
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const defaultFile = "skills/build-aac-student-supports/assets/eye-gaze-single-file-template.html";
const targetFile = process.env.ACCENT_QA_FILE || defaultFile;

async function openActivity(page, relativeOrAbsolutePath) {
  await page.addInitScript(() => {
    class FakeUtterance {
      constructor(text) { this.text = text; this.lang = ""; this.onstart = null; this.onend = null; this.onerror = null; }
    }
    Object.defineProperty(window, "SpeechSynthesisUtterance", { configurable: true, value: FakeUtterance });
    Object.defineProperty(window, "speechSynthesis", {
      configurable: true,
      value: { cancel() {}, speak(utterance) { utterance.onstart?.(); } },
    });
  });
  const absolute = path.isAbsolute(relativeOrAbsolutePath)
    ? relativeOrAbsolutePath
    : path.join(root, relativeOrAbsolutePath);
  await page.goto(pathToFileURL(absolute).href);
  await page.waitForLoadState("load");
  return page.evaluate(() => Boolean(window.AACBoard));
}

function overflow(page) {
  return page.evaluate(() => ({
    horizontal: document.documentElement.scrollWidth - window.innerWidth,
    vertical: document.documentElement.scrollHeight - window.innerHeight,
  }));
}

function visibleTargetBoxes(page) {
  return page.evaluate(() => {
    const candidates = document.querySelectorAll("[data-student-target], button");
    return [...new Set(candidates)]
      .filter((el) => {
        if (el.offsetParent === null && getComputedStyle(el).position !== "fixed") return false;
        const style = getComputedStyle(el);
        return style.visibility !== "hidden" && style.display !== "none";
      })
      .map((el) => {
        const rect = el.getBoundingClientRect();
        return {
          id: el.id || el.getAttribute("aria-label") || el.textContent.trim().slice(0, 30),
          width: rect.width,
          height: rect.height,
          left: rect.left,
          top: rect.top,
          right: rect.right,
          bottom: rect.bottom,
        };
      });
  });
}

for (const profile of PROFILES) {
  test(`${targetFile} fits ${profile.name} ${profile.width}x${profile.height}`, async ({ page }) => {
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.setViewportSize({ width: profile.width, height: profile.height });
    const hasRuntime = await openActivity(page, targetFile);

    // Setup phase (or whole page for non-runtime activities).
    let spill = await overflow(page);
    expect(spill.horizontal, "horizontal overflow before start").toBeLessThanOrEqual(1);
    for (const box of await visibleTargetBoxes(page)) {
      expect(box.width, `${box.id} width at setup`).toBeGreaterThanOrEqual(MIN_TARGET);
      expect(box.height, `${box.id} height at setup`).toBeGreaterThanOrEqual(MIN_TARGET);
      expect(box.left, `${box.id} on-screen left`).toBeGreaterThanOrEqual(-1);
      expect(box.right, `${box.id} on-screen right`).toBeLessThanOrEqual(profile.width + 1);
      expect(box.top, `${box.id} on-screen top`).toBeGreaterThanOrEqual(-1);
      expect(box.bottom, `${box.id} on-screen bottom`).toBeLessThanOrEqual(profile.height + 1);
    }

    if (hasRuntime) {
      const start = page.getByRole("button", { name: "Start board" });
      if (await start.isVisible().catch(() => false)) {
        await start.click();
      }
      spill = await overflow(page);
      expect(spill.horizontal, "horizontal overflow on board").toBeLessThanOrEqual(1);
      if (profile.mustFit) {
        expect(spill.vertical, "vertical overflow on board (student-mode scroll)").toBeLessThanOrEqual(1);
        for (const box of await visibleTargetBoxes(page)) {
          expect(box.width, `${box.id} width on board`).toBeGreaterThanOrEqual(MIN_TARGET);
          expect(box.height, `${box.id} height on board`).toBeGreaterThanOrEqual(MIN_TARGET);
          expect(box.left, `${box.id} fully on-screen left`).toBeGreaterThanOrEqual(-1);
          expect(box.top, `${box.id} fully on-screen top`).toBeGreaterThanOrEqual(-1);
          expect(box.bottom, `${box.id} fully on-screen`).toBeLessThanOrEqual(profile.height + 1);
          expect(box.right, `${box.id} fully on-screen`).toBeLessThanOrEqual(profile.width + 1);
        }
      }
    } else if (profile.mustFit) {
      expect(spill.vertical, "vertical overflow (student-mode scroll)").toBeLessThanOrEqual(1);
    }

    expect(errors, "page errors").toEqual([]);
  });
}
