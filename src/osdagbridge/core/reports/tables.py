# =============================================================================
# OsdagBridge Report — table builder
#
# All report tables go through ReportTable, which renders a PyLaTeX LongTable
# with:
#   * the caption + column header on the first page (\endfirsthead)
#   * "Table x.y (continued)" + the same header on every following page (\endhead)
#   * a "Continued on next page" line at every page break (\endfoot)
#   * column widths given as fractions of \linewidth, so a table can never be
#     wider than the text block
#   * row groups (one girder / one bracing panel) that are never split across
#     pages — a page break inside a \multirow block is what used to push the
#     girder label (e.g. "G4") down into the footer.
#
# Styling (fonts, padding, colours) is read from styles.THEME only.
# =============================================================================

from typing import Iterable, List, Optional, Sequence, Tuple, Union

from pylatex import LongTable, NoEscape

from osdagbridge.core.reports.styles import THEME

_ALIGN = {
    "L": r">{\raggedright\arraybackslash}",
    "C": r">{\centering\arraybackslash}",
    "R": r">{\raggedleft\arraybackslash}",
}


def col_spec(align: str, frac: float) -> str:
    """p-column whose width is `frac` of the line width (padding/rules included)."""
    return (_ALIGN[align.upper()] + r"p{\dimexpr " + f"{frac:.3f}"
            + r"\linewidth-2\tabcolsep-1.5\arrayrulewidth\relax}")


ColumnDef = Tuple[str, str, float]  # (header text, align L/C/R, width fraction)


class ReportTable:
    """Builder for a captioned longtable with repeating headers.

    Example
    -------
    t = ReportTable("Dead Load -- Self Weight",
                    [("Parameter", "L", 0.50), ("Value", "C", 0.30), ("Unit", "C", 0.20)])
    t.add_row(["Steel density", "78.5", r"kN/m$^3$"])
    tex = t.dumps()
    """

    def __init__(self, caption: str, columns: Sequence[ColumnDef],
                 label: Optional[str] = None, note: Optional[str] = None,
                 header_tex: Optional[str] = None, font: Optional[str] = None):
        self.caption = caption
        self.columns = list(columns)
        self.label = label
        self.note = note
        self.header_tex = header_tex   # custom (multi-row) header, already ending in \\
        self.font = font
        self._body: List[str] = []

        total = sum(c[2] for c in self.columns)
        if total > 1.001:
            # scale down rather than overflow the margin
            self.columns = [(h, a, w / total) for h, a, w in self.columns]

    def head(self, i: int, text: str, span: int = 1) -> str:
        """Header cell for a hand-built (multi-row) header: centred, bold and
        wrapping inside the combined width of columns i .. i+span-1."""
        w = sum(c[2] for c in self.columns[i:i + span])
        width = (r"\dimexpr " + f"{w:.3f}" + r"\linewidth-2\tabcolsep-1.5\arrayrulewidth\relax")
        spec = ("|" if i == 0 else "") + r">{\centering\arraybackslash}p{" + width + "}|"
        return r"\multicolumn{" + str(span) + "}{" + spec + r"}{\textbf{" + text + "}}"

    @property
    def ncols(self) -> int:
        return len(self.columns)

    # ── body ────────────────────────────────────────────────────────────────

    def add_row(self, cells: Sequence, rule: bool = True) -> "ReportTable":
        self._body.append(self._row(cells) + (r" \hline" if rule else ""))
        return self

    def add_rows(self, rows: Iterable[Sequence]) -> "ReportTable":
        for r in rows:
            self.add_row(r)
        return self

    def add_group(self, label: str, rows: Sequence[Sequence], first_col_span: int = 1) -> "ReportTable":
        """Rows that share a merged label in the first column and must stay
        on one page. Each row in `rows` excludes the label column."""
        rows = list(rows)
        if not rows:
            return self
        n = len(rows)
        lines = []
        for i, r in enumerate(rows):
            lead = (r"\multirow{" + str(n) + r"}{=}{" + str(label) + "}") if i == 0 else ""
            line = self._row([lead] + list(r))
            if i < n - 1:
                # \\* forbids a break after the row, but \cline is a row of its
                # own, so the break after the rule has to be forbidden as well.
                line = (line[:-2] + r"\\*" + " " + r"\cline{" + f"{first_col_span + 1}-{self.ncols}" + "}"
                        + r"\noalign{\penalty10000}")
            else:
                line += r" \hline"
            lines.append(line)
        self._body.append("\n".join(lines))
        return self

    def add_subheader(self, text: str) -> "ReportTable":
        self._body.append(r"\rowcolor{" + THEME.table.subheader_bg + r"}\multicolumn{" + str(self.ncols)
                          + r"}{|l|}{\textbf{" + text + r"}} \\* \hline\noalign{\penalty10000}")
        return self

    def add_span_row(self, text: str, align: str = "c") -> "ReportTable":
        self._body.append(r"\multicolumn{" + str(self.ncols) + "}{|" + align + "|}{" + text + r"} \\ \hline")
        return self

    def add_raw(self, tex: str) -> "ReportTable":
        self._body.append(tex)
        return self

    def is_empty(self) -> bool:
        return not self._body

    # ── rendering ───────────────────────────────────────────────────────────

    @staticmethod
    def _row(cells: Sequence) -> str:
        return " & ".join("" if c is None else str(c) for c in cells) + r" \\"

    def _header(self) -> str:
        if self.header_tex:
            return self.header_tex
        # header cells are centred but keep the column width, so they still wrap
        cells = []
        for i, (h, _, w) in enumerate(self.columns):
            spec = ("|" if i == 0 else "") + col_spec("C", w) + "|"
            cells.append(r"\multicolumn{1}{" + spec + r"}{\textbf{" + h + "}}")
        return r"\rowcolor{" + THEME.table.header_bg + "}" + " & ".join(cells) + r" \\"

    def _spec(self) -> str:
        return "|" + "|".join(col_spec(a, w) for _, a, w in self.columns) + "|"

    def dumps(self) -> str:
        ts = THEME.table
        font = self.font or (ts.wide_font if self.ncols >= ts.wide_threshold else ts.font)

        table = LongTable(NoEscape(self._spec()))
        label = (r"\label{" + self.label + "}") if self.label else ""
        # first page head
        table.append(NoEscape(r"\caption{" + self.caption + "}" + label + r"\\"))
        table.append(NoEscape(r"\hline"))
        table.append(NoEscape(self._header()))
        table.append(NoEscape(r"\hline"))
        table.append(NoEscape(r"\endfirsthead"))
        # head on continuation pages
        table.append(NoEscape(r"\caption[]{" + self.caption + " " + ts.continued_text + r"}\\"))
        table.append(NoEscape(r"\hline"))
        table.append(NoEscape(self._header()))
        table.append(NoEscape(r"\hline"))
        table.append(NoEscape(r"\endhead"))
        # foot at a page break / at the very end
        table.append(NoEscape(r"\multicolumn{" + str(self.ncols) + r"}{r@{}}{\footnotesize "
                              + ts.continues_text + r"} \\"))
        table.append(NoEscape(r"\endfoot"))
        table.append(NoEscape(r"\endlastfoot"))
        for chunk in self._body:
            table.append(NoEscape(chunk))

        # The empty paragraph hands any heading just above to the page builder
        # before longtable measures the free space (\LT@start reads \pagetotal);
        # without it a table right under a heading can print its "continued"
        # head before the heading.
        out = ("\\leavevmode\\par\\vspace{-\\baselineskip}\n"
               "\\begingroup" + font + "\n" + table.dumps() + "\n\\endgroup\n")
        if self.note:
            out += r"\nopagebreak\vspace{-2pt}\noindent{" + ts.note_font + r"\textit{Note: " + self.note + "}}\n"
        return "\n" + out + r"\vspace{0.6em}" + "\n"


