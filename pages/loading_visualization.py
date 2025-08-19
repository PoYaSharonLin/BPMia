import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
from utils.ui_helper import UIHelper
from openpyxl.utils import column_index_from_string


color_mapping = {
    "140S_DRAM": "#F4CBA3",       # Light Peach
    "150S_DRAM": "#A3B8CC",       # Light Blue-Gray
    "160S_DRAM": "#FFEB99",       # Light Yellow
    "170S_DRAM": "#999999",       # Medium Gray
    "150S_HBM3E": "#00AEEF",      # Dark Blue
    "150S_HBM4": "#7FDBFF",       # Light Blue
    "150S_non-HBM": "#00008B",    # Dark Blue
    "160S_HBM4E": "#FFC107",      # Vibrant Yellow
    "160S_non-HBM": "#FF8C00",    # Dark Orange
    "Total_DRAM": "#51A687"       # Green
}


custom_order = [
    "FQ425", "FQ126", "FQ226", "FQ326", "FQ426",
    "FQ127", "FQ227", "FQ327", "FQ427",
    "FQ128", "FQ228", "FQ328", "FQ428"
]


def parse_cell(cell):
    col = ''.join(filter(str.isalpha, cell))
    row = int(''.join(filter(str.isdigit, cell)))
    return column_index_from_string(col) - 1, row - 1  # Convert to 0-based index

def prepare_line_plot_data(df, start_col, end_col, x_row, y_start_row, y_end_row, group_col_index):
    primary_labels = df.iloc[x_row, start_col:end_col + 1]
    secondary_labels = df.iloc[x_row-2, start_col:end_col + 1]
    y_values = df.iloc[y_start_row:y_end_row + 1, start_col:end_col + 1]
    group_labels = df.iloc[y_start_row:y_end_row + 1, group_col_index].values

    # Mask rows with 0s
    non_zero_mask = ~(y_values == 0).all(axis=1)
    y_values_filtered = y_values[non_zero_mask]
    group_labels_filtered = group_labels[non_zero_mask]

    plot_data = pd.DataFrame(y_values_filtered.values, columns=primary_labels)
    plot_data['Group'] = group_labels_filtered
    plot_data_melted = plot_data.melt(id_vars='Group', var_name='Time Period', value_name='Wafer Output')

    return plot_data, plot_data_melted, primary_labels, secondary_labels

def create_line_plot(plot_data_melted, title, primary_labels, secondary_labels):
    fig = go.Figure()

    
    # Create grouped secondary labels (e.g., FY21 shown only once)
    grouped_secondary_labels = []
    last_label = None
    for label in secondary_labels:
        if label != last_label:
            grouped_secondary_labels.append(label)
            last_label = label
        else:
            grouped_secondary_labels.append('')  # Empty to avoid repetition

    fig.add_trace(go.Scatter(
        x=primary_labels,               
        y=[None] * len(primary_labels), 
        mode='lines',                  
        showlegend=False,               
        hoverinfo='skip',               
        xaxis='x2'                      
    ))

    for group in plot_data_melted['Group'].unique():
        group_data = plot_data_melted[plot_data_melted['Group'] == group]
        fig.add_trace(go.Scatter(
            x=group_data['Time Period'],
            y=group_data['Wafer Output'],
            mode='lines',
            name=group,
            line=dict(color=color_mapping.get(group, None),
                      width=4  
            ),  
            xaxis='x'  
        ))

    fig.update_layout(
        title=title,
        xaxis=dict(
            tickvals=primary_labels,
            ticktext=primary_labels,
            tickfont=dict(size=8),  
            side='bottom'
        ),
        xaxis2=dict(
            tickvals=primary_labels,  
            ticktext=grouped_secondary_labels,
            tickfont=dict(size=12), 
            overlaying='x',
            side='top',
            showline=True,
            showgrid=False,
            zeroline=False

        ),
        yaxis=dict(title='Wafer Output')
    )

    return fig



def to_wlabel(s: str) -> str:
    # Convert "JUN 22-2025" -> "W22-2025"; leave anything else unchanged (e.g., "Group")
    m = re.fullmatch(r'[A-Z]{3}\s(\d{2})-(\d{4})', str(s).strip())
    return f'W{m.group(1)}-{m.group(2)}' if m else str(s)

def fmt_num(s): 
    return s.round(0).astype(int).map(lambda x: f"{x:,}")

def fmt_pct(s):
    return s.fillna(0).map(lambda x: f"{x:.1f}%")


