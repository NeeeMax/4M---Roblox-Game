// Retention check of the STREET economy, a node port of docs/economy/street_sim.luau (same policy, no lune needed).
// It reads the REAL constants from src/shared/Config/Tycoon.luau and the decor prices of bays 1 to 5 from DecorTheme01 ... 05
// (bays 6 to 30: the part counts and last prices of the theme builders, RewardMult x6 per theme, like street_sim).
//   node docs/tools/street_retention.js                      -- report for the constants in src/ now
//   EFF=0.35 node docs/tools/street_retention.js            -- slower player (share of the time really spent hitting the Shiba)
// Prints: time to first purchase, first decor / Intern, purchase cadence of the first minutes, the time of Shiba 2 to 10 (active and
// idle) and how far a player gets in sessions of 10, 15 and 25 minutes (with and without a modelled offline credit).
// Known difference: Shiba 2 to 5 come about 10% later than street_sim reports (stage 1 about 8.9 instead of 8 min): use it to compare
// before and after a change, and re-check with `lune run docs/economy/street_sim`.
const fs = require("fs");
const path = require("path");
const ROOT = process.env.REPO || path.join(__dirname, "..", "..");
const read = f => fs.readFileSync(path.join(ROOT, "src/shared/Config", f), "utf8");

function loadConfig(over = {}) {
  const t = read("Tycoon.luau");
  const sw0 = t.indexOf("Swing = {");
  const st0 = t.lastIndexOf("Street = {");
  const swingText = t.slice(sw0, st0);
  const streetText = t.slice(st0, t.indexOf("Rings = {"));
  const num = (txt, key) => {
    const m = txt.match(new RegExp("\\b" + key + " = ([0-9.e+-]+)"));
    if (!m) throw new Error("missing " + key);
    return Number(m[1]);
  };
  const sf = streetText.match(/StageFactor = \{([\s\S]*?)\}/)[1];
  const factors = [...sf.matchAll(/^\s*([0-9.]+),/gm)].map(m => Number(m[1]));
  const C = { Swing: {}, Street: {} };
  for (const k of ["Cooldown", "CooldownPerTier", "MaxBaseCooldown", "MinCooldown", "MinCooldownGrowth", "PayoutPerLevel", "StreetLevelSeconds", "StreetLevelGrowth", "StreetLevelCap", "EffectInterval"]) C.Swing[k] = num(swingText, k);
  for (const k of ["Bays", "BaseIncome", "TierGrowth", "ReadyLevel", "LevelFactorPower", "BaySeconds", "DecorScale", "AutomationSeconds", "AutomationGrowth", "AutomationFirstPrice", "DecorChains"]) C.Street[k] = num(streetText, k);
  C.Street.StageFactor = factors;
  for (const [k, v] of Object.entries(over)) {
    if (k in C.Swing) C.Swing[k] = v;
    else if (k in C.Street) C.Street[k] = v;
  }
  return C;
}

// decor parts per bay: [{ps, rm}]
function loadThemes() {
  const themes = {};
  for (let bay = 1; bay <= 5; bay++) {
    const txt = read(`DecorTheme0${bay}.luau`);
    const body = txt.slice(txt.indexOf("Parts = {"));
    const blocks = body.split(/\n\t\t\tId = /).slice(1);
    themes[bay] = blocks.map(b => ({
      ps: Number(b.match(/PriceSeconds = ([0-9.]+)/)[1]),
      rm: Number((b.match(/RewardMult = ([0-9.]+)/) || [0, 1])[1]),
    }));
  }
  const counts = n => (n <= 3 ? 10 : n <= 8 ? 15 : n <= 14 ? 20 : n <= 21 ? 25 : 30);
  const last = { 6: 380, 7: 440, 8: 520, 9: 560, 10: 600, 11: 700, 12: 750, 13: 800, 14: 850, 15: 850, 16: 900, 17: 900, 18: 950, 19: 950, 20: 1000, 21: 400, 22: 500, 23: 600, 24: 700, 25: 800, 26: 900, 27: 1000, 28: 1100, 29: 1150, 30: 1200 };
  for (let bay = 6; bay <= 30; bay++) {
    const n = counts(bay), parts = [];
    for (let i = 1; i <= n; i++) {
      let p = 10 * Math.pow(last[bay] / 10, (i - 1) / (n - 1));
      p = bay <= 10 ? Math.floor(p + 0.5) : bay <= 20 ? Math.floor(p / 5 + 0.5) * 5 : Math.round(p);
      parts.push({ ps: p, rm: Math.pow(6, 1 / n) });
    }
    themes[bay] = parts;
  }
  return themes;
}

