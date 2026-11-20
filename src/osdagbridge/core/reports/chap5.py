# =============================================================================
# Chapter 5: Design Checks
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================
from __future__ import annotations
from typing import TYPE_CHECKING

from osdagbridge.core.utils.common import (
    KEY_DD_AS_BOT,
    KEY_DD_AS_LONG,
    KEY_DD_AS_MIN,
    KEY_DD_AS_REQ_BOT,
    KEY_DD_AS_REQ_TOP,
    KEY_DD_AS_TOP,
    KEY_DD_COVER_OK,
    KEY_DD_DIA_BOT,
    KEY_DD_D_BOT,
    KEY_DD_FY,
    KEY_DD_GAMMA_DL,
    KEY_DD_GAMMA_LL,
    KEY_DD_HAS_OVERHANG,
    KEY_DD_IMPACT_FACTOR,
    KEY_DD_MIN_COVER,
    KEY_DD_MU_BOT,
    KEY_DD_MU_OH,
    KEY_DD_MU_TOP,
    KEY_DD_M_BARRIER,
    KEY_DD_M_DL,
    KEY_DD_M_DL_OH,
    KEY_DD_M_LL,
    KEY_DD_M_LL_OH,
    KEY_DD_M_ULS_HOG,
    KEY_DD_M_ULS_OH,
    KEY_DD_M_ULS_SAG,
    KEY_DD_PUNCH_C1,
    KEY_DD_PUNCH_C2,
    KEY_DD_PUNCH_OK,
    KEY_DD_PUNCH_U1,
    KEY_DD_PUNCH_VED,
    KEY_DD_PUNCH_VED_KN,
    KEY_DD_SHEAR_OK,
    KEY_DD_SHEAR_VED,
    KEY_DD_SHEAR_VRDC,
    KEY_DD_SPACING_MAX,
    KEY_DD_SPAN,
    KEY_DD_SPC_BOT,
    KEY_DD_TYRE_LENGTH,
    KEY_DD_TYRE_WIDTH,
    KEY_DD_VEHICLE,
    KEY_DD_VRD_C_MPA,
    KEY_DD_WDL,
    KEY_DD_WHEEL_LOAD,
    KEY_DD_WK_BOT,
    KEY_DD_WK_LIMIT,
    KEY_DD_WK_OH,
    KEY_DD_WK_TOP,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DS_BOTTOM_CLEAR_COVER,
    KEY_DS_REINF_MATERIAL,
    KEY_DS_STUD_DIAMETER,
    KEY_DS_TOP_CLEAR_COVER,
    KEY_MATERIAL_DECK_FCK,
    KEY_MATERIAL_DECK_FCTM,
    KEY_MP_ED_TYPE,
    KEY_SD_BOTTOM_FLANGE_THICKNESS,
    KEY_SD_BOTTOM_FLANGE_WIDTH,
    KEY_SD_BS_FCD,
    KEY_SD_BS_FCDW_LC,
    KEY_SD_BS_FCDW_WB,
    KEY_SD_BS_FPSD,
    KEY_SD_BS_R,
    KEY_SD_CLASS_FLANGE,
    KEY_SD_CLASS_WEB,
    KEY_SD_COMPOSITE_IZ,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
    KEY_SD_EFFECTIVE_SLAB_WIDTH,
    KEY_SD_FLANGE_CLASS_LIMIT,
    KEY_SD_FLANGE_SLENDERNESS,
    KEY_SD_HIGH_SHEAR,
    KEY_SD_IS_FQ,
    KEY_SD_IS_FQD,
    KEY_SD_IS_IYS_MIN,
    KEY_SD_IS_IYS_PROV,
    KEY_SD_LTB_CHI,
    KEY_SD_LTB_LAMBDA,
    KEY_SD_LTB_MB,
    KEY_SD_LTB_MCR,
    KEY_SD_MDV,
    KEY_SD_MD_CAPACITY,
    KEY_SD_MN_AXIAL,
    KEY_SD_MN_MOMENT,
    KEY_SD_MN_RATIO,
    KEY_SD_MU_APPLIED,
    KEY_SD_PANEL_CD,
    KEY_SD_PNA_DEPTH,
    KEY_SD_SC_D_LIMIT,
    KEY_SD_SC_EDGE_DIST,
    KEY_SD_SC_Qr_kN,
    KEY_SD_SC_Qu_kN,
    KEY_SD_SC_REQ_EDGE_DIST,
    KEY_SD_SC_SL1,
    KEY_SD_SC_SL2,
    KEY_SD_SC_SR,
    KEY_SD_SECTION_CLASS,
    KEY_SD_SECTION_PROP_AREA,
    KEY_SD_SECTION_PROP_IZ,
    KEY_SD_SECTION_PROP_ZUZ,
    KEY_SD_SECTION_PROP_ZZ,
    KEY_SD_SHEAR_AV,
    KEY_SD_SHEAR_KV,
    KEY_SD_SHEAR_LAMBDA_W,
    KEY_SD_SHEAR_TAU_B,
    KEY_SD_SHEAR_VCR,
    KEY_SD_SHEAR_VU,
    KEY_SD_STIFF_END_COUNT,
    KEY_SD_STIFF_END_THICK,
    KEY_SD_STIFF_INT_SPACING,
    KEY_SD_STIFF_INT_THICK,
    KEY_SD_STIFF_LONG,
    KEY_SD_STIFF_METHOD,
    KEY_SD_STRESS_STEEL,
    KEY_SD_STRESS_STEEL_ALLOWABLE,
    KEY_SD_TOP_FLANGE_THICKNESS,
    KEY_SD_TOP_FLANGE_WIDTH,
    KEY_SD_TOTAL_DEPTH,
    KEY_SD_TS_VL,
    KEY_SD_TS_VRD,
    KEY_SD_ULS_PER_GIRDER,
    KEY_SD_WEB_CLASS_LIMIT,
    KEY_SD_WEB_SLENDERNESS,
    KEY_SD_WEB_THICKNESS,
    KEY_SPAN,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_NO_OF_GIRDERS,
    KEY_UTIL_FLEXURE,
    KEY_UTIL_INTERACTION,
    KEY_UTIL_LTB,
    KEY_UTIL_SHEAR
)

from osdagbridge.core.reports.report_utils import _tex, _render_value, get_girder_entries
from osdagbridge.core.reports.styles import pass_fail, status_tex, ur_tex
from osdagbridge.core.reports.tables import ReportTable, kv_table
from osdagbridge.core.reports import charts

if TYPE_CHECKING:
    pass

NA = "---"

# Column layout shared by the per-girder check tables (5.3 - 5.6)
CHECK_COLS = [("Girder", "C", 0.10), ("Parameter", "L", 0.33), ("Formula / Reference", "C", 0.24),
              ("Value", "C", 0.19), ("Status", "C", 0.14)]


def _fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _dfmt(v, nd=2):
    """Format a number to nd decimals; empty string when missing."""
    f = _fnum(v)
    return f"{f:.{nd}f}" if f is not None else ""


def _with(v, unit, nd=2):
    s = _dfmt(v, nd)
    return (s + " " + unit) if (s and unit) else s


def _le_status(actual, limit):
    """PASS when actual <= limit."""
    a, l = _fnum(actual), _fnum(limit)
    if a is None or l is None:
        return NA
    return pass_fail(a <= l)


def _ge_status(provided, required):
    """PASS when provided >= required."""
    p, r = _fnum(provided), _fnum(required)
    if p is None or r is None:
        return NA
    return pass_fail(p >= r)


def _interaction_status(ratio):
    # Engine bands: PASS < 0.90, WARN < 1.00, FAIL >= 1.00
    if ratio is None:
        return NA
    if ratio < 0.90:
        return status_tex("PASS")
    if ratio < 1.00:
        return status_tex("WARN")
    return status_tex("FAIL")


def _pct_ratio(v):
    """Utilization stored as percent → ratio."""
    f = _fnum(v)
    return f / 100.0 if f is not None else None


