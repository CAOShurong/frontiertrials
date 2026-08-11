const { test, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;

async function expectNoAutomatedWcagViolations(page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(results.violations).toEqual([]);
}

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() => localStorage.clear());
  await page.reload();
});

test("reports validation errors at the field that needs attention", async ({ page }) => {
  await page.getByRole("button", { name: "Start blind review" }).press("Enter");

  const title = page.getByLabel("Task title");
  await expect(title).toBeFocused();
  await expect(title).toHaveAttribute("aria-invalid", "true");
  await expect(title).toHaveAttribute("aria-describedby", "capture-message");
  await expect(page.getByRole("alert")).toHaveText("Give this task a short title.");
});

test("completes a multi-pair trial with predictable keyboard focus", async ({ page }) => {
  await page.getByRole("button", { name: "Load a fictional example" }).click();
  await page.getByRole("button", { name: "Add another product" }).click();
  const names = page.locator(".candidate-name");
  const answers = page.locator(".candidate-response");
  await names.nth(2).fill("Summit Max");
  await answers.nth(0).fill(Array.from({ length: 180 }, (_, index) => `Northstar line ${index + 1}`).join("\n"));
  await answers.nth(2).fill("A third complete fictional answer for the same task.");

  await page.getByRole("button", { name: "Start blind review" }).press("Enter");
  await expect(page.getByRole("heading", { name: "Which answer would you rather use?" })).toBeFocused();
  await expect(page.getByRole("status", { name: "" }).filter({ hasText: "Comparison 1 of 3" })).toBeVisible();

  const scrollableAnswers = page.locator(".answer-card pre");
  const longAnswer = (await scrollableAnswers.nth(0).evaluate((element) => element.scrollHeight > element.clientHeight))
    ? scrollableAnswers.nth(0)
    : scrollableAnswers.nth(1);
  await longAnswer.focus();
  await longAnswer.press("PageDown");
  await expect.poll(() => longAnswer.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);

  for (let comparison = 1; comparison <= 3; comparison += 1) {
    const vote = page.getByRole("button", { name: "Response A is better" });
    await vote.focus();
    await vote.press("Enter");
    if (comparison < 3) {
      await expect(page.getByRole("heading", { name: "Which answer would you rather use?" })).toBeFocused();
      await expect(page.locator("#review-progress")).toHaveText(`Comparison ${comparison + 1} of 3`);
    }
  }

  await expect(page.getByRole("heading", { name: "What this task supports." })).toBeFocused();
  await page.getByRole("button", { name: "Save to local history" }).press("Enter");
  await expect(page.getByRole("button", { name: "Save to local history" })).toBeDisabled();
  await expect(page.locator("#save-status")).toContainText("Saved in this browser");

  await page.getByRole("button", { name: "History", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Your own evidence, accumulated task by task." })).toBeFocused();
  await expect(page.locator("#history-trials")).toHaveText("1");
});

test("keeps controls visible to keyboard users and the page inside the mobile viewport", async ({ page }) => {
  await page.getByRole("button", { name: "History" }).click();
  const fileInput = page.locator("#import-history");
  await fileInput.focus();
  await expect(fileInput).toBeFocused();
  const outlineWidth = await fileInput.locator("..").evaluate((element) => getComputedStyle(element).outlineWidth);
  expect(Number.parseFloat(outlineWidth)).toBeGreaterThanOrEqual(3);

  const viewport = await page.evaluate(() => ({ document: document.documentElement.scrollWidth, window: innerWidth }));
  expect(viewport.document).toBeLessThanOrEqual(viewport.window);
  for (const step of await page.locator(".stepper li").all()) {
    expect(Number.parseFloat(await step.evaluate((element) => getComputedStyle(element).fontSize))).toBeGreaterThan(0);
  }
});

test("has no automatically detectable WCAG A or AA violations in key states", async ({ page }) => {
  await expectNoAutomatedWcagViolations(page);
  await page.getByRole("button", { name: "Load a fictional example" }).click();
  await page.getByRole("button", { name: "Start blind review" }).click();
  await expectNoAutomatedWcagViolations(page);
  await page.getByRole("button", { name: "History" }).click();
  await expectNoAutomatedWcagViolations(page);
});