function makeMath(C) {
  const S = C.Swing, ST = C.Street;
  const M = {};
  M.streetTierIncome = t => ST.BaseIncome * Math.pow(ST.TierGrowth, t);
  M.baseCooldown = t => Math.min(S.MaxBaseCooldown, S.Cooldown + S.CooldownPerTier * t);
  M.minCooldownFor = t => Math.min(S.MinCooldown * Math.pow(S.MinCooldownGrowth, t), M.baseCooldown(t));
  M.cooldown = (t, l) => {
    const b = M.baseCooldown(t);
    const p = Math.min(1, Math.max(0, (l - 1) / (S.StreetLevelCap - 1)));
    return b * Math.pow(M.minCooldownFor(t) / b, p);
  };
  M.payout = (t, l) => M.streetTierIncome(t) * M.baseCooldown(t) * (1 + S.PayoutPerLevel * (l - 1));
  M.rate = (t, l) => M.payout(t, l) / M.cooldown(t, l);
  M.readyIncome = t => M.rate(t, ST.ReadyLevel);
  M.autoPrice = (t, n) => (n === 0 && t === 0 ? ST.AutomationFirstPrice : Math.floor(M.readyIncome(t) * ST.AutomationSeconds * Math.pow(ST.AutomationGrowth, n)));
  M.levelCost = (t, l) => {
    const tf = Math.pow(Math.max(1, ST.StageFactor[t] || 1), ST.LevelFactorPower);
    return Math.max(1, Math.floor(M.rate(t, l) * S.StreetLevelSeconds * Math.pow(S.StreetLevelGrowth, l - 1) * tf));
  };
  M.decorPrice = (bay, ps) => Math.floor(M.readyIncome(bay - 1) * ps * ST.DecorScale * (ST.StageFactor[bay - 1] || 1));
  M.bayPrice = bay => (bay <= 1 ? 0 : Math.floor(M.readyIncome(bay - 2) * ST.BaySeconds * (ST.StageFactor[bay - 2] || 1)));
  return M;
}

const PERK_KINDS = ["Burst", "Neighbors", "Chance", "Synergy", "Global", "Rhythm"];
function perkList() {
  const P = [
    { k: "Global", v: 0.05 }, { k: "Burst", m: 3, d: 4, p: 20 }, { k: "Neighbors", v: 0.25 }, { k: "Synergy" },
    { k: "Rhythm", m: 5, e: 10 }, { k: "Rhythm", m: 5, e: 10 }, { k: "Burst", m: 4, d: 2, p: 12 },
    { k: "Chance", c: 0.08, m: 10 }, { k: "Neighbors", v: 0.3 }, { k: "Synergy" },
  ];
  for (let tier = P.length + 1; tier <= 30; tier++) {
    const kind = PERK_KINDS[(tier - 1) % 6];
    const s = 1 + (tier - 10) * 0.03;
    if (kind === "Burst") P.push({ k: kind, m: 4 * s, d: 3, p: 12 });
    else if (kind === "Neighbors") P.push({ k: kind, v: 0.3 * s });
    else if (kind === "Chance") P.push({ k: kind, c: 0.1, m: 10 * s });
    else if (kind === "Global") P.push({ k: kind, v: 0.05 * s });
    else if (kind === "Rhythm") P.push({ k: kind, m: 6 * s, e: 8 });
    else P.push({ k: kind });
  }
  return P;
}
const PERKS = perkList();
const MILESTONES = [10, 25, 50];
const milestones = l => MILESTONES.filter(m => l >= m).length;

function selfPerk(p) {
  if (p.k === "Burst") return 1 + (p.m - 1) * p.d / p.p;
  if (p.k === "Chance") return 1 + p.c * (p.m - 1);
  if (p.k === "Rhythm") return 1 + (p.m - 1) / p.e;
  return 1;
}

