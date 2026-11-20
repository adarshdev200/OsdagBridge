from osdagbridge.core.reports import charts
from osdagbridge.core.reports.tables import ReportTable

# (S.N., description, key prefix in the BOQ dict)
BOQ_ITEMS = [
    ("1",    "Structural Steel (IS 2062) for Girders", "steel_girders"),
    ("2(a)", "Cross Bracing - Top Chord",              "bracing_top"),
    ("2(b)", "Cross Bracing - Bottom Chord",           "bracing_bot"),
    ("2(c)", "Cross Bracing - Diagonal",               "bracing_diag"),
    ("3",    "End Diaphragms (both supports)",         "end_diaphragm"),
    ("4",    "Concrete (M40) for Deck Slab",           "concrete_deck"),
    ("5",    "Reinforcement Steel (Fe 500)",           "rebar_deck"),
    ("6",    "Shear Stud Connectors",                  "shear_studs"),
    ("7",    "Crash Barrier",                          "crash_barrier"),
]


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _get(d, key):
    v = d.get(key, "N.A.")
    return "N.A." if v in (None, "") else str(v)


def quantity_summary(q):
    """Chart inputs: steel tonnage per element, concrete volume and rebar weight."""
    cb = [_num(q.get(f"{p}_wt_total")) for p in ("bracing_top", "bracing_bot", "bracing_diag")]
    cb = [x for x in cb if x is not None]
    steel = [
        ("Girders", _num(q.get("steel_girders_wt_total"))),
        ("Cross Bracing", sum(cb) if cb else None),
        ("End Diaphragms", _num(q.get("end_diaphragm_wt_total"))),
    ]
    return steel, _num(q.get("concrete_deck_vol_total")), _num(q.get("rebar_deck_wt_total"))


def ch7_quantities(input_dict, asset_dir=None):
    t = ReportTable(r"Bill of Materials (Steel, Concrete and Reinforcement Quantities)", [
        ("S.N.", "C", 0.07), ("Item Description", "L", 0.25), ("Unit Volume", "C", 0.22),
        ("Qty.", "C", 0.08), (r"Total Volume (m$^3$)", "C", 0.12), ("Unit Weight (MT)", "C", 0.12),
        ("Total Weight (MT)", "C", 0.14),
    ], label="tab:bom", font=r"\footnotesize",
        note=r"Steel density 7.85 t/m$^3$, concrete 2.5 t/m$^3$. Reinforcement taken as 120 kg per m$^3$ of deck concrete.")

    for sn, desc, key in BOQ_ITEMS:
        t.add_row([sn, desc, _get(input_dict, f"{key}_vol_formula"), _get(input_dict, f"{key}_qty"),
                   _get(input_dict, f"{key}_vol_total"), _get(input_dict, f"{key}_wt_single"),
                   _get(input_dict, f"{key}_wt_total")])

    steel, conc, rebar = quantity_summary(input_dict)
    steel_total = sum(v for _, v in steel if v is not None)
    if steel_total > 0:
        t.add_raw(r"\multicolumn{6}{|r|}{\textbf{Total structural steel (girders + bracing + diaphragms)}} & \textbf{"
                  + f"{steel_total:.2f}" + r"} \\ \hline")

    figs = ""
    if asset_dir:
        try:
            figs = charts.figure_tex(
                charts.quantity_charts(asset_dir, steel, conc, rebar),
                r"Material quantities --- (a) structural steel tonnage by element, "
                r"(b) deck concrete volume (m$^3$) vs. reinforcement steel weight (MT)",
                label="fig:material-quantities")
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Quantity chart skipped: %s", exc)

    return r"""
\chapter{Material Take-off \& Quantity Summary}
\label{ch:material-takeoff}

The quantities below are computed from the final member sizes and the bridge geometry. They are intended for preliminary estimation; wastage, connections and splices are not included.
""" + t.dumps() + figs
