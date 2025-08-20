from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from openpyxl.utils import column_index_from_string
from plotly.subplots import make_subplots
from datetime import datetime

import streamlit as st

# --------------------------------------------------------------------------------------
# Constants & Configuration
# --------------------------------------------------------------------------------------

SHEET_NAME = "OMT DRAM BC"

# Default ranges (user can override via UI)
DEFAULT_DELTA_START = "CR46"
DEFAULT_DELTA_END = "JE60"

DEFAULT_ALL_START = "CR5"
DEFAULT_ALL_END = "JE17"

# Column in Excel that contains the group/process label (e.g., "Group", sometimes "Group ")
DEFAULT_GROUP_COL_LETTER = "D"

# Colors (fallback palette for unknown series)
COLOR_MAPPING: Dict[str, str] = {
    "140S_DRAM": "#F4CBA3",
    "150S_DRAM": "#A3B8CC",
    "160S_DRAM": "#FFEB99",
    "170S_DRAM": "#999999",
    "150S_HBM3E": "#00AEEF",   # If data uses HBM3 instead of HBM3E we handle below
    "150S_HBM4": "#7FDBFF",
    "150S_non-HBM": "#00008B",
    "160S_HBM4E": "#FFC107",
    "160S_non-HBM": "#FF8C00",
    "Total_DRAM": "#51A687",
}

# Accepted series groupings
HBM_SERIES = {"150S_HBM3", "150S_HBM3E", "150S_HBM4", "160S_HBM4E"}
NON_HBM_SERIES = {"140S_DRAM", "150S_non-HBM", "160S_non-HBM", "170S_DRAM"}

# Regex for "week-like" labels (e.g., W22-2025)
WEEK_LABEL_RE = re.compile(r"W\d{2}-\d{4}")

# Plotly theme
PLOTLY_TEMPLATE = "plotly_white"


# --------------------------------------------------------------------------------------
# Data classes
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class RangeRef:
    start_col: int
    start_row: int
    end_col: int
    end_row: int


@dataclass
class HeaderInfo:
    primary_labels: List[str]   # e.g. weekly labels like "JUN 22-2025"
    secondary_labels: List[str] # e.g. quarters like "FQ425"


@dataclass
class LinePlotData:
    table: pd.DataFrame            # rows: products/processes, columns: weeks + Group
    melted: pd.DataFrame           # for line chart (Time Period, Wafer Output, Group)
    headers: HeaderInfo
    group_col: str


# --------------------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------------------

def parse_cell(cell: str) -> Tuple[int, int]:
    """
    Convert an Excel-style address (e.g., 'CR46') into 0-based (col, row).
    """
    col_str = "".join(filter(str.isalpha, cell))
    row_str = "".join(filter(str.isdigit, cell))
    if not col_str or not row_str:
        raise ValueError(f"Invalid Excel address: {cell}")
    col = column_index_from_string(col_str) - 1
    row = int(row_str) - 1
    return col, row


def parse_range(start_cell: str, end_cell: str) -> RangeRef:
    sc, sr = parse_cell(start_cell)
    ec, er = parse_cell(end_cell)
    if sc > ec or sr > er:
        raise ValueError("Start cell must be top-left of end cell.")
    return RangeRef(sc, sr, ec, er)


def to_wlabel(s: str) -> str:
    """
    Convert 'JUN 22-2025' -> 'W22-2025'; otherwise return input unchanged.
    """
    m = re.fullmatch(r"[A-Z]{3}\s(\d{2})-(\d{4})", str(s).strip())
    return f"W{m.group(1)}-{m.group(2)}" if m else str(s)


def fmt_num(s: pd.Series) -> pd.Series:
    return s.round(0).astype(int).map(lambda x: f"{x:,}")


def fmt_pct(s: pd.Series) -> pd.Series:
    return s.fillna(0).map(lambda x: f"{x:.1f}%")


def detect_group_column(df: pd.DataFrame) -> str:
    """
    Find the column whose stripped name equals 'Group'.
    """
    candidates = [c for c in df.columns if str(c).strip() == "Group"]
    if not candidates:
        raise ValueError("Could not find a 'Group' column (even with trailing-space tolerance).")
    return candidates[0]


def color_for(series: str, fallback_idx: int) -> str:
    if series in COLOR_MAPPING:
        return COLOR_MAPPING[series]
    # smooth over '150S_HBM3' vs '150S_HBM3E'
    if series == "150S_HBM3" and "150S_HBM3E" in COLOR_MAPPING:
        return COLOR_MAPPING["150S_HBM3E"]
    # fallback qualitative palette
    palette = px.colors.qualitative.D3
    return palette[fallback_idx % len(palette)]