def _girder_table(caption, columns, girder_entries, rows_for, label=None, note=None):
    t = ReportTable(caption, columns, label=label, note=note)
    for i, (lbl, _) in enumerate(girder_entries, start=1):
        t.add_group(_tex(lbl), rows_for(i))
    return t.dumps()


# ── Plate girder ─────────────────────────────────────────────────────────────

def _plate_girder_section(bridge, girder_entries):
    od = bridge.output_dict
    rv = lambda key, unit="": _render_value(od, key) + (" " + unit if unit and _render_value(od, key) else "")

    props = [
        ("Depth, $D$ (mm)", rv(KEY_SD_TOTAL_DEPTH)),
        ("Top Flange Width, $b_{tf}$ (mm)", rv(KEY_SD_TOP_FLANGE_WIDTH)),
        ("Bottom Flange Width, $b_{bf}$ (mm)", rv(KEY_SD_BOTTOM_FLANGE_WIDTH)),
        ("Top Flange Thickness, $t_{tf}$ (mm)", rv(KEY_SD_TOP_FLANGE_THICKNESS)),
        ("Bottom Flange Thickness, $t_{bf}$ (mm)", rv(KEY_SD_BOTTOM_FLANGE_THICKNESS)),
        ("Web Thickness, $t_w$ (mm)", rv(KEY_SD_WEB_THICKNESS)),
        ("Gross Area, $A$ (cm$^2$)", rv(KEY_SD_SECTION_PROP_AREA)),
        ("Moment of Inertia, $I_z$ (cm$^4$)", rv(KEY_SD_SECTION_PROP_IZ)),
        ("Elastic Section Modulus, $Z_{ez}$ (cm$^3$)", rv(KEY_SD_SECTION_PROP_ZZ)),
        ("Plastic Section Modulus, $Z_{pz}$ (cm$^3$)", rv(KEY_SD_SECTION_PROP_ZUZ)),
        ("Effective Slab Width, $b_{eff}$ (mm)", rv(KEY_SD_EFFECTIVE_SLAB_WIDTH)),
        ("Transformed Composite $I_z$ (cm$^4$)", rv(KEY_SD_COMPOSITE_IZ)),
        ("Depth to Plastic Neutral Axis (mm)", rv(KEY_SD_PNA_DEPTH)),
    ]
    t51 = _girder_table(r"Girder Section Properties (Final Optimized / User-selected)",
                        [("Girder", "C", 0.14), ("Property", "L", 0.56), ("Value", "C", 0.30)],
                        girder_entries, lambda i: props, label="tab:girder-props")

    cls = [
        ("Top Flange", rv(KEY_SD_FLANGE_SLENDERNESS), rv(KEY_SD_FLANGE_CLASS_LIMIT), rv(KEY_SD_CLASS_FLANGE)),
        ("Web", rv(KEY_SD_WEB_SLENDERNESS), rv(KEY_SD_WEB_CLASS_LIMIT), rv(KEY_SD_CLASS_WEB)),
        ("Overall Section", NA, NA, rv(KEY_SD_SECTION_CLASS)),
    ]
    t52 = _girder_table(r"Girder Section Classification",
                        [("Girder", "C", 0.12), ("Element", "L", 0.24), ("Slenderness Ratio", "C", 0.21),
                         ("Class Limit", "C", 0.19), ("Classification", "C", 0.24)],
                        girder_entries, lambda i: cls, note="IS 800:2007 Table 2")

    flex = _pct_ratio(od.get(KEY_UTIL_FLEXURE))
    moment = [
        (r"Applied Moment, $M_u$", "Governing LC (ULS)", rv(KEY_SD_MU_APPLIED, "kN-m"), NA),
        (r"Design Moment Capacity, $M_d$", "IRC 22 Cl. 603.3.1", rv(KEY_SD_MD_CAPACITY, "kN-m"), NA),
        (r"Utilization Ratio, $M_u / M_d$", r"$M_u / M_d$", ur_tex(flex) if flex is not None else "",
         pass_fail(flex <= 1.0) if flex is not None else NA),
    ]
    t53 = _girder_table(r"Moment Capacity Check", CHECK_COLS, girder_entries, lambda i: moment,
                        note="IRC 22 Cl. 603.3.1, IS 800 Cl. 8.2.1")

    shear_ur = _pct_ratio(od.get(KEY_UTIL_SHEAR))
    shear = [
        (r"Applied Shear, $V_u$", "Governing LC (ULS)", rv(KEY_SD_SHEAR_VU, "kN"), NA),
        (r"Shear Area, $A_v$", r"$d_w \times t_w$", rv(KEY_SD_SHEAR_AV, "mm$^2$"), NA),
        (r"Panel Aspect Ratio, $c/d$", NA, rv(KEY_SD_PANEL_CD), NA),
        (r"Shear Buckling Coefficient, $k_v$", "IS 800 Cl. 8.4.2.2", rv(KEY_SD_SHEAR_KV), NA),
        (r"Web Slenderness, $\lambda_w$", r"$\sqrt{f_{yw}/(\sqrt{3}\,\tau_{cr})}$", rv(KEY_SD_SHEAR_LAMBDA_W), NA),
        (r"Design Shear Stress, $\tau_b$", "IRC 22 Cl. 603.3.3.2", rv(KEY_SD_SHEAR_TAU_B, "MPa"), NA),
        (r"Shear Buckling Resistance, $V_{cr}$", r"$A_v \times \tau_b$", rv(KEY_SD_SHEAR_VCR, "kN"), NA),
        (r"Utilization Ratio, $V_u / V_d$", r"$V_u / V_d$", ur_tex(shear_ur) if shear_ur is not None else "",
         pass_fail(shear_ur <= 1.0) if shear_ur is not None else NA),
    ]
    t54 = _girder_table(r"Shear Capacity Check", CHECK_COLS, girder_entries, lambda i: shear,
                        note="IS 800 Cl. 8.4, IRC 22 Cl. 603.3.3.2")

    mv = _pct_ratio(od.get(KEY_UTIL_INTERACTION))
    mn_r, mn_ax, mn_mo = od.get(KEY_SD_MN_RATIO), od.get(KEY_SD_MN_AXIAL), od.get(KEY_SD_MN_MOMENT)
    if mn_r is None or mn_ax is None or mn_mo is None:
        mn_cond = mn_val = mn_status = "N/A"
    else:
        mn_cond = f"{mn_ax:.2f} + {mn_mo:.2f} = {mn_r:.3f}"
        mn_val = f"{mn_r:.3f}"
        mn_status = _interaction_status(mn_r)
    inter = [
        ("High Shear Condition?", r"$V_u > 0.6\,V_d$", rv(KEY_SD_HIGH_SHEAR), NA),
        (r"Reduced Moment Capacity, $M_{dv}$", "IRC 22 Cl. 603.3.3.3", rv(KEY_SD_MDV, "kN-m"), NA),
        (r"Interaction: $M_u \leq M_{dv}$", NA, _dfmt(mv), _interaction_status(mv)),
        (r"Interaction: $N_u/N_{Rd} + M_u/M_{dv} \leq 1.0$", mn_cond, mn_val, mn_status),
    ]
    t55 = _girder_table(r"Interaction Checks (M-V and M-N)",
                        [("Girder", "C", 0.10), ("Check", "L", 0.33), ("Condition", "C", 0.24),
                         ("Value", "C", 0.19), ("Status", "C", 0.14)],
                        girder_entries, lambda i: inter, note="IRC 22 Cl. 603.3.3.3")

    ltb = _pct_ratio(od.get(KEY_UTIL_LTB))
    ltb_rows = [
        (r"Elastic Critical Moment, $M_{cr}$", "IRC 22 Cl. 603.3.3.1", rv(KEY_SD_LTB_MCR, "kN-m"), NA),
        (r"Non-dim. Slenderness, $\bar{\lambda}_{LT}$", r"$\sqrt{M_p / M_{cr}}$", rv(KEY_SD_LTB_LAMBDA), NA),
        (r"LTB Reduction Factor, $\chi_{LT}$", "IS 800 Cl. 8.2.2", rv(KEY_SD_LTB_CHI), NA),
        (r"LTB Resistance, $M_b$", r"$\chi_{LT}\,M_p / \gamma_{m0}$", rv(KEY_SD_LTB_MB, "kN-m"), NA),
        (r"$M_u \leq M_b$", r"$M_u / M_b$", _dfmt(ltb), _interaction_status(ltb)),
    ]
    t56 = _girder_table(r"Lateral Torsional Buckling Check -- Construction Stage", CHECK_COLS,
                        girder_entries, lambda i: ltb_rows, note="IRC 22 Cl. 603.3.3.1, IS 800 Cl. 8.2.2")

    stiff = [
        ("Shear Buckling Design Method", rv(KEY_SD_STIFF_METHOD)),
        ("Intermediate Stiffener Thickness (mm)", rv(KEY_SD_STIFF_INT_THICK)),
        ("Intermediate Stiffener Spacing (mm)", rv(KEY_SD_STIFF_INT_SPACING)),
        ("End Panel Stiffener Thickness (mm)", rv(KEY_SD_STIFF_END_THICK)),
        ("No. of End Panel Stiffeners", rv(KEY_SD_STIFF_END_COUNT)),
        ("Longitudinal Stiffeners", rv(KEY_SD_STIFF_LONG)),
    ]
    t57 = _girder_table(r"Stiffener Design Summary",
                        [("Girder", "C", 0.14), ("Item", "L", 0.52), ("Value", "C", 0.34)],
                        girder_entries, lambda i: stiff)

    # Intermediate stiffener checks only have data in Custom design mode (in
    # Optimized mode the stiffeners are auto-sized and there is nothing to verify).
    t58 = ""
    if str(bridge.input_dict.get(KEY_DESIGN_MODE, "Optimized")).strip().lower() in {"custom", "customized"}:
        ist = [
            (r"Min. Moment of Inertia, $I_s$", rv(KEY_SD_IS_IYS_MIN, "mm$^4$"), rv(KEY_SD_IS_IYS_PROV, "mm$^4$"),
             _ge_status(od.get(KEY_SD_IS_IYS_PROV), od.get(KEY_SD_IS_IYS_MIN))),
            (r"Buckling Resistance, $F_{qd} \geq F_q$", rv(KEY_SD_IS_FQ, "kN"), rv(KEY_SD_IS_FQD, "kN"),
             _ge_status(od.get(KEY_SD_IS_FQD), od.get(KEY_SD_IS_FQ))),
        ]
        t58 = _girder_table(r"Intermediate Stiffener Checks",
                            [("Girder", "C", 0.10), ("Check", "L", 0.34), ("Required", "C", 0.21),
                             ("Provided", "C", 0.21), ("Status", "C", 0.14)],
                            girder_entries, lambda i: ist, note="IS 800 Cl. 8.7.1.2")

    # Bearing stiffener checks (IS 800 Cl. 8.7.3). Resistances are 0 in
    # guidance-only mode → N/A.
    bs_r = od.get(KEY_SD_BS_R)

    def bs_check(key):
        prov = _fnum(od.get(key))
        if prov is None or prov <= 0.0 or bs_r is None:
            return ("N/A", "N/A", "N/A")
        return (f"{bs_r} kN", f"{prov} kN", _ge_status(prov, bs_r))

    bs = [("Web Buckling Resistance",) + bs_check(KEY_SD_BS_FCDW_WB),
          ("Local Crushing Resistance",) + bs_check(KEY_SD_BS_FCDW_LC),
          ("Bearing Capacity",) + bs_check(KEY_SD_BS_FPSD),
          ("Column Buckling Resistance",) + bs_check(KEY_SD_BS_FCD)]
    t59 = _girder_table(r"End Panel Stiffener Checks",
                        [("Girder", "C", 0.10), ("Check", "L", 0.34), ("Required", "C", 0.21),
                         ("Provided", "C", 0.21), ("Status", "C", 0.14)],
                        girder_entries, lambda i: bs, note="IS 800 Cl. 8.7.3")

    # Serviceability — deflection (IRC 22 Cl. 604.3.2); per-girder actuals are
    # persisted in output_dict under the "G1".."Gn" suffix by design().
    span = _fnum(bridge.input_dict.get(KEY_SPAN))
    allow_ll = span * 1000.0 / 800.0 if span else None
    allow_tot = span * 1000.0 / 600.0 if span else None

    def defl_rows(i):
        live = od.get(f"{KEY_SD_DEFL_LIVE}.G{i}")
        total = od.get(f"{KEY_SD_DEFL_TOTAL}.G{i}")
        return [
            (r"Live Load Deflection, $\delta_{LL}$ (mm)", f"L/800 = {allow_ll:.1f} mm" if allow_ll else "",
             _dfmt(live, 3), _le_status(live, allow_ll)),
            (r"Total Load Deflection, $\delta_{total}$ (mm)", f"L/600 = {allow_tot:.1f} mm" if allow_tot else "",
             _dfmt(total, 3), _le_status(total, allow_tot)),
        ]
    t510 = _girder_table(r"Serviceability -- Deflection Checks",
                         [("Girder", "C", 0.10), ("Check", "L", 0.34), ("Allowable", "C", 0.22),
                          ("Actual", "C", 0.20), ("Status", "C", 0.14)],
                         girder_entries, defl_rows, note="IRC 22 Cl. 604.3.2")

    dr = od.get("design_results", {}) or {}
    sig, sig_allow = dr.get(KEY_SD_STRESS_STEEL), dr.get(KEY_SD_STRESS_STEEL_ALLOWABLE)
    t511 = ReportTable(r"Serviceability -- Maximum Stress Limitation", [
        ("Girder", "C", 0.10), ("Element", "L", 0.30), ("Allowable Stress", "C", 0.22),
        ("Actual Stress", "C", 0.22), ("Status", "C", 0.16)], note="IRC 22 Cl. 604.3.1")
    for lbl, _ in girder_entries:
        t511.add_row([_tex(lbl), r"Structural Steel ($0.9\,f_y$)", _with(sig_allow, "MPa"),
                      _with(sig, "MPa"), _le_status(sig, sig_allow)])

    # Fatigue (IRC 22 Cl. 605): governing of normal/shear per girder
    fat = ((dr.get(KEY_SD_ULS_PER_GIRDER, {}) or {}).get("fatigue", {}) or {})
    t512 = ReportTable(r"Serviceability -- Fatigue Assessment", [
        ("Girder", "C", 0.12), (r"Stress Range, $\Delta\sigma$", "C", 0.24), (r"Fatigue Limit, $f_{fd}$", "C", 0.24),
        ("UR", "C", 0.20), ("Status", "C", 0.20)],
        note=r"IRC 22 Cl. 605 --- governing of normal and shear fatigue (worst by DCR). "
             r"Capacity reduction factor $\mu_r$ applied where plate thickness $>$ 25 mm.")
    for i, (lbl, _) in enumerate(girder_entries, start=1):
        g = fat.get(f"G{i}", {}) or {}
        t512.add_row([_tex(lbl), _with(g.get("demand"), "MPa"), _with(g.get("capacity"), "MPa"),
                      ur_tex(g.get("ur")) if g.get("ur") is not None else "", status_tex(g.get("status"))])

    # Girder design summary — controlling check per girder (highest DCR)
    pg = dr.get("per_girder", {}) or {}
    t513 = ReportTable(r"Girder Design Summary (DCR / Utilization Ratio)", [
        ("Girder", "C", 0.09), ("Controlling LC / Combination", "L", 0.27), ("Controlling Check", "L", 0.18),
        ("Demand", "C", 0.13), ("Capacity", "C", 0.13), ("UR", "C", 0.08), ("Status", "C", 0.12)],
        note=r"UR = Demand / Capacity; $\leq 1.0$ is a passing check. The controlling check is the "
             r"criterion with the highest UR for each girder, with the load case/combination that drives it.")
    for i, (lbl, _) in enumerate(girder_entries, start=1):
        gd = pg.get(f"G{i}", {}) or {}
        checks = gd.get("checks") or []
        if not checks:
            t513.add_row([_tex(lbl), "", "", "", "", "", ""])
            continue
        ctrl = max(checks, key=lambda c: c.get("dcr") or 0.0)
        ctrl_lc, best = None, None
        for lc_name, lc_data in (gd.get("per_lc") or {}).items():
            if str(lc_name).lower().startswith("envelope"):
                continue
            for chk in lc_data.get("checks") or []:
                if chk.get("id") == ctrl.get("check_id"):
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best:
                        best, ctrl_lc = d, lc_name
        if ctrl_lc is None:
            ctrl_lc = (gd.get("demand") or {}).get("governing_combination") or ""
        du, cu = ctrl.get("demand_unit"), ctrl.get("capacity_unit")
        du = du if du not in ("-", "–") else ""
        cu = cu if cu not in ("-", "–") else ""
        t513.add_row([_tex(lbl), _tex(str(ctrl_lc)), _tex(str(ctrl.get("name", ""))),
                      _with(ctrl.get("demand"), du), _with(ctrl.get("capacity"), cu),
                      ur_tex(ctrl.get("dcr"), 3), status_tex(ctrl.get("status"))])

    # Shear connectors (bridge level)
    t514 = ReportTable(r"Shear Connector Capacity", [
        ("Parameter", "L", 0.25), ("Formula", "C", 0.39), ("Value", "C", 0.14), ("Reference", "L", 0.22)])
    t514.add_row([r"Design Resistance, $Q_u$",
                  r"\makecell{$Q_u=\min(Q_{u,s},\,Q_{u,c})$\\[2pt]$Q_{u,s}=\dfrac{0.8\,f_u\,(\pi d^2/4)}{\gamma_v}$\\[2pt]"
                  r"$Q_{u,c}=\dfrac{0.29\,\alpha\,d^2\sqrt{f_{ck}\,E_{cm}}}{\gamma_v}$}",
                  _with(dr.get(KEY_SD_SC_Qu_kN), "kN"), "IRC 22 Cl. 606.3.1 (Eq. 6.1)"])
    t514.add_row([r"Fatigue Shear Resistance, $Q_r$", r"IRC 22 Table 8 ($\phi d$, $N_{sc}$)",
                  _with(dr.get(KEY_SD_SC_Qr_kN), "kN"), "IRC 22 Cl. 606.3.2 (Table 8)"])

    sc_prov = dr.get("stud_spacing_provided_mm")
    t515 = ReportTable(r"Shear Connector Spacing", [
        ("Criterion", "L", 0.32), ("Governing Spacing", "C", 0.24), ("Spacing Provided", "C", 0.24),
        ("Status", "C", 0.20)],
        note=r"IRC 22 Cl. 606.4, 606.9. Governing spacing $= \min(S_{L1}, S_{L2}, S_R)$.")
    for crit, req in (("ULS Shear (SL1)", dr.get(KEY_SD_SC_SL1)), ("Full Composite (SL2)", dr.get(KEY_SD_SC_SL2)),
                      ("SLS Fatigue (SR)", dr.get(KEY_SD_SC_SR)),
                      ("Max. Spacing Limit (IRC 22)", dr.get("stud_spacing_max_mm"))):
        t515.add_row([crit, _with(req, "mm", 1), _with(sc_prov, "mm", 1), _le_status(sc_prov, req)])

    ts_vl, ts_vrd = _fnum(dr.get(KEY_SD_TS_VL)), _fnum(dr.get(KEY_SD_TS_VRD))
    ts_ur = (ts_vl / ts_vrd) if (ts_vl is not None and ts_vrd) else None
    ts_ok = dr.get("transverse_shear_ok")
    # Provided transverse steel = deck main bars (bottom + top) crossing the shear
    # plane; read from the deck design (the steel designer runs before it).
    dd = od.get("deck_design_results", {}) or {}
    try:
        ast_prov = (float(dd.get("rebar_bottom_area") or 0) + float(dd.get("rebar_top_area") or 0)) / 100.0
    except (TypeError, ValueError):
        ast_prov = None
    ast_req = dr.get("Ast_required_cm2_per_m")
    stud_d = bridge.input_dict.get(KEY_DS_STUD_DIAMETER)
    d_lim, edge, edge_req = dr.get(KEY_SD_SC_D_LIMIT), dr.get(KEY_SD_SC_EDGE_DIST), dr.get(KEY_SD_SC_REQ_EDGE_DIST)
    t516 = ReportTable(r"Transverse Shear and Detailing Checks", [
        ("Check", "L", 0.42), ("Value", "L", 0.42), ("Status", "C", 0.16)], note="IRC 22 Cl. 606.6, 606.10.")
    t516.add_rows([
        (r"Longitudinal Shear per unit length, $V_L$", _with(ts_vl, "kN/m"), NA),
        (r"Transverse Shear Capacity of Slab, $V_{Rd}$", _with(ts_vrd, "kN/m"), NA),
        ("Transverse Shear Check", r"$V_L/V_{Rd}$ = " + (ur_tex(ts_ur) if ts_ur is not None else NA),
         pass_fail(ts_ok) if ts_ok is not None else NA),
        (r"Min. Transverse Reinforcement, $A_{st,min}$",
         "Required " + _with(ast_req, r"cm$^2$/m") + ", Provided " + _with(ast_prov, r"cm$^2$/m"),
         _ge_status(ast_prov, ast_req)),
        (r"Stud Diameter $\leq 2\,t_f$", r"$d$ = " + _with(stud_d, "mm", 1) + r" $\leq 2t_f$ = " + _with(d_lim, "mm", 1),
         _le_status(stud_d, d_lim)),
        ("Stud Edge Distance", "Provided " + _with(edge, "mm", 1) + r" (req. $\geq$ " + _with(edge_req, "mm", 1) + ")",
         _ge_status(edge, edge_req)),
    ])

    return (t51 + t52 + t53 + t54 + t55 + t56 + t57 + t58 + t59 + t510
            + t511.dumps() + t512.dumps() + t513.dumps() + t514.dumps() + t515.dumps() + t516.dumps())


