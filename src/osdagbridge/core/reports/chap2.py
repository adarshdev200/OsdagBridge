# Chapter 2: Input Parameters — exact LaTeX template match


from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_CB_LOAD,
    KEY_CB_TYPE,
    KEY_CROSS_BRACING,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DO_GAMMA_C_BASIC,
    KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_MF,
    KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V,
    KEY_END_DIAPHRAGM,
    KEY_FOOTPATH,
    KEY_GIRDER,
    KEY_INCLUDE_MEDIAN,
    KEY_MD_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_MEMBER_ID,
    KEY_MP_CB_SELECT_GIRDERS,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TYPE,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_MEMBER_ID,
    KEY_MP_ED_SELECT_GIRDERS,
    KEY_MP_ED_TYPE,
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_SYMMETRY,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_TYPE,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_WEB_TYPE,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_LONGITUDINAL,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_SPACING,
    KEY_RL_LOAD_VALUE,
    KEY_RL_TYPE,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SKEW_ANGLE,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS
)

from osdagbridge.core.reports.report_utils import _render_value, get_girder_entries, _tex
from osdagbridge.core.reports.tables import ReportTable, kv_table

DEG = r"$^\circ$"
DEG_C = r"$^\circ$C"


def _v(d, key):
    return _render_value(d, key)


def ch2_input_parameters(m, input_dict, output_dict=None):
    girder_entries = get_girder_entries(input_dict)
    n_girders = len(girder_entries)

    lat, lon = _v(input_dict, 'latitude'), _v(input_dict, 'longitude')
    latlon = (lat + ", " + lon) if (lat or lon) else ""
    tmax, tmin = _v(input_dict, 'shade_temp_max'), _v(input_dict, 'shade_temp_min')

    location = kv_table(r"Project Location", [
        ("Project Location", _tex(m.project_location), ""),
        ("Latitude / Longitude", latlon, DEG),
        ("Seismic Zone (IRC 6)", _v(input_dict, 'seismic_zone'), ""),
        ("Basic Wind Speed (IRC 6)", _v(input_dict, 'wind_speed'), "m/s"),
        ("Shade Temperature Max / Min (IRC 6)", (tmax + " / " + tmin) if (tmax or tmin) else "", DEG_C),
    ], label="tab:project-location")

    geometry = kv_table(r"Bridge Geometry", [
        ("Type of Structure", _v(input_dict, KEY_STRUCTURE_TYPE), ""),
        ("Span", _v(input_dict, KEY_SPAN), "m"),
        ("Carriageway Width", _v(input_dict, KEY_CARRIAGEWAY_WIDTH), "m"),
        ("Include Median", _v(input_dict, KEY_INCLUDE_MEDIAN), ""),
        ("Footpath", _v(input_dict, KEY_FOOTPATH), ""),
        ("Skew Angle (IRC 24 Cl. 504.8 limit: $\\pm$15" + DEG + ")", _v(input_dict, KEY_SKEW_ANGLE), DEG),
    ], label="tab:bridge-geometry")

    material = kv_table(r"Material Selection", [
        ("Girder Steel Grade (IS 2062)", _v(input_dict, KEY_GIRDER), ""),
        ("Cross Bracing Steel Grade", _v(input_dict, KEY_CROSS_BRACING), ""),
        ("End Diaphragm Steel Grade", _v(input_dict, KEY_END_DIAPHRAGM), ""),
        ("Concrete Deck Grade (IRC 22)", _v(input_dict, KEY_DECK_CONCRETE_GRADE_BASIC), ""),
    ], label="tab:material")

    lanes = _v(input_dict, KEY_WC_LD_LANE_TABLE_COUNT)
    lanes_ref = "IRC 5 Cl. 104.3.1"
    if not lanes:
        try:
            from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
            lanes = str(IRC6_2017.table_6(float(input_dict.get(KEY_CARRIAGEWAY_WIDTH))))
            lanes_ref = "IRC 6 Table 6, from carriageway width"
        except (TypeError, ValueError):
            lanes = ""

    typical = kv_table(r"Typical Section Details", [
        ("Overall Bridge Width", _v(input_dict, KEY_TS_OVERALL_WIDTH), "m"),
        ("No. of Girders", _v(input_dict, KEY_TS_NO_OF_GIRDERS), "--"),
        ("Girder Spacing", _v(input_dict, KEY_TS_GIRDER_SPACING), "m"),
        ("Deck Overhang Width", _v(input_dict, KEY_TS_DECK_OVERHANG), "m"),
        ("Deck Thickness", _v(input_dict, KEY_TS_DECK_THICKNESS), "mm"),
        ("Footpath Width (IRC 5 Cl. 104.3.6, min. 1.5 m)", _v(input_dict, KEY_TS_FOOTPATH_WIDTH), "m"),
        ("No. of Design Lanes (" + lanes_ref + ")", lanes, "--"),
    ], label="tab:typical-section")

    comp_rows = [
        ("Crash Barrier Type", _v(input_dict, KEY_CB_TYPE), ""),
        ("Crash Barrier Load", _v(input_dict, KEY_CB_LOAD), "kN/m"),
    ]
    # Median row only shown when the user included a median
    if str(input_dict.get(KEY_INCLUDE_MEDIAN, "")).strip().lower() in ("yes", "true", "1"):
        comp_rows.append(("Median Type", _v(input_dict, KEY_MD_TYPE), ""))
    comp_rows += [
        ("Railing Type", _v(input_dict, KEY_RL_TYPE), ""),
        ("Railing Load", _v(input_dict, KEY_RL_LOAD_VALUE), "kN/m"),
        ("Wearing Course Material", _v(input_dict, KEY_WC_MATERIAL), ""),
        ("Wearing Course Thickness", _v(input_dict, KEY_WC_THICKNESS), "mm"),
    ]
    components = kv_table(r"Components Details", comp_rows, label="tab:components")

    return r"""
\chapter{Input Parameters}

This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly distinguished from software-assumed defaults. Where the user did not supply a value, the software has applied the IRC/IS code default or an empirical guideline; these are annotated with an asterisk (\sdstar{}).

\section{Basic Inputs (User-Defined)}
\label{sec:basic-inputs}

\noindent\textit{These inputs are mandatory and were provided by the user.}

""" + location + geometry + material + r"""

\section{Additional Inputs}
\label{sec:additional-inputs}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.

""" + typical + components \
        + _girder_tables(input_dict, n_girders) \
        + _bracing_tables(input_dict, n_girders) \
        + _shear_connector_table(input_dict, output_dict) \
        + _safety_factors_table(input_dict)


