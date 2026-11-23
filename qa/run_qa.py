"""Browser QA for Delhi Bus Bheed (Phase 2 twin), run against a LOCAL
static server over the app/ folder — the same files that go into the
deploy zip.

Covers the interaction inventory's browser checks, plus two checks added
23 Nov 2026 after the Phase 2 demo recording exposed a real bug: a plain
mouse click on a stop node never opened its panel, because the board's
drag handler calls setPointerCapture on pointerdown and the browser then
delivers the click to the SVG instead of the node. The old suite only
ever selected nodes by keyboard / DOM events, so it missed this.

New checks use the REAL mouse (page.mouse), never DOM clicks:
  * real mouse click on a stop node's centre opens its panel;
  * real drag starting on a stop node pans the view and does NOT select.

Usage: python3 qa/run_qa.py   (exit 0 = all checks passed)
Writes qa/qa_results.json with per-check results.
"""
import functools
import http.server
import json
import os
import sys
import threading

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(HERE, "..", "app")
PORT = 8077
BASE = f"http://127.0.0.1:{PORT}/"

results = []


def check(name, ok, detail=""):
    results.append({"check": name, "pass": bool(ok), "detail": str(detail)})
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""), flush=True)
    return ok


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=APP_DIR)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    httpd.daemon_threads = True
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def node_index_by_name(page, name):
    return page.evaluate(
        "(name) => { const ns = document.querySelectorAll('#twinSvg g.node');"
        " for (let i = 0; i < ns.length; i++) {"
        "   const al = ns[i].getAttribute('aria-label') || '';"
        "   if (al.startsWith(name)) return i; } return -1; }", name)


def node_centre(page, idx):
    box = page.locator("#twinSvg g.node circle.core").nth(idx).bounding_box()
    assert box, f"node {idx} has no bounding box"
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


def hit_node_at(page, x, y):
    return page.evaluate(
        "([x, y]) => { const el = document.elementFromPoint(x, y);"
        " if (!el) return -1;"
        " const ns = document.querySelectorAll('#twinSvg g.node');"
        " for (let i = 0; i < ns.length; i++) if (ns[i].contains(el)) return i;"
        " return -1; }", [x, y])


def node_centre_visible(page, idx):
    """Scroll the node itself into view and wait until its centre is
    stable across two reads and a hit test really lands on this node
    (the page scrolls smoothly, so a fixed sleep races the scroll)."""
    page.locator("#twinSvg g.node").nth(idx).scroll_into_view_if_needed()
    prev = None
    for _ in range(16):
        page.wait_for_timeout(300)
        cx, cy = node_centre(page, idx)
        if prev and abs(cx - prev[0]) < 1 and abs(cy - prev[1]) < 1:
            hit = hit_node_at(page, cx, cy)
            if hit == idx:
                return cx, cy, hit
        prev = (cx, cy)
    cx, cy = node_centre(page, idx)
    return cx, cy, hit_node_at(page, cx, cy)


def pick_visible_node(page, exclude):
    """Index of a node whose core centre is currently inside the board's
    on-screen rect and really hit-testable, or -1. No scrolling needed."""
    return page.evaluate(
        "(exclude) => { const svg = document.querySelector('#twinSvg');"
        " const sr = svg.getBoundingClientRect();"
        " const ns = document.querySelectorAll('#twinSvg g.node');"
        " for (let i = 0; i < ns.length; i++) {"
        "   if (i === exclude) continue;"
        "   const r = ns[i].querySelector('circle.core').getBoundingClientRect();"
        "   const cx = r.x + r.width / 2, cy = r.y + r.height / 2;"
        "   if (cx < sr.x + 30 || cx > sr.right - 30 ||"
        "       cy < sr.y + 30 || cy > sr.bottom - 30) continue;"
        "   if (cx < 0 || cy < 0 || cx > innerWidth || cy > innerHeight) continue;"
        "   const el = document.elementFromPoint(cx, cy);"
        "   if (el && ns[i].contains(el)) return i; }"
        " return -1; }", exclude)


def board_into_view(page):
    page.locator("#twinSvg").scroll_into_view_if_needed()
    page.wait_for_timeout(900)