# ── Deck slab ────────────────────────────────────────────────────────────────

class _Deck:
    """Helpers around output_dict["deck_report_values"] (keys = common.KEY_DD_*)."""
    PH = r"\placeholder{---}"

    def __init__(self, rpt):
        self.rpt = rpt or {}
        self.has = bool(self.rpt)
        self.oh = bool(self.rpt.get(KEY_DD_HAS_OVERHANG))

    def v(self, key, default=0.0):
        f = _fnum(self.rpt.get(key))
        return default if f is None else f

    def f(self, key, nd=2, scale=1.0):
        if not self.has:
            return self.PH
        val = self.rpt.get(key)
        if val is None or val == "":
            return self.PH
        x = _fnum(val)
        return f"{x * scale:.{nd}f}" if x is not None else str(val)

    def ok(self, cond):
        return pass_fail(cond) if self.has else NA

    def ohf(self, key, nd=2, unit=""):
        if not self.has:
            return self.PH
        if not self.oh:
            return "N/A"
        return self.f(key, nd) + unit

    def crack(self):
        wks = [self.v(KEY_DD_WK_BOT), self.v(KEY_DD_WK_TOP)] + ([self.v(KEY_DD_WK_OH)] if self.oh else [])
        return max(wks)

    def ratio(self, dem_key, cap_key):
        cap = self.v(cap_key)
        return (self.v(dem_key) / cap) if (self.has and cap > 0) else None


