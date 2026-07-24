"""
File: mis_visualization.py
Description: runs the MIS simulation while recording every round and renders the
             run as a self-contained HTML page (SVG + vanilla JS, no dependencies)
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
    round and after each round. Returns (supervisor, history).
    """
    supervisor = Supervisor(algorithm.nodes, algorithm)
    history = [snapshot(algorithm.nodes)]
    while not algorithm.is_goal_met(algorithm.nodes):
        supervisor.run_round()
        history.append(snapshot(algorithm.nodes))
    return supervisor, history


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


def render_html(algorithm, history) -> str:
    in_set, checks = _checks(algorithm)
    run = {
        "n": algorithm.n,
        "seed": algorithm.seed,
        "rounds": len(history),
        "statuses": history,
        "ranks": algorithm.ranks,
        "edges": sorted(
            [u, v] for u in algorithm.graph for v in algorithm.graph[u] if u < v
        ),
        "mis": sorted(in_set),
        "checks": checks,
    }
    return _TEMPLATE.replace("__RUN_DATA__", json.dumps(run))


def write_html(algorithm, history, output_path) -> None:
    with open(output_path, "w") as f:
        f.write(render_html(algorithm, history))


_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Greedy Randomized MIS - simulation run</title>
<style>
  body { font-family: -apple-system, "Segoe UI", sans-serif; margin: 2rem auto; max-width: 860px; color: #222; }
  h1 { font-size: 1.3rem; }
  .meta, .legend { color: #555; font-size: 0.9rem; margin: 0.3rem 0; }
  .legend span { display: inline-block; margin-right: 1.2rem; }
  .dot { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 4px; vertical-align: -1px; }
  .controls { margin: 1rem 0; }
  button { font-size: 1rem; padding: 0.35rem 1rem; margin-right: 0.5rem; cursor: pointer; }
  #round-label { font-weight: 600; margin-left: 0.5rem; }
  #verdict { margin-top: 1rem; padding: 0.6rem 1rem; border-radius: 6px; font-weight: 600; }
  .pass { background: #e6f6e6; color: #1a7f1a; }
  .fail { background: #fdeaea; color: #b30000; }
  svg { border: 1px solid #ddd; border-radius: 8px; background: #fafafa; width: 100%; height: auto; }
</style>
</head>
<body>
<h1>Greedy Randomized Maximal Independent Set</h1>
<div class="meta" id="meta"></div>
<div class="legend">
  <span><span class="dot" style="background:#9e9e9e"></span>undecided</span>
  <span><span class="dot" style="background:#2e9e46"></span>in MIS</span>
  <span><span class="dot" style="background:#e0e0e0; border:1px solid #bbb"></span>out</span>
  <span>number inside node = id, small label = rank in &pi;</span>
</div>
<div class="controls">
  <button id="prev">&#8592; Prev</button>
  <button id="next">Next &#8594;</button>
  <button id="play">Play</button>
  <span id="round-label"></span>
</div>
<svg id="graph" viewBox="0 0 800 600"></svg>
<div id="verdict"></div>
<script>
const RUN = __RUN_DATA__;

const svg = document.getElementById("graph");
const W = 800, H = 600, R = Math.min(W, H) / 2 - 70;
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

for (const [u, v] of RUN.edges) {
  svg.appendChild(el("line", {
    x1: pos[u][0], y1: pos[u][1], x2: pos[v][0], y2: pos[v][1],
    stroke: "#c9c9c9", "stroke-width": 2, id: "edge-" + u + "-" + v
  }));
}

const circles = [], labels = [];
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

const COLORS = { undecided: "#9e9e9e", in_mis: "#2e9e46", out: "#e0e0e0" };
let round = 0, timer = null;

function draw() {
  const statuses = RUN.statuses[round];
  statuses.forEach((s, i) => {
    circles[i].setAttribute("fill", COLORS[s]);
    circles[i].setAttribute("opacity", s === "out" ? 0.55 : 1);
  });
  for (const [u, v] of RUN.edges) {
    const active = statuses[u] === "undecided" && statuses[v] === "undecided";
    document.getElementById("edge-" + u + "-" + v)
      .setAttribute("stroke", active ? "#8fb4d9" : "#dddddd");
  }
  document.getElementById("round-label").textContent =
    round === 0 ? "initial state" : "after round " + round + " / " + (RUN.rounds - 1);
}

document.getElementById("prev").onclick = () => { round = Math.max(0, round - 1); draw(); };
document.getElementById("next").onclick = () => { round = Math.min(RUN.rounds - 1, round + 1); draw(); };
document.getElementById("play").onclick = function () {
  if (timer) { clearInterval(timer); timer = null; this.textContent = "Play"; return; }
  round = 0; draw();
  this.textContent = "Stop";
  timer = setInterval(() => {
    if (round >= RUN.rounds - 1) { clearInterval(timer); timer = null; document.getElementById("play").textContent = "Play"; return; }
    round++; draw();
  }, 900);
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
