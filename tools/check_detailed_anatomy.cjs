#!/usr/bin/env node
// Functional and visual smoke check for source-mesh anatomy. Needs a running Primer.
// NODE_PATH=/path/to/bundled/node_modules node tools/check_detailed_anatomy.cjs URL
"use strict";
// Evidence uses a fresh private temporary directory; printed as EVIDENCE_DIRECTORY.
// Legacy output-directory argument (slot 3) is ignored; see docs/browser-qa.md.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");
const { createEvidenceDirectory, loopbackQaUrl } = require("./qa-browser.cjs");
const base = loopbackQaUrl(process.argv[2] || "http://127.0.0.1:56139");
const out = createEvidenceDirectory();
const source = JSON.parse(
  fs.readFileSync(
    path.resolve(__dirname, "../web/anatomy/bodyparts3d/manifest.json"),
    "utf8",
  ),
);
(async () => {

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1260, height: 1100 },
  });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(base + "/#/radiology");
  await page.locator("main").waitFor();
  if (!(await page.evaluate(() => !!window.PrimerDetailedAnatomy)))
    await page.addScriptTag({
      url: base + "/app/radiology-detailed-anatomy.js",
    });
  const results = [];
  for (const family of Object.keys(source.regions)) {
    await page.evaluate((f) => {
      document.querySelector(".detailed-anatomy")?.dispose();
      document
        .querySelector("main")
        .replaceChildren(window.PrimerDetailedAnatomy.render({ family: f }));
    }, family);
    const model = page.locator(".detailed-anatomy");
    await model
      .locator("canvas[data-rendered=true]")
      .waitFor({ timeout: 60000 });
    assert.equal(
      await model.getAttribute("data-error"),
      null,
      family + ": render failed",
    );
    const meshCount = await model.getAttribute("data-meshes");
    assert.equal(Number(meshCount), source.regions[family].parts.length);
    const visibleParts = await model.locator("[data-part]:visible").count();
    assert.equal(
      visibleParts,
      source.regions[family].parts.filter((p) => p.layer === "bone").length,
      family + ": layer filter",
    );
    const pixels = async () =>
      model.locator("canvas").evaluate((c) => {
        const gl = c.getContext("webgl");
        const a = new Uint8Array(c.width * c.height * 4);
        gl.readPixels(0, 0, c.width, c.height, gl.RGBA, gl.UNSIGNED_BYTE, a);
        let solid = 0;
        for (let i = 3; i < a.length; i += 4) if (a[i] > 0) solid++;
        return solid;
      });
    assert.ok((await pixels()) > 5000, family + ": empty rendering");
    const initial = await model
      .locator("canvas")
      .evaluate((c) => c.toDataURL());
    await model.getByRole("button", { name: "Posterior", exact: true }).click();
    await page.waitForFunction(() =>
      document
        .querySelector(".detailed-anatomy canvas")
        .dataset.view.startsWith("3.14"),
    );
    assert.notEqual(
      await model.locator("canvas").evaluate((c) => c.toDataURL()),
      initial,
      family + ": rotation changes view",
    );
    await model.getByRole("button", { name: "Anterior", exact: true }).click();
    await model.screenshot({ path: path.join(out, family + ".png") });
    await model
      .getByRole("button", {
        name: source.regions[family].labels[1],
        exact: true,
      })
      .click();
    await page.waitForFunction(
      () =>
        document.querySelector(".detailed-anatomy canvas").dataset.layer ===
        "soft",
    );
    assert.equal(
      await model.locator("[data-part]:visible").count(),
      source.regions[family].parts.filter((p) => p.layer === "soft").length,
    );
    assert.ok((await pixels()) > 500, family + ": soft-tissue rendering");
    await model.locator("[data-part]:visible").first().click();
    await model.getByRole("button", { name: "Isolate", exact: true }).click();
    assert.equal(
      await model
        .getByRole("button", { name: "Isolate", exact: true })
        .getAttribute("aria-pressed"),
      "true",
    );
    await model.getByRole("button", { name: "Together", exact: true }).click();
    await page.waitForFunction(
      () =>
        document.querySelector(".detailed-anatomy canvas").dataset.layer ===
        "all",
    );
    await model.screenshot({ path: path.join(out, family + "-combined.png") });
    results.push({
      family,
      meshCount: Number(meshCount),
      triangles: Number(await model.getAttribute("data-triangles")),
      rendered: true,
      controls: true,
    });
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => {
    document.querySelector(".detailed-anatomy")?.dispose();
    document
      .querySelector("main")
      .replaceChildren(
        window.PrimerDetailedAnatomy.render({ family: "shoulder" }),
      );
  });
  await page.locator(".detailed-anatomy canvas[data-rendered=true]").waitFor();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  assert.equal(overflow, false, "Mobile horizontal overflow");
  await page
    .locator(".detailed-anatomy")
    .screenshot({ path: path.join(out, "shoulder-mobile.png") });
  assert.equal(errors.length, 0, errors.join("\n"));
  fs.writeFileSync(
    path.join(out, "results.json"),
    JSON.stringify({ results, mobile: true, errors }, null, 2),
  );
  console.log(
    JSON.stringify({
      families: results.length,
      meshes: Object.keys(source.parts).length,
      bytes: Object.values(source.parts).reduce((n, p) => n + p.bytes, 0),
      mobile: true,
      errors,
    }),
  );
  await browser.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
