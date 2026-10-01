// Finds Config.Street.StageFactor[n] so that every stage of the street tycoon takes its target time (active player), using
// docs/economy/street_sim. Stage n = from buying Shiba n to buying Shiba n + 1. Run from the repo root:
//   node docs/tools/calibrate_street.js [D1=8] [DG=1.17] [LAST=29] [KEY=VALUE ...]
// D1 = minutes of stages 1 to 3, DG = every later stage takes this much longer, KEY=VALUE = constants for the sim (BAY_SECONDS=300 ...).
// Prints the factors; paste them into Street.StageFactor in src/shared/Config/Tycoon.luau. The result is also kept in street_factors.json
// (delete it to start over, keep it to resume).
const { execSync } = require("child_process");
const fs = require("fs");
process.env.PATH += ";" + process.env.USERPROFILE + "\\.rokit\\bin";
const OUT = "street_factors.json";
const extra = Object.fromEntries(process.argv.slice(2).map(a => a.split("=")));
const MIN_FIRST = Number(extra.D1 || 8); // minutes of the first three stages
const GROWTH = Number(extra.DG || 1.17); // each later stage takes this much longer
const LAST = Number(extra.LAST || 29);
delete extra.D1;
delete extra.DG;
delete extra.LAST;
const target = n => (n <= 3 ? MIN_FIRST : MIN_FIRST * Math.pow(GROWTH, n - 3)) * 60;

function stageSeconds(factors, n) {
  const env = {
    ...process.env,
    PLAYER: "active",
    RESULT: "1",
    STOP_BAY: String(n + 1),
    FACTORS: factors.join(","),
    MAX_HOURS: "100000",
    ...extra,
  };
  const out = execSync("lune run docs/economy/street_sim", { env, encoding: "utf8", timeout: 1800000, maxBuffer: 1 << 26 });
  const times = {};
  for (const m of out.matchAll(/BAYTIME (\d+) ([0-9.e+]+)/g)) times[Number(m[1])] = Number(m[2]);
  if (times[n + 1] === undefined) return null;
  return times[n + 1] - times[n];
}

let factors = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, "utf8")) : [];
for (let n = factors.length + 1; n <= LAST; n++) {
  const goal = target(n);
  let x = Math.log(factors.length ? factors[factors.length - 1] * 1.2 : 1);
  let prev = null;
  let best = null;
  for (let iter = 0; iter < 9; iter++) {
    const f = Math.exp(x);
    const d = stageSeconds([...factors, f], n);
    if (d === null) {
      console.log(`stage ${n}: no result at factor ${f}`);
      x += 1;
      continue;
    }
    const y = Math.log(d / goal);
    console.log(`stage ${n} iter ${iter}: factor ${f.toPrecision(4)} -> ${(d / 60).toFixed(1)} min (target ${(goal / 60).toFixed(1)})`);
    if (!best || Math.abs(y) < Math.abs(best.y)) best = { f, y, d };
    if (Math.abs(y) < 0.04) break;
    let slope = 0.8;
    if (prev && Math.abs(x - prev.x) > 1e-6) {
      const s = (y - prev.y) / (x - prev.x);
      if (s > 0.2 && s < 3) slope = s;
    }
    prev = { x, y };
    x = x - y / slope;
  }
  factors.push(best.f);
  fs.writeFileSync(OUT, JSON.stringify(factors));
  console.log(`== stage ${n} done: factor ${best.f.toPrecision(5)} (${(best.d / 60).toFixed(1)} min)`);
}
console.log("FACTORS=" + factors.map(f => Number(f.toPrecision(4))).join(","));
