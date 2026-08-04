import { defineConfig } from "@playwright/test";

const installedChrome = process.env.PLAYWRIGHT_USE_INSTALLED_CHROME === "1";

export default defineConfig({
  testDir: "./browser-tests",
  timeout: 30_000,
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "line",
  use: {
    browserName: "chromium",
    channel: installedChrome ? "chrome" : undefined,
    headless: true,
  },
  projects: [
    {
      name: "accent-1000-classroom",
      testIgnore: /accent-display\.spec\.mjs/,
      use: { viewport: { width: 1280, height: 800 } },
    },
    { name: "accent-1400-classroom", use: { viewport: { width: 1920, height: 1080 } } },
    {
      name: "classroom-laptop",
      testIgnore: /accent-display\.spec\.mjs/,
      use: { viewport: { width: 1366, height: 768 } },
    },
  ],
});
