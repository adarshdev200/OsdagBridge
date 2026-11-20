# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_BL_IRC_CLASS_SV,
    KEY_CB_LOAD,
    KEY_FOOTPATH,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_ECCENTRICITY,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _tex, _render_value
from osdagbridge.core.reports.tables import ReportTable, kv_table
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

G = 9.81  # kN per tonne

# Vehicles offered in Additional Inputs > Loading > Live Load.
# (label, selection key, braking key, gross weight (t), impact rule)
# Braking is taken whenever the vehicle is selected, except Class SV which has
# its own opt-in checkbox (same rule as the Generate Results dialog).
# Gross weights are the IRC 6:2017 Cl. 204 train/vehicle loads.
IRC_VEHICLES = [
    ("Class A",           KEY_LL_IRC_CLASS_A,       KEY_LL_IRC_CLASS_A,       55.4, "class_a"),
    ("Class AA Wheeled",  KEY_LL_IRC_AA_WHEELED,    KEY_LL_IRC_AA_WHEELED,    40.0, "wheeled"),
    ("Class AA Tracked",  KEY_LL_IRC_AA_TRACKED,    KEY_LL_IRC_AA_TRACKED,    70.0, "tracked"),
    ("Class 70R Wheeled", KEY_LL_IRC_70R_WHEELED,   KEY_LL_IRC_70R_WHEELED,  100.0, "wheeled"),
    ("Class 70R Tracked", KEY_LL_IRC_70R_TRACKED,   KEY_LL_IRC_70R_TRACKED,   70.0, "tracked"),
    ("Class 70R Bogie",   KEY_LL_IRC_70R_BOGIE,     KEY_LL_IRC_70R_BOGIE,     40.0, "wheeled"),
    ("Class SV",          KEY_LL_IRC_CLASS_SV,      KEY_BL_IRC_CLASS_SV,     385.0, "none"),
    ("Class Fatigue",     KEY_LL_IRC_CLASS_FATIGUE, KEY_LL_IRC_CLASS_FATIGUE, 40.0, "class_a"),
]

BRAKING_FRACTION = 0.20   # IRC 6 Cl. 211.2 — 20 % of the first train load


def _checked(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in ("true", "yes", "1", "checked")
    return bool(v)


def _f(v, nd=2, default=""):
    try:
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return default


def impact_increment(rule: str, span: float):
    """IM for a steel superstructure, IRC 6:2017 Cl. 208 (None = not applied)."""
    fig5 = 9.0 / (13.5 + min(max(span, 3.0), 45.0))   # Cl. 208.2 / Fig. 5, steel
    if rule == "class_a":
        return fig5
    if rule == "tracked":
        if span <= 5.0:
            return 0.25
        if span < 9.0:                                  # 25 % at 5 m → 10 % at 9 m
            return 0.25 - 0.15 * (span - 5.0) / 4.0
        return 0.10
    if rule == "wheeled":
        return 0.25 if span <= 23.0 else fig5
    return None


def selected_vehicles(input_dict):
    """Rows for the selected vehicles only (custom vehicles appended)."""
    out = []
    for label, sel_key, bl_key, tonnes, rule in IRC_VEHICLES:
        if _checked(input_dict.get(sel_key)):
            out.append({"name": label, "weight_kN": tonnes * G, "rule": rule,
                        "braking": _checked(input_dict.get(bl_key))})
    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict) and c.get("name"):
                w = c.get("total_load_kN") or c.get("total_load")
                out.append({"name": c["name"], "weight_kN": w, "rule": "class_a", "braking": True})
            elif isinstance(c, str):
                out.append({"name": c, "weight_kN": None, "rule": "class_a", "braking": True})
    return out