def _deck_section(bridge, deck):
    ind = bridge.input_dict
    rv = lambda key: _render_value(ind, key)
    dk = deck

    loading = kv_table(r"Deck Slab --- Loading and Geometry", [
        (r"Effective Span of Deck Slab, $l_{eff}$ (girder spacing, c/c)", dk.f(KEY_DD_SPAN, 0, 1000.0), "mm"),
        (r"Deck Thickness, $t_s$", rv(KEY_TS_DECK_THICKNESS), "mm"),
        ("Clear Cover, Top / Bottom (IRC 112 Cl. 15.2)", rv(KEY_DS_TOP_CLEAR_COVER) + " / " + rv(KEY_DS_BOTTOM_CLEAR_COVER), "mm"),
        ("Concrete Grade (IRC 112 Cl. 6.4)", rv(KEY_DECK_CONCRETE_GRADE_BASIC)
         + r" ($f_{ck}$ = " + rv(KEY_MATERIAL_DECK_FCK) + r", $f_{ctm}$ = " + rv(KEY_MATERIAL_DECK_FCTM) + ")", "MPa"),
        ("Reinforcement Grade (IRC 112 Cl. 6.2)", rv(KEY_DS_REINF_MATERIAL) + r" ($f_y$ = " + dk.f(KEY_DD_FY, 0) + ")", "MPa"),
        (r"Dead Load per Unit Area, $w_{DL}$ (slab self-weight)", dk.f(KEY_DD_WDL), r"kN/m\textsuperscript{2}"),
        ("IRC 6 Wheel Load (Class A / 70R)", dk.f(KEY_DD_WHEEL_LOAD, 1), "kN"),
        ("Tyre Contact Width, transverse (IRC 6 Annex A)", dk.f(KEY_DD_TYRE_WIDTH, 0, 1000.0), "mm"),
        ("Impact Factor (IRC 6 Cl. 208.2)", dk.f(KEY_DD_IMPACT_FACTOR, 3), "--"),
        ("Governing Live Load Case", dk.f(KEY_DD_VEHICLE), "--"),
    ])

    g_dl, g_ll = dk.f(KEY_DD_GAMMA_DL), dk.f(KEY_DD_GAMMA_LL)
    flex = ReportTable(r"Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)", [
        ("Location", "C", 0.15), ("Parameter", "L", 0.31), ("Formula / Reference", "C", 0.22),
        ("Value", "C", 0.19), ("Status", "C", 0.13)],
        note="IRC 112 Cl. 12.2. Distribution (longitudinal) reinforcement designed for 20\\% of main steel moment (IRC 21 Cl. 305.18).")
    flex.add_group(r"\makecell{At Midspan\\(Sagging)}", [
        (r"Transverse BM (DL), $M_{T,DL}$", r"$w_{DL}\,l_{eff}^2/10$", dk.f(KEY_DD_M_DL) + " kN-m/m", NA),
        (r"Transverse BM (LL), $M_{T,LL}$", "Effective width (IRC 112 B3.1)", dk.f(KEY_DD_M_LL) + " kN-m/m", NA),
        (r"Total Design BM, $M_{u,sag}$", g_dl + " DL + " + g_ll + " LL", dk.f(KEY_DD_M_ULS_SAG) + " kN-m/m", NA),
        (r"Effective depth, $d$", r"$t_s - c_{nom} - \phi/2$", dk.f(KEY_DD_D_BOT, 1) + " mm", NA),
        (r"Moment Capacity, $M_{Rd}$", "IRC 112 Cl. 12.2", dk.f(KEY_DD_MU_BOT) + " kN-m/m",
         dk.ok(dk.v(KEY_DD_MU_BOT) >= dk.v(KEY_DD_M_ULS_SAG))),
    ])
    flex.add_group(r"\makecell{At Support\\(Hogging)}", [
        (r"Total Design BM, $M_{u,hog}$", g_dl + " DL + " + g_ll + " LL", dk.f(KEY_DD_M_ULS_HOG) + " kN-m/m", NA),
        (r"Required Top Steel, $A_{st,top}$", r"$M_u / (0.87\,f_y\,d)$", dk.f(KEY_DD_AS_REQ_TOP, 0) + r" mm$^2$/m", NA),
        (r"Moment Capacity, $M_{Rd}$", "IRC 112 Cl. 12.2", dk.f(KEY_DD_MU_TOP) + " kN-m/m",
         dk.ok(dk.v(KEY_DD_MU_TOP) >= dk.v(KEY_DD_M_ULS_HOG))),
    ])

    pcols = [("Parameter", "L", 0.36), ("Formula / Reference", "C", 0.28), ("Value", "C", 0.22), ("Status", "C", 0.14)]
    oh = ReportTable(r"Deck Slab --- Cantilever Overhang Flexure Check", pcols,
                     note="IRC 6 Cl. 206.4 crash barrier loads applied at kerb face; IRC 112 Cl. 12.2 flexure.")
    oh.add_rows([
        (r"Overhang Length, $l_{oh}$", NA, _render_value(ind, KEY_TS_DECK_OVERHANG) + " m", NA),
        ("Crash Barrier Load Moment", "IRC 6 Cl. 206.4", dk.ohf(KEY_DD_M_BARRIER, unit=" kN-m/m"), NA),
        ("Dead Load Moment", r"$w_{DL}\,l_{oh}^2/2$ + railing", dk.ohf(KEY_DD_M_DL_OH, unit=" kN-m/m"), NA),
        ("Live Load Moment (eccentric wheel)", r"Wheel load $\times$ arm", dk.ohf(KEY_DD_M_LL_OH, unit=" kN-m/m"), NA),
        (r"Total Hogging Moment, $M_{u,oh}$", g_dl + " DL + " + g_ll + " (LL + CB)", dk.ohf(KEY_DD_M_ULS_OH, unit=" kN-m/m"), NA),
        (r"Moment Capacity (top steel), $M_{Rd,oh}$", "IRC 112 Cl. 12.2", dk.ohf(KEY_DD_MU_OH, unit=" kN-m/m"),
         dk.ok(dk.v(KEY_DD_MU_OH) >= dk.v(KEY_DD_M_ULS_OH)) if dk.oh else ("N/A" if dk.has else NA)),
    ])

    punch_ur = dk.ratio(KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA)
    punch = ReportTable(r"Deck Slab --- Punching Shear Check (IRC~112 Cl.~10.4.6)", pcols,
                        note=r"Punching shear reinforcement is not normally required for deck slabs with $d \geq 200$ mm "
                             r"and adequate longitudinal reinforcement.")
    punch.add_rows([
        (r"Design Wheel Load (ULS), $V_{Ed}$", r"$\gamma_Q\,(1+IF)\,P_w$", dk.f(KEY_DD_PUNCH_VED_KN, 1) + " kN", NA),
        ("Tyre Contact Area", r"$a \times b$ (IRC 6 Annex~A)",
         dk.f(KEY_DD_TYRE_WIDTH, 0, 1000.0) + r" $\times$ " + dk.f(KEY_DD_TYRE_LENGTH, 0) + " mm", NA),
        (r"Loaded Area at mid-depth, $b_0$", r"$c_1 \times c_2$ (incl.\ WC dispersion)",
         dk.f(KEY_DD_PUNCH_C1, 0) + r" $\times$ " + dk.f(KEY_DD_PUNCH_C2, 0) + " mm", NA),
        (r"Control Perimeter, $u_1$", r"$2(c_1+c_2) + 4\pi d$", dk.f(KEY_DD_PUNCH_U1, 0) + " mm", NA),
        (r"Punching Shear Stress, $v_{Ed}$", r"$V_{Ed} / (u_1\,d)$", dk.f(KEY_DD_PUNCH_VED, 3) + " MPa", NA),
        (r"Punching Resistance, $v_{Rd,c}$", r"IRC 112 Eq.\ 10.1", dk.f(KEY_DD_VRD_C_MPA, 3) + " MPa", NA),
        ("Punching Shear Check", r"$v_{Ed} \leq v_{Rd,c}$", ur_tex(punch_ur) if punch_ur is not None else dk.PH,
         dk.ok(bool(dk.rpt.get(KEY_DD_PUNCH_OK)))),
    ])

    gov_wk = dk.crack()
    crack = kv_table(r"Crack Width Check (Deck Slab)", [
        (r"Min. Reinforcement for Crack Control, $A_{s,min}$ [IRC 112 Cl. 16.5.1]", dk.f(KEY_DD_AS_MIN, 0), r"mm$^2$/m"),
        ("Provided Reinforcement (bottom)",
         r"$\phi$" + dk.f(KEY_DD_DIA_BOT, 0) + " @ " + dk.f(KEY_DD_SPC_BOT, 0) + " c/c (" + dk.f(KEY_DD_AS_BOT, 0) + r" mm$^2$/m)", "mm"),
        ("Max. Permissible Crack Width", dk.f(KEY_DD_WK_LIMIT), "mm"),
        (r"Calculated Crack Width, $w_k$ (governing)", f"{gov_wk:.4f}" if dk.has else dk.PH, "mm"),
        ("Crack Width Check", dk.ok(dk.has and gov_wk <= dk.v(KEY_DD_WK_LIMIT)), "--"),
    ])

    d_bot = dk.v(KEY_DD_D_BOT)
    shear_ur = dk.ratio(KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC)
    one_way = ReportTable(r"One-Way (Beam) Shear Check (Deck Slab)", pcols,
                          note="IRC 112 Cl. 10.3.2. Shear reinforcement not provided in deck slabs; capacity relies on "
                               "concrete and main reinforcement.")
    one_way.add_rows([
        (r"Design Shear per unit width, $V_{Ed}$", r"$\gamma_{DL} V_{DL} + \gamma_{LL}(1{+}IF)V_{LL}$",
         dk.f(KEY_DD_SHEAR_VED) + " kN/m", NA),
        (r"Effective depth, $d$", r"$t_s - c_{nom} - \phi/2$", dk.f(KEY_DD_D_BOT, 1) + " mm", NA),
        (r"Size factor, $k$", r"$1 + \sqrt{200/d} \leq 2.0$",
         f"{min(1.0 + (200.0 / d_bot) ** 0.5, 2.0):.3f}" if (dk.has and d_bot > 0) else dk.PH, NA),
        (r"Long.\ reinforcement ratio, $\rho_l$", r"$A_{sl}/(b_w\,d) \leq 0.02$",
         f"{min(dk.v(KEY_DD_AS_BOT) / (1000.0 * d_bot), 0.02):.4f}" if (dk.has and d_bot > 0) else dk.PH, NA),
        (r"Shear resistance (no stirrups), $V_{Rd,c}$", r"$v_{Rd,c}\,b_w\,d$ (Cl.\ 10.3.2)", dk.f(KEY_DD_SHEAR_VRDC) + " kN/m", NA),
        ("One-Way Shear Check", r"$V_{Ed} \leq V_{Rd,c}$", ur_tex(shear_ur) if shear_ur is not None else dk.PH,
         dk.ok(bool(dk.rpt.get(KEY_DD_SHEAR_OK)))),
    ])

    detail = ReportTable(r"Reinforcement Detailing Summary (Deck Slab)", [
        ("Parameter", "L", 0.38), ("Required / Limit", "C", 0.24), ("Provided", "C", 0.24), ("Status", "C", 0.14)],
        note="IRC 112 Cl. 16.3, IS 456 Cl. 26.5.")
    mm2 = r" mm$^2$/m"
    detail.add_subheader(r"Main Reinforcement --- Bottom (Transverse)")
    detail.add_rows([
        (r"Required Area, $A_{st,req}$", dk.f(KEY_DD_AS_REQ_BOT, 0) + mm2, dk.f(KEY_DD_AS_BOT, 0) + mm2,
         dk.ok(dk.v(KEY_DD_AS_BOT) >= dk.v(KEY_DD_AS_REQ_BOT))),
        (r"Bar Diameter $\times$ Spacing", r"$\phi \geq 10$ mm (IRC 112)",
         r"$\phi$" + dk.f(KEY_DD_DIA_BOT, 0) + " @ " + dk.f(KEY_DD_SPC_BOT, 0) + " mm c/c", NA),
        (r"Min.\ Reinforcement $A_{s,min}$ (IRC 112 Cl. 16.3.1)", dk.f(KEY_DD_AS_MIN, 0) + mm2, dk.f(KEY_DD_AS_BOT, 0) + mm2,
         dk.ok(dk.v(KEY_DD_AS_BOT) >= dk.v(KEY_DD_AS_MIN))),
        (r"Max.\ Bar Spacing (IRC 112 Cl. 16.3.2)", dk.f(KEY_DD_SPACING_MAX, 0) + " mm", dk.f(KEY_DD_SPC_BOT, 0) + " mm",
         dk.ok(0.0 < dk.v(KEY_DD_SPC_BOT) <= dk.v(KEY_DD_SPACING_MAX))),
    ])
    detail.add_subheader(r"Distribution Reinforcement --- Longitudinal")
    detail.add_row([r"Required Area, $A_{st,dist}$", r"$\geq 20\%$ of main steel", dk.f(KEY_DD_AS_LONG, 0) + mm2,
                    dk.ok(dk.v(KEY_DD_AS_LONG) >= max(0.20 * dk.v(KEY_DD_AS_BOT), dk.v(KEY_DD_AS_MIN)))])
    detail.add_subheader(r"Top Reinforcement (Support / Cantilever Overhang)")
    detail.add_row([r"Required Area, $A_{st,top}$", dk.f(KEY_DD_AS_REQ_TOP, 0) + mm2, dk.f(KEY_DD_AS_TOP, 0) + mm2,
                    dk.ok(dk.v(KEY_DD_AS_TOP) >= dk.v(KEY_DD_AS_REQ_TOP))])
    detail.add_subheader(r"Cover and Detailing")
    detail.add_row(["Clear Cover (IRC 112 Cl. 15.2)", r"$\geq$ " + dk.f(KEY_DD_MIN_COVER, 0) + " mm (Table 14.2)",
                    "Top " + _render_value(ind, KEY_DS_TOP_CLEAR_COVER) + " / Bottom "
                    + _render_value(ind, KEY_DS_BOTTOM_CLEAR_COVER) + " mm",
                    dk.ok(bool(dk.rpt.get(KEY_DD_COVER_OK)))])

    return (loading + flex.dumps() + oh.dumps() + punch.dumps() + crack + one_way.dumps() + detail.dumps())


