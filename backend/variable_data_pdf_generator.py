from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import datetime

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                else:
                    items.append((f"{new_key}[{i}]", str(item)))
        else:
            items.append((new_key, str(v)))
    return dict(items)

def generate_variable_pdf(data_dict: dict, output_filepath: str):
    doc = SimpleDocTemplate(output_filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("Variables y Valores de la Aplicación", styles['h1']))
    story.append(Paragraph(f"Generado el: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", styles['h3']))
    story.append(Spacer(1, 0.2 * letter[1])) # Add some space

    # Flatten the data dictionary
    flattened_data = flatten_dict(data_dict)

    # Prepare data for table
    table_data = [['Variable Name', 'Value']]
    for key, value in flattened_data.items():
        table_data.append([str(key), str(value)])

    # Create table
    # Calculate column widths to fit content, with a max for the value column
    page_width = letter[0] # Get page width
    left_margin = 72 # Default ReportLab left margin
    right_margin = 72 # Default ReportLab right margin
    usable_width = page_width - left_margin - right_margin

    col1_width = usable_width * 0.70
    col2_width = usable_width * 0.30
    col_widths = [col1_width, col2_width]

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
        ('FONTSIZE', (0,0), (-1,-1), 8), # Reduce font size to 8 points
    ]))

    story.append(table)
    try:
        doc.build(story)
    except Exception as e:
        print(f"Error building PDF: {e}")
