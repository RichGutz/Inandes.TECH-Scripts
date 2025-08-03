from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import datetime

def generate_variable_pdf(data_dict: dict, output_filepath: str):
    doc = SimpleDocTemplate(output_filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Variables y Valores de la Aplicación", styles['h1']))
    story.append(Paragraph(f"Generado el: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", styles['h3']))
    story.append(Spacer(1, 0.2 * letter[1])) # Add some space

    # Prepare data for table
    table_data = [['Variable Name', 'Value']]
    for key, value in data_dict.items():
        # Handle dictionaries and lists for better readability
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                table_data.append([f"{key}.{sub_key}", str(sub_value)])
        elif isinstance(value, list):
            for i, item in enumerate(value):
                table_data.append([f"{key}[{i}]", str(item)])
        else:
            table_data.append([str(key), str(value)])

    # Create table
    # Calculate column widths to fit content, with a max for the value column
    col_widths = [200, 350] # Fixed width for variable name, flexible for value

    table = Table(table_data, colWidths=col_widths)

    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')), # Green header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E8F5E9')), # Light green background for rows
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#A5D6A7')), # Lighter green grid
        ('VALIGN', (0,0), (-1,-1), 'TOP'), # Align content to top
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))

    story.append(table)
    doc.build(story)