# ── Cross bracing / end diaphragm ────────────────────────────────────────────

def _transverse_section(tm, title):
    """Section/slenderness/capacity tables for one TransverseMemberData group."""
    pairs = tm.pairs()

    props = ReportTable(title + r" --- Connection and Section Properties", [
        ("Panel", "C", 0.13), ("Member", "L", 0.17), ("Connection", "C", 0.16), ("Section", "C", 0.22),
        (r"$A_g$ (mm$^2$)", "C", 0.16), (r"$r_{min}$ (mm)", "C", 0.16)],
        note=r"$A_g$ = gross cross-sectional area; $r_{min}$ = minimum radius of gyration.")
    slender = ReportTable(title + r" --- Slenderness Ratio Check (IS~800 Cl.~3.8)", [
        ("Panel", "C", 0.13), ("Member", "L", 0.17), ("Nature", "C", 0.10), (r"Eff. Length $KL$ (mm)", "C", 0.17),
        (r"$KL/r$", "C", 0.13), ("Limit", "C", 0.13), ("Status", "C", 0.17)],
        note=r"Limit = 250 for compression members, 400 for tension members. $K = 1.0$ for members with both ends pinned.")
    cap = ReportTable(title + r" --- Capacity Summary", [
        ("Panel", "C", 0.11), ("Member", "L", 0.12), ("Section", "C", 0.15), ("Governing LC", "L", 0.18),
        ("Demand (kN)", "C", 0.12), ("Capacity (kN)", "C", 0.12), ("UR", "C", 0.08), ("Status", "C", 0.12)],
        note="Designed per IS 800 Cl. 7 (compression) and Cl. 6 (tension) using the Osdag member design modules.")

    if not pairs:
        for t in (props, slender, cap):
            t.add_span_row(r"\textit{No " + title.lower() + r" design results available}")
        return props.dumps() + slender.dumps() + cap.dumps()

    no_forces = not tm.has_forces()
    pending = (r"\textit{Member forces for the " + title.lower() + r"s are not computed by the analysis "
               r"in this version --- design check pending}")

    for pair in pairs:
        p_rows, c_rows = [], []
        for member, label in (("diagonal", "Diagonal"), ("chord", "Top / Bottom chord")):
            force, ftype = tm.governing_force(pair, member)
            area, rmin = tm.section_props(pair, member)
            p_rows.append((label, tm.connection(pair, member, ftype), tm.section(pair, member, ftype), area, rmin))
            c_rows.append((label.split(" /")[0] if member == "chord" else label, tm.section(pair, member, ftype),
                           tm.gov_lc(pair, member, ftype), force, tm.capacity(pair, member, ftype),
                           ur_tex(tm.efficiency(pair, member, ftype), 3), tm.status(pair, member, ftype)))
        props.add_group(_tex(pair), p_rows)
        if not no_forces:
            cap.add_group(_tex(pair), c_rows)

        s_rows = []
        kl_d, sl_d = tm.effective_length("diagonal"), tm.slenderness(pair, "diagonal")
        s_rows.append(("Diagonal", "C", kl_d, sl_d, "250", _le_status(sl_d, 250)))
        kl_c, sl_c = tm.effective_length("chord"), tm.slenderness(pair, "chord")
        if tm.has_chord("top"):
            s_rows.append(("Top chord", "C", kl_c, sl_c, "250", _le_status(sl_c, 250)))
        if tm.has_chord("bottom"):
            s_rows.append(("Bottom chord", "T", kl_c, sl_c, "400", _le_status(sl_c, 400)))
        if not no_forces:
            slender.add_group(_tex(pair), s_rows)

    if no_forces:
        slender.add_span_row(pending)
        cap.add_span_row(pending)
    return props.dumps() + slender.dumps() + cap.dumps()