def _girder_tables(input_dict, n_girders):
    # Fetch backend-populated labels via exact suffix pattern (defaults.py)
    # KEY_MP_GD_SELECT_GIRDER.G{i}    = 'G{i}'
    # KEY_MP_GD_MEMBER_ID.G{i}.M1     = 'G{i}M1'
    # All other girder/stiffener keys: {BASE_KEY}.G{i}.M1
    n = n_girders if n_girders >= 1 else 1
    girder_entries = get_girder_entries(input_dict)
    if not girder_entries:
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]

    def gv(base, i):
        return _v(input_dict, f"{base}.G{i}.M1")

    def mm(base, i):
        # design() converts the girder plate sizes to metres in place
        # (_convert_girder_dims_mm_to_m), so the same key can hold mm or m.
        v = input_dict.get(f"{base}.G{i}.M1")
        try:
            f = float(v)
        except (TypeError, ValueError):
            return _tex(v) if v not in (None, "") else ""
        if 0 < f < 5:
            f *= 1000.0
        return f"{f:.0f}" if abs(f - round(f)) < 1e-6 else f"{f:.1f}"

    general = ReportTable(r"Girder General Information", [
        ("Girder", "C", 0.13), ("Member ID", "C", 0.15), ("Design Mode", "C", 0.22),
        ("Girder Type", "C", 0.25), ("Girder Symmetry", "C", 0.25),
    ], label="tab:girder-general")
    dims = ReportTable(r"Girder Section Dimensions (mm)", [
        ("Girder", "C", 0.12), ("Total Depth, $D$", "C", 0.16), ("Web, $t_w$", "C", 0.14),
        ("Top Flange ($b_{tf} \\times t_{tf}$)", "C", 0.29), ("Bottom Flange ($b_{bf} \\times t_{bf}$)", "C", 0.29),
    ], label="tab:girder-dims")
    restraint = ReportTable(r"Girder Restraint and Stiffener Details", [
        ("Girder", "C", 0.11), ("Torsional / Warping Restraint", "L", 0.17), ("Web Philosophy", "L", 0.14),
        ("Intermediate Stiffeners", "L", 0.20), ("Longitudinal Stiffeners", "L", 0.16),
        ("Bearing Stiffener", "L", 0.22),
    ], label="tab:girder-restraint")

    for i, (lbl, mid) in enumerate(girder_entries, start=1):
        lbl_t = _tex(lbl)
        general.add_row([lbl_t, _tex(mid), _v(input_dict, KEY_DESIGN_MODE),
                         gv(KEY_MP_GIRDER_TYPE, i), gv(KEY_MP_GIRDER_SYMMETRY, i)])
        dims.add_row([lbl_t, mm(KEY_MP_GIRDER_DEPTH, i), mm(KEY_MP_GIRDER_WEB_THICKNESS, i),
                      mm(KEY_MP_GIRDER_TOP_FLANGE_WIDTH, i) + r" $\times$ " + mm(KEY_MP_GIRDER_TOP_FLANGE_THICKNESS, i),
                      mm(KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH, i) + r" $\times$ " + mm(KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS, i)])
        restraint.add_row([
            lbl_t,
            gv(KEY_MP_GIRDER_TORSIONAL_RESTRAINT, i) + ", " + gv(KEY_MP_GIRDER_WARPING_RESTRAINT, i),
            gv(KEY_MP_GIRDER_WEB_TYPE, i),
            gv(KEY_MP_STIFFENER_INTERMEDIATE, i)
            + r"; spacing " + gv(KEY_MP_STIFFENER_INTERMEDIATE_SPACING, i) + " mm"
            + r"; $t$ = " + gv(KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS, i) + " mm",
            gv(KEY_MP_STIFFENER_LONGITUDINAL, i),
            "No. " + gv(KEY_MP_STIFFENER_NO_BEARING_STIFFENERS, i)
            + r"; spacing " + gv(KEY_MP_STIFFENER_SPACING, i) + " mm"
            + r"; $t$ = " + gv(KEY_MP_STIFFENER_BEARING_THICKNESS, i) + " mm",
        ])

    return general.dumps() + dims.dumps() + restraint.dumps()


