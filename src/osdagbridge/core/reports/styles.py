# =============================================================================
# OsdagBridge Report — Style configuration
#
# Every layout / visual setting used by the report lives here: page geometry,
# fonts, colours, table padding, header/footer, status colours and the
# matplotlib style used for the charts. Chapter files must not hardcode any of
# these — import from this module instead, so a global change (e.g. margins or
# the table header colour) is a one-line edit.
# =============================================================================

from dataclasses import dataclass, field
from typing import Dict


# ── Page & document ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PageStyle:
    paper: str = "a4paper"
    font_size: str = "11pt"
    margin_left: str = "22mm"
    margin_right: str = "22mm"
    margin_top: str = "20mm"
    margin_bottom: str = "18mm"
    # Header/footer are counted inside the margins (includeheadfoot), so the
    # body can never run into them.
    head_height: str = "15pt"
    head_sep: str = "6mm"
    foot_skip: str = "11mm"
    line_spread: str = "1.10"
    # Minimum free space before a (non-breaking) table / figure may start on the
    # current page; below this it moves to the next page. Longtables are not
    # listed: they check the space for caption + header + first row themselves,
    # and an extra \needspace in front of them causes duplicated heads.
    table_needspace: str = "9\\baselineskip"
    figure_needspace: str = "12\\baselineskip"
    # A heading needs room for itself plus the start of what follows, otherwise
    # the heading is left alone at the foot of the page.
    section_needspace: str = "14\\baselineskip"
    # Rows longtable processes per pass; must be >= rows in the head (3 max here).
    # Smaller chunks let a long table start on a partly filled page.
    lt_chunk_size: int = 4
    # LaTeX defaults. 10000 forbids any break near a paragraph end, which pushes
    # a following longtable into a bad break.
    club_penalty: int = 150
    widow_penalty: int = 150


# ── Colours (HTML hex, no '#') ───────────────────────────────────────────────

@dataclass(frozen=True)
class Palette:
    osdag_green: str = "91B014"      # brand colour, header/footer rules
    osdag_dark: str = "4A5A0A"       # headings
    table_head: str = "E8F0CC"       # header row background
    table_subhead: str = "F3F7E4"    # group / sub-header rows
    table_rule: str = "9AA0A6"
    text_muted: str = "5F6368"
    pass_green: str = "2E7D32"
    fail_red: str = "C62828"
    warn_amber: str = "B26A00"
    # chart colours
    chart_pass: str = "7FA712"
    chart_fail: str = "D32F2F"
    chart_warn: str = "F2A900"
    chart_limit: str = "D32F2F"
    chart_steel: str = "4F6D7A"
    chart_concrete: str = "A3A3A3"
    chart_rebar: str = "C77D2E"

    def latex_definitions(self) -> str:
        names = {
            "osdagGreen": self.osdag_green,
            "osdagDark": self.osdag_dark,
            "tableHead": self.table_head,
            "tableSubHead": self.table_subhead,
            "tableRule": self.table_rule,
            "textMuted": self.text_muted,
            "passGreen": self.pass_green,
            "failRed": self.fail_red,
            "warnAmber": self.warn_amber,
        }
        return "\n".join(r"\definecolor{%s}{HTML}{%s}" % kv for kv in names.items())

    def hex(self, name: str) -> str:
        return "#" + getattr(self, name)


# ── Tables ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TableStyle:
    col_sep: str = "5pt"              # \tabcolsep
    array_stretch: str = "1.25"       # row height multiplier
    extra_row_height: str = "1.5pt"   # padding above cell text
    rule_width: str = "0.4pt"
    header_bg: str = "tableHead"      # colour name from Palette
    subheader_bg: str = "tableSubHead"
    font: str = r"\small"             # body font for normal tables
    wide_font: str = r"\footnotesize" # tables with many columns
    wide_threshold: int = 7           # >= this many columns → wide_font
    lt_pre: str = "4pt"               # space above a longtable
    lt_post: str = "8pt"              # space below a longtable
    caption_skip: str = "4pt"
    continued_text: str = r"\textit{(continued)}"
    continues_text: str = r"\textit{Continued on next page}"
    note_font: str = r"\footnotesize"


