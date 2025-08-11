import streamlit as st
import pandas as pd
from datetime import datetime
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

def create_total_QoQ(df):
    # Extract quarter labels and Total DRAM values
    quarter_labels = df.iloc[0, 2:].values
    total_dram_values = df[df.iloc[:, 0] == 'Total_DRAM'].iloc[0, 2:].astype(float).values
    
    # # Create a DataFrame with quarter labels and corresponding Total DRAM values
    # data = pd.DataFrame({
    #     'Quarter': quarter_labels,
    #     'Total_DRAM': total_dram_values
    # })
    
    # # Group by quarter and calculate percentage change: ((last - first) / first) * 100
    # quarter_changes = data.groupby('Quarter')['Total_DRAM'].agg(['first', 'last'])
    # quarter_changes['Percentage_Change'] = ((quarter_changes['last'] - quarter_changes['first']) / quarter_changes['first']) * 100

    return quarter_labels

    


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
                    st.markdown("**Select a week range**")
                    
                    # Step 1: Extract week and year from 'Time Period' string
                    plot_data_melted_delta[['Month', 'WeekYear']] = plot_data_melted_delta['Time Period'].str.split(' ', expand=True)
                    plot_data_melted_delta[['Week', 'Year']] = plot_data_melted_delta['WeekYear'].str.split('-', expand=True).astype(int)
                    
                    # Step 2: Create 'Fiscal Year Week' label
                    plot_data_melted_delta['Fiscal Year Week'] = plot_data_melted_delta.apply(
                        lambda x: f"W{x['Week']:02d}-{x['Year']}", axis=1
                    )
                    
                    # Step 3: Create datetime object for each week (Monday of the week)
                    plot_data_melted_delta['Week Start Date'] = plot_data_melted_delta.apply(
                        lambda x: datetime.strptime(f"{x['Year']}-W{x['Week']:02d}-5", "%G-W%V-%u"), axis=1
                    )
                    
                    # Step 4: Create label-to-date mapping
                    df_filtered = plot_data_melted_delta.copy()
                    labels = df_filtered['Fiscal Year Week'].drop_duplicates().tolist()
                    unique_periods = df_filtered['Week Start Date'].sort_values().unique()
                    label_to_period = dict(zip(labels, unique_periods))


                    
                    
                    if labels:
                        # Sort labels chronologically based on their corresponding dates
                        sorted_labels = sorted(labels, key=lambda x: label_to_period[x])
                    
                        # Select start and end week using selectbox
                        start_label = st.selectbox("Start Week", options=sorted_labels, index=0)
                        end_label = st.selectbox("End Week", options=sorted_labels, index=len(sorted_labels) - 1)
                    
                        start_week = label_to_period[start_label]
                        end_week = label_to_period[end_label]
                    
                        # Ensure start_week is before or equal to end_week
                        if start_week <= end_week:
                            # Step 6: Filter data
                            filtered_data = df_filtered[
                                (df_filtered['Week Start Date'] >= start_week) & (df_filtered['Week Start Date'] <= end_week)
                            ]
                    
                            # Step 7: Display filtered data
                            st.write("Start Date:", start_week)
                            st.write("End Date:", end_week)
                        else:
                            st.warning("Start week must be before or equal to end week.")
                    
                    else:
                        st.info("No valid dates to build week options.")
            
                with col4: 
                    plot_data_all, plot_data_melted_all, primary_labels_all, secondary_labels_all = prepare_line_plot_data(
                    df, start_col, end_col, x_row=2, y_start_row=0, y_end_row=17, group_col_index=column_index_from_string('D') - 1
                )   

                    st.dataframe(plot_data_all)                  # Product (rows) x Quarter (cols)
                    total_QoQ = create_total_QoQ(plot_data_all)
                    st.write(total_QoQ)
                    # st.write("Wafer Output by Product:")
                    # st.dataframe(wafer_output_by_product)
                    
                    # st.write("Percentage by Product (% of quarter total):")
                    # st.dataframe(percentage_by_product.round(2))
                    
                    # st.write("QoQ Change for Total_DRAM (fraction):")
                    # st.dataframe(total_dram_qoq.round(4))


            except Exception as e:
                st.error(f"Error processing file: {e}")

    except Exception as e:
        st.error(f"Error in main application: {str(e)}")

if __name__ == "__main__":
    main()