# --------------------------------------------------------------------------------------
# I/O & caching
# --------------------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def read_excel_sheet(file, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(file, sheet_name=sheet_name, engine="openpyxl")


# --------------------------------------------------------------------------------------
# Core transforms
# --------------------------------------------------------------------------------------

def prepare_line_plot_data(
    df: pd.DataFrame,
    r: RangeRef,
    x_row: int,
    y_start_row: int,
    y_end_row: int,
    group_col_letter: str = DEFAULT_GROUP_COL_LETTER,
) -> LinePlotData:
    """
    Extract the main matrix and header rows for the line chart & downstream tables.
    """
    primary_labels = df.iloc[x_row, r.start_col : r.end_col + 1].tolist()
    secondary_labels = df.iloc[x_row - 2, r.start_col : r.end_col + 1].tolist()

    # Data block for rows (products/process series)
    y_values = df.iloc[y_start_row : y_end_row + 1, r.start_col : r.end_col + 1]
    group_col_idx = column_index_from_string(group_col_letter) - 1
    group_labels = df.iloc[y_start_row : y_end_row + 1, group_col_idx].values

    # Drop all-zero rows
    non_zero_mask = ~(y_values == 0).all(axis=1)
    y_values = y_values[non_zero_mask]
    group_labels = group_labels[non_zero_mask]

    table = pd.DataFrame(y_values.values, columns=primary_labels)
    table["Group"] = group_labels

    # Melt for the line chart
    melted = table.melt(id_vars="Group", var_name="Time Period", value_name="Wafer Output")

    # Detect actual group column name (strip-safe)
    group_col = detect_group_column(table)

    return LinePlotData(
        table=table,
        melted=melted,
        headers=HeaderInfo(primary_labels=primary_labels, secondary_labels=secondary_labels),
        group_col=group_col,
    )


def aggregate_process_share_by_quarter(
    table: pd.DataFrame,
    headers: HeaderInfo,
    group_col: str,
    exclude_labels: Iterable[str] = ("Total_DRAM", "process_series", "150S_DRAM", "160S_DRAM"),
) -> pd.DataFrame:
    """
    For each quarter, compute percentage share of each process series.
    Columns sum to 100.
    """
    time_cols = [c for c in table.columns if c != group_col and c != "Unnamed: 0"]
    # numeric conversion once
    wide = table.copy()
    wide[time_cols] = wide[time_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)

    mask_products = (
        wide[group_col].notna()
        & wide[group_col].astype(str).str.strip().ne("")
        & ~wide[group_col].astype(str).str.strip().isin(exclude_labels)
    )
    products = wide.loc[mask_products, time_cols]
    products.index = wide.loc[mask_products, group_col].astype(str)

    # Group week columns into quarters in the given order
    q_series = pd.Series(headers.secondary_labels, index=headers.primary_labels)
    products = products.reindex(columns=headers.primary_labels)  # keep ordering
    collapsed = products.T.groupby(q_series, sort=False).sum().T

    share_pct = collapsed.div(collapsed.sum(axis=0), axis=1) * 100
    return share_pct.round(1)



def build_week_options(headers: HeaderInfo) -> List[Tuple[str, str]]:
    """
    Returns list of (display_label_with_quarter, original_week_label) for week-like columns.
    Example display: 'W22-2025 (FQ425)'
    """
    options: List[Tuple[str, str]] = []
    for i, lbl in enumerate(headers.primary_labels):
        disp = to_wlabel(lbl)
        # Safely fetch the quarter at the same position as the week
        quarter = str(headers.secondary_labels[i]) if i < len(headers.secondary_labels) else ""
        if WEEK_LABEL_RE.fullmatch(disp):
            if quarter and quarter.strip():
                disp = f"{disp} ({quarter})"
            options.append((disp, lbl))
    return options


