# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

from osdagbridge.core.reports.report_utils import _fig_or_placeholder, _render_value, _tex, get_girder_entries
from osdagbridge.core.reports.styles import THEME, status_tex
from osdagbridge.core.reports.tables import ReportTable, col_spec, kv_table
from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SD_SECTION_DESIGNATION,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS
)


def _max_float(values):
    """Return the largest value coercible to float, or None if there are none."""
    out = None
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if out is None or f > out:
            out = f
    return out


def _max_member_efficiency(pair_designs):
    """Maximum Osdag 'efficiency' (utilization ratio) over a cross-bracing or
    end-diaphragm result dump (nested pair -> member -> force_type -> raw).
    Reads already-computed results only; nothing is recalculated here."""
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
    if not isinstance(pair_designs, dict):
        return None
    best = None
    for members in pair_designs.values():
        if not isinstance(members, dict):
            continue
        for force_types in members.values():
            if not isinstance(force_types, dict):
                continue
            for raw in force_types.values():
                try:
                    val = _extract_osdag_summary(raw or {}).get("efficiency")
                    if val is None:
                        continue
                    f = float(val)
                except (TypeError, ValueError, AttributeError):
                    continue
                if best is None or f > best:
                    best = f
    return best


def executive_summary(input_dict, output_dict, fig_paths) -> str:
    plan_fig = _fig_or_placeholder(fig_paths.get('girder_top'), 'Figure 1 -- Overall Bridge Plan')
    cs_fig = _fig_or_placeholder(fig_paths.get('cross_section'),
                                  'Figure 2 -- Typical Cross-Section (with girder, deck, barriers, footpath)')
    geom_fig = _fig_or_placeholder(fig_paths.get('final_geometry'),
                                    'Figure 3 -- 3D View of Bridge Superstructure')

    # All girders share the same section, governing check, and UR.
    # The section designation is produced by the designer pipeline, so it lives
    # in output_dict (not input_dict).
    sec = _render_value(output_dict, KEY_SD_SECTION_DESIGNATION)

    # ── Pull the stored result dicts once, then work off these locals ─────────
    # (no value is recomputed here — the pipeline already filled these in).
    design_results = output_dict.get("design_results", {}) or {}
    per_girder     = design_results.get("per_girder", {}) or {}
    deck_results   = output_dict.get("deck_design_results", {}) or {}
    cb_results     = output_dict.get("crossbracing_design_results", {}) or {}
    ed_results     = output_dict.get("end_diaphragm_design_results", {}) or {}

    # Overall Design Status — girder checks only: Pass if every check passes,
    # otherwise Fail with the names of the failing checks. Each check carries a
    # pre-computed {name, dcr, status}.
    failing = []                        # failing check names (order-preserving, deduped)
    gov_name, gov_dcr = "", None
    girder_max_ur = None
    for g, gd in per_girder.items():
        if str(g).startswith("EB"):     # skip edge-beam pseudo girders
            continue
        for chk in (gd.get("checks") or []):
            try:
                _val = chk.get("dcr")
                if _val is None:
                    dcr = None
                else:
                    dcr = float(_val)
            except (TypeError, ValueError):
                dcr = None
            name = str(chk.get("name", "")).strip()
            is_fail = ("FAIL" in str(chk.get("status", "")).upper()) or (dcr is not None and dcr > 1.0)
            if is_fail and name and name not in failing:
                failing.append(name)
            if dcr is not None:
                if gov_dcr is None or dcr > gov_dcr:
                    gov_dcr, gov_name = dcr, name
                if girder_max_ur is None or dcr > girder_max_ur:
                    girder_max_ur = dcr

    if not per_girder:
        overall_design_status = ""
    elif failing:
        overall_design_status = "Fail (" + ", ".join(failing) + ")"
    else:
        overall_design_status = "Pass"

    # Overall Utilization Ratio — the maximum UR across all bridge components,
    # tagged with the governing component (e.g. "1.05 (Deck slab)").
    component_urs = []                  # (ur_value, component_label)
    if girder_max_ur is not None:
        component_urs.append((girder_max_ur, "Girder"))
    deck_max = _max_float([v for k, v in deck_results.items() if str(k).startswith("ur_")])
    if deck_max is not None:
        component_urs.append((deck_max, "Deck slab"))
    for results, label in ((cb_results, "Cross bracing"), (ed_results, "End diaphragm")):
        m = _max_member_efficiency(results)
        if m is not None:
            component_urs.append((m, label))
    if component_urs:
        max_ur, max_label = max(component_urs, key=lambda t: t[0])
        overall_utilization_ratio = f"{max_ur:.2f} ({max_label})"
    else:
        overall_utilization_ratio = ""

    gov = _tex(gov_name) if gov_name not in (None, '', 'None') else ''
    ur = _tex(overall_utilization_ratio) if overall_utilization_ratio else ''

    # Key design outcomes — one line per component from the stored results
    lim = THEME.chart.ur_limit
    by_component = {}
    for v, label in component_urs:
        by_component[label] = v
    outcome_rows = []
    for label in ("Girder", "Deck slab", "Cross bracing", "End diaphragm"):
        v = by_component.get(label)
        if label == "Girder" and failing:
            verdict = "FAIL"
        elif v is None:
            verdict = None
        else:
            verdict = "PASS" if v <= lim else "FAIL"
        outcome_rows.append((label + " design",
                             f"{v:.2f}" if v is not None else "---",
                             status_tex(verdict) if verdict else r"\textit{Not designed}"))
    outcomes = ReportTable(r"Key Design Outcomes", [
        ("Component", "L", 0.46), ("Max. UR", "C", 0.24), ("Result", "C", 0.30)], label="tab:key-outcomes")
    outcomes.add_rows(outcome_rows)

    # --- Final geometry table: one column per girder ---
    # defaults.py populates: KEY_MP_GD_SELECT_GIRDER + '.G{i}' = 'G{i}'
    #                        KEY_MP_GD_MEMBER_ID     + '.G{i}.M1' = 'G{i}M1'
    labels = get_girder_entries(input_dict)
    if not labels:
        labels = [("", "")]
    n_cols = len(labels)

    # Fractions of \linewidth, so any number of girders fits the text block
    label_frac = 0.22
    g_frac = (1.0 - label_frac) / n_cols
    font = r"\small" if n_cols <= 4 else r"\footnotesize"
    spec = "|" + col_spec("L", label_frac) + "|" + "|".join([col_spec("C", g_frac)] * n_cols) + "|"

    def row(name, cells):
        return r"\textbf{" + name + "} & " + " & ".join(cells) + r" \\ \hline"

    header = (r"\rowcolor{tableHead}\textbf{Girder} & "
              + " & ".join(r"\textbf{" + _tex(lbl) + "}" for lbl, _ in labels) + r" \\ \hline")
    table1 = ("{" + font + "\n"
              r"\begin{longtable}{" + spec + "}\n"
              r"\caption{Final Bridge Geometry (after optimization)}\label{tab:final-geometry}\\" + "\n"
              r"\hline" + "\n" + header + "\n"
              r"\endfirsthead" + "\n"
              r"\caption[]{Final Bridge Geometry (after optimization) \textit{(continued)}}\\" + "\n"
              r"\hline" + "\n" + header + "\n"
              r"\endhead" + "\n"
              + row("Member ID", [_tex(mid) for _, mid in labels]) + "\n"
              + row("Section Designation", [sec] * n_cols) + "\n"
              + row("Governing Check", [gov] * n_cols) + "\n"
              + row("Utilization Ratio", [ur] * n_cols) + "\n"
              r"\end{longtable}" + "\n}\n")

    overview = kv_table(r"Project Overview", [
        ("Bridge Type", _render_value(input_dict, KEY_STRUCTURE_TYPE), ""),
        ("Design Standard", "IRC 5, IRC 6, IRC 22, IRC 24, IS 800", ""),
        ("Span", _render_value(input_dict, KEY_SPAN), "m"),
        ("Carriageway Width", _render_value(input_dict, KEY_CARRIAGEWAY_WIDTH), "m"),
        ("No. of Girders", _render_value(input_dict, KEY_TS_NO_OF_GIRDERS), "--"),
        ("Girder Spacing", _render_value(input_dict, KEY_TS_GIRDER_SPACING), "m"),
        ("Deck Thickness", _render_value(input_dict, KEY_TS_DECK_THICKNESS), "mm"),
        ("Overall Design Status", status_tex(_tex(overall_design_status)) if overall_design_status else "", ""),
        ("Governing Check", gov, ""),
        ("Overall Utilization Ratio (max)", ur, ""),
    ], label="tab:project-overview")

    return r"""
\newpage
{\centering\LARGE\bfseries\color{osdagDark} Executive Summary\par}
\addcontentsline{toc}{chapter}{Executive Summary}
\renewcommand{\thetable}{ES.\arabic{table}}
\vspace{0.8em}

This section provides a concise summary of the bridge design, key inputs, governing loads, and final design outcomes.

\section*{Project Overview}
\addcontentsline{toc}{section}{Project Overview}
\label{sec:project-overview}
""" + overview + plan_fig + r"""

\newpage

""" + cs_fig + '\n\n' + geom_fig + '\n\n' + table1 + r"""
\noindent{\footnotesize\textit{Note: Utilization ratio (UR) = demand / capacity. A value $\leq 1.0$ indicates a passing check.}}

\section*{Key Design Outcomes Summary}
\addcontentsline{toc}{section}{Key Design Outcomes Summary}
\label{sec:key-outcomes}
""" + outcomes.dumps() + r"""

\section*{Design Assumptions and Limitations}
\addcontentsline{toc}{section}{Design Assumptions and Limitations}
\label{sec:assumptions}

\begin{itemize}
\item Additional inputs not provided by the user were assumed by software per IRC/IS code defaults or practical consideration.
\item Grillage analysis was performed using OSPGrillage assuming simply supported I-girders.
\item Substructure and foundation design are not included in this report.
\item Splice connections and bearings are not designed in this version.
\end{itemize}

\renewcommand{\thetable}{\thechapter.\arabic{table}}
"""
