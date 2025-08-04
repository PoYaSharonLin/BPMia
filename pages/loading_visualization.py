import streamlit as st
import pandas as pd
from utils.ui_helper import UIHelper
from openpyxl.utils import column_index_from_string


st.title("📊 Loading Visualization")
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
start_cell = st.text_input("Enter start cell (e.g., D3):", value="D3")
end_cell = st.text_input("Enter end cell (e.g., JE17):", value="JE17")

if start_cell and end_cell:
  try:
    # Parse cell references
        def parse_cell(cell):
            col = ''.join(filter(str.isalpha, cell))
            row = int(''.join(filter(str.isdigit, cell)))
            return column_index_from_string(col) - 1, row - 1  # Convert to 0-based index

        start_col, start_row = parse_cell(start_cell)
        end_col, end_row = parse_cell(end_cell)
    
  except Expection as e: 
    st.error(f"Missing Start or End Range: {e}")

if uploaded_file:
    try:
        # Read the Excel file
        sheet_name = "F16 DRAM BC"
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name, engine='openpyxl')

        # Slice the DataFrame
        df_range = df.iloc[start_row:end_row + 1, start_col:end_col + 1]

        st.success(f"Showing data from {start_cell} to {end_cell}")
        st.dataframe(df_range)

    except Exception as e:
        st.error(f"Error reading range: {e}")

def main(): 
  try: 
    UIHelper.config_page()
    UIHelper.setup_sidebar()

  except Exception as e: 
    st.error(f"Error in main application: {str(e)}")

if __name__ == "__main__":
    main()
    
