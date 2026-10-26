// AuLens: fetch MCX gold futures Bhavcopy + Due Date Rates from inside a real browser session.
//
// MCX sits behind Akamai, which answers 403 to scripts (requests, curl, headless browsers), so
// this runs in YOUR browser on an MCX page, using the same endpoints the site's own pages call.
// Endpoint map and evidence: docs/MCX_DATA_API.md.
//
// 1. Open https://www.mcxindia.com/market-data/bhavcopy in Chrome.
// 2. Open DevTools -> Console, paste this whole file, press Enter.
// 3. Run, e.g.:   await aulensFetch({ start: "2026-10-26", end: "2026-10-30" })
// 4. Move the downloaded files: gold_bhavcopy_*.csv -> data/raw/, mcx_ddr_*.csv -> data/raw/ddr/
// 5. python scripts/build_dataset.py --raw data/raw
//
// Pass { download: false } to get the CSV text back without saving files.

async function aulensFetch({ start, end, pauseMs = 800, download = true }) {
  const GOLD = /^GOLD(M|TEN|GUINEA|PETAL)?$/;
  const BHAV_COLS = ["Date", "Symbol", "ExpiryDate", "Open", "High", "Low", "Close", "PreviousClose",
                     "Volume", "OpenInterest", "Value", "InstrumentName"];
  // jQuery's $.ajax sends X-Requested-With; the endpoints answer 404 HTML without it.
  const headers = { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest", Accept: "application/json" };
  const pad = (n) => String(n).padStart(2, "0");
  const ddmmyyyy = (d) => `${pad(d.getUTCDate())}/${pad(d.getUTCMonth() + 1)}/${d.getUTCFullYear()}`;
  const iso = (d) => d.toISOString().slice(0, 10);
  const esc = (v) => (v == null ? "" : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const getJson = async (path, params) => {
    const r = await fetch(`${path}?${new URLSearchParams(params)}`, { headers });
    const text = await r.text();
    if (!text.trim().startsWith("{")) throw new Error(`${path}: HTTP ${r.status}, not JSON (are you on mcxindia.com?)`);
    return JSON.parse(text);
  };

  const from = new Date(`${start}T00:00:00Z`), to = new Date(`${end}T00:00:00Z`);
  if (!(from <= to)) throw new Error("start must be on or before end (YYYY-MM-DD)");

  // Bhavcopy, one request per weekday. Holidays return an empty Data list (not the nearest day).
  const rows = [], skipped = [];
  for (let d = new Date(from); d <= to; d.setUTCDate(d.getUTCDate() + 1)) {
    if (d.getUTCDay() === 0 || d.getUTCDay() === 6) continue;
    const j = await getJson("/market-data/bhavcopy/GetDateWiseBhavCopy", { InstrumentName: "FUTCOM", fromDate: ddmmyyyy(d) });
    const want = `${pad(d.getUTCMonth() + 1)}/${pad(d.getUTCDate())}/${d.getUTCFullYear()}`;
    const gold = (j.Data || []).filter((x) => GOLD.test(String(x.Symbol).trim()));
    if (!gold.length || gold.some((x) => x.Date !== want)) skipped.push(iso(d));
    else rows.push(...gold);
    await sleep(pauseMs);
  }
  const bhav = [BHAV_COLS.join(","), ...rows.map((r) => BHAV_COLS.map((c) => esc(r[c])).join(","))].join("\n") + "\n";

  // Due Date Rates (final settlement prices). Dates are /Date(ms)/ at IST midnight.
  const ddrRows = [];
  for (const symbol of ["GOLD", "GOLDM", "GOLDTEN", "GOLDGUINEA", "GOLDPETAL"]) {
    const j = await getJson("/market-data/ddr/GetDDR", { symbol, fromDate: ddmmyyyy(from), toDate: ddmmyyyy(to) });
    for (const x of (j.Data || []).slice().reverse()) {
      const day = new Date(Number(String(x.date).match(/\d+/)[0]) + 5.5 * 3600e3).toISOString().slice(0, 10);
      ddrRows.push([day, String(x.symbol).trim(), x.ddrNormal, x.baseQty].join(","));
    }
    await sleep(pauseMs);
  }
  const ddr = ["Date,Symbol,DDR,BaseQtyGrams", ...ddrRows].join("\n") + "\n";

  const tag = `${start.replace(/-/g, "")}_${end.replace(/-/g, "")}`;
  if (download) {
    for (const [name, text] of [[`gold_bhavcopy_${tag}.csv`, bhav], [`mcx_ddr_${tag}.csv`, ddr]]) {
      const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(new Blob([text], { type: "text/csv" })), download: name });
      document.body.appendChild(a); a.click(); a.remove();
    }
  }
  console.log(`AuLens: ${rows.length} Bhavcopy rows, ${ddrRows.length} DDRs, no data on: ${skipped.join(", ") || "none"}`);
  return { bhav, ddr, rows: rows.length, ddrs: ddrRows.length, skipped };
}