def _vehicle_table(input_dict):
    try:
        span = float(input_dict.get(KEY_SPAN))
    except (TypeError, ValueError):
        span = None
    ecc = _f(input_dict.get(KEY_LL_ECCENTRICITY), 2,
             default=_f(IRC6_2017.cl_211_3_braking_force_location()["height_m"], 2))

    t = ReportTable(r"Vehicular Live Load (LL) --- IRC 6", [
        ("Vehicle", "L", 0.22), ("Total Load (kN)", "C", 0.14), ("Impact Factor", "C", 0.14),
        ("Considered?", "C", 0.16), ("Value (kN)", "C", 0.16), ("Eccentricity (m)", "C", 0.18),
    ], label="tab:vehicle-ll")
    h = t.head
    t.header_tex = (r"\rowcolor{tableHead}" + " & ".join([
        h(0, "Vehicle"), h(1, "Total Load"), h(2, "Impact Factor"), h(3, "Braking Load (IRC 6 Cl. 211)", span=3)])
        + r" \\" + "\n" + r"\cline{4-6}" + "\n" + r"\rowcolor{tableHead}" + " & ".join([
        h(0, ""), h(1, "(kN)"), h(2, r"$1 + I_M$"), h(3, "Considered?"), h(4, "Value (kN)"), h(5, "Eccentricity (m)")])
        + r" \\")

    vehicles = selected_vehicles(input_dict)
    if not vehicles:
        t.add_span_row(r"\textit{No vehicle selected in Additional Inputs $\rightarrow$ Loading $\rightarrow$ Live Load}")
    for v in vehicles:
        im = impact_increment(v["rule"], span) if span else None
        imp = _f(1.0 + im, 3) if im is not None else r"--\textsuperscript{\dag}"
        w = v["weight_kN"]
        if v["braking"]:
            brake = _f(BRAKING_FRACTION * float(w), 1, default="---") if w else "---"
            row = [_tex(v["name"]), _f(w, 1, "---"), imp, "Yes", brake, ecc]
        else:
            row = [_tex(v["name"]), _f(w, 1, "---"), imp, "No", "--", "--"]
        t.add_row(row)

    try:
        dla = 1.0 + IRC6_2017.cl_208_3_impact_factor(span) if span else None
    except Exception:
        dla = None
    note = (r"Impact factor per IRC 6 Cl. 208.2/208.3 (steel superstructure, span "
            + (_f(span, 2) + " m" if span else "--") + "). "
            r"Braking value = 20\% of the vehicle load (Cl. 211.2), applied at the stated height above the deck (Cl. 211.3). "
            r"\textsuperscript{\dag}Impact is not applied to Class SV, which crosses at crawl speed (Cl. 204.5).")
    if dla is not None:
        note += r" The grillage analysis applies $1 + I_M$ = " + _f(dla, 3) + r" to the moving-load cases."
    t.note = note
    return t.dumps()


def _footpath_table(input_dict):
    has_fp = str(input_dict.get(KEY_FOOTPATH, "")).strip().lower() not in ("", "none", "no", "false")
    fp_mode = str(input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "") or "").strip()
    fp_value = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")

    if fp_mode.lower() in ("as per irc 6", "as per irc6", "automatic", ""):
        try:
            pressure, source = _f(IRC6_2017.cl_206_1_footway_load(), 3), "IRC 6 Cl. 206.1"
        except Exception:
            pressure, source = "", "IRC 6 Cl. 206.1"
    else:
        pressure, source = _f(fp_value, 3), "User defined"

    t = ReportTable(r"Footpath Live Load (Pedestrian) --- IRC 6", [
        ("Parameter", "L", 0.40), ("Value", "C", 0.22), ("Unit", "C", 0.14), ("Reference", "L", 0.24),
    ], label="tab:footpath-ll")
    t.add_row(["Footpath", _render_value(input_dict, KEY_FOOTPATH) or "None", "--", "Basic inputs"])
    if has_fp:
        t.add_row(["Footpath Width", _render_value(input_dict, KEY_TS_FOOTPATH_WIDTH), "m", "IRC 5 Cl. 104.3.6"])
        t.add_row(["Pressure Mode", _tex(fp_mode or "As per IRC 6"), "--", "Additional inputs"])
        t.add_row(["Footpath Live Load Intensity", pressure, r"kN/m\textsuperscript{2}", source])
    else:
        t.add_span_row(r"\textit{No footpath provided --- footpath live load not applicable}")
    return t.dumps()


