"""Tests for the report table builder, live-load tables, BOQ and charts."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from osdagbridge.core.reports.tables import ReportTable, kv_table  # noqa: E402
from osdagbridge.core.reports.styles import THEME, status_tex, ur_tex  # noqa: E402


# ── table builder ────────────────────────────────────────────────────────────

def _table():
    t = ReportTable("Demo", [("Girder", "C", 0.2), ("Check", "L", 0.5), ("Value", "C", 0.3)])
    t.add_group("G1", [["Moment", "0.8"], ["Shear", "0.4"]])
    t.add_row(["G2", "Moment", "0.7"])
    return t.dumps()


def test_header_repeats_on_every_page():
    tex = _table()
    assert r"\endfirsthead" in tex and r"\endhead" in tex
    # the header row is emitted once for the first page and once for the rest
    assert tex.count(r"\textbf{Girder}") == 2
    assert "(continued)" in tex


def test_group_rows_are_not_split_across_pages():
    tex = _table()
    assert r"\multirow{2}{=}{G1}" in tex
    assert r"\\* \cline{2-3}" in tex


def test_widths_never_exceed_text_width():
    t = ReportTable("Wide", [("A", "L", 0.8), ("B", "L", 0.8)])
    assert sum(w for _, _, w in t.columns) == pytest.approx(1.0)


def test_kv_table_with_units():
    tex = kv_table("Loads", [("Span", "30", "m")])
    assert r"\textbf{Unit}" in tex and "30 & m" in tex


def test_status_and_ur_colours():
    assert "failRed" in status_tex("FAIL")
    assert "passGreen" in status_tex("PASS")
    assert "failRed" in ur_tex(1.2)
    assert ur_tex(0.5) == "0.50"
    assert ur_tex(None) == "---"


# ── chapter 3 live loads ─────────────────────────────────────────────────────

chap3 = pytest.importorskip("osdagbridge.core.reports.chap3")


def test_only_selected_vehicles_are_listed():
    from osdagbridge.core.utils.common import KEY_LL_IRC_CLASS_A, KEY_LL_IRC_CLASS_SV, KEY_BL_IRC_CLASS_SV
    names = [v["name"] for v in chap3.selected_vehicles({
        KEY_LL_IRC_CLASS_A: True, KEY_LL_IRC_CLASS_SV: True, KEY_BL_IRC_CLASS_SV: False})]
    assert names == ["Class A", "Class SV"]


def test_class_sv_braking_follows_its_own_checkbox():
    from osdagbridge.core.utils.common import KEY_LL_IRC_CLASS_SV, KEY_BL_IRC_CLASS_SV
    sv = chap3.selected_vehicles({KEY_LL_IRC_CLASS_SV: True, KEY_BL_IRC_CLASS_SV: False})[0]
    assert sv["braking"] is False


@pytest.mark.parametrize("rule,span,expected", [
    ("class_a", 30.0, 9.0 / 43.5),
    ("tracked", 5.0, 0.25),
    ("tracked", 7.0, 0.175),
    ("tracked", 30.0, 0.10),
    ("wheeled", 20.0, 0.25),
    ("wheeled", 30.0, 9.0 / 43.5),
])
def test_impact_factor_irc6_cl208(rule, span, expected):
    assert chap3.impact_increment(rule, span) == pytest.approx(expected)


def test_impact_not_applied_to_special_vehicle():
    assert chap3.impact_increment("none", 30.0) is None


# ── BOQ: end diaphragms ──────────────────────────────────────────────────────

def test_end_diaphragm_beam_quantities():
    from osdagbridge.core.boq.boq_generator import _end_diaphragm_quantities
    from osdagbridge.core.utils.common import KEY_TS_GIRDER_SPACING
    out = {f"transverse_member_design.ed.section_properties.end_diaphragm.G{i}G{i+1}.A": 50.0
           for i in range(1, 4)}
    q = {}
    _end_diaphragm_quantities(q, {KEY_TS_GIRDER_SPACING: 2.5}, out, 4)
    # 3 bays x 2 supports, 50 cm^2 x 2.5 m each
    assert q["end_diaphragm_qty"] == "6"
    assert float(q["end_diaphragm_vol_total"]) == pytest.approx(6 * 0.005 * 2.5, rel=1e-3)


# ── charts ───────────────────────────────────────────────────────────────────

def test_ur_chart_written(tmp_path):
    pytest.importorskip("matplotlib")
    from osdagbridge.core.reports import charts
    path = charts.ur_chart(str(tmp_path), "Girders", [("Moment", 0.8), ("Shear", 1.1), ("LTB", None)])
    assert path and os.path.getsize(path) > 0
    assert charts.ur_chart(str(tmp_path), "Empty", [("x", None)]) is None
    tex = charts.figure_tex(path, "UR")
    assert r"\begin{figure}[H]" in tex and r"\includegraphics" in tex