def main():
    try:
        UIHelper.config_page()
        UIHelper.setup_sidebar()

        st.title("📊Loading Mia")
        uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
        col1, col2 = st.columns(2)
        with col1:
            start_cell = st.text_input("Enter start cell (e.g., CR46):", value="CR44")
        with col2:
            end_cell = st.text_input("Enter end cell (e.g., JE60):", value="JE59")

        if uploaded_file:
            try:
                sheet_name = "OMT DRAM BC"
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name, engine='openpyxl')

                # Parse cell references
                try:
                    start_col, start_row = parse_cell(start_cell)
                    end_col, end_row = parse_cell(end_cell)
                except Exception as e:
                    st.error(f"Invalid cell range format: {e}")
                    return

                # Slice the DataFrame
                df_range = df.iloc[start_row:end_row + 1, start_col:end_col + 1]
                # st.success(f"Showing data from {start_cell} to {end_cell} from excel sheet")
                st.dataframe(df_range)


                # Delta Line plot 
                plot_data_delta, plot_data_melted_all, primary_labels, secondary_labels= prepare_line_plot_data(
                    df, start_col, end_col, x_row=2, y_start_row=44, y_end_row=58, group_col_index=column_index_from_string('D') - 1
                )
                fig_delta = create_line_plot(plot_data_melted_all, "OMT DRAM BC Delta", primary_labels, secondary_labels)
                st.plotly_chart(fig_delta, use_container_width=True)
                
                st.markdown("### Data Overview")
                st.markdown("**Overall Process Series Portion**")
                plot_data_all, plot_data_melted_all, primary_labels_all, secondary_labels_all = prepare_line_plot_data(
                df, start_col, end_col, x_row=2, y_start_row=0, y_end_row=17, group_col_index=column_index_from_string('D') - 1
                )   

                # Detect the Group column robustly (your file has a trailing space: 'Group ')
                portion_df = plot_data_all.copy()
                group_col = next((c for c in portion_df.columns if c.strip() == "Group"), None)
                if group_col is None:
                    raise ValueError("Could not find a 'Group' column in plot_data_all.")
                
                # Time columns are everything except 'Unnamed: 0' and Group column
                time_cols = [c for c in portion_df.columns if c not in ("Unnamed: 0", group_col)]
                
                # Convert weekly values to numeric just once
                portion_df[time_cols] = portion_df[time_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
                
                quarter = plot_data_all.loc[0, time_cols].astype(str)
                quarter.name = "quarter"

                # --- Select product rows by label instead of hard-coded iloc slice ---
                is_product = (
                    portion_df[group_col].notna()
                    & portion_df[group_col].astype(str).str.strip().ne("")
                    & portion_df[group_col].astype(str).str.strip().ne("Total_DRAM")  # exclude total row
                    & portion_df[group_col].astype(str).str.strip().ne("process_series")
                    & portion_df[group_col].astype(str).str.strip().ne("150S_DRAM")
                    & portion_df[group_col].astype(str).str.strip().ne("160S_DRAM")
                )
                process_series_value = portion_df.loc[is_product, time_cols + [group_col]].copy()
                
                # First row: quarter labels (already provided in `quarter`, aligned to time_cols)
                quarter_df = pd.DataFrame([quarter.loc[time_cols].astype(str)], columns=time_cols)
                
                # Build a table with quarter row (top) + product rows (below) – only time columns
                portion_table = pd.concat([quarter_df, process_series_value[time_cols]], axis=0, ignore_index=True)
                
                # Series labels from the product names
                series_labels = process_series_value[group_col].astype(str).values
                
                # Values excluding the first (quarter) row; set product names as index
                portion_values = portion_table.iloc[1:, :].set_index(pd.Index(series_labels, name="Product"))
                
                # --- Aggregate weeks → quarters ---
                # Preserve quarter order as they appear in time_cols
                portion_collapsed = portion_values.T.groupby(quarter.loc[time_cols], sort=False).sum().T
                
                # percentages per quarter
                portion_share_pct = (portion_collapsed.div(portion_collapsed.sum(axis=0), axis=1) * 100).round(1)
                formatted_portion_share_pct = portion_share_pct.apply(fmt_pct)
                st.dataframe(formatted_portion_share_pct)


                
                date_table = plot_data_all.copy()
                w_row = pd.Series({col: to_wlabel(col) for col in date_table.columns}, name='Week')
                date_table_with_week = pd.concat([w_row.to_frame().T, date_table], ignore_index=False)

                # create select table
                week_row = date_table_with_week.loc['Week'].astype(str)
                mask = week_row.str.fullmatch(r"W\d{2}-\d{4}")
                ordered_week_cols = week_row.index[mask].tolist()     
                week_labels = week_row[mask].tolist()
                
                first_row = date_table.iloc[0, :]
                final_week_labels = [
                    f"{label} ({first_row[col]})" for label, col in zip(week_labels, ordered_week_cols)
                ]

                st.markdown("### Select a date range to view HBM/nonHBM data")
                c1, c2 = st.columns(2)
                with c1:
                    start_week = st.selectbox("Start week", final_week_labels, index=0)
                with c2:
                    end_week = st.selectbox("End week", final_week_labels, index=len(week_labels) - 1)
                
                i0, i1 = final_week_labels.index(start_week), final_week_labels.index(end_week)
                if i0 > i1:
                    i0, i1 = i1, i0
                
                selected_week_cols = ordered_week_cols[i0 : i1 + 1]
                
                # Keep non-week columns (IDs, descriptors) pinned on the left
                non_week_cols = [c for c in date_table_with_week.columns if c not in ordered_week_cols]
                filtered = pd.concat(
                    [date_table_with_week[non_week_cols], date_table_with_week[selected_week_cols]],
                    axis=1
                )
            

                if start_week and end_week: 
                    quarter_map = filtered.iloc[1, 1:].tolist()
                    process_series = filtered.iloc[4:, 0].reset_index(drop=True)
                    values = filtered.iloc[4:, 1:].reset_index(drop=True)
                    values.columns = quarter_map
                    values.insert(0, 'process_series', process_series)
                    
                    hbm_series = {'150S_HBM3', '150S_HBM4', '160S_HBM4E'}
                    non_hbm_series = {'140S_DRAM', '150S_non-HBM', '160S_non-HBM', '170S_DRAM'}
                    
                    hbm_df = values[values['process_series'].isin(hbm_series)].set_index('process_series').apply(pd.to_numeric, errors='coerce')
                    non_hbm_df = values[values['process_series'].isin(non_hbm_series)].set_index('process_series').apply(pd.to_numeric, errors='coerce')

                    
                    hbm_by_quarter = hbm_df.groupby(hbm_df.columns, axis=1).sum()
                    non_hbm_by_quarter = non_hbm_df.groupby(non_hbm_df.columns, axis=1).sum()

                    
                    hbm_total = hbm_by_quarter.sum()
                    non_hbm_total = non_hbm_by_quarter.sum()

                    # customized quarter orders               
                    quarters_in_order = []
                    seen = set()
                    for q in quarter_map:
                        if q not in seen:
                            quarters_in_order.append(q)
                            seen.add(q)
                    
                    all_quarters = hbm_total.index.union(non_hbm_total.index)
                    quarters = [q for q in quarters_in_order if q in all_quarters]
                    
                    totals = (
                        pd.DataFrame({'HBM': hbm_total, 'nonHBM': non_hbm_total})
                        .reindex(quarters)
                        .fillna(0)
                    )

                    
                    summary = totals.copy()
                    summary["Total"] = summary["HBM"] + summary["nonHBM"]
                    summary = summary.reindex(quarters).fillna(0)
                    summary["HBM %"] = (summary["HBM"] / summary["Total"] * 100) 
                    summary["nonHBM %"] = (summary["nonHBM"] / summary["Total"] * 100) 
                    
                    overall = pd.Series({
                        "HBM": summary["HBM"].sum(),
                        "nonHBM": summary["nonHBM"].sum(),
                        "Total": summary["Total"].sum()
                    }, name="Overall")
                    overall["HBM %"] = (overall["HBM"] / overall["Total"] * 100) if overall["Total"] != 0 else 0
                    overall["nonHBM %"] = (overall["nonHBM"] / overall["Total"] * 100) if overall["Total"] != 0 else 0
                    summary_with_overall = pd.concat([summary, overall.to_frame().T], axis=0)
                    
                    
                    disp = pd.DataFrame({
                        "Quarter": summary_with_overall.index.tolist(),
                        "HBM": fmt_num(summary_with_overall["HBM"]),
                        "nonHBM": fmt_num(summary_with_overall["nonHBM"]),
                        "Total": fmt_num(summary_with_overall["Total"]),
                        "HBM %": fmt_pct(summary_with_overall["HBM %"]),
                        "nonHBM %": fmt_pct(summary_with_overall["nonHBM %"]),
                    })

                    # Build hbm_by_quarter / hbm_total percentage table 
                    # Build non_hbm_by_quarter / non_hbm_total percentage table 

                    hbm_den = hbm_total.copy()
                    hbm_den = hbm_den.where(hbm_den != 0)  # NaN where zero
                    non_hbm_den = non_hbm_total.copy()
                    non_hbm_den = non_hbm_den.where(non_hbm_den != 0)
                    
                    hbm_pct = (hbm_by_quarter.div(hbm_den, axis=1) * 100)
                    non_hbm_pct = (non_hbm_by_quarter.div(non_hbm_den, axis=1) * 100)


                    # Reindex columns to the selected quarter order and format for display
                    hbm_pct_disp = (
                        hbm_pct.reindex(columns=quarters)
                        .fillna(0)
                        .round(1)
                        .astype(str) + '%'
                    )
                    
                    non_hbm_pct_disp = (
                        non_hbm_pct.reindex(columns=quarters)
                        .fillna(0)
                        .round(1)
                        .astype(str) + '%'
                    )
                    
                    quarters = list(portion_collapsed.columns)    # x-axis
                    products = list(portion_collapsed.index)      # stacked series

                    # Helper to build table cell lists (first column = process_series name)
                    def table_cells(df_pct_str):
                        return [df_pct_str.index.tolist()] + [df_pct_str[q].tolist() for q in df_pct_str.columns]

                    
                    # Build subplot
                    fig_HBM = make_subplots(
                        rows=2, cols=2,
                        column_widths=[0.5, 0.5],
                        shared_xaxes=False,
                        specs=[
                                [{"type": "xy"}, {"type": "domain"}],  # Left: bar chart, Right: nested tables
                                [{"type": "domain"}, {"type": "domain"}]
                            ],
                            subplot_titles=["HBM vs non-HBM by Quarter", "non-HBM Process Series Tables", "HBM/non-HBM Totals & %", "HBM Process Series Tables"]

                    )

                    
                    # Bar traces (stacked)
                    
                    fig_HBM.add_trace(
                        go.Bar(name='HBM', x=totals.index, y=totals['HBM']),
                        row=1, col=1
                    )
                    fig_HBM.add_trace(
                        go.Bar(name='nonHBM', x=totals.index, y=totals['nonHBM']),
                        row=1, col=1
                    )

                    # total table                   
                    fig_HBM.add_trace(
                        go.Table(
                            header=dict(
                                values=["Quarter", "HBM", "nonHBM", "Total", "HBM %", "nonHBM %"],
                                fill_color="#505A5F",
                                font=dict(color="white", size=12),
                                align="center"
                            ),
                            cells=dict(
                                values=[
                                    disp["Quarter"],
                                    disp["HBM"],
                                    disp["nonHBM"],
                                    disp["Total"],
                                    disp["HBM %"],
                                    disp["nonHBM %"],
                                ],
                                fill_color=[["#F5F7FA" if (i % 2 == 0) else "#FFFFFF" for i in range(len(disp))]] * 6,
                                align="center",
                                height=26
                            ),
                            columnwidth=[90, 90, 90, 90, 90, 100]
                        ),
                        row=2, col=1
                    )

                    

                    # non HBM Percentage Table trace
                    
                    fig_HBM.add_trace(
                        go.Table(
                            header=dict(
                                values=['Process Series'] + quarters,
                                fill_color='#87CEFA',
                                font=dict(color='white', size=12),
                                align='center'
                            ),
                            cells=dict(
                                values=table_cells(non_hbm_pct_disp),
                                fill_color=[['#cbe5f5'] * len(non_hbm_pct_disp.index)] + [['#FFFFFF'] * len(quarters)],
                                align=['left'] + ['center'] * len(quarters),
                                height=26
                            ),
                            columnwidth=[120] + [60] * len(quarters)
                        ),
                        row=1, col=2
                    )

                    
                    # HBM Percentage Table trace: hbm_by_quarter / hbm_total
                    
                    fig_HBM.add_trace(
                        go.Table(
                            header=dict(
                                values=['Process'] + quarters,
                                fill_color='#0078D7',
                                font=dict(color='white', size=12),
                                align='center'
                            ),
                            cells=dict(
                                values=table_cells(hbm_pct_disp),
                                fill_color=[['#cad8e3'] * len(hbm_pct_disp.index)] + [['#FFFFFF'] * len(hbm_pct_disp.index)] * len(quarters),
                                align=['left'] + ['center'] * len(quarters),
                                height=26
                            ),
                            columnwidth=[120] + [60] * len(quarters)
                        ),
                        row=2, col=2
                    )
                    

                    
                    
                    fig_HBM.update_layout(
                        barmode='stack',
                        xaxis_title='Quarter',
                        yaxis_title='Wafer Output',
                        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                        height=600,
                        margin=dict(t=60, b=40, l=40, r=20)
                    )

                    
                    # Streamlit
                    st.plotly_chart(fig_HBM, use_container_width=True)



            except Exception as e:
                st.error(f"Error processing file: {e}")

    except Exception as e:
        st.error(f"Error in main application: {str(e)}")

if __name__ == "__main__":
    main()
