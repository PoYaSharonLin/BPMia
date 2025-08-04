import streamlit as st
import pandas as pd
import plotly.express as px
from utils.ui_helper import UIHelper
from openpyxl.utils import column_index_from_string

def parse_cell(cell):
    col = ''.join(filter(str.isalpha, cell))
    row = int(''.join(filter(str.isdigit, cell)))
    return column_index_from_string(col) - 1, row - 1  # Convert to 0-based index

def main():
    try:
        UIHelper.config_page()
        UIHelper.setup_sidebar()

        st.title("📊 Loading Visualization")
        uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
        start_cell = st.text_input("Enter start cell (e.g., D3):", value="D3")
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
                start_col_plot = column_index_from_string('CR') - 1
                end_col_plot = column_index_from_string('JE') - 1
                x_row = 3  # Excel row 4 (0-based index)
                y_start_row = 4  # Excel row 5
                y_end_row = 16  # Excel row 17
                group_col_index = column_index_from_string('D') - 1

                x_raw = df.iloc[x_row, start_col_plot:end_col_plot + 1].values
                x_labels = pd.to_datetime(x_raw, unit='D', origin='1899-12-30').strftime('%b %d-%Y')
                y_values = df.iloc[y_start_row:y_end_row + 1, start_col_plot:end_col_plot + 1]
                group_labels = df.iloc[y_start_row:y_end_row + 1, group_col_index].values

                # Prepare data for plotting
                plot_data = pd.DataFrame(y_values.values, columns=x_labels)
                plot_data['Group'] = group_labels

                # Melt the DataFrame to long format
                plot_data_melted = plot_data.melt(id_vars='Group', var_name='X', value_name='Y')

                # Create the plot
                fig = px.line(plot_data_melted, x='X', y='Y', color='Group', markers=True,
                              title='Line Plot Grouped by Column D')

                # Display the plot in Streamlit
                st.plotly_chart(fig)

            except Exception as e:
                st.error(f"Error processing file: {e}")

    except Exception as e:
        st.error(f"Error in main application: {str(e)}")

if __name__ == "__main__":
    main()