# ── Header / footer ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class HeaderFooterStyle:
    footer_left: str = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
    page_format: str = r"Page \thepage\ of \pageref{LastPage}"
    rule_color: str = "osdagGreen"
    rule_width: str = "0.8pt"
    font: str = r"\footnotesize"


# ── Headings ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class HeadingStyle:
    chapter_font: str = r"\normalfont\LARGE\bfseries\color{osdagDark}"
    section_font: str = r"\normalfont\Large\bfseries\color{osdagDark}"
    subsection_font: str = r"\normalfont\large\bfseries"
    chapter_before: str = "0pt"
    chapter_after: str = "14pt"


# ── Charts (matplotlib) ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class ChartStyle:
    dpi: int = 200
    width_in: float = 7.0
    height_in: float = 3.4
    font_family: str = "DejaVu Sans"
    font_size: int = 9
    title_size: int = 10
    grid_alpha: float = 0.35
    bar_width: float = 0.6
    ur_limit: float = 1.0
    ur_warn: float = 0.9
    latex_width: str = r"0.95\linewidth"
    drawing_width: str = r"0.85\linewidth"      # CAD views in Chapter 6
    drawing_max_height: str = r"0.42\textheight"

    def rc_params(self) -> Dict[str, object]:
        return {
            "font.family": self.font_family,
            "font.size": self.font_size,
            "axes.titlesize": self.title_size,
            "axes.titleweight": "bold",
            "axes.labelsize": self.font_size,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.alpha": self.grid_alpha,
            "grid.linestyle": "-",
            "xtick.labelsize": self.font_size - 1,
            "ytick.labelsize": self.font_size - 1,
            "legend.fontsize": self.font_size - 1,
            "legend.frameon": False,
            "savefig.dpi": self.dpi,
            "savefig.bbox": "tight",
        }


@dataclass(frozen=True)
class Theme:
    page: PageStyle = field(default_factory=PageStyle)
    colors: Palette = field(default_factory=Palette)
    table: TableStyle = field(default_factory=TableStyle)
    header_footer: HeaderFooterStyle = field(default_factory=HeaderFooterStyle)
    headings: HeadingStyle = field(default_factory=HeadingStyle)
    chart: ChartStyle = field(default_factory=ChartStyle)


THEME = Theme()


# ── Status text helpers (used by every chapter) ──────────────────────────────

def status_tex(status) -> str:
    """Coloured PASS / FAIL / WARN label. Anything else is returned as-is."""
    s = "" if status is None else str(status).strip()
    up = s.upper()
    if not s:
        return "---"
    if "FAIL" in up:
        return r"\textcolor{failRed}{\textbf{" + s + "}}"
    if "WARN" in up:
        return r"\textcolor{warnAmber}{\textbf{" + s + "}}"
    if "PASS" in up or up == "OK":
        return r"\textcolor{passGreen}{\textbf{" + s + "}}"
    return s


def pass_fail(ok) -> str:
    if ok is None:
        return "---"
    return status_tex("PASS" if ok else "FAIL")


