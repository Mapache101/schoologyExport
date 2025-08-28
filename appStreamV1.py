import streamlit as st
import pandas as pd
import io

def create_single_trimester_gradebook(df, trimester_to_keep):
    """
    Filters the gradebook to keep only general student information and all
    grade columns for a single, specified trimester.

    Args:
        df (pd.DataFrame): The original gradebook DataFrame.
        trimester_to_keep (str): The trimester to keep (e.g., 'Term1', 'Term2', 'Term3').

    Returns:
        pd.DataFrame: A new DataFrame with only the specified trimester's columns.
    """
    # Define the general columns to always keep
    general_columns = [
        "First Name", "Last Name", "Unique User ID", "Overall", "2025"
    ]
    
    # Identify the start and end columns for each trimester
    # We use a pattern to find the first category score column for each term
    trimester_start_cols = {}
    for col in df.columns:
        if "Term1 - 2025 - AUTO EVAL - Category Score" in col:
            trimester_start_cols["Term1"] = col
        if "Term2 - 2025 - AUTO EVAL - Category Score" in col:
            trimester_start_cols["Term2"] = col
        if "Term3 - 2025 - AUTO EVAL - Category Score" in col:
            trimester_start_cols["Term3"] = col

    # Check if we found the required start columns
    if trimester_to_keep not in trimester_start_cols:
        st.error(f"Could not find a starting column for {trimester_to_keep}. Please check your file format.")
        return None

    # Get the column index for the start of the selected trimester
    start_col_index = df.columns.get_loc(trimester_start_cols[trimester_to_keep])
    
    # Determine the end index of the trimester's grade columns
    end_col_index = None
    if trimester_to_keep == "Term1":
        if "Term2" in trimester_start_cols:
            end_col_index = df.columns.get_loc(trimester_start_cols["Term2"])
    elif trimester_to_keep == "Term2":
        if "Term3" in trimester_start_cols:
            end_col_index = df.columns.get_loc(trimester_start_cols["Term3"])
    elif trimester_to_keep == "Term3":
        # If it's the last trimester, we go to the end of the DataFrame
        end_col_index = len(df.columns)

    if end_col_index is None:
        # If no end column was found, assume this is the last term in the file
        end_col_index = len(df.columns)

    # Slice the DataFrame to get the columns for the selected trimester's grades
    trimester_grade_columns = df.columns[start_col_index:end_col_index].tolist()
    
    # Combine general columns with the selected trimester's grade columns
    columns_to_keep = general_columns + trimester_grade_columns
            
    # Create the new DataFrame with the filtered columns
    filtered_df = df[columns_to_keep]

    return filtered_df

# --- Streamlit App ---

st.title("Gradebook Trimester Filter")
st.write("Upload a gradebook CSV and select a trimester to keep. All other trimester grades will be removed.")

uploaded_file = st.file_uploader("Upload Gradebook CSV", type="csv")

if uploaded_file:
    # Read the uploaded CSV file into a pandas DataFrame
    df = pd.read_csv(uploaded_file)
    
    st.success("File uploaded successfully!")
    st.subheader("Select Trimester to Keep")

    # Dropdown menu to select the trimester
    trimester_choice = st.selectbox(
        "Choose the trimester you want to see grades for:",
        ("Term1", "Term2", "Term3")
    )

    if st.button("Generate Single Trimester Gradebook"):
        # Process the DataFrame
        try:
            filtered_gradebook = create_single_trimester_gradebook(df, trimester_choice)
            
            if filtered_gradebook is not None:
                st.success(f"✅ Gradebook filtered successfully to show only grades for {trimester_choice}!")

                # Create a CSV in-memory for download
                csv_buffer = io.StringIO()
                filtered_gradebook.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)
                
                st.download_button(
                    label="📥 Download Filtered CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"gradebook_only_{trimester_choice}.csv",
                    mime="text/csv"
                )
                
                st.write("---")
                st.subheader("Preview of the New Gradebook:")
                st.dataframe(filtered_gradebook.head())
                st.write(f"This preview shows the first 5 rows of the new gradebook. The total number of columns is {len(filtered_gradebook.columns)}.")
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.write("Please ensure the uploaded file is a valid gradebook CSV.")
