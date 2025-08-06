import streamlit as st
import pandas as pd
import plotly.express as px
from utils.ui_helper import UIHelper
from openpyxl.utils import column_index_from_string
from streamlit_plotly_events import plotly_events


def parse_cell(cell):
    col = ''.join(filter(str.isalpha, cell))
    row = int(''.join(filter(str.isdigit, cell)))
    return column_index_from_string(col) - 1, row - 1  # Convert to 0-based index

def prepare_plot_data(df, start_col, end_col, x_row, y_start_row, y_end_row, group_col_index):
    x_labels = df.iloc[x_row, start_col:end_col + 1]
    y_values = df.iloc[y_start_row:y_end_row + 1, start_col:end_col + 1]
    group_labels = df.iloc[y_start_row:y_end_row + 1, group_col_index].values

    plot_data = pd.DataFrame(y_values.values, columns=x_labels)
    plot_data['Group'] = group_labels
    plot_data_melted = plot_data.melt(id_vars='Group', var_name='Time Period', value_name='Wafer Output')

    return plot_data, plot_data_melted

def create_plots(plot_data_melted, title):
    fig = px.line(plot_data_melted, x='Time Period', y='Wafer Output', color='Group', markers=True,
                  title=title)
    click_fig = px.line(plot_data_melted, x='Time Period', y='Wafer Output', color='Group', markers=True)
    click_fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
    return fig, click_fig


def create_plots(plot_data_melted, title):
    fig = px.line(plot_data_melted, x='Time Period', y='Wafer Output', color='Group', markers=True,
                  title=title)
    click_fig = px.line(plot_data_melted, x='Time Period', y='Wafer Output', color='Group', markers=True)
    click_fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
    return fig, click_fig


def main():
    try:
        UIHelper.config_page()
        UIHelper.setup_sidebar()

        st.title("📊 BC Visualization")
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
                st.success(f"Showing data from {start_cell} to {end_cell}")
                st.dataframe(df_range)

                # Plot 
                plot_data_all, plot_data_melted_all = prepare_plot_data(
                    df, start_col, end_col, x_row=2, y_start_row=3, y_end_row=17, group_col_index=column_index_from_string('D') - 1
                )
                fig_all, click_fig_all = create_plots(plot_data_melted_all, title="OMT DRAM BC")
                

                st.plotly_chart(fig_all, use_container_width=True)
                st.markdown("**Click on a data point to update the pie chart**")
                col3, col4 = st.columns([2,1])
                with col3: 
                    selected_points_all = plotly_events(click_fig_all, click_event=True, hover_event=False, override_width=1150)
                    

                with col4:
                    # Show selected point info
                    if selected_points_all:
                        clicked_all = selected_points_all[0]
                        time_period_all = clicked_all['x']
                        filtered_data_all = plot_data_melted_all[plot_data_melted_all['Time Period'] == time_period_all]
                        filtered_data_all = filtered_data_all[filtered_data_all['Group'] != "Total DRAM"]

                    
                        # Pie chart for that time period
                        pie_fig_all = px.pie(filtered_data_all, names='Group', values='Wafer Output', title=f'Wafer Output for {time_period_all}')
                        st.plotly_chart(pie_fig_all)
                    else:
                        st.write("No point clicked yet.")
                        
                plot_data_delta, plot_data_melted_delta = prepare_plot_data(
                    df, start_col, end_col, x_row=2, y_start_row=44, y_end_row=58, group_col_index=column_index_from_string('D') - 1
                )
                fig_delta, click_fig_delta = create_plots(plot_data_melted_delta, title="OMT DRAM BC Delta")
                
                st.plotly_chart(fig_delta, use_container_width=True)
                st.markdown("**Click on a data point to update the pie chart**")
                col3, col4 = st.columns([2,1])
                with col3: 
                    st.markdown("**Select a date range to view wafer output flow**")
                    start_date, end_date = st.date_input("Date Range", [plot_data_melted_delta['Time Period'].min(), plot_data_melted_delta['Time Period'].max()])

                    

                with col4:
                    # Show selected point info
                    if selected_points_delta:
                        clicked_delta = selected_points_delta[0]
                        time_period_delta = clicked_delta['x']
                        filtered_data_delta = plot_data_melted_delta[plot_data_melted_delta['Time Period'] == time_period_delta]
                        filtered_data_delta = filtered_data_delta[filtered_data_delta['Group'] != "Total DRAM"]

                    
                        # Pie chart for that time period
                        pie_fig_delta = px.pie(filtered_data_delta, names='Group', values='Wafer Output', title=f'Wafer Output for {time_period_delta}')
                        st.plotly_chart(pie_fig_delta)
                    else:
                        st.write("No point clicked yet.")


            except Exception as e:
                st.error(f"Error processing file: {e}")

    except Exception as e:
        st.error(f"Error in main application: {str(e)}")

if __name__ == "__main__":
    main()
