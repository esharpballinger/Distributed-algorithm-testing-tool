"""
File: mis_visualization.py
Description: runs the MIS simulation while recording every round (node statuses
             and all messages exchanged) and renders the run as a self-contained
             HTML page (SVG + vanilla JS, no dependencies)
Author: Evan Sharp-Ballinger and Gonzalo Estrella
"""

import json

from src.supervisor import Supervisor
from src.maximal_independent_set import Status


def snapshot(nodes):
    return [node.data.value for node in nodes]


def run_with_history(algorithm):
    """
    Run the simulation round by round, capturing node statuses before the first
    round and after each round, plus every message sent in each round.
    Returns (supervisor, history, messages) where messages[k] is the list of
    messages delivered during round k+1, each as
    {"from": sender, "to": receiver, "status": ..., "rank": ...}.
    """
    supervisor = Supervisor(algorithm.nodes, algorithm)
    history = [snapshot(algorithm.nodes)]
    messages = []
    while not algorithm.is_goal_met(algorithm.nodes):
        supervisor.run_round()
        # messages_queue still holds this round's traffic after run_round
        messages.append([
            {
                "from": m.sender,
                "to": m.receiver,
                "status": m.payload[0].value,
                "rank": m.payload[1],
            }
            for m in supervisor.messages_queue
        ])
        history.append(snapshot(algorithm.nodes))
    return supervisor, history, messages


def _checks(algorithm):
    in_set = {node.id for node in algorithm.nodes if node.data is Status.IN_MIS}
    independent = all(not (algorithm.graph[v] & in_set) for v in in_set)
    maximal = all(
        algorithm.graph[v] & in_set for v in range(algorithm.n) if v not in in_set
    )
    return in_set, {
        "independent": independent,
        "maximal": maximal,
        "matches_greedy": in_set == algorithm.expected_mis,
    }


def render_html(algorithm, history, messages) -> str:
    in_set, checks = _checks(algorithm)
    run = {
        "n": algorithm.n,
        "seed": algorithm.seed,
        "rounds": len(history),
        "statuses": history,
        "messages": messages,
        "ranks": algorithm.ranks,
        "edges": sorted(
            [u, v] for u in algorithm.graph for v in algorithm.graph[u] if u < v
        ),
        "mis": sorted(in_set),
        "checks": checks,
    }
    return _TEMPLATE.replace("__RUN_DATA__", json.dumps(run))


def write_html(algorithm, history, messages, output_path) -> None:
    with open(output_path, "w") as f:
        f.write(render_html(algorithm, history, messages))


