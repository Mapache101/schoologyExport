import streamlit as st
import pandas as pd
import io

def create_single_trimester_gradebook(df, trimester_to_keep):
    """
    Filters the gradebook to keep only general student information and columns
    for a single, specified trimester.

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
    
    # Identify the prefix for the columns to keep based on the user's selection
    prefix_to_keep = f"{trimester_to_keep} - 2025"

    # Columns to be included in the new DataFrame
    columns_to_keep = []

    # First, add the general columns in the correct order
    for col in general_columns:
        if col in df.columns:
            columns_to_keep.append(col)

    # Then, find all columns for the selected trimester and add them
    for col in df.columns:
        if col.startswith(prefix_to_keep):
            columns_to_keep.append(col)
            
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
