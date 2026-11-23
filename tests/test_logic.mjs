/* Unit tests for the page's pure logic block (<script id="logic"> in
   app/index.html), run against the real shipped data files.
   Run: node tests/test_logic.mjs   (from the project root) */
import { readFileSync } from "node:fs";
import assert from "node:assert";

const html = readFileSync(new URL("../app/index.html", import.meta.url), "utf8");
const m = html.match(/<script id="logic">([\s\S]*?)<\/script>/);
assert.ok(m, "logic script block not found in index.html");
const BheedLogic = new Function(m[1] + "; return BheedLogic;")();
const L = BheedLogic;

const twin = JSON.parse(readFileSync(new URL("../app/twin.json", import.meta.url), "utf8"));
const crowd = JSON.parse(readFileSync(new URL("../app/crowdedness.json", import.meta.url), "utf8"));
const routeBands = {};
for (const r of Object.keys(crowd.routes)) routeBands[r] = crowd.routes[r].bands;

let passed = 0;
function test(name, fn) { fn(); passed++; console.log("ok -", name); }

/* The JS band rule must reproduce Phase 1's shipped bands for every route —
   the same pin the Python tests apply to the model. */
test("bandString reproduces Phase 1 bands for all 1,249 routes", () => {
  for (const r of Object.keys(crowd.routes)) {
    assert.equal(L.bandString(twin.route_hours[r]), crowd.routes[r].bands, r);
  }
});

test("bandString of the city peaks at 9 AM in the top band", () => {
  assert.equal(L.bandString(twin.city_hours).charAt(9), "B");
});

test("bestWindows finds the quiet runs of a known band string", () => {
  const wins = L.bestWindows("BBKKKKKKAAAAAAAAKKKKKKKK".slice(0, 24));
  assert.ok(wins.length >= 1);
  assert.equal(wins[0].len, 8);
  assert.equal(wins[0].start, 8);
  // every route's bands contain exactly 8 A's -> at least one window
  assert.ok(L.bestWindows(crowd.routes["717A"].bands).length >= 1);
});

test("nearestQuieter keeps Phase 1 behaviour on 717A at 9 AM", () => {
  const s = L.nearestQuieter(crowd.routes["717A"].bands, 9,
    { B: "Bahut bheed", K: "Khadi bheed", A: "Aaram se seat milegi" });
  assert.equal(s.good, true);
  assert.equal(s.title, "A quieter time nearby");
});

test("compareHours: 717A at 9 AM has a calmer later hour with fewer boardings", () => {
  const cmp = L.compareHours(twin.route_hours["717A"], crowd.routes["717A"].bands, 9);
  assert.ok(cmp);
  assert.ok(L.RANK[cmp.bestBand] < L.RANK[cmp.nowBand]);
  assert.ok(cmp.bestBoardings < cmp.nowBoardings);
  assert.ok(cmp.dropPct > 0);
});

test("compareHours returns null in the quietest band", () => {
  const bands = crowd.routes["717A"].bands;
  const aHour = bands.indexOf("A");
  assert.equal(L.compareHours(twin.route_hours["717A"], bands, aHour), null);
});

test("routesFromStop sorts quietest first and uses real stop data", () => {
  const stop = twin.stops[0];
  const rows = L.routesFromStop(stop, 9, routeBands);
  assert.ok(rows.length > 0);
  for (let i = 1; i < rows.length; i++) {
    assert.ok(L.RANK[rows[i - 1].band] <= L.RANK[rows[i].band], "not sorted by band rank");
  }
  for (const r of rows) assert.equal(r.atStop, stop.routes.find(x => x.route === r.route).hours[9]);
});

test("redistribute conserves boardings (717A @ 9, 764 @ 18, 729 @ 8)", () => {
  for (const [route, hour] of [["717A", 9], ["764", 18], ["729", 8]]) {
    const res = L.redistribute({ route, stops: twin.whatif[route].stops },
      twin.route_hours, routeBands, hour);
    assert.equal(res.total, twin.route_hours[route][hour]);
    const movedSum = res.rows.reduce((t, r) => t + r.extra, 0);
    assert.ok(Math.abs(movedSum - res.moved) < 1e-6, "rows do not add up to moved");
    assert.ok(Math.abs(res.moved + res.unassigned + res.rest - res.total) < 1e-6,
      `${route}@${hour}: moved+unassigned+rest != total`);
    assert.ok(res.rows.length > 0, "no route takes any load");
    for (const r of res.rows) {
      assert.equal(r.before, twin.route_hours[r.route][hour]);
      assert.ok(Math.abs(r.after - (r.before + r.extra)) < 1e-6);
      assert.equal(r.bandBefore, routeBands[r.route].charAt(hour));
    }
  }
});

test("redistribute: 717A's load really lands on its sibling routes", () => {
  const res = L.redistribute({ route: "717A", stops: twin.whatif["717A"].stops },
    twin.route_hours, routeBands, 9);
  const names = res.rows.map(r => r.route);
  assert.ok(names.includes("717B") || names.includes("717"),
    "expected a 717-family alternative among load takers, got " + names.join(","));
});

test("bandAfterLoad can push a quiet hour into a busier band", () => {
  const hours = twin.route_hours["764"];
  const before = L.bandAt(hours, 3);           // 3 AM: quiet for 764
  const after = L.bandAfterLoad(hours, 3, 100000);
  assert.equal(before, "A");
  assert.equal(after, "B");
});

console.log(`\n${passed} logic tests passed`);
