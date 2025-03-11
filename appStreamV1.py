import streamlit as st
import pandas as pd
import re
import io
import xlsxwriter
from datetime import datetime

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
            # Replace any parentheses content with the category, adding an empty space before the category.
            if re.search(r'\([^)]*\)', new_name):
                new_name = re.sub(r'\([^)]*\)', f" {category}", new_name).strip()
            else:
                new_name = f"{new_name} {category}".strip()
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

        # Access the workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        # Create formats: one for headers (bold + border) and one for regular cells (border only)
        #header_format = workbook.add_format({'bold': True, 'border': 1})
        header_format = workbook.add_format({'bold': True, 'border': 1, 'rotation': 90, 'shrink': True})
        border_format = workbook.add_format({'border': 1})

        # Write teacher info cells with border formatting
        worksheet.write('A1', 'Docente:', border_format)
        worksheet.write('B1', docente, border_format)
        worksheet.write('A2', 'Area:', border_format)
        worksheet.write('B2', area, border_format)
        worksheet.write('A3', 'Curso:', border_format)
        worksheet.write('B3', curso, border_format)
        worksheet.write('A4', 'Nivel:', border_format)
        worksheet.write('B4', nivel, border_format)
        
        # Write current date in cell A5 with the format yy-mm-dd
        timestamp = datetime.now().strftime("%y-%m-%d")
        worksheet.write('A5', timestamp, border_format)

        # Re-write the header row (row 6) with bold formatting and borders
        for col_num, value in enumerate(df_final.columns):
            worksheet.write(6, col_num, value, header_format)

        # Adjust column widths: widen columns with "nombre" or "apellido"
        for idx, col_name in enumerate(df_final.columns):
            if "nombre" in col_name.lower() or "apellido" in col_name.lower():
                worksheet.set_column(idx, idx, 25)  # Set a wider width for name columns
            elif col_name.startswith("blank_"):
                worksheet.set_column(idx, idx, 2)   # Narrow column for blank columns
            else:
                worksheet.set_column(idx, idx, 5)  # Default width for other columns

        # Determine the range for the data (including header)
        num_rows = df_final.shape[0]
        num_cols = df_final.shape[1]
        # Data starts at row 6 (header) and ends at row 6 + number of data rows
        data_start_row = 6  
        data_end_row = 6 + num_rows  
        # Apply a conditional format with a formula that always evaluates to TRUE to add borders to all cells
        worksheet.conditional_format(data_start_row, 0, data_end_row, num_cols - 1, {
            'type': 'formula',
            'criteria': '=TRUE',
            'format': border_format
        })

    output.seek(0)
    return output

def main():
    st.title("Griffin's CSV a Excel v.042")

    docente = st.text_input("Escriba el nombre del docente:")
    area = st.text_input("Escriba el área:")
    curso = st.text_input("Escriba el curso:")
    nivel = st.text_input("Escriba el nivel:")

    uploaded_file = st.file_uploader("Subir archivo CSV", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            output_excel = process_data(df, docente, area, curso, nivel)
            st.download_button(
                label="Descargar Gradebook organizado (Excel)",
                data=output_excel,
                file_name="final_cleaned_gradebook.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("Procesamiento completado!")
        except Exception as e:
            st.error(f"Ha ocurrido un error: {e}")

if __name__ == "__main__":
    main()