def _transverse_ur(tm):
    """(compression row, tension row, slenderness row, chart items) for the summary."""
    def worst(force_type):
        best = None
        for pair in tm.pairs():
            for member in ("diagonal", "chord"):
                ur = _fnum(tm.efficiency(pair, member, force_type))
                if ur is not None and (best is None or ur > best[0]):
                    best = (ur, pair, member, tm.capacity(pair, member, force_type))
        if best is None:
            return (NA, NA, NA, NA), None
        ur, pair, member, cap = best
        dem = f"{float(cap) * ur:.2f} kN" if cap else NA
        return (tm.gov_lc(pair, member, force_type) or NA, dem, (cap + " kN") if cap else NA, ur_tex(ur)), ur

    def slender():
        best = None
        for pair in tm.pairs():
            for member in ("diagonal", "chord"):
                sf = _fnum(tm.slenderness(pair, member))
                if sf is None:
                    continue
                lim = 400.0 if member == "chord" else 250.0
                if best is None or sf / lim > best[0]:
                    best = (sf / lim, sf, lim)
        if best is None:
            return (NA, NA, NA, NA), None
        ratio, sf, lim = best
        return (NA, f"{sf:.1f}", f"{lim:.0f}", ur_tex(ratio)), ratio

    c_row, c_ur = worst("compression")
    t_row, t_ur = worst("tension")
    s_row, s_ur = slender()
    items = [("Compression", c_ur), ("Tension", t_ur), ("Slenderness", s_ur)]
    return c_row, t_row, s_row, items