def _horizontal_forces_table(input_dict, vehicles):
    braked = [v for v in vehicles if v["braking"] and v["weight_kN"]]
    gov = max(braked, key=lambda v: float(v["weight_kN"])) if braked else None
    ecc = _f(input_dict.get(KEY_LL_ECCENTRICITY), 2, default="1.20")
    rows = [
        ("Governing Braking Force (" + (_tex(gov["name"]) if gov else "--") + ")",
         _f(BRAKING_FRACTION * float(gov["weight_kN"]), 1) if gov else "--", "kN", "IRC 6 Cl. 211.2"),
        ("Height of Braking Force above Deck", ecc, "m", "IRC 6 Cl. 211.3"),
        ("Centrifugal Force", "Not applicable", "--", "IRC 6 Cl. 212 (straight alignment)"),
    ]
    t = ReportTable(r"Horizontal Forces Associated with Live Load", [
        ("Parameter", "L", 0.40), ("Value", "C", 0.20), ("Unit", "C", 0.12), ("Reference", "L", 0.28),
    ], label="tab:ll-horizontal")
    t.add_rows(rows)
    t.note = r"Centrifugal force $C = WV^2/(127R)$ acts only on bridges on a horizontal curve; the bridge is modelled as straight ($R \to \infty$)."
    return t.dumps()