_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Greedy Randomized MIS - simulation run</title>
<style>
  body { font-family: -apple-system, "Segoe UI", sans-serif; margin: 2rem auto; max-width: 1000px; color: #222; }
  h1 { font-size: 1.3rem; }
  .meta, .legend { color: #555; font-size: 0.9rem; margin: 0.3rem 0; }
  .legend span { display: inline-block; margin-right: 1.1rem; }
  .dot { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 4px; vertical-align: -1px; }
  .bar { display: inline-block; width: 16px; height: 4px; margin-right: 4px; vertical-align: 3px; }
  .controls { margin: 1rem 0; }
  button { font-size: 1rem; padding: 0.35rem 1rem; margin-right: 0.5rem; cursor: pointer; }
  #round-label { font-weight: 600; margin-left: 0.5rem; }
  .panel { display: flex; gap: 1rem; align-items: flex-start; }
  svg { border: 1px solid #ddd; border-radius: 8px; background: #fafafa; flex: 1 1 640px; height: auto; }
  #log { flex: 0 0 280px; border: 1px solid #ddd; border-radius: 8px; padding: 0.6rem 0.9rem; font-size: 0.85rem; max-height: 560px; overflow-y: auto; }
  #log h2 { font-size: 0.95rem; margin: 0 0 0.4rem; }
  #log div { padding: 1px 0; font-family: "SF Mono", Menlo, monospace; }
  .m-rank { color: #4a7fb5; }
  .m-in { color: #2e9e46; font-weight: 600; }
  .m-out { color: #c0392b; }
  #verdict { margin-top: 1rem; padding: 0.6rem 1rem; border-radius: 6px; font-weight: 600; }
  .pass { background: #e6f6e6; color: #1a7f1a; }
  .fail { background: #fdeaea; color: #b30000; }
</style>
</head>
<body>
<h1>Greedy Randomized Maximal Independent Set</h1>
<div class="meta" id="meta"></div>
<div class="legend">
  <span><span class="dot" style="background:#9e9e9e"></span>undecided</span>
  <span><span class="dot" style="background:#2e9e46"></span>in MIS</span>
  <span><span class="dot" style="background:#e0e0e0; border:1px solid #bbb"></span>out</span>
  <span><span class="bar" style="background:#4a7fb5"></span>rank message &pi;</span>
  <span><span class="bar" style="background:#2e9e46"></span>"joined MIS"</span>
  <span><span class="bar" style="background:#c0392b"></span>"I'm out"</span>
</div>
<div class="controls">
  <button id="prev">&#8592; Prev</button>
  <button id="next">Next &#8594;</button>
  <button id="play">Play</button>
  <span id="round-label"></span>
</div>
<div class="panel">
  <svg id="graph" viewBox="0 0 720 600"></svg>
  <div id="log"><h2>Messages this round</h2><div id="log-body"></div></div>
</div>
<div id="verdict"></div>
<script>
const RUN = __RUN_DATA__;

const svg = document.getElementById("graph");
const W = 720, H = 600, R = Math.min(W, H) / 2 - 80;
const pos = [];
for (let i = 0; i < RUN.n; i++) {
  const a = 2 * Math.PI * i / RUN.n - Math.PI / 2;
  pos.push([W / 2 + R * Math.cos(a), H / 2 + R * Math.sin(a)]);
}

const NS = "http://www.w3.org/2000/svg";
function el(tag, attrs, text) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (text !== undefined) e.textContent = text;
  return e;
}

// arrowhead markers, one per message type
const MSG_COLORS = { undecided: "#4a7fb5", in_mis: "#2e9e46", out: "#c0392b" };
const defs = el("defs", {});
for (const type in MSG_COLORS) {
  const marker = el("marker", {
    id: "arrow-" + type, viewBox: "0 0 10 10", refX: 9, refY: 5,
    markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse"
  });
  marker.appendChild(el("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: MSG_COLORS[type] }));
  defs.appendChild(marker);
}
svg.appendChild(defs);

for (const [u, v] of RUN.edges) {
  svg.appendChild(el("line", {
    x1: pos[u][0], y1: pos[u][1], x2: pos[v][0], y2: pos[v][1],
    stroke: "#d5d5d5", "stroke-width": 1.5, id: "edge-" + u + "-" + v
  }));
}

// message layer sits above edges, below nodes
const msgLayer = el("g", { id: "msg-layer" });
svg.appendChild(msgLayer);

const circles = [];
for (let i = 0; i < RUN.n; i++) {
  const c = el("circle", { cx: pos[i][0], cy: pos[i][1], r: 22, stroke: "#666", "stroke-width": 1.5 });
  svg.appendChild(c);
  circles.push(c);
  svg.appendChild(el("text", {
    x: pos[i][0], y: pos[i][1] + 5, "text-anchor": "middle",
    "font-size": 15, "font-weight": 600
  }, i));
  svg.appendChild(el("text", {
    x: pos[i][0], y: pos[i][1] - 30, "text-anchor": "middle",
    "font-size": 11, fill: "#777"
  }, "\\u03c0=" + RUN.ranks[i]));
}

const NODE_COLORS = { undecided: "#9e9e9e", in_mis: "#2e9e46", out: "#e0e0e0" };
let frame = 0, timer = null;

function msgLabel(m) {
  if (m.status === "undecided") return "\\u03c0=" + m.rank;
  return m.status === "in_mis" ? "IN" : "OUT";
}

function drawMessages(batch) {
  msgLayer.replaceChildren();
  for (const m of batch) {
    const [x1, y1] = pos[m.from], [x2, y2] = pos[m.to];
    const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy);
    const ux = dx / len, uy = dy / len;          // along the edge
    const px = -uy, py = ux;                     // perpendicular offset so both directions show
    const off = 7;
    const sx = x1 + ux * 26 + px * off, sy = y1 + uy * 26 + py * off;
    const ex = x2 - ux * 30 + px * off, ey = y2 - uy * 30 + py * off;
    const color = MSG_COLORS[m.status];
    msgLayer.appendChild(el("line", {
      x1: sx, y1: sy, x2: ex, y2: ey, stroke: color, "stroke-width": 2,
      "marker-end": "url(#arrow-" + m.status + ")"
    }));
    msgLayer.appendChild(el("text", {
      x: sx + (ex - sx) * 0.45 + px * 10, y: sy + (ey - sy) * 0.45 + py * 10,
      "text-anchor": "middle", "font-size": 10.5, fill: color, "font-weight": 600
    }, msgLabel(m)));
  }
}

function drawLog(batch) {
  const body = document.getElementById("log-body");
  body.replaceChildren();
  if (!batch.length) {
    const d = document.createElement("div");
    d.textContent = frame === 0 ? "initial state - nothing sent yet" : "no messages";
    body.appendChild(d);
    return;
  }
  for (const m of batch) {
    const d = document.createElement("div");
    d.className = m.status === "undecided" ? "m-rank" : (m.status === "in_mis" ? "m-in" : "m-out");
    const what = m.status === "undecided" ? "rank \\u03c0=" + m.rank
               : m.status === "in_mis" ? "\\u201cI joined the MIS\\u201d"
               : "\\u201cI\\u2019m out\\u201d";
    d.textContent = m.from + " \\u2192 " + m.to + " : " + what;
    body.appendChild(d);
  }
}

function draw() {
  const statuses = RUN.statuses[frame];
  statuses.forEach((s, i) => {
    circles[i].setAttribute("fill", NODE_COLORS[s]);
    circles[i].setAttribute("opacity", s === "out" ? 0.55 : 1);
  });
  const batch = frame === 0 ? [] : RUN.messages[frame - 1];
  drawMessages(batch);
  drawLog(batch);
  document.getElementById("round-label").textContent =
    frame === 0
      ? "initial state"
      : "round " + frame + " / " + (RUN.rounds - 1) + "  (" + batch.length + " message" + (batch.length === 1 ? "" : "s") + ")";
}

document.getElementById("prev").onclick = () => { frame = Math.max(0, frame - 1); draw(); };
document.getElementById("next").onclick = () => { frame = Math.min(RUN.rounds - 1, frame + 1); draw(); };
document.getElementById("play").onclick = function () {
  if (timer) { clearInterval(timer); timer = null; this.textContent = "Play"; return; }
  frame = 0; draw();
  this.textContent = "Stop";
  timer = setInterval(() => {
    if (frame >= RUN.rounds - 1) { clearInterval(timer); timer = null; document.getElementById("play").textContent = "Play"; return; }
    frame++; draw();
  }, 1400);
};

document.getElementById("meta").textContent =
  "n = " + RUN.n + "   |   seed = " + RUN.seed + "   |   finished in " + (RUN.rounds - 1) +
  " round(s)   |   MIS = {" + RUN.mis.join(", ") + "}";

const ok = RUN.checks.independent && RUN.checks.maximal && RUN.checks.matches_greedy;
const verdict = document.getElementById("verdict");
verdict.className = ok ? "pass" : "fail";
verdict.textContent = (ok ? "\\u2713 " : "\\u2717 ") +
  "independent: " + RUN.checks.independent +
  "   |   maximal: " + RUN.checks.maximal +
  "   |   matches sequential greedy: " + RUN.checks.matches_greedy;

draw();
</script>
</body>
</html>
"""