function make(over = {}, opts = {}) {
  const C = loadConfig(over);
  const M = makeMath(C);
  const T = loadThemes();
  const BAYS = C.Street.Bays;
  const CAP = C.Swing.StreetLevelCap;
  const CPS = opts.clicksPerSecond ?? 3;
  const EFF = opts.clickEff ?? 0.5;

  function newState() {
    return { shibas: [{ level: 1, auto: false }], bought: new Set(), autos: 0 }; // shibas[i] = bay i+1
  }
  const decorMult = (st, bay) => {
    let m = 1;
    T[bay].forEach((p, i) => { if (st.bought.has(`${bay}_${i}`)) m *= p.rm; });
    return m;
  };
  function laneRate(st, bay) {
    const sh = st.shibas[bay - 1];
    const tier = bay - 1;
    let r = M.rate(tier, sh.level) * selfPerk(PERKS[tier]) * decorMult(st, bay);
    let bonus = 0;
    for (const o of [bay - 1, bay + 1]) {
      const n = st.shibas[o - 1];
      if (o >= 1 && n) { const p = PERKS[o - 1]; if (p.k === "Neighbors") bonus += p.v; }
    }
    return r * (1 + bonus);
  }
  function globalMult(st) {
    let extra = 0;
    st.shibas.forEach((sh, i) => { const p = PERKS[i]; if (p.k === "Global") extra += p.v * milestones(sh.level); });
    return 1 + extra;
  }
  function incomes(st) {
    const g = globalMult(st);
    let auto = 0, bestManual = 0;
    st.shibas.forEach((sh, i) => {
      const bay = i + 1;
      const rate = laneRate(st, bay) * g;
      if (sh.auto) auto += rate;
      else {
        const cd = M.cooldown(i, sh.level);
        const manual = rate * Math.min(1, cd * CPS);
        if (manual > bestManual) bestManual = manual;
      }
    });
    return { auto, manual: bestManual };
  }
  const MULT = opts.mult ?? 1;
  const total = (st, clicking) => { const i = incomes(st); return (i.auto + (clicking ? i.manual * EFF : 0)) * MULT; };
  const remainingDecor = (st, bay) => T[bay].map((_, i) => i).filter(i => !st.bought.has(`${bay}_${i}`));

  // run: play for `limit` seconds of play time (or until STOP_BAY) from a given state. Returns events.
  function run(idle, st, money, now, limit, events, clickingIn) {
    let clicking = clickingIn;
    const end = now + limit;
    while (now < end) {
      if (opts.stopBay && st.shibas.length >= opts.stopBay) break;
      const income = total(st, clicking);
      if (income <= 0) break;
      const bay = st.shibas.length;
      const cands = [];
      const rest = remainingDecor(st, bay);
      const hasNext = bay < BAYS;
      let packageCost = 0;
      for (const i of rest) packageCost += M.decorPrice(bay, T[bay][i].ps);
      const bayPrice = hasNext ? M.bayPrice(bay + 1) : 0;
      packageCost += bayPrice;
      // level ups
      st.shibas.forEach((sh, i) => {
        if (sh.level < CAP) {
          const cost = M.levelCost(i, sh.level);
          sh.level++;
          const gain = total(st, clicking) - income;
          sh.level--;
          cands.push({ cost, gain, kind: "level", bay: i + 1, apply: () => { sh.level++; } });
        }
      });
      // interns
      st.shibas.forEach((sh, i) => {
        if (!sh.auto) {
          const cost = M.autoPrice(i, st.autos);
          sh.auto = true;
          const gain = total(st, clicking) - income;
          sh.auto = false;
          cands.push({ cost, gain: idle ? gain * 50 : gain, kind: "intern", bay: i + 1, apply: () => { sh.auto = true; st.autos++; if (idle) clicking = false; } });
        }
      });
      // decor (heads of the two chains) / next bay
      if (rest.length > 0) {
        for (let pos = 0; pos < Math.min(2, rest.length); pos++) {
          const i = rest[pos];
          const open = i < 2 || st.bought.has(`${bay}_${i - 2}`);
          if (open) {
            const cost = M.decorPrice(bay, T[bay][i].ps);
            st.bought.add(`${bay}_${i}`);
            const gain = total(st, clicking) - income;
            st.bought.delete(`${bay}_${i}`);
            cands.push({ cost, gain, progress: true, kind: "decor", bay, part: i, apply: () => st.bought.add(`${bay}_${i}`) });
          }
        }
      } else if (hasNext) {
        cands.push({ cost: bayPrice, gain: 0, progress: true, kind: "bay", bay: bay + 1, apply: () => st.shibas.push({ level: 1, auto: false }) });
      }
      if (!cands.length) break;
      let goal;
      for (const c of cands) if (c.progress && (!goal || c.cost < goal.cost)) goal = c;
      let pick = goal;
      const goalWait = goal ? Math.max(0, goal.cost - money) / income : Infinity;
      if (!goal || goalWait > 0) {
        let best, bestTime;
        for (const c of cands) {
          if (c.progress) continue;
          const wait = Math.max(0, c.cost - money) / income;
          const payback = c.cost / Math.max(c.gain, 1e-12);
          const useful = c.kind === "intern" && idle ? true : wait + payback < goalWait * 0.9;
          if (useful && wait < goalWait && (!best || wait < bestTime)) { best = c; bestTime = wait; }
        }
        if (best) pick = best;
      }
      if (!pick) break;
      const wait = Math.max(0, pick.cost - money) / income;
      if (now + wait > end) {
        // session ends before the purchase
        money += income * (end - now);
        now = end;
        break;
      }
      now += wait;
      money += income * wait - pick.cost;
      pick.apply();
      events.push({ t: now, kind: pick.kind, bay: pick.bay, part: pick.part, cost: pick.cost, income: total(st, clicking), payback: pick.cost / Math.max(pick.gain, 1e-12), wait });
    }
    return { money, now, clicking };
  }
  return { C, M, T, newState, run, total, incomes, laneRate };
}


