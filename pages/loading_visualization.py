import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
                plot_data_delta, plot_data_melted_delta, primary_labels, secondary_labels= prepare_line_plot_data(
                    df, start_col, end_col, x_row=2, y_start_row=44, y_end_row=58, group_col_index=column_index_from_string('D') - 1
                )
                fig_delta = create_line_plot(plot_data_melted_delta, "OMT DRAM BC Delta", primary_labels, secondary_labels)
                st.plotly_chart(fig_delta, use_container_width=True)
                
                st.markdown("### Select a date range to view YoY & QoQ data")
                col3, col4 = st.columns([1,2])
                with col3: 
                    plot_data_melted_delta['Time Period'] = pd.to_datetime(plot_data_melted_delta['Time Period'], errors='coerce')
                    try:
                        start_date, end_date = st.date_input("Date Range", [plot_data_melted_delta['Time Period'].min(), plot_data_melted_delta['Time Period'].max()])
                        filtered_data = plot_data_melted_delta[
                                    (plot_data_melted_delta['Time Period'] >= pd.to_datetime(start_date)) &
                                    (plot_data_melted_delta['Time Period'] <= pd.to_datetime(end_date))
                                ]
                    except Exception as e:
                        st.error(f"Date Range Selection Error: {e}")
                        
                with col4: 
                    st.markdown("#### YoY")
                    st.markdown("#### QoQ")

            except Exception as e:
                st.error(f"Error processing file: {e}")

    except Exception as e:
        st.error(f"Error in main application: {str(e)}")

if __name__ == "__main__":
    main()