def main():
    httpd = serve()
    failures = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            ctx = browser.new_context(viewport={"width": 1280, "height": 720})
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            page.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

            resp = page.goto(BASE, wait_until="networkidle", timeout=60000)
            check("page loads over HTTP", resp and resp.status == 200, f"status={resp.status if resp else None}")
            page.wait_for_selector("#twinSvg g.node", timeout=30000)
            n = page.locator("#twinSvg g.node").count()
            check("twin board renders all stop nodes", n == 110, f"nodes={n}")
            label = page.locator(".sim-label").inner_text().strip()
            check("simulation label is honest (pattern, not live)",
                  label == "PATTERN SIMULATION · OCT 2026 E-TICKET DATA · NOT LIVE", label)

            # Play / pause the shared clock.
            board_into_view(page)
            t0 = page.locator("#clockTime").inner_text().strip()
            page.locator("#playBtn").click()
            page.wait_for_timeout(3200)
            t1 = page.locator("#clockTime").inner_text().strip()
            check("Play the day advances the simulated hour", t1 != t0, f"{t0} -> {t1}")
            page.locator("#playBtn").click()  # Pause
            page.wait_for_timeout(400)
            t2 = page.locator("#clockTime").inner_text().strip()
            page.wait_for_timeout(1600)
            t3 = page.locator("#clockTime").inner_text().strip()
            check("Pause stops the simulated hour", t2 == t3, f"held at {t3}")

            # NEW: real mouse click on the busiest stop node opens its panel.
            busiest = page.locator("#bsBusiest").inner_text().strip()
            idx = node_index_by_name(page, busiest)
            check("busiest stop has a node on the board", idx >= 0, f"{busiest} -> node {idx}")
            cx, cy, hit = node_centre_visible(page, idx)
            check("mouse point really lands on the busiest node", hit == idx,
                  f"elementFromPoint -> node {hit}")
            page.mouse.click(cx, cy)  # real mouse: down+up, no DOM events
            try:
                page.wait_for_selector("#stopPanel.open", timeout=6000)
                opened = True
            except Exception:
                opened = False
            check("NEW: real mouse click on a stop node opens its panel", opened)
            heading = page.locator("#stopPanel h3").inner_text().strip() if opened else ""
            check("NEW: mouse-clicked panel shows that stop", heading == busiest, heading)
            routes = page.locator("#stopPanel .sp-route").count() if opened else 0
            check("stop panel lists routes from the stop", routes > 0, f"{routes} route buttons")

            # Keyboard path still works (regression).
            board_into_view(page)
            other = page.locator("#twinSvg g.node").nth(5)
            other_name = (other.get_attribute("aria-label") or "").split(" — ")[0].split(" at ")[0]
            other.focus()
            page.keyboard.press("Enter")
            page.wait_for_timeout(1200)
            heading = page.locator("#stopPanel h3").inner_text().strip()
            check("keyboard Enter on a node still opens its panel", heading == other_name, heading)

            # Zoom in, then NEW: a real drag that starts on a node must pan
            # the view and must NOT select that node.
            board_into_view(page)
            page.locator("#zoomIn").click()
            page.wait_for_timeout(800)
            vb_zoom = page.locator("#twinSvg").get_attribute("viewBox")
            check("zoom + changes the viewBox", vb_zoom != "0 0 1160 640", vb_zoom)
            sel_before = page.locator("#stopSelect").input_value()
            drag_idx = pick_visible_node(page, int(sel_before))
            check("a stop node is on screen to start the drag on", drag_idx >= 0,
                  f"node {drag_idx}")
            dx, dy = node_centre(page, drag_idx)
            dhit = hit_node_at(page, dx, dy)
            check("drag start point really lands on a node", dhit == drag_idx,
                  f"elementFromPoint -> node {dhit}")
            page.mouse.move(dx, dy)
            page.mouse.down()
            for i in range(1, 11):
                page.mouse.move(dx + i * 14, dy + i * 7)
                page.wait_for_timeout(40)
            page.mouse.up()
            page.wait_for_timeout(800)
            vb_after = page.locator("#twinSvg").get_attribute("viewBox")
            sel_after = page.locator("#stopSelect").input_value()
            check("NEW: real drag starting on a node pans the view", vb_after != vb_zoom,
                  f"{vb_zoom} -> {vb_after}")
            check("NEW: that drag does NOT select the node", sel_after == sel_before,
                  f"selection stayed stop #{sel_before}")
            page.locator("#zoomReset").click()
            page.wait_for_timeout(800)
            vb_reset = page.locator("#twinSvg").get_attribute("viewBox")
            check("zoom reset restores the full board exactly", vb_reset == "0 0 1160 640", vb_reset)

            # Stop select dropdown.
            board_into_view(page)
            page.select_option("#stopSelect", index=10)
            page.wait_for_timeout(1000)
            sel_name = page.evaluate(
                "() => document.querySelector('#stopSelect')"
                ".selectedOptions[0].textContent.split(' — ')[0]")
            heading = page.locator("#stopPanel h3").inner_text().strip()
            check("stop select dropdown opens that stop's panel", heading == sel_name.strip(), heading)

            # Planner: search and load route 717A.
            page.locator("#planner").scroll_into_view_if_needed()
            page.wait_for_timeout(800)
            page.locator("#routeSearch").click()
            page.keyboard.press("Control+a")
            page.keyboard.press("Backspace")
            page.locator("#routeSearch").press_sequentially("717A", delay=60)
            page.wait_for_selector("#routeResults .route-option", timeout=10000)
            page.locator("#routeResults .route-option", has_text="717A").first.click()
            page.wait_for_function(
                "() => document.querySelector('#routeMeta').textContent.includes('717A')",
                timeout=15000)
            meta = page.locator("#routeMeta").inner_text().strip()
            check("route search loads route 717A", "717A" in meta, meta[:60])

            # 9 AM curve bar -> verdict.
            page.locator("#resultInner").scroll_into_view_if_needed()
            page.wait_for_timeout(600)
            page.locator("#curveSvg rect.bar").nth(9).click()
            page.wait_for_function(
                "() => document.querySelector('#hourBig').textContent.trim() === '9 AM'",
                timeout=10000)
            band = page.locator("#bandName").inner_text().strip()
            check("9 AM verdict for 717A is its peak band", band == "Bahut bheed", band)

            # What-if.
            page.locator("#whatifBox").scroll_into_view_if_needed()
            page.wait_for_timeout(600)
            page.locator("#whatifRun").click()
            page.wait_for_selector("#wiResults table tbody tr", timeout=15000)
            rows = page.locator("#wiResults table tbody tr").count()
            check("what-if shares the load across routes", rows == 6, f"{rows} load-taking routes")

            # Low-motion toggle.
            page.locator("#twin").scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            page.locator("#motionToggle").click()
            page.wait_for_timeout(400)
            lm = page.evaluate("() => document.body.classList.contains('low-motion')")
            check("low-motion toggle turns low-motion on", lm)
            page.locator("#motionToggle").click()
            page.wait_for_timeout(400)
            lm = page.evaluate("() => document.body.classList.contains('low-motion')")
            check("low-motion toggle turns it back off", not lm)

            check("zero console errors (desktop)", len(errors) == 0, "; ".join(errors[:3]))
            ctx.close()

            # Mobile: tap (touch pointer) on a node opens its panel too.
            mctx = browser.new_context(viewport={"width": 390, "height": 844},
                                       has_touch=True, is_mobile=True)
            mpage = mctx.new_page()
            merrors = []
            mpage.on("pageerror", lambda e: merrors.append("pageerror: " + str(e)))
            mpage.on("console", lambda m: merrors.append("console: " + m.text) if m.type == "error" else None)
            mpage.goto(BASE, wait_until="networkidle", timeout=60000)
            mpage.wait_for_selector("#twinSvg g.node", timeout=30000)
            check("mobile: board renders on a phone viewport",
                  mpage.locator("#twinSvg g.node").count() == 110)
            mpage.locator("#twinSvg").scroll_into_view_if_needed()
            mpage.wait_for_timeout(900)
            mbusiest = mpage.locator("#bsBusiest").inner_text().strip()
            midx = node_index_by_name(mpage, mbusiest)
            mcx, mcy, mhit = node_centre_visible(mpage, midx)
            mpage.touchscreen.tap(mcx, mcy)
            try:
                mpage.wait_for_selector("#stopPanel.open", timeout=6000)
                mopened = True
            except Exception:
                mopened = False
            mheading = mpage.locator("#stopPanel h3").inner_text().strip() if mopened else ""
            check("mobile: touch tap on a stop node opens its panel",
                  mopened and mheading == mbusiest, mheading)
            check("zero console errors (mobile)", len(merrors) == 0, "; ".join(merrors[:3]))
            mctx.close()
            browser.close()
    finally:
        httpd.shutdown()

    failures = sum(1 for r in results if not r["pass"])
    out = {"total": len(results), "passed": len(results) - failures,
           "failed": failures, "results": results}
    with open(os.path.join(HERE, "qa_results.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nQA: {out['passed']}/{out['total']} passed, {failures} failed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
