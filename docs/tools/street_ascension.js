// Ascension check of the STREET economy (docs/economy/BALANCING.md → Ascension in the street mode). Reuses the simulation of
// docs/tools/street_retention.js and reads the rule from the real Config files:
//   Config/Tycoon.luau Ascension  PerAscension, StreetFirstShiba, StreetShibaStep   (Shiba needed for Ascension n = First + Step * n, max Bays)
//   Config/EconomyConfig.luau     StreetOfflineShare, StreetOfflineSeconds
//   node docs/tools/street_ascension.js                 -- active player (EFF 0.5)
//   EFF=0.35 node docs/tools/street_ascension.js        -- slower player
//   RUNS=10 node docs/tools/street_ascension.js         -- how many runs to print (default 8)
// Each run starts fresh (what the server does: no Shibas, no steps, no money) with the income multiplier 1 + PerAscension * n and
// plays until the Shiba number the next Ascension needs is bought. Prints the time of the run, the Shiba needed and the factor
// against run 1. Active = clicks half of the time until the first Intern (as street_sim), then the Interns pay.
const fs = require("fs");
const path = require("path");
const { make } = require("./street_retention.js");
const ROOT = process.env.REPO || path.join(__dirname, "..", "..");
const read = f => fs.readFileSync(path.join(ROOT, "src/shared/Config", f), "utf8");
const num = (txt, key) => {
  const m = txt.match(new RegExp("\\b" + key + " = ([0-9.e+-]+)"));
  if (!m) throw new Error("missing " + key);
  return Number(m[1]);
};
const tycoon = read("Tycoon.luau");
const asc = tycoon.slice(tycoon.indexOf("Ascension = {"));
const PER = num(asc, "PerAscension"), FIRST = num(asc, "StreetFirstShiba"), STEP = num(asc, "StreetShibaStep");
const BAYS = num(tycoon.slice(tycoon.lastIndexOf("Street = {")), "Bays");
const eco = read("EconomyConfig.luau");
const SHARE = num(eco, "StreetOfflineShare"), CAPS = num(eco, "StreetOfflineSeconds");
const eff = Number(process.env.EFF || 0.5);
const runs = Number(process.env.RUNS || 8);
const f = t => (t < 5400 ? (t / 60).toFixed(0) + " min" : (t / 3600).toFixed(2) + " h");

console.log(`street ascension check (click efficiency ${eff}; multiplier 1 + ${PER} n; Shiba needed = ${FIRST} + ${STEP} n, max ${BAYS})`);
console.log("| Run | Ascensions done | Income multiplier | Shiba needed to ascend | Time of the run | vs run 1 | Time of Shiba 2 (this run) |");
console.log("|---|---|---|---|---|---|---|");
let first = 0;
for (let n = 0; n < runs; n++) {
  const need = Math.min(BAYS, FIRST + STEP * n);
  const mult = 1 + PER * n;
  const S = make({}, { clickEff: eff, mult, stopBay: need });
  const st = S.newState();
  const ev = [];
  S.run(false, st, 0, 0, 40 * 3600, ev, true);
  const bays = ev.filter(e => e.kind === "bay");
  const reached = st.shibas.length;
  const t = bays.length ? bays[bays.length - 1].t : NaN;
  if (n === 0) first = t;
  const second = bays.find(e => e.bay === 2);
  console.log(`| ${n + 1} | ${n} | x${mult.toFixed(2)} | ${need}${reached < need ? ` (only ${reached} reached)` : ""} | ${f(t)} | ${(t / first).toFixed(2)} | ${second ? f(second.t) : "-"} |`);
}
console.log(`\nOffline (EconomyConfig): ${SHARE * 100}% of the sampled income per minute, at most ${CAPS / 3600} h away: a full credit is ${(SHARE * CAPS / 60).toFixed(0)} min of active income.`);
