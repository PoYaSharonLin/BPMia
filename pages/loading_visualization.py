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
            end_cell = st.text_input("Enter end cell (e.g., JE17):", value="JE17")

        if uploaded_file:
            try:
                sheet_name = "F16 DRAM BC"
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

                # Define the range for plotting
                x_row = 2  # Excel row 4 (0-based index)
                y_start_row = 3  # Excel row 5
                y_end_row = 17  # Excel row 17
                group_col_index = column_index_from_string('D') - 1

                x_labels = df.iloc[x_row, start_col:end_col + 1]
                y_values = df.iloc[y_start_row:y_end_row + 1, start_col:end_col + 1]
                group_labels = df.iloc[y_start_row:y_end_row + 1, group_col_index].values
                
                
                # Prepare data for plotting
                plot_data = pd.DataFrame(y_values.values, columns=x_labels)
                plot_data['Group'] = group_labels

                # Melt the DataFrame to long format
                plot_data_melted = plot_data.melt(id_vars='Group', var_name='Time Period', value_name='Wafer Output')

                # Create the plot
                fig = px.line(plot_data_melted, x='Time Period', y='Wafer Output', color='Group', markers=True,
                              title='BC Projection')
                click_fig = px.line(plot_data_melted, x='Time Period', y='Wafer Output', color='Group', markers=True)
                click_fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("**Click on a data point to update the pie chart**")
                col3, col4 = st.columns([2, 1])  
                with col3: 
                    selected_points = plotly_events(click_fig, click_event=True, hover_event=False, override_width=1100)
                    

                with col4:
                    # Show selected point info
                    if selected_points:
                        clicked = selected_points[0]
                        time_period = clicked['x']
                        filtered_data = plot_data_melted[plot_data_melted['Time Period'] == time_period]
                        filtered_data = filtered_data[filtered_data['Group'] != "Total DRAM"]

                    
                        # Pie chart for that time period
                        pie_fig = px.pie(filtered_data, names='Group', values='Wafer Output', title=f'Wafer Output for {time_period}')
                        st.plotly_chart(pie_fig)
                    else:
                        st.write("No point clicked yet.")


            except Exception as e:
                st.error(f"Error processing file: {e}")

    except Exception as e:
        st.error(f"Error in main application: {str(e)}")

if __name__ == "__main__":
    main()
