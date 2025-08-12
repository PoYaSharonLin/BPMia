import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
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


def main():
    try:
        UIHelper.config_page()
        UIHelper.setup_sidebar()

        st.title("📊Loading Mia")
        uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
        col1, col2 = st.columns(2)
        with col1:
            start_cell = st.text_input("Enter start cell (e.g., CR3):", value="CR3")
        with col2:
            end_cell = st.text_input("Enter end cell (e.g., JE16):", value="JE16")

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
                st.success(f"Showing data from {start_cell} to {end_cell} from excel sheet")
                st.dataframe(df_range)


                # Delta Line plot 
                plot_data_delta, plot_data_melted_all, primary_labels, secondary_labels= prepare_line_plot_data(
                    df, start_col, end_col, x_row=2, y_start_row=44, y_end_row=58, group_col_index=column_index_from_string('D') - 1
                )
                fig_delta = create_line_plot(plot_data_melted_all, "OMT DRAM BC Delta", primary_labels, secondary_labels)
                st.plotly_chart(fig_delta, use_container_width=True)
                
                st.markdown("### Select a date range to view YoY & QoQ data")
                st.markdown("**Overall QoQ**")
                plot_data_all, plot_data_melted_all, primary_labels_all, secondary_labels_all = prepare_line_plot_data(
                df, start_col, end_col, x_row=2, y_start_row=0, y_end_row=17, group_col_index=column_index_from_string('D') - 1
            )   

                # st.dataframe(plot_data_all)                  # Product (rows) x Quarter (cols)
                quarter = plot_data_all.iloc[0]
                dram_value = plot_data_all.iloc[10]
                total_dram = pd.DataFrame([quarter,dram_value])
                group_labels = total_dram.iloc[0, 1:-1]  
                values = total_dram.iloc[1, 1:-1].astype(float)
                total_df = pd.DataFrame({'Group': group_labels, 'Value': values})
                collapsed = total_df.groupby('Group').sum().reset_index()
                
                collapsed['Group'] = pd.Categorical(collapsed['Group'], categories=custom_order, ordered=True)
                df_sorted = collapsed.sort_values('Group')
                percentage_df = df_sorted.copy()
                percentage_df.columns = ['Quarter', 'Total Wafer Out']
                percentage_df['Total Wafer Out'] = pd.to_numeric(percentage_df['Total Wafer Out'], errors='coerce')
                percentage_df['% Change'] = round(percentage_df['Total Wafer Out'].pct_change() * 100, 2)
                st.dataframe(percentage_df.T)
                
                col3, col4 = st.columns([1,2])
                with col3: 
                    st.markdown("**Select a week range**")
                    date_table = plot_data_all.copy()
                    w_row = pd.Series({col: to_wlabel(col) for col in date_table.columns}, name='Week')
                    date_table_with_week = pd.concat([w_row.to_frame().T, date_table], ignore_index=False)

                    # create select table
                    week_row = date_table_with_week.loc['Week'].astype(str)
                    mask = week_row.str.fullmatch(r"W\d{2}-\d{4}")
                    ordered_week_cols = week_row.index[mask].tolist()     
                    week_labels = week_row[mask].tolist()          
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        start_week = st.selectbox("Start week", week_labels, index=0)
                    with c2:
                        end_week = st.selectbox("End week", week_labels, index=len(week_labels) - 1)
                    
                    i0, i1 = week_labels.index(start_week), week_labels.index(end_week)
                    if i0 > i1:
                        i0, i1 = i1, i0
                    
                    selected_week_cols = ordered_week_cols[i0 : i1 + 1]
                    
                    # Keep non-week columns (IDs, descriptors) pinned on the left
                    non_week_cols = [c for c in date_table_with_week.columns if c not in ordered_week_cols]
                    filtered = pd.concat(
                        [date_table_with_week[non_week_cols], date_table_with_week[selected_week_cols]],
                        axis=1
                    )
            
                with col4: 
                    st.markdown("**Selected Range Product Portion**")
                    if start_week and end_week: 
                        quarter_map = filtered.iloc[1, 1:].tolist()
                        process_series = filtered.iloc[4:, 0].reset_index(drop=True)
                        values = filtered.iloc[4:, 1:].reset_index(drop=True)
                        values.columns = quarter_map
                        values.insert(0, 'process_series', process_series)
                        
                        hbm_series = {'150S_HBM3', '150S_HBM4', '160S_HBM4E'}
                        non_hbm_series = {'140S_DRAM', '150S_non-HBM', '160S_non-HBM', '170S_DRAM'}
                        
                        hbm_df = values[values['process_series'].isin(hbm_series)].drop('process_series', axis=1).apply(pd.to_numeric, errors='coerce')
                        non_hbm_df = values[values['process_series'].isin(non_hbm_series)].drop('process_series', axis=1).apply(pd.to_numeric, errors='coerce')

                        
                        hbm_by_quarter = hbm_df.groupby(hbm_df.columns, axis=1).sum()
                        non_hbm_by_quarter = non_hbm_df.groupby(non_hbm_df.columns, axis=1).sum()

                        
                        hbm_total = hbm_by_quarter.sum()
                        non_hbm_total = non_hbm_by_quarter.sum()

                                                
                        fig = go.Figure()
                        fig.add_trace(go.Bar(name='HBM', x=hbm_total.index, y=hbm_total.values))
                        fig.add_trace(go.Bar(name='nonHBM', x=non_hbm_total.index, y=non_hbm_total.values))
                        fig.update_layout(barmode='stack', title='HBM vs non-HBM by Quarter', xaxis_title='Quarter', yaxis_title='Value')
                    
                        st.plotly_chart(fig)




            except Exception as e:
                st.error(f"Error processing file: {e}")

    except Exception as e:
        st.error(f"Error in main application: {str(e)}")

if __name__ == "__main__":
    main()