# ── Shortcuts for the common table shapes ────────────────────────────────────

Cell = Union[str, float, int, None]


def kv_table(caption: str, rows: Sequence[Tuple[Cell, ...]], *, with_unit: bool = True,
             headers: Tuple[str, ...] = ("Parameter", "Value", "Unit"),
             widths: Optional[Tuple[float, ...]] = None, label: Optional[str] = None,
             note: Optional[str] = None) -> str:
    """Parameter / Value (/ Unit) table — the most common table in the report."""
    if with_unit:
        widths = widths or (0.46, 0.38, 0.16)
        cols = [(headers[0], "L", widths[0]), (headers[1], "L", widths[1]), (headers[2], "C", widths[2])]
    else:
        widths = widths or (0.42, 0.58)
        cols = [(headers[0], "L", widths[0]), (headers[1], "L", widths[1])]
    t = ReportTable(caption, cols, label=label, note=note)
    for r in rows:
        r = list(r)
        if not with_unit and len(r) == 3:
            # fold the unit into the value column
            r = [r[0], (str(r[1]) + (" " + str(r[2]) if r[2] else "")) if r[1] not in (None, "") else ""]
        t.add_row([("" if c is None else c) for c in r[:len(cols)]])
    return t.dumps()


def simple_tabular(rows: Sequence[Tuple[str, str]], widths=(0.36, 0.64)) -> str:
    """Two-column boxed tabular (no caption), e.g. the title page block."""
    spec = "|" + col_spec("L", widths[0]) + "|" + col_spec("L", widths[1]) + "|"
    body = "\n".join(r"\textbf{" + k + "} & " + (v or "") + r" \\ \hline" for k, v in rows)
    return r"\begin{tabular}{" + spec + "}\n\\hline\n" + body + "\n\\end{tabular}\n"