def _bracing_tables(input_dict, n_girders):
    n = n_girders if n_girders >= 2 else 2

    cb = ReportTable(r"Member Properties: Cross Bracing Details", [
        ("Location", "C", 0.16), ("Member IDs", "C", 0.18), ("Type of Bracing", "C", 0.22),
        ("Bracing Section", "C", 0.28), ("Spacing (m)", "C", 0.16),
    ], label="tab:cb-details")
    ed = ReportTable(r"Member Properties: End Diaphragm Details", [
        ("Location", "C", 0.18), ("Member IDs", "C", 0.22), ("Type", "C", 0.25),
        ("Section", "C", 0.35),
    ], label="tab:ed-details")

    for i in range(1, n):
        cb_sfx = f"G{i}G{i+1}.B{i}M1"
        ed_sfx = f"G{i}G{i+1}.E{i}M1"
        cb.add_row([
            _v(input_dict, f"{KEY_MP_CB_SELECT_GIRDERS}.{cb_sfx}"),
            _v(input_dict, f"{KEY_MP_CB_MEMBER_ID}.{cb_sfx}"),
            _v(input_dict, f"{KEY_MP_CB_TYPE}.{cb_sfx}"),
            _v(input_dict, f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.{cb_sfx}"),
            _v(input_dict, f"{KEY_MP_CB_SPACING}.{cb_sfx}"),
        ])
        ed.add_row([
            _v(input_dict, f"{KEY_MP_ED_SELECT_GIRDERS}.{ed_sfx}"),
            _v(input_dict, f"{KEY_MP_ED_MEMBER_ID}.{ed_sfx}"),
            _v(input_dict, f"{KEY_MP_ED_TYPE}.{ed_sfx}"),
            _v(input_dict, f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}.{ed_sfx}"),
        ])
    return cb.dumps() + ed.dumps()


def _shear_connector_table(input_dict, output_dict=None):
    # Stud computed properties live in output_dict (populated by store_design_results)
    od = output_dict or {}
    return r"\label{subsec:shear-connectors}" + kv_table(r"Shear Connector Details", [
        ("Stud Diameter", _v(od, KEY_SD_SHEAR_DIAMETER), "mm"),
        ("Stud Height", _v(od, KEY_SD_SHEAR_HEIGHT), "mm"),
        ("Stud Yield Strength, $f_y$", _v(od, KEY_SD_SHEAR_YIELD_STRENGTH), "MPa"),
        ("Stud Ultimate Strength, $f_u$", _v(od, KEY_SD_SHEAR_ULTIMATE_STRENGTH), "MPa"),
        ("No. of Studs per Section", _v(od, KEY_SD_SHEAR_STUDS_PER_SECTION), "--"),
    ])


def _safety_factors_table(input_dict):
    return r"\label{subsec:safety-factors}" + kv_table(r"Partial Safety Factors", [
        (r"$\gamma_{M0}$ (Yielding / Buckling)", _v(input_dict, KEY_DO_GAMMA_M0)),
        (r"$\gamma_{M1}$ (Ultimate Stress)", _v(input_dict, KEY_DO_GAMMA_M1)),
        (r"$\gamma_C$ (Concrete, Basic)", _v(input_dict, KEY_DO_GAMMA_C_BASIC)),
        (r"$\gamma_s$ (Reinforcement)", _v(input_dict, KEY_DO_GAMMA_S)),
        (r"$\gamma_v$ (Shear Connectors)", _v(input_dict, KEY_DO_GAMMA_V)),
        (r"$\gamma_{fft}$ (Fatigue Load)", _v(input_dict, KEY_DO_GAMMA_FLT)),
        (r"$\gamma_{Mft}$ (Fatigue Strength)", _v(input_dict, KEY_DO_GAMMA_MF)),
    ], with_unit=False, headers=("Factor", "Value"), widths=(0.6, 0.4),
        note="All values are per IRC 22 Table 1 unless user-modified.")
