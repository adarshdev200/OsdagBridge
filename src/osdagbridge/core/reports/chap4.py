from typing import TYPE_CHECKING
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
)
from osdagbridge.core.reports.report_utils import _tex, _fig_embed
from osdagbridge.core.reports.styles import status_tex
from osdagbridge.core.reports.tables import ReportTable, kv_table

if TYPE_CHECKING:
    from .report_generator import ReportDataBridge

def ch4_analysis(asum, fig_paths, bridge: "ReportDataBridge", span_m: float):
    lc_summary  = (asum or {}).get('load_cases', {})
    rxn_summary = (asum or {}).get('reactions',  {})

    def _is_moving(lc_name: str) -> bool:
        n = lc_name.lower()
        return "moving" in n or " pos_" in n

    lc_summary  = {k: v for k, v in lc_summary.items()  if not _is_moving(k)}
    rxn_summary = {k: v for k, v in rxn_summary.items() if not _is_moving(k)}

    def _fmt(val, nd=3):
        try:
            return f"{float(val):.{nd}f}"
        except (TypeError, ValueError):
            return r"---"

    demands = ReportTable(r"Summary of Maximum Demands", [
        ("Load Case", "L", 0.18), ("BM", "C", 0.11), ("Girder", "C", 0.09), ("Loc", "C", 0.08),
        ("SF", "C", 0.11), ("Girder", "C", 0.09), ("Loc", "C", 0.08), ("Left", "C", 0.13), ("Right", "C", 0.13),
    ], label="tab:max-demands")
    h = demands.head
    demands.header_tex = (r"\rowcolor{tableHead}" + " & ".join([
        h(0, "Load Case /"), h(1, "Bending Moment", 3), h(4, "Shear Force", 3), h(7, "Support Reaction (kN)", 2)])
        + r" \\" + "\n" + r"\cline{2-9}" + "\n" + r"\rowcolor{tableHead}" + " & ".join([
        h(0, "Combination"), h(1, "Max (kNm)"), h(2, "Girder"), h(3, "Loc. (m)"), h(4, "Max (kN)"),
        h(5, "Girder"), h(6, "Loc. (m)"), h(7, "Left"), h(8, "Right")]) + r" \\")

    all_lcs = list(lc_summary.keys()) + [k for k in rxn_summary if k not in lc_summary]
    for lc in all_lcs:
        bm_d = lc_summary.get(lc) or {}
        rxn_d = rxn_summary.get(lc) or {}
        demands.add_row([
            _tex(lc), _fmt(bm_d.get('max_bm')), _tex(bm_d.get('bm_girder', '---')), _fmt(bm_d.get('bm_location')),
            _fmt(bm_d.get('max_sf')), _tex(bm_d.get('sf_girder', '---')), _fmt(bm_d.get('sf_location')),
            _fmt(rxn_d.get('left_kN')), _fmt(rxn_d.get('right_kN')),
        ])
    if not all_lcs:
        demands.add_span_row(r"\textit{No analysis results available}")

    _span_m         = float(bridge.input_dict.get(KEY_SPAN, 0) or 0)
    _allow_live_mm  = _span_m * 1000.0 / 800.0
    _allow_total_mm = _span_m * 1000.0 / 600.0

    # Find governing girder — worst (max) deflection across all girders
    try:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1) or 1)
    except (TypeError, ValueError):
        n = 1

    _live_mm  = None
    _total_mm = None
    for _gi in range(1, n + 1):
        _l = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{_gi}")
        _t = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{_gi}")
        if _l is not None:
            _live_mm  = max(_live_mm, float(_l))  if _live_mm  is not None else float(_l)
        if _t is not None:
            _total_mm = max(_total_mm, float(_t)) if _total_mm is not None else float(_t)

    _live_str        = f"{_live_mm:.3f} mm"  if _live_mm  is not None else "---"
    _total_str       = f"{_total_mm:.3f} mm" if _total_mm is not None else "---"
    _allow_live_str  = f"L/800 = {_allow_live_mm:.1f} mm"
    _allow_total_str = f"L/600 = {_allow_total_mm:.1f} mm"
    _live_status     = status_tex("PASS" if _live_mm  <= _allow_live_mm  else "FAIL") if _live_mm  is not None else "---"
    _total_status    = status_tex("PASS" if _total_mm <= _allow_total_mm else "FAIL") if _total_mm is not None else "---"

    deflection = kv_table(r"Deflection Summary (Live Load \& Total Load)", [
        (r"Deflection due to Live Load, $\delta_{LL}$", _live_str),
        (r"Allowable Live Load Deflection, $\Delta_{allow}$", _allow_live_str),
        (r"Live Load Deflection Check", _live_status),
        (r"Deflection due to Total Load, $\delta_{total}$", _total_str),
        (r"Allowable Total Deflection, $\Delta_{allow}$", _allow_total_str),
        (r"Total Load Deflection Check", _total_status),
    ], with_unit=False, label="tab:deflection-summary",
        note=r"Governing (maximum) deflection over all girders; limits per IRC 22 Cl. 604.3.2.")
    return r"""
\chapter{Analysis Results}

A grillage model was used for structural analysis. The deck is idealized as a grid of elastic beam elements --- longitudinal members represent the composite steel girders with effective slab, and transverse members represent the slab or cross frames. This section summarizes the critical output from that analysis.

""" + demands.dumps() + deflection + r"""

\vspace{1em}
\noindent
""" + _fig_embed(fig_paths.get('bm_envelope'), 'Bending Moment Envelope (Envelope ULS): Max/min BM along span. X-axis: distance from left support (m). Y-axis: Bending Moment (kN-m).', width=r'0.75\textwidth') + r"""
""" + _fig_embed(fig_paths.get('sf_envelope'), 'Shear Force Envelope (Envelope ULS): Max/min SF along span. X-axis: distance from left support (m). Y-axis: Shear Force (kN).', width=r'0.75\textwidth') + r"""
""" + _fig_embed(fig_paths.get('defl_ll'), 'Vertical Deflection D$_y$ (1.0 LL): Maximum deflection along span. Load Case: 1.0 LL, Combination: $D_y$. Nodes shown. Isometric view.', width=r'0.75\textwidth') + r"""
"""

