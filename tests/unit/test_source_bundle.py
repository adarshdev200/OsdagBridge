"""Tests for saving the report's LaTeX source as a compilable zip."""
import os
import shutil
import sys
import zipfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from osdagbridge.core.reports.source_bundle import (  # noqa: E402
    bundle_name, find_compiler, write_source_bundle,
)


def _build_dir(tmp_path):
    d = tmp_path / "build"
    (d / "images").mkdir(parents=True)
    (d / "report.tex").write_text(r"\includegraphics{images/plan.png}")
    (d / "images" / "plan.png").write_bytes(b"png")
    for junk in ("report.aux", "report.toc", "report.pdf", "report.log"):
        (d / junk).write_text("x")
    return d


def test_bundle_keeps_tex_and_images_with_relative_paths(tmp_path):
    zip_path = write_source_bundle(str(_build_dir(tmp_path)), str(tmp_path / "out.zip"))
    names = zipfile.ZipFile(zip_path).namelist()
    # the .tex refers to images/plan.png, so the zip must use the same layout
    assert "report.tex" in names and "images/plan.png" in names


def test_absolute_build_paths_become_relative(tmp_path):
    d = _build_dir(tmp_path)
    absolute = str(d / "images" / "plan.png").replace(os.sep, "/")
    (d / "report.tex").write_text(r"\includegraphics{" + absolute + "}")
    zf = zipfile.ZipFile(write_source_bundle(str(d), str(tmp_path / "out.zip")))
    assert zf.read("report.tex").decode() == r"\includegraphics{images/plan.png}"


def test_bundle_drops_build_files_and_keeps_log_only_on_request(tmp_path):
    d = _build_dir(tmp_path)
    plain = zipfile.ZipFile(write_source_bundle(str(d), str(tmp_path / "a.zip"))).namelist()
    assert not any(n.endswith((".aux", ".toc", ".pdf", ".log")) for n in plain)
    with_log = zipfile.ZipFile(write_source_bundle(str(d), str(tmp_path / "b.zip"),
                                                   include_log=True)).namelist()
    assert "report.log" in with_log


def test_no_bundle_without_a_tex_file(tmp_path):
    (tmp_path / "empty").mkdir()
    assert write_source_bundle(str(tmp_path / "empty"), str(tmp_path / "x.zip")) is None
    assert not (tmp_path / "x.zip").exists()


def test_find_compiler(tmp_path):
    assert find_compiler("") is None
    assert find_compiler("no-such-latex-binary-xyz") is None
    assert find_compiler(str(tmp_path / "missing" / "pdflatex")) is None
    fake = tmp_path / "pdflatex"
    fake.write_text("")
    assert find_compiler(str(fake)) == str(fake)


def test_bundle_name():
    assert bundle_name("bridge_report") == "bridge_report_latex_source.zip"


# ── generate_report without a LaTeX installation ─────────────────────────────

rg = pytest.importorskip("osdagbridge.core.reports.report_generator")


def _request(out_dir, include_source):
    md = rg.ReportMetadata(project_name="Demo", project_location="", designer="",
                           client="", company="")
    opts = rg.ReportOptions(sections=[], include_figures=False, include_toc=False,
                            include_pdf=True, include_source=include_source)
    return rg.ReportRequest(metadata=md, options=opts, output_dir=str(out_dir), file_stem="demo")


def test_missing_pdflatex_still_saves_the_source(tmp_path, monkeypatch):
    monkeypatch.setattr(rg, "find_compiler", lambda _c: None)
    req = _request(tmp_path, include_source=False)
    result = rg.generate_report(rg.build_report_payload(req, {}, {}), req)

    assert result.pdf_path is None
    assert "pdflatex was not found" in result.message
    assert result.source_zip and os.path.exists(result.source_zip)
    assert "demo.tex" in zipfile.ZipFile(result.source_zip).namelist()


def test_stale_pdf_is_not_reported_as_new_output(tmp_path, monkeypatch):
    (tmp_path / "demo.pdf").write_bytes(b"%PDF old report")
    monkeypatch.setattr(rg, "find_compiler", lambda _c: None)
    req = _request(tmp_path, include_source=False)
    result = rg.generate_report(rg.build_report_payload(req, {}, {}), req)
    assert result.pdf_path is None
    assert not (tmp_path / "demo.pdf").exists()


@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="needs pdflatex")
def test_source_zip_on_request(tmp_path):
    req = _request(tmp_path, include_source=True)
    result = rg.generate_report(rg.build_report_payload(req, {}, {}), req)
    assert result.pdf_path and os.path.exists(result.pdf_path)
    assert result.source_zip and os.path.exists(result.source_zip)
