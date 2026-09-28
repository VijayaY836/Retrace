import { pct } from "../api";

function combos(dims, raw) {
  let out = [{}];
  for (const d of dims) out = out.flatMap((c) => raw[d].map((v) => ({ ...c, [d]: v })));
  return out;
}

export default function CoverageMap({ a }) {
  const cov = a.coverage;
  const dims = cov.dims;
  const rowDims = dims.slice(0, Math.ceil(dims.length / 2));
  const colDims = dims.slice(Math.ceil(dims.length / 2));
  const rows = combos(rowDims, cov.raw_levels);
  const cols = colDims.length ? combos(colDims, cov.raw_levels) : [{}];
  const label = (c, ds) => ds.map((d) => cov.levels[d][cov.raw_levels[d].indexOf(c[d])]).join(" · ");
  const find = (r, c) => cov.cells.find((x) => Object.entries({ ...r, ...c }).every(([k, v]) => x.cell[k] === v));
  const top = cov.ranked[0];
  const isTop = (cell) => top && dims.every((d) => top.cell[d] === cell.cell[d]);

  return (
    <div className="px-4 py-3">
      <p className="text-[13px] text-ink-2">
        Every combination of the conditions that matter in {a.area_label.toLowerCase()}:{" "}
        <b className="text-ok">{cov.counts.tested} tested</b>, <b className="text-ink-2">{cov.counts.untested} never tested</b>
        {cov.counts.planned > 0 && <>, <b className="text-hs">{cov.counts.planned} planned</b></>}.
      </p>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full border-separate border-spacing-1 text-center text-[12px]">
          <thead>
            <tr>
              <th className="text-left text-[11px] font-semibold text-ink-3">{rowDims.map((d) => cov.dim_labels[dims.indexOf(d)]).join(" · ")}</th>
              {cols.map((c, i) => <th key={i} className="px-1 text-[11px] font-semibold text-ink-2">{label(c, colDims) || "Result"}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <th className="whitespace-nowrap pr-2 text-left text-[12px] font-semibold text-ink-2">{label(r, rowDims)}</th>
                {cols.map((c, j) => {
                  const cell = find(r, c);
                  if (!cell) return <td key={j} />;
                  const e = cell.experiments[0];
                  const topCell = isTop(cell);
                  const cls = cell.status === "tested" ? (e.lift >= 0 ? "bg-ok-soft text-ok border-ok-mid" : "bg-fault-soft text-fault border-fault-mid")
                    : cell.status === "planned" ? "bg-hs-soft text-hs border-hs/40"
                    : cell.status === "inconclusive" ? "bg-sunk text-ink-3 border-line"
                    : topCell ? "bg-warn-soft text-warn border-warn anim-warn" : "border-dashed border-line text-ink-3";
                  return (
                    <td key={j} className={`h-14 min-w-[92px] rounded border px-1 ${cls}`} title={cell.label}>
                      {cell.status === "tested" && <><div className="font-display text-[15px] font-bold">{pct(e.lift)}</div><div className="text-[10px]">{cell.experiments.map((x) => x.id).join(", ")}</div></>}
                      {cell.status === "inconclusive" && <><div className="font-semibold">inconclusive</div><div className="text-[10px]">{e.id}</div></>}
                      {cell.status === "planned" && <><div className="font-semibold">planned</div><div className="text-[10px]">{cell.planned}</div></>}
                      {cell.status === "untested" && (topCell ? <><div className="font-semibold">Top gap</div><div className="text-[10px]">never tested</div></> : <div className="text-[11px]">never tested</div>)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {top && (
        <div className="mt-3 rounded border border-warn-mid bg-warn-soft px-3 py-2 text-[13px]">
          <p className="font-semibold text-warn">Most informative next experiment: {top.label}</p>
          <p className="mt-0.5 text-ink">{top.why}</p>
        </div>
      )}
    </div>
  );
}