module.exports = { make, loadConfig };
if (require.main !== module) return;
const f = t => (t === undefined ? "-" : t < 90 ? t.toFixed(0) + "s" : t < 5400 ? (t / 60).toFixed(1) + "m" : (t / 3600).toFixed(2) + "h");
const eff = Number(process.env.EFF || 0.5);
const S = make({}, { clickEff: eff });
function timeline(idle, limit) {
  const st = S.newState();
  const ev = [];
  S.run(idle, st, 0, 0, limit, ev, true);
  return ev;
}
const ev = timeline(false, 4 * 3600);
const idleEv = timeline(true, 4 * 3600);
const at = (list, n) => list.find(e => e.kind === "bay" && e.bay === n)?.t;
const decor = ev.filter(e => e.kind === "decor");
let gap = 0, gapAt = 0, prev = 0;
for (const e of ev) { if (e.t > 180) break; if (e.t - prev > gap) { gap = e.t - prev; gapAt = prev; } prev = e.t; }
console.log(`street retention check (click efficiency ${eff}, stage factors from Config/Tycoon)`);
console.log(`first purchase ${f(ev[0].t)} | first decor ${f(decor[0].t)} | house (x2) ${f(decor[1].t)} | first Intern ${f(ev.find(e => e.kind === "intern").t)} (idle ${f(idleEv.find(e => e.kind === "intern").t)})`);
console.log(`purchases in the first 3 min ${ev.filter(e => e.t <= 180).length}, first 10 min ${ev.filter(e => e.t <= 600).length}; longest wait in the first 3 min ${f(gap)} (starting at ${f(gapAt)})`);
console.log("Shiba n bought (active): " + [2, 3, 4, 5, 6, 8, 10].map(n => `${n}: ${f(at(ev, n))}`).join(" | "));
console.log("Shiba n bought (idle):   " + [2, 3, 4, 5, 6, 8, 10].map(n => `${n}: ${f(at(idleEv, n))}`).join(" | "));
for (const [name, plan] of [["D1 10 / D2 15 / D3 25 min", [10, 15, 25]], ["10 min, then 22 min a day for 6 days", [10, 22, 22, 22, 22, 22, 22]]]) {
  for (const off of [null, { share: 0.4, capH: 1 }]) {
    const st = S.newState();
    const evs = [];
    let money = 0, now = 0;
    const rows = [];
    plan.forEach((minutes, i) => {
      if (i > 0 && off) money += off.share * S.incomes(st).auto * Math.min(20 * 3600, off.capH * 3600);
      const r = S.run(false, st, money, now, minutes * 60, evs, true);
      money = r.money;
      now = r.now;
      rows.push(`${st.shibas.length} Shibas/${st.autos} Interns`);
    });
    console.log(`sessions ${name}, offline ${off ? "40% of automated income, max 1 h (proposal)" : "none (street mode today)"}: ${rows.join(" > ")}`);
  }
}
