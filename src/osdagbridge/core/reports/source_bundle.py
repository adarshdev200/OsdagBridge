# =============================================================================
# OsdagBridge Report — LaTeX source bundle
#
# The report is compiled in a temporary folder that also holds the generated
# figures and logos. A lone .tex copied out of that folder cannot be compiled
# again (its images are gone with the folder), so the source is handed out as
# a zip of the whole build folder instead. Unzipped, it compiles as is with
# pdflatex, or can be uploaded straight to Overleaf.
#
# The bundle is written when the user asks for it, and also whenever no PDF
# could be made (pdflatex missing or the compile failed), so the work done
# up to that point is never thrown away.
# =============================================================================

import os
import shutil
import zipfile
from typing import Optional

# LaTeX by-products that only clutter the bundle; the log is kept on request
# because it is the first thing anyone needs when a compile has failed.
_BUILD_JUNK = (".aux", ".toc", ".out", ".lof", ".lot", ".pdf", ".synctex.gz", ".fls", ".fdb_latexmk")


def find_compiler(compiler: str) -> Optional[str]:
    """Full path of the LaTeX compiler, or None when it is not installed."""
    if not compiler:
        return None
    if os.path.dirname(compiler):
        return compiler if os.path.isfile(compiler) else None
    return shutil.which(compiler)


def bundle_name(file_stem: str) -> str:
    return file_stem + "_latex_source.zip"


def _relative_tex(text: str, build_dir: str) -> str:
    """Turn absolute paths into the build folder (figures and charts are
    included by full path) into paths relative to the .tex, which is where
    pdflatex runs after unzipping."""
    prefixes = {os.path.abspath(build_dir), os.path.realpath(build_dir)}
    # longest first, so /private/var/... is not left half-replaced by /var/...
    for prefix in sorted(prefixes, key=len, reverse=True):
        text = text.replace(prefix.replace(os.sep, "/").rstrip("/") + "/", "")
    return text


def write_source_bundle(build_dir: str, zip_path: str, include_log: bool = False) -> Optional[str]:
    """Zip the report build folder (tex, images, logos, attachments).

    Paths inside the zip are relative to the build folder and the .tex is
    rewritten to match, so the unzipped folder compiles anywhere.
    Returns the zip path, or None if there was nothing to write.
    """
    entries = []
    for root, _dirs, files in os.walk(build_dir):
        for name in sorted(files):
            lower = name.lower()
            if lower.endswith(_BUILD_JUNK):
                continue
            if lower.endswith(".log") and not include_log:
                continue
            full = os.path.join(root, name)
            entries.append((full, os.path.relpath(full, build_dir).replace(os.sep, "/")))
    if not any(arc.endswith(".tex") for _, arc in entries):
        return None

    os.makedirs(os.path.dirname(os.path.abspath(zip_path)), exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for full, arc in sorted(entries, key=lambda e: e[1]):
            if arc.lower().endswith(".tex"):
                with open(full, encoding="utf-8", errors="replace") as fh:
                    zf.writestr(arc, _relative_tex(fh.read(), build_dir))
            else:
                zf.write(full, arc)
    return zip_path