# ── Overall summary (Section 5.5) ────────────────────────────────────────────

def _overall_summary(bridge, deck, asset_dir):
    od = bridge.output_dict
    pg = (od.get("design_results", {}) or {}).get("per_girder", {}) or {}

    def lc_short(lc):
        return _tex(str(lc).strip())

    def gov_lc(g, ids):
        best = None
        for lc, ld in ((pg.get(g) or {}).get("per_lc") or {}).items():
            if str(lc).lower().startswith("envelope"):
                continue
            for chk in (ld.get("checks") or []):
                if chk.get("id") in ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, lc)
        return lc_short(best[1]) if best else NA

    def dcr_row(ids, fallback_unit=""):
        """Worst girder for the given DCR-engine check ids → (cells, ur)."""
        best = None
        for g, gd in pg.items():
            if str(g).startswith("EB"):
                continue
            for chk in (gd.get("checks") or []):
                if chk.get("check_id") in ids:
                    d = chk.get("dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, chk.get("demand"), chk.get("capacity"),
                                chk.get("demand_unit") or "", chk.get("capacity_unit") or "", g)
        if best is not None:
            d, dem, cap, du, cu, g = best
            return (gov_lc(g, ids), _with(dem, du.strip()) or NA, _with(cap, cu.strip()) or NA, ur_tex(d)), d
        # SLS-conditional checks (e.g. deflection) only appear per load case
        best = None
        for g, gd in pg.items():
            if str(g).startswith("EB"):
                continue
            for lc, ld in (gd.get("per_lc") or {}).items():
                if str(lc).lower().startswith("envelope"):
                    continue
                for chk in (ld.get("checks") or []):
                    if chk.get("id") in ids:
                        d = chk.get("dcr") or 0.0
                        if best is None or d > best[0]:
                            best = (d, chk.get("demand"), chk.get("capacity"), lc)
        if best is None:
            return (NA, NA, NA, NA), None
        d, dem, cap, lc = best
        return (lc_short(lc), _with(dem, fallback_unit) or NA, _with(cap, fallback_unit) or NA, ur_tex(d)), d

    dk = deck
    deck_combo = (r"Basic ULS: " + _tex(f"{dk.v(KEY_DD_GAMMA_DL):g}DL + {dk.v(KEY_DD_GAMMA_LL):g}LL")) if dk.has else NA

    def deck_row(dem_key, cap_key, unit, is_oh=False):
        if not dk.has:
            return (NA, NA, NA, NA), None
        if is_oh and not dk.oh:
            return (deck_combo, "N/A", "N/A", "N/A"), None
        dem, cap = dk.v(dem_key), dk.v(cap_key)
        ur = (dem / cap) if cap > 0 else None
        return (deck_combo, f"{dem:.2f} {unit}", f"{cap:.2f} {unit}", ur_tex(ur)), ur

    def sls_frequent():
        best = None
        for g, gd in pg.items():
            if str(g).startswith("EB"):
                continue
            for lc, ld in (gd.get("per_lc") or {}).items():
                if "frequent" in str(lc).lower():
                    d = ld.get("max_dcr") or 0.0
                    if best is None or d > best[0]:
                        best = (d, lc)
        return _tex(str(best[1]).strip()) if best else "Frequent SLS"

    wk_lim = dk.v(KEY_DD_WK_LIMIT)
    gov_wk = dk.crack()
    crack_ur = (gov_wk / wk_lim) if (dk.has and wk_lim > 0) else None
    crack = ((sls_frequent() if dk.has else NA), (f"{gov_wk:.3f} mm" if dk.has else NA),
             (f"{wk_lim:.3f} mm" if dk.has else NA), ur_tex(crack_ur) if crack_ur is not None else NA)

    table = ReportTable(r"Overall Design Check Summary --- All Members", [
        ("Member / Check", "L", 0.27), ("Governing Load Combination", "L", 0.31), ("Demand", "C", 0.15),
        ("Capacity", "C", 0.15), ("UR", "C", 0.12)], label="tab:overall-summary",
        note=r"UR = Demand / Capacity. Values $\leq 1.0$ are passing checks; values above 1.0 are shown in red.")

    def add(label, row):
        table.add_row([label] + [x if x else NA for x in row])

    girder_items, deck_items = [], []
    table.add_subheader("Steel Plate Girders")
    for label, ids, unit in (("Moment", {1}, ""), ("Shear", {2}, ""), ("LTB (construction)", {5}, ""),
                             ("Deflection", {13, 14}, "mm"), ("Stress", {11}, "MPa"), ("Fatigue", {8, 9}, "MPa"),
                             ("Transverse Shear (slab)", {16}, "")):
        row, ur = dcr_row(ids, unit)
        add(label, row)
        girder_items.append((label.replace(" (construction)", "").replace(" (slab)", ""), ur))

    table.add_subheader("Concrete Deck Slab")
    for label, args in (("Flexure (sagging)", (KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT, "kN-m/m")),
                        ("Flexure (hogging)", (KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP, "kN-m/m")),
                        ("Cantilever Overhang", (KEY_DD_M_ULS_OH, KEY_DD_MU_OH, "kN-m/m", True)),
                        ("Punching Shear", (KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA, "MPa")),
                        ("One-Way Shear", (KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC, "kN/m"))):
        row, ur = deck_row(*args)
        add(label, row)
        deck_items.append((label, ur))
    add("Crack Width", crack)

    # The deck designer also stores its own utilisation ratios (ur_*), incl. the
    # SLS stress and composite-section crack checks that have no demand/capacity
    # pair in deck_report_values. Use those for the chart so the governing deck
    # UR here matches the executive summary.
    dd = od.get("deck_design_results", {}) or {}

    def ur_max(*keys):
        vals = [_fnum(dd.get(k)) for k in keys]
        vals = [v for v in vals if v is not None]
        return max(vals) if vals else None

    sls_ur = ur_max("ur_bot_sls_c", "ur_top_sls_c", "ur_oh_sls_c", "ur_bot_sls_s", "ur_top_sls_s",
                    "ur_oh_sls_s", "ur_composite_conc_stress", "ur_composite_rebar_stress")
    comp_crack = _fnum(dd.get("ur_composite_crack"))
    if sls_ur is not None:
        add("SLS Stress (concrete / rebar)", ("Frequent / Rare SLS", NA, NA, ur_tex(sls_ur)))
    if comp_crack is not None:
        add("Crack Width (composite section)", ("Frequent SLS", NA, NA, ur_tex(comp_crack)))
    if dd:
        deck_items = [
            ("Flexure (sagging)", ur_max("ur_bot_uls")),
            ("Flexure (hogging)", ur_max("ur_top_uls")),
            ("Cantilever Overhang", ur_max("ur_oh_uls")),
            ("Punching Shear", ur_max("ur_bot_punch", "ur_oh_punch")),
            ("One-Way Shear", ur_max("ur_bot_shear", "ur_oh_shear")),
            ("SLS Stress", sls_ur),
            ("Crack Width", ur_max("ur_bot_crack", "ur_top_crack", "ur_oh_crack", "ur_composite_crack")),
        ]
    else:
        deck_items.append(("Crack Width", crack_ur))

    table.add_subheader("Cross Bracing")
    c_row, t_row, s_row, cb_items = _transverse_ur(bridge.cb)
    add("Compression", c_row)
    add("Tension", t_row)
    add("Slenderness", s_row)

    table.add_subheader("End Diaphragms")
    ed_type = ""
    for k, v in bridge.input_dict.items():
        if str(k).startswith(KEY_MP_ED_TYPE) and v:
            ed_type = str(v)
            break
    if bridge.ed.pairs() and bridge.ed.has_forces():
        c_row, t_row, s_row, ed_items = _transverse_ur(bridge.ed)
        add("Compression", c_row)
        add("Tension", t_row)
        add("Slenderness", s_row)
    else:
        ed_items = []
        if ed_type and "brac" not in ed_type.lower():
            msg = _tex(ed_type) + r" end diaphragm --- design to be added"
        elif bridge.ed.pairs():
            msg = "Member forces not computed in this version --- design pending"
        else:
            msg = "No end diaphragm design results available"
        table.add_raw(r"\multicolumn{1}{|l|}{Design} & \multicolumn{4}{c|}{\textit{" + msg + r"}} \\ \hline")

    # ── UR charts ────────────────────────────────────────────────────────────
    groups = [("Steel Plate Girders", girder_items), ("Concrete Deck Slab", deck_items),
              ("Cross Bracing", cb_items), ("End Diaphragms", ed_items)]
    figs = ""
    if asset_dir:
        try:
            figs += charts.figure_tex(charts.ur_overview_chart(asset_dir, groups),
                                      r"Governing utilization ratio of each primary element (red dashed line: UR = 1.0)",
                                      label="fig:ur-overview")
            for name, items in groups:
                figs += charts.figure_tex(charts.ur_chart(asset_dir, name, items),
                                          name + r" --- utilization ratio per check (UR = Demand / Capacity)",
                                          label="fig:ur-" + name.lower().replace(" ", "-"),
                                          width=r"0.85\linewidth")
        except Exception as exc:  # a chart failure must not cost the whole report
            import logging
            logging.getLogger(__name__).warning("UR charts skipped: %s", exc)

    return table.dumps(), figs, groups