def ch3_loads(input_dict):
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    vb_val = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
    if not vz_val or not pz_val:
        try:
            _h   = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(vb_val))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass

    # Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah          = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av          = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z    = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st   = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp   = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res  = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            sl_zone_factor = sl_zone_factor or _res.get("Z")
            sl_spectral    = sl_spectral or _res.get("Sa_g_adjusted")
            sl_ah          = sl_ah or _res.get("Ah")
            sl_av          = sl_av or round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    # Temperature: effective bridge temperature range from shade temperatures
    tl_min = input_dict.get(KEY_TL_BRIDGE_TEMP_MIN)
    tl_max = input_dict.get(KEY_TL_BRIDGE_TEMP_MAX)
    tl_rise = input_dict.get(KEY_TL_TEMP_RISE)
    tl_fall = input_dict.get(KEY_TL_TEMP_FALL)
    _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
    _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP) or input_dict.get('shade_temp_min')
    if not (tl_min and tl_max) and _tmax and _tmin:
        try:
            _res = IRC6_2017.cl_215_2_effective_bridge_temperature(float(_tmax), float(_tmin), 'metallic', False)
            tl_min, tl_max = _res.get('T_min', 0), _res.get('T_max', 0)
            _mean = (tl_max + tl_min) / 2.0
            tl_rise, tl_fall = tl_max - _mean, _mean - tl_min
        except Exception:
            pass

    # --- Load Combinations (generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        'dead_load':         'DL',
        'surfacing':         'SIDL',
        'live_load':         'LL',
        'wind_load':         'WL',
        'thermal_load':      'TL',
        'vehicle_collision': 'VC',
        'barge_impact':      'BI',
        'floating_bodies':   'FB',
        'seismic':           'EQ',
    }

    def _fmt_factors(factors):
        """Format a factors dict into a compact load-case string for the table."""
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):  # permanent load with adding/relieving
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            elif val is not None:
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    combos = ReportTable(r"Load Combinations (IRC 6 Annex B)", [
        ("Combination ID", "C", 0.18), ("Load Cases and Partial Factors", "L", 0.82),
    ], label="tab:load-combos",
        note=r"All IRC 6 load combinations are auto-generated by OsdagBridge; factors shown as adding/relieving where applicable. "
             r"User-defined custom combinations, if any, are appended.")
    for i, combo in enumerate(IRC6_2017.uls_load_combinations(), start=1):
        combos.add_row([f"ULS-{i:02d}", _fmt_factors(combo['factors'])])
    for i, combo in enumerate(IRC6_2017.sls_load_combinations(), start=1):
        combos.add_row([f"SLS-{i:02d}", _fmt_factors(combo['factors'])])

    rv = lambda key: _render_value(input_dict, key)
    deg = r"$^\circ$C"
    wc = rv(KEY_WC_MATERIAL)
    wc_t = rv(KEY_WC_THICKNESS)

    dead = kv_table(r"Dead Load (DL) --- Self Weight", [
        ("Steel Unit Weight", rv(KEY_MATERIAL_GIRDER_DENSITY), r"kN/m\textsuperscript{3}"),
        ("Concrete Deck Unit Weight", rv(KEY_MATERIAL_DECK_DENSITY), r"kN/m\textsuperscript{3}"),
        ("Self-Weight Factor", rv(KEY_PL_SELF_WEIGHT_FACTOR), "--"),
    ], label="tab:dead-load")

    sidl = kv_table(r"Superimposed Dead Load for Surfacing (DW / SIDL)", [
        ("Wearing Course Material", wc, "--"),
        ("Wearing Course Thickness", wc_t, "mm"),
        ("Crash Barrier Load (per barrier)", rv(KEY_CB_LOAD), "kN/m"),
        ("Railing Load", (rv(KEY_RL_LOAD_VALUE) + r"\sdstar{}") if rv(KEY_RL_LOAD_VALUE) else "", "kN/m"),
    ], label="tab:sidl")

    wind = kv_table(r"Wind Load (WL) --- IRC 6 Cl. 209", [
        ("Basic Wind Speed, $V_b$ (from project location)", _f(vb_val, 2), "m/s"),
        ("Terrain Type", rv(KEY_WL_TERRAIN_TYPE), "--"),
        ("Average Exposed Height, $H$", rv(KEY_WL_AVG_EXPOSED_HEIGHT), "m"),
        ("Hourly Mean Wind Speed, $V_z$", _f(vz_val, 2), "m/s"),
        ("Hourly Wind Pressure, $P_z$", _f(pz_val, 2), r"N/m\textsuperscript{2}"),
        ("Transverse Wind Force", rv(KEY_WL_TRANSVERSE_WIND_FORCE), "kN"),
        ("Longitudinal Wind Force", rv(KEY_WL_LONGITUDINAL_WIND_FORCE), "kN"),
        ("Vertical Wind Force", rv(KEY_WL_VERTICAL_WIND_FORCE), "kN"),
    ], label="tab:wind")

    seismic = kv_table(r"Earthquake Load (EL) --- IRC 6 Cl. 218", [
        ("Seismic Zone (from project location)", rv('seismic_zone') or rv(KEY_SL_SEISMIC_ZONE), "--"),
        ("Zone Factor, $Z$", _f(sl_zone_factor, 2), "--"),
        ("Importance Factor, $I$", rv(KEY_SL_IMPORTANCE_FACTOR), "--"),
        ("Type of Soil", rv(KEY_SL_SOIL_TYPE), "--"),
        ("Spectral Acceleration Coefficient, $S_a/g$", _f(sl_spectral, 3), "--"),
        ("Horizontal Seismic Coefficient, $A_h$", _f(sl_ah, 4), "--"),
        ("Vertical Seismic Coefficient, $A_v$", _f(sl_av, 4), "--"),
    ], label="tab:seismic")

    temp = kv_table(r"Temperature Load (TL) --- IRC 6 Cl. 215", [
        ("Maximum Shade Temperature", _f(_tmax, 1), deg),
        ("Minimum Shade Temperature", _f(_tmin, 1), deg),
        ("Effective Bridge Temperature Range",
         (_f(tl_min, 2) + " to " + _f(tl_max, 2)) if (tl_min is not None and tl_max is not None) else "", deg),
        ("Temperature Rise / Fall for Design",
         ("+" + _f(tl_rise, 2) + r" / $-$" + _f(tl_fall, 2)) if (tl_rise is not None and tl_fall is not None) else "", deg),
    ], label="tab:temperature")

    vehicles = selected_vehicles(input_dict)

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\section{Permanent Loads}
""" + dead + sidl + r"""
\section{Live Loads}
\label{sec:live-loads}

Vehicular live loads are those selected under \textit{Additional Inputs $\rightarrow$ Loading $\rightarrow$ Live Load}. Pedestrian (footpath) live load is reported separately.

""" + _vehicle_table(input_dict) + _footpath_table(input_dict) + _horizontal_forces_table(input_dict, vehicles) + r"""
\section{Environmental Loads}
""" + wind + seismic + temp + r"""
\section{Load Combinations}
""" + combos.dumps()