def ur_tex(value, nd: int = 2) -> str:
    """Utilization ratio, red when it exceeds the limit."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return "---"
    s = f"{f:.{nd}f}"
    if f > THEME.chart.ur_limit:
        return r"\textcolor{failRed}{\textbf{" + s + "}}"
    return s


# ── Preamble pieces ──────────────────────────────────────────────────────────

def geometry_options() -> str:
    p = THEME.page
    return (f"{p.paper}, left={p.margin_left}, right={p.margin_right}, "
            f"top={p.margin_top}, bottom={p.margin_bottom}, "
            f"headheight={p.head_height}, headsep={p.head_sep}, "
            f"footskip={p.foot_skip}, includeheadfoot")


def style_preamble() -> str:
    """LaTeX lines that apply the theme. Inserted once in the preamble."""
    p, t, h = THEME.page, THEME.table, THEME.headings
    return "\n".join([
        THEME.colors.latex_definitions(),
        "",
        "% -- Text flow",
        r"\linespread{" + p.line_spread + "}",
        r"\clubpenalty=" + str(p.club_penalty),
        r"\widowpenalty=" + str(p.widow_penalty),
        r"\displaywidowpenalty=" + str(p.widow_penalty),
        r"\raggedbottom",
        "",
        "% -- Tables",
        r"\setlength{\tabcolsep}{" + t.col_sep + "}",
        r"\renewcommand{\arraystretch}{" + t.array_stretch + "}",
        r"\setlength{\extrarowheight}{" + t.extra_row_height + "}",
        r"\setlength{\arrayrulewidth}{" + t.rule_width + "}",
        r"\arrayrulecolor{tableRule}",
        r"\setlength{\LTpre}{" + t.lt_pre + "}",
        r"\setlength{\LTpost}{" + t.lt_post + "}",
        r"\setlength{\LTleft}{0pt}",
        r"\setlength{\LTright}{\fill}",   # the caption row needs stretch here
        r"\setlength{\LTcapwidth}{\linewidth}",
        r"\captionsetup[table]{skip=" + t.caption_skip + "}",
        # flush the caption with the left edge of the table
        r"\captionsetup[longtable]{margin=0pt, singlelinecheck=false, justification=raggedright}",
        r"\BeforeBeginEnvironment{table}{\needspace{" + p.table_needspace + "}}",
        r"\setcounter{LTchunksize}{" + str(p.lt_chunk_size) + "}",
        r"\BeforeBeginEnvironment{figure}{\needspace{" + p.figure_needspace + "}}",
        # colortbl's \cline ends with \vskip, and glue after a row is always a
        # legal page break, so \\* could not hold a girder group together (the
        # merged "G4" label then ran into the footer). A kern is not a breakpoint.
        r"\makeatletter",
        r"\patchcmd{\@cline}{\noalign{\vskip-\arrayrulewidth}}{\noalign{\kern-\arrayrulewidth}}{}"
        r"{\PackageWarning{osdagbridge}{could not patch \string\cline}}",
        r"\makeatother",
        "",
        "% -- Headings",
        chapter_format(),
        r"\titleformat{\section}{" + h.section_font + r"}{\thesection}{0.8em}{}",
        r"\titleformat{\subsection}{" + h.subsection_font + r"}{\thesubsection}{0.8em}{}",
        r"\titlespacing*{\section}{0pt}{14pt plus 4pt minus 2pt}{6pt plus 2pt}",
        r"\titlespacing*{\subsection}{0pt}{10pt plus 3pt minus 2pt}{4pt plus 2pt}",
        r"\pretocmd{\section}{\needspace{" + p.section_needspace + r"}}{}{}",
        r"\pretocmd{\subsection}{\needspace{" + p.section_needspace + r"}}{}{}",
    ])


def chapter_format() -> str:
    h = THEME.headings
    return (r"\titleformat{\chapter}[block]{" + h.chapter_font + r"\centering}"
            r"{\thechapter}{1em}{}" + "\n"
            r"\titlespacing*{\chapter}{0pt}{" + h.chapter_before + "}{" + h.chapter_after + "}")


def fancy_page_style(name: str, left_head: str, right_head: str, with_head: bool = True) -> str:
    """fancyhdr page style built from HeaderFooterStyle."""
    hf = THEME.header_footer
    head = ""
    if with_head:
        head = (r"  \fancyhead[L]{" + hf.font + " " + left_head + "}\n"
                r"  \fancyhead[R]{" + hf.font + " " + right_head + "}\n"
                r"  \renewcommand{\headrule}{{\color{" + hf.rule_color + r"}"
                r"\hrule width\headwidth height " + hf.rule_width + "}}\n")
    else:
        head = r"  \renewcommand{\headrulewidth}{0pt}" + "\n"
    # The "* Software default value" note is printed inside the footer box,
    # above the rule, only on pages that actually use a default value.
    return (r"\fancypagestyle{" + name + "}{\n"
            r"  \fancyhf{}" + "\n"
            + head +
            r"  \fancyfoot[L]{" + hf.font + " " + hf.footer_left + "}\n"
            r"  \fancyfoot[R]{" + hf.font + " " + hf.page_format + "}\n"
            r"  \renewcommand{\footrule}{%" + "\n"
            r"    \ifbool{hasSDonPage}{\vbox to 0pt{\vss\hbox to\headwidth{\footnotesize"
            r"\textit{* Software default value}\hfil}\vskip3pt}}{}%" + "\n"
            r"    {\color{" + hf.rule_color + r"}\hrule width\headwidth height " + hf.rule_width + r"}\vskip4pt}" + "\n"
            "}")