def compute_hbm_nonhbm_summary(
    table: pd.DataFrame,
    headers: HeaderInfo,
    group_col: str,
    selected_week_labels: Sequence[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Build totals and per-process % tables for the selected week range.
    Returns:
      - totals_by_quarter (HBM, nonHBM)
      - summary_with_overall (HBM, nonHBM, Total, %, %)
      - hbm_pct_disp (per-process % of HBM total by quarter)
      - nonhbm_pct_disp (per-process % of nonHBM total by quarter)
      - quarters (ordered)
    """
    # Ensure numeric
    values = table.copy()
    time_cols = [c for c in values.columns if c != group_col and c != "Unnamed: 0"]
    values[time_cols] = values[time_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)

    # Subset selected weeks in the same order, and map to quarters
    selected = list(selected_week_labels)
    # Align to headers order strictly
    selected = [c for c in headers.primary_labels if c in selected]
    if not selected:
        # If no week-like labels were detected, fallback to all columns
        selected = headers.primary_labels

    # Build quarter mapping for selected weeks (in order)
    quarter_for_week = [headers.secondary_labels[headers.primary_labels.index(c)] for c in selected]
    quarter_index = pd.Index(quarter_for_week, name="Quarter")

    # Split HBM vs non-HBM
    values = values.set_index(group_col)
    hbm_df = values.loc[values.index.isin(HBM_SERIES), selected]
    non_df = values.loc[values.index.isin(NON_HBM_SERIES), selected]

    # By quarter
    hbm_by_q = hbm_df.groupby(quarter_index, axis=1).sum()
    non_by_q = non_df.groupby(quarter_index, axis=1).sum()

    # Totals for stacked bars
    hbm_total = hbm_by_q.sum(axis=0)
    non_total = non_by_q.sum(axis=0)

    # Keep quarters in first-seen order
    quarters_in_order: List[str] = []
    seen = set()
    for q in quarter_for_week:
        if q not in seen:
            seen.add(q)
            quarters_in_order.append(q)

    all_quarters = hbm_total.index.union(non_total.index)
    quarters = [q for q in quarters_in_order if q in all_quarters]

    totals = (
        pd.DataFrame({"HBM": hbm_total, "nonHBM": non_total})
        .reindex(quarters)
        .fillna(0.0)
    )

    summary = totals.copy()
    summary["Total"] = summary["HBM"] + summary["nonHBM"]
    summary["HBM %"] = (summary["HBM"] / summary["Total"] * 100).where(summary["Total"].ne(0), 0)
    summary["nonHBM %"] = (summary["nonHBM"] / summary["Total"] * 100).where(summary["Total"].ne(0), 0)

    overall = pd.Series(
        {
            "HBM": summary["HBM"].sum(),
            "nonHBM": summary["nonHBM"].sum(),
            "Total": summary["Total"].sum(),
        },
        name="Overall",
    )
    overall["HBM %"] = (overall["HBM"] / overall["Total"] * 100) if overall["Total"] != 0 else 0
    overall["nonHBM %"] = (overall["nonHBM"] / overall["Total"] * 100) if overall["Total"] != 0 else 0
    summary_with_overall = pd.concat([summary, overall.to_frame().T], axis=0)

    # Percentage tables by process (divide each process by the total of its category per quarter)
    hbm_den = hbm_total.where(hbm_total != 0)
    non_den = non_total.where(non_total != 0)
    hbm_pct = (hbm_by_q.div(hbm_den, axis=1) * 100).reindex(columns=quarters).fillna(0).round(1)
    non_pct = (non_by_q.div(non_den, axis=1) * 100).reindex(columns=quarters).fillna(0).round(1)

    # Format for display
    hbm_pct_disp = hbm_pct.astype(str) + "%"
    non_pct_disp = non_pct.astype(str) + "%"

    return totals, summary_with_overall, hbm_pct_disp, non_pct_disp, quarters


# --------------------------------------------------------------------------------------
# Plotting
# --------------------------------------------------------------------------------------

def create_line_plot(melted: pd.DataFrame, headers: HeaderInfo) -> go.Figure:
    """
    Build a multi-series line chart with a secondary x-axis for non-repeating quarter labels.
    """
    # top x-axis with grouped quarter labels (avoid repetition)
    grouped_quarters: List[str] = []
    last = None
    for q in headers.secondary_labels:
        if q != last:
            grouped_quarters.append(q)
            last = q
        else:
            grouped_quarters.append("")

    fig = go.Figure()

    # Dummy trace to activate x2 axis (top)
    fig.add_trace(
        go.Scatter(
            x=headers.primary_labels,
            y=[None] * len(headers.primary_labels),
            mode="lines",
            showlegend=False,
            hoverinfo="skip",
            xaxis="x2",
        )
    )

    for i, group in enumerate(melted["Group"].dropna().unique()):
        gdf = melted[melted["Group"] == group]
        fig.add_trace(
            go.Scatter(
                x=gdf["Time Period"],
                y=gdf["Wafer Output"],
                mode="lines",
                name=str(group),
                line=dict(color=color_for(str(group), i), width=4),
                xaxis="x",
            )
        )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="OMT DRAM BC Delta",
        xaxis=dict(
            tickvals=headers.primary_labels,
            ticktext=headers.primary_labels,
            tickfont=dict(size=9),
            side="bottom",
            showgrid=False,
        ),
        xaxis2=dict(
            tickvals=headers.primary_labels,
            ticktext=grouped_quarters,
            tickfont=dict(size=12),
            overlaying="x",
            side="top",
            showline=True,
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(title="Wafer Output"),
        legend=dict(orientation="v", yanchor="top", y=1.02, xanchor="right", x=1),
        margin=dict(t=60, b=40, l=40, r=20),
        height=420,
    )
    return fig
def create_hbm_nonhbm_figure(
    totals: pd.DataFrame,
    summary_with_overall: pd.DataFrame,
    hbm_pct_disp: pd.DataFrame,
    non_pct_disp: pd.DataFrame,
    quarters: List[str],
) -> go.Figure:
    """
    Composite figure: stacked bar (HBM vs nonHBM) + totals table + two per-process % tables.
    """
    def table_cells(df_pct_str: pd.DataFrame) -> List[List[str]]:
        # First column = index (process series), then one column per quarter
        return [df_pct_str.index.tolist()] + [df_pct_str[q].tolist() for q in df_pct_str.columns]

    disp = pd.DataFrame(
        {
            "Quarter": summary_with_overall.index.tolist(),
            "HBM": fmt_num(summary_with_overall["HBM"]),
            "nonHBM": fmt_num(summary_with_overall["nonHBM"]),
            "Total": fmt_num(summary_with_overall["Total"]),
            "HBM %": fmt_pct(summary_with_overall["HBM %"]),
            "nonHBM %": fmt_pct(summary_with_overall["nonHBM %"]),
        }
    )

    fig = make_subplots(
        rows=2, cols=2,
        column_widths=[0.5, 0.5],
        specs=[
            [{"type": "xy"}, {"type": "domain"}],
            [{"type": "domain"}, {"type": "domain"}],
        ],
        subplot_titles=[
            "HBM vs non-HBM by Quarter",
            "non-HBM Process Series (%)",
            "HBM/non-HBM Totals & %",
            "HBM Process Series (%)",
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.08,
    )

    # Stacked bars
    fig.add_trace(go.Bar(name="HBM", x=totals.index, y=totals["HBM"], marker_color="#0078D7"), row=1, col=1)
    fig.add_trace(go.Bar(name="nonHBM", x=totals.index, y=totals["nonHBM"], marker_color="#A0AEB2"), row=1, col=1)

    # Totals table
    fig.add_trace(
        go.Table(
            header=dict(
                values=["Quarter", "HBM", "nonHBM", "Total", "HBM %", "nonHBM %"],
                fill_color="#505A5F",
                font=dict(color="white", size=12),
                align="center",
            ),
            cells=dict(
                values=[disp[c] for c in ["Quarter", "HBM", "nonHBM", "Total", "HBM %", "nonHBM %"]],
                fill_color=[["#F5F7FA" if (i % 2 == 0) else "#FFFFFF" for i in range(len(disp))]] * 6,
                align="center",
                height=26,
            ),
            columnwidth=[90, 90, 90, 90, 90, 100],
        ),
        row=2, col=1,
    )

    # non-HBM percentage table
    fig.add_trace(
        go.Table(
            header=dict(values=["Process Series"] + quarters, fill_color="#87CEFA", font=dict(color="white", size=12), align="center"),
            cells=dict(
                values=table_cells(non_pct_disp),
                fill_color=[["#cbe5f5"] * len(non_pct_disp.index)] + [["#FFFFFF"] * len(quarters)],
                align=["left"] + ["center"] * len(quarters),
                height=26,
            ),
            columnwidth=[140] + [64] * len(quarters),
        ),
        row=1, col=2,
    )

    # HBM percentage table
    fig.add_trace(
        go.Table(
            header=dict(values=["Process Series"] + quarters, fill_color="#0078D7", font=dict(color="white", size=12), align="center"),
            cells=dict(
                values=table_cells(hbm_pct_disp),
                fill_color=[["#cad8e3"] * len(hbm_pct_disp.index)] + [["#FFFFFF"] * len(quarters)],
                align=["left"] + ["center"] * len(quarters),
                height=26,
            ),
            columnwidth=[140] + [64] * len(quarters),
        ),
        row=2, col=2,
    )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        barmode="stack",
        xaxis_title="Quarter",
        yaxis_title="Wafer Output",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=650,
        margin=dict(t=80, b=40, l=40, r=20),
    )
    return fig


# --------------------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------------------

def page_header():
    st.set_page_config(page_title="📊 Loading Mia", layout="wide")
    st.title("📊 Loading Mia")


def render_bc_delta_section(df: pd.DataFrame):
    st.markdown("### BC Delta")

    c1, c2 = st.columns(2)
    with c1:
        start_cell = st.text_input("Enter start cell (e.g., CR46):", value=DEFAULT_DELTA_START)
    with c2:
        end_cell = st.text_input("Enter end cell (e.g., JE60):", value=DEFAULT_DELTA_END)

    try:
        r = parse_range(start_cell, end_cell)
    except Exception as e:
        st.error(f"Invalid cell range: {e}")
        st.stop()

    # Build line plot data from the specified range
    line = prepare_line_plot_data(
        df=df,
        r=r,
        x_row=2,
        y_start_row=r.start_row,
        y_end_row=r.end_row,
        group_col_letter=DEFAULT_GROUP_COL_LETTER,
    )
    fig = create_line_plot(line.melted, line.headers)
    st.plotly_chart(fig, use_container_width=True)

    return line  # we reuse headers (labels) later
def render_current_bc_section(df: pd.DataFrame, headers_from_delta: Optional[HeaderInfo]):
    st.markdown("### Current BC")
    st.markdown("**Process Series Portion**")

    c3, c4 = st.columns(2)
    with c3:
        start_cell_all = st.text_input("Enter start cell (e.g., CR5):", value=DEFAULT_ALL_START)
    with c4:
        end_cell_all = st.text_input("Enter end cell (e.g., JE17):", value=DEFAULT_ALL_END)

    try:
        r_all = parse_range(start_cell_all, end_cell_all)
    except Exception as e:
        st.error(f"Invalid cell range: {e}")
        st.stop()

    # Reuse the same header row indices to keep logic consistent
    data_all = prepare_line_plot_data(
        df=df,
        r=r_all,
        x_row=2,
        y_start_row=r_all.start_row,
        y_end_row=r_all.end_row,
        group_col_letter=DEFAULT_GROUP_COL_LETTER,
    )

    # --- Process Series Portion table (weeks -> quarters) ---
    share_pct = aggregate_process_share_by_quarter(
        data_all.table, data_all.headers, data_all.group_col
    )
    st.dataframe(share_pct.apply(fmt_pct))

    # --- HBM vs non-HBM, with week selection ---
    st.markdown("### Select a date range to view HBM / non-HBM data")

    # Prefer the header labels from the broader range if supplied; otherwise use this section's headers
    headers = headers_from_delta or data_all.headers
    week_options = build_week_options(headers)
    if not week_options:
        st.warning("No week-like columns found (expected labels such as 'JUN 22-2025'). Showing all.")
        # Fallback: still append quarter when available
        week_options = [
            (
                f"{to_wlabel(lbl)} ({headers.secondary_labels[i]})"
                if i < len(headers.secondary_labels) and str(headers.secondary_labels[i]).strip()
                else to_wlabel(lbl),
                lbl,
            )
            for i, lbl in enumerate(headers.primary_labels)
        ]


    disp_labels = [d for (d, _) in week_options]
    default_start_idx = 0
    default_end_idx = len(disp_labels) - 1

    co1, co2 = st.columns(2)
    with co1:
        start_disp = st.selectbox("Start week", disp_labels, index=default_start_idx)
    with co2:
        end_disp = st.selectbox("End week", disp_labels, index=default_end_idx)

    i0, i1 = disp_labels.index(start_disp), disp_labels.index(end_disp)
    if i0 > i1:
        i0, i1 = i1, i0
    selected_weeks = [orig for (_, orig) in week_options[i0 : i1 + 1]]

    totals, summary, hbm_pct_disp, non_pct_disp, quarters = compute_hbm_nonhbm_summary(
        table=data_all.table,
        headers=headers,
        group_col=data_all.group_col,
        selected_week_labels=selected_weeks,
    )

    fig_hbm = create_hbm_nonhbm_figure(totals, summary, hbm_pct_disp, non_pct_disp, quarters)
    st.plotly_chart(fig_hbm, use_container_width=True)


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------

def main():
    page_header()

    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
    if not uploaded_file:
        st.info("Please upload an Excel file (.xlsx) containing sheet "
                f"'{SHEET_NAME}' to begin.")
        st.stop()

    try:
        df = read_excel_sheet(uploaded_file, SHEET_NAME)
    except Exception as e:
        st.error(f"Error reading Excel: {e}")
        st.stop()

    # Section 1: BC Delta (returns header labels we can reuse)
    line_from_delta = render_bc_delta_section(df)

    # Section 2: Current BC (portion table + HBM vs non-HBM with week selection)
    render_current_bc_section(df, headers_from_delta=line_from_delta.headers)


if __name__ == "__main__":
    main()