def ch5_design_checks(checks_data, bridge, asset_dir=None) -> str:
    """Chapter 5 — Design Checks.

    Parameters
    ----------
    checks_data : dict
        Raw checks payload (currently unused; data is sourced from bridge).
    bridge : ReportDataBridge
        Provides input_dict, output_dict, and helper methods.
    asset_dir : str, optional
        Folder for the generated UR charts. Charts are skipped when None.
    """
    girder_entries = get_girder_entries(bridge.input_dict)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]

    deck = _Deck(bridge.output_dict.get("deck_report_values", {}))
    summary_table, summary_figs, _ = _overall_summary(bridge, deck, asset_dir)

    return r"""
\chapter{Design Checks}

This section presents all structural design checks performed by OsdagBridge. For each member, the demand from the governing load combination, the code-based capacity, and the utilization ratio are tabulated. All checks reference IS 800:2007 and IRC 22:2014 unless stated otherwise.

\section{Plate Girder Design}
\label{sec:plate-girder}
""" + _plate_girder_section(bridge, girder_entries) + r"""

\section{Deck Slab Design}
\label{sec:deck-design}

The reinforced concrete deck slab is designed per IRC~112:2011 (flexure, shear, crack width) and IRC~22:2014 (composite construction). Wheel loads are distributed using Pigeaud's method. The deck is checked for flexure in the transverse and longitudinal directions, punching shear, one-way (beam) shear, crack width, and reinforcement detailing.
""" + _deck_section(bridge, deck) + r"""

\section{Cross Bracing Design}
\label{sec:cross-bracing}

Cross bracing between adjacent plate girders provides lateral stability during construction, resists transverse loads (wind, seismic, braking) in service, and prevents lateral torsional buckling of the girders. Members are designed per IS~800:2007 Cl.~7 (compression) and Cl.~6 (tension). Forces are derived from the grillage model under the governing load combination (DL + LL + WL).
""" + _transverse_section(bridge.cb, "Cross Bracing") + r"""

\section{End Diaphragm Design}
\label{sec:end-diaphragm}

End diaphragms at the supports transfer transverse loads to the bearings, restrain the bottom flanges against lateral displacement, and maintain the girder cross-section geometry during construction and in service. They are designed per IS~800:2007 and IRC~24:2010 Cl.~507.
""" + _transverse_section(bridge.ed, "End Diaphragm") + r"""

\section{Overall Design Check Summary}
\label{sec:overall-summary}

Table~\ref{tab:overall-summary} lists the governing utilization ratio of every primary element. The charts that follow show the same results graphically; bars above the red dashed line (UR $>$ 1.0) indicate a failing check.
""" + summary_table + summary_figs
