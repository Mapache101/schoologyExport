import streamlit as st
import pandas as pd
import re
import io
import xlsxwriter

# Define code prefixes and their categories
CODE_PREFIXES = {
    'AV': 'AUTO EVAL',
    'TB': 'TO BE_SER',
    'TD': 'TO DECIDE_DECIDIR',
    'TH': 'TO DO_HACER',
    'TK': 'TO KNOW_SABER'
}

def process_data(df, docente, area, curso, nivel):
    # Drop unwanted columns if present
    columns_to_drop = [
        "Nombre de usuario",
        "Promedio General",
        "Term1 - 2024",
        "Term1 - 2024 - AUTO EVAL TO BE_SER - Puntuación de categoría",
        "Term1 - 2024 - TO BE_SER - Puntuación de categoría",
        "Term1 - 2024 - TO DECIDE_DECIDIR - Puntuación de categoría",
        "Term1 - 2024 - TO DO_HACER - Puntuación de categoría",
        "Term1 - 2024 - TO KNOW_SABER - Puntuación de categoría"
    ]
    df.drop(columns=columns_to_drop, inplace=True, errors='ignore')

    # Process columns: separate coded columns from general ones
    columns_info = []  # Will store info for coded columns
    general_columns = []  # All other columns
    exclude_phrase = "(Contar en la calificación)"
    columns_to_remove = {"ID de usuario único", "ID de usuario unico"}

    for col in df.columns:
        # Skip columns that contain the exclude phrase or are in the removal set
        if exclude_phrase in col or col in columns_to_remove:
            continue

        # Look for coded columns matching a pattern like "AV01 <rest of column name>"
        match = re.match(r'^([A-Z]{2}\d{2})\s+(.*)', col)
        if match:
            code = match.group(1)
            new_name = match.group(2).strip()
            prefix = code[:2]
            seq_num = int(code[2:])
            category = CODE_PREFIXES.get(prefix, 'Other')
            columns_info.append({
                'original': col,
                'new_name': new_name,
                'category': category,
                'seq_num': seq_num
            })
        else:
            general_columns.append(col)

    # Reorder general columns so that columns containing "nombre" or "apellido" come first
    name_columns = [col for col in general_columns if "nombre" in col.lower() or "apellido" in col.lower()]
    other_general = [col for col in general_columns if col not in name_columns]
    general_columns_reordered = name_columns + other_general

    # First, reorder the DataFrame using the original ordering we had
    # (This ordering does not yet include blank columns)
    sorted_coded = sorted(columns_info, key=lambda x: (list(CODE_PREFIXES.values()).index(x['category']) if x['category'] in CODE_PREFIXES.values() else 999, x['seq_num']))
    new_order = general_columns_reordered + [col['original'] for col in sorted_coded]

    # Create a cleaned DataFrame and rename coded columns
    df_cleaned = df[new_order].copy()
    rename_dict = {col['original']: col['new_name'] for col in columns_info}
    df_cleaned.rename(columns=rename_dict, inplace=True)

    # ---------------------------------------------------------------------------
    # Build final ordering for the Excel output with an empty column between coded groups

    # The general columns remain in the front.
    final_general = general_columns_reordered

    # Create groups for coded columns based on CODE_PREFIXES order.
    groups = []
    for prefix, category in CODE_PREFIXES.items():
        group = [d for d in columns_info if d['category'] == category]
        group_sorted = sorted(group, key=lambda x: x['seq_num'])
        group_names = [d['new_name'] for d in group_sorted]
        if group_names:
            groups.append(group_names)

    # Combine groups with an extra "blank" column inserted between each (except after the last)
    final_coded_order = []
    for i, group in enumerate(groups):
        final_coded_order.extend(group)
        if i < len(groups) - 1:
            # Use a unique dummy column name; later we will fill it with empty values
            blank_col_name = f"blank_{i}"
            final_coded_order.append(blank_col_name)

    # Combine the final general and coded column orders
    final_order = final_general + final_coded_order

    # Insert the blank columns (if not already present) with empty values.
    for col in final_order:
        if col.startswith("blank_") and col not in df_cleaned.columns:
            df_cleaned[col] = ""

    # Reorder the DataFrame according to final_order.
    df_final = df_cleaned[final_order]

    # ---------------------------------------------------------------------------
    # Export to Excel with a header section for teacher info

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write the DataFrame starting at row 7 (i.e., startrow=6) so that we can add header info above.
        df_final.to_excel(writer, sheet_name='Sheet1', startrow=6, index=False)

        # Access the worksheet to add header information in specific cells.
        worksheet = writer.sheets['Sheet1']
        worksheet.write('A1', 'Docente:')
        worksheet.write('B1', docente)
        worksheet.write('A2', 'Area:')
        worksheet.write('B2', area)
        worksheet.write('A3', 'Curso:')
        worksheet.write('B3', curso)
        worksheet.write('A4', 'Nivel:')
        worksheet.write('B4', nivel)

        # Optionally, you can adjust the column width for blank columns (or hide headers)
        # For instance, set a narrow width for columns whose header starts with "blank_"
        for idx, col_name in enumerate(df_final.columns):
            if col_name.startswith("blank_"):
                worksheet.set_column(idx, idx, 2)  # Narrow column for visual separation

    output.seek(0)
    return output

def main():
    st.title("Gradebook Cleaner")

    docente = st.text_input("Enter the name of Docente (e.g., Daniel Olguin):")
    area = st.text_input("Enter the area:")
    curso = st.text_input("Enter the curso:")
    nivel = st.text_input("Enter the nivel:")

    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            output_excel = process_data(df, docente, area, curso, nivel)
            st.download_button(
                label="Download Cleaned Gradebook (Excel)",
                data=output_excel,
                file_name="final_cleaned_gradebook.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("Processing complete!")
        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
