const { test, expect } = require("@playwright/test");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

test("blind packet renders and preserves a completed ballot without HTML injection sinks", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(pathToFileURL(path.join(__dirname, "../../examples/demo/packets/reviewer-one.html")).href);

  await expect(page.getByRole("heading", { level: 2 })).toBeVisible();
  const hostileText = '<img src=x onerror="window.__packetXss=true">';
  await page.evaluate((value) => {
    window.__packetXss = false;
    data.items[0].task.title = value;
    data.items[0].left.content = value;
    render();
  }, hostileText);
  await expect(page.getByRole("heading", { level: 2 })).toHaveText(hostileText);
  await expect(page.locator("#mount img")).toHaveCount(0);
  expect(await page.evaluate(() => window.__packetXss)).toBe(false);
  await expect(page.locator(".answer .content")).toHaveCount(2);
  const scoreSelectors = page.locator("select[data-side]");
  await expect(scoreSelectors).toHaveCount(10);
  for (const selector of await scoreSelectors.all()) await selector.selectOption("3");
  await page.getByRole("radio", { name: "left" }).check();
  await page.locator("#confidence").selectOption("4");
  await page.getByLabel("Decision rationale").fill("The left response is more actionable.");
  await page.getByRole("button", { name: "Save & next" }).click();

  await expect(page.locator("#progress")).toHaveText("2 / 48");
  expect(errors).toEqual([]);
  expect(await page.locator("#mount").evaluate((element) => element.querySelectorAll("script").length)).toBe(0);
});
