import streamlit as st
import pandas as pd
import io

def create_filtered_gradebook(df, trimester_to_exclude):
    """
    Excludes grade columns for a specified trimester from the gradebook.

    Args:
        df (pd.DataFrame): The original gradebook DataFrame.
        trimester_to_exclude (str): The trimester to exclude (e.g., 'Term1', 'Term2', 'Term3').

    Returns:
        pd.DataFrame: A new DataFrame with the specified trimester's columns removed.
    """
    # Define the general columns to always keep
    general_columns = [
        "First Name", "Last Name", "Unique User ID", "Overall", "2025", "Term1 - 2025",
        "Term2 - 2025", "Term3 - 2025"
    ]
    
    # Identify the prefix for the columns to exclude
    prefix_to_exclude = f"{trimester_to_exclude} - 2025"

    # Columns to keep initially
    columns_to_keep = []

    # Iterate through all columns to decide which to keep
    for col in df.columns:
        # Keep general columns and any columns that don't start with the exclusion prefix
        if col in general_columns or not col.startswith(prefix_to_exclude):
            columns_to_keep.append(col)

    # Create the new DataFrame with the filtered columns
    filtered_df = df[columns_to_keep]

    return filtered_df

# --- Streamlit App ---

st.title("Gradebook Trimester Filter")
st.write("Upload a Schoology gradebook CSV and select a trimester to exclude.")

uploaded_file = st.file_uploader("Upload Gradebook CSV", type="csv")

if uploaded_file:
    # Read the uploaded CSV file into a pandas DataFrame
    df = pd.read_csv(uploaded_file)
    
    st.success("File uploaded successfully!")
    st.subheader("Select Trimester to Exclude")

    # Dropdown menu to select the trimester
    trimester_choice = st.selectbox(
        "Choose the trimester you want to remove grades for:",
        ("Term1", "Term2", "Term3")
    )

    if st.button("Generate Filtered Gradebook"):
        # Process the DataFrame
        try:
            filtered_gradebook = create_filtered_gradebook(df, trimester_choice)
            st.success(f"✅ Grades for {trimester_choice} have been removed.")

            # Create a CSV in-memory for download
            csv_buffer = io.StringIO()
            filtered_gradebook.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            
            st.download_button(
                label="📥 Download Filtered CSV",
                data=csv_buffer.getvalue(),
                file_name=f"gradebook_without_{trimester_choice}.csv",
                mime="text/csv"
            )
            
            st.write("---")
            st.subheader("Preview of the New Gradebook:")
            st.dataframe(filtered_gradebook.head())
            st.write(f"This preview shows the first 5 rows of the new gradebook. The total number of columns is {len(filtered_gradebook.columns)}.")
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.write("Please ensure the uploaded file is a valid Schoology gradebook.")
