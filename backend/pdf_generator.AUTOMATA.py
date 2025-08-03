from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.platypus import PageBreak
import os
import datetime
import random

def generate_pdf(output_filepath, data):
    doc = SimpleDocTemplate(output_filepath, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.375*inch, bottomMargin=0.375*inch)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    styles.add(ParagraphStyle(name='RightAlign', alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='CenterAlign', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='LeftAlign', alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='SmallFont', fontSize=7))
    styles.add(ParagraphStyle(name='BoldSmallFont', fontSize=7, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='BoldNormal', fontName='Helvetica-Bold'))

    # New styles for alignment with bold fonts
    styles.add(ParagraphStyle(name='BoldNormalRight', parent=styles['BoldNormal'], alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='BoldSmallFontRight', parent=styles['BoldSmallFont'], alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='BoldSmallFontCenter', parent=styles['BoldSmallFont'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='BoldExtraSmallFontCenter', parent=styles['BoldSmallFont'], alignment=TA_CENTER, fontSize=6, textColor=colors.blue))
    styles.add(ParagraphStyle(name='BoldNormalCenter', parent=styles['BoldNormal'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='SmallFontCenter', parent=styles['SmallFont'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='BlueSmallFont', fontSize=7, fontName='Helvetica', textColor=colors.blue))
    styles.add(ParagraphStyle(name='TinyFont', fontSize=5))
    styles.add(ParagraphStyle(name='SmallTinyFont', fontSize=6))
    logo_path = "C:/Users/rguti/Inandes.TECH/inputs_para_generated_pdfs/LOGO.png"
    inandes_logo = None
    if os.path.exists(logo_path):
        inandes_logo = Image(logo_path, width=1.5*inch, height=0.5*inch)
    else:
        print(f"Warning: Logo not found at {logo_path}. Using placeholder text.")
        inandes_logo = Paragraph("INANDES Logo Placeholder", styles['RightAlign'])

    # Left column content (Main Title + Client Info)
    left_column_content = []
    left_column_content.append(Paragraph("<b>FONDO NSG MIPYME - INANDES FACTOR CAPITAL S.A.C.</b>", styles['LeftAlign']))
    left_column_content.append(Spacer(1, 0.1 * inch))

    client_info_data = [
        [Paragraph("<b>CONTRATO</b>", styles['SmallFont']), Paragraph(data.get('contract_name', 'INANDES FACTOR CAPITAL SAC'), styles['SmallFont'])],
        [Paragraph("<b>CLIENTE</b>", styles['SmallFont']), Paragraph(data.get('client_name', 'MILENIO CONSULTORES SAC'), styles['BlueSmallFont'])],
        [Paragraph("<b>RUC</b>", styles['SmallFont']), Paragraph(data.get('client_ruc', '20422894854'), styles['BlueSmallFont'])],
        [Paragraph("<b>RELACION DE</b>", styles['SmallFont']), Paragraph(data.get('relation_type', 'FACTURA(S)'), styles['BlueSmallFont'])],
    ]
    client_info_table = Table(client_info_data, colWidths=[0.8*inch, 5.2*inch])
    client_info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    left_column_content.append(client_info_table)

    # Main header table (combining left column content and logo)
    header_table_data = [
        [left_column_content, inandes_logo]
    ]
    header_table = Table(header_table_data, colWidths=[6*inch, 1.5*inch]) # Adjust colWidths as needed
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.05 * inch))

    # Anexo and Date
    styles.add(ParagraphStyle(name='BoldSize7', fontName='Helvetica-Bold', fontSize=7))
    styles.add(ParagraphStyle(name='BoldSize7Right', parent=styles['BoldSize7'], alignment=TA_RIGHT))

    anexo_date_data = [
        [Paragraph(f"<b>ANEXO {data.get('anexo_number', '31')}</b>", styles['BoldSize7']),
         Paragraph(f"<b>FECHA</b> {data.get('document_date', 'JUEVES 29, MAY, 2025')}", styles['BoldSize7Right'])]
    ]
    anexo_date_table = Table(anexo_date_data, colWidths=[doc.width / 2.0, doc.width / 2.0])
    anexo_date_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
    ]))
    story.append(anexo_date_table)
    story.append(Spacer(1, 0.1 * inch))

    # Table Headers
    table1_headers = [
        Paragraph("<b>Nro. Facturas</b>", styles['BoldSmallFont']),
        Paragraph("<b>Fecha de Vencimiento</b>", styles['BoldSmallFont']),
        Paragraph("<b>Fecha de Desembolso</b>", styles['BoldSmallFont']),
        Paragraph("<b># de días</b>", styles['BoldSmallFont']),
        Paragraph("<b>Girador</b>", styles['BoldSmallFont']),
        Paragraph("<b>Aceptante</b>", styles['BoldSmallFont']),
        Paragraph("<b>MONTO NETO SOLES (PEN) / DOLARES (USD)</b>", styles['BoldSmallFont']),
        Paragraph("<b>Detracción / Retención</b>", styles['BoldSmallFont']),
    ]

    # Table Data (Example - replace with actual data from 'data' dictionary)
    table1_data = [table1_headers]
    styles.add(ParagraphStyle(name='ExtraSmallFont', fontSize=7))
    for item in data.get('facturas_comision', []):
        table1_data.append([
            Paragraph(item.get('nro_factura', ''), styles['ExtraSmallFont']),
            Paragraph(item.get('fecha_vencimiento', ''), styles['ExtraSmallFont']),
            Paragraph(item.get('fecha_desembolso', ''), styles['ExtraSmallFont']),
            Paragraph(str(item.get('dias', '')), styles['ExtraSmallFont']),
            Paragraph(item.get('girador', ''), styles['ExtraSmallFont']),
            Paragraph(item.get('aceptante', ''), styles['ExtraSmallFont']),
            Paragraph(f"PEN {item.get('monto_neto', '')}", styles['ExtraSmallFont']),
            Paragraph(f"{item.get('detraccion_retencion', '')}%", styles['ExtraSmallFont']),
        ])
    table1_data.append([
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("<b>Total</b>", styles['BoldSmallFont']),
        Paragraph(f"PEN {data.get('total_monto_neto', '72,768.41')}", styles['BoldSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
    ])
    table1_data.append([
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("<b>(-) Detracciones</b>", styles['BoldSmallFont']),
        Paragraph(f"PEN {data.get('detracciones_total', '2,911.00')}", styles['BoldSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
    ])
    table1_data.append([
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("<b>Total Neto</b>", styles['BoldSmallFont']),
        Paragraph(f"PEN {data.get('total_neto', '69,857.41')}", styles['BoldSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
    ])

    table1 = Table(table1_data, colWidths=[1.26*inch, 0.85*inch, 0.85*inch, 0.5*inch, 1.16*inch, 1.16*inch, 1.1*inch, 0.7*inch])
    table1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (7, 0), colors.lightgrey), # Header background for all columns
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, 0), 0.5, colors.black), # Grid for header
        ('GRID', (0, 1), (-1, -4), 0.5, colors.black), # Grid for data rows
        ('GRID', (5, -3), (6, -1), 0.5, colors.black), # Grid for content cells in summary rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white), # Body background
        ('BACKGROUND', (6, -3), (6, -3), colors.lightgrey), # Shade Total PEN cell
        ('BACKGROUND', (6, -1), (6, -1), colors.lightgrey), # Shade Total Neto PEN cell
        ('BACKGROUND', (5, -3), (5, -3), colors.lightgrey), # Shade Total cell
        ('BACKGROUND', (5, -1), (5, -1), colors.lightgrey), # Shade Total Neto cell
    ]))
    story.append(table1)
    story.append(Spacer(1, 0.1 * inch))

    # --- BASE DESCUENTO INTERES COBRADO Table ---
    # Re-doing table2 as an 8-column, 6-row table (0-indexed: columns 0-7, rows 0-5)
    table2_data = [
        # Row 0: Headers
        [
            Paragraph("<b>Nro. Facturas</b>", styles['BoldSmallFont']),
            Paragraph("<b>BASE DESCUENTO</b>", styles['BoldSmallFont']),
            Paragraph("<b>INTERES COBRADO</b>", styles['BoldSmallFont']),
            Paragraph("<b>IGV</b>", styles['BoldSmallFont']),
            Paragraph("<b>ABONO</b>", styles['BoldSmallFont']),
            Paragraph("", styles['BoldSmallFont']), # Placeholder for column 5 header
            Paragraph("", styles['BoldSmallFont']), # Placeholder for column 6 header
            Paragraph("", styles['BoldSmallFont']), # Placeholder for column 7 header
        ],
        # Row 1: Data row 1
        [
            Paragraph(data.get('facturas_descuento', [{},{}])[0].get('nro_factura', ''), styles['SmallFont']),
            Paragraph(f"PEN {data.get('facturas_descuento', [{},{}])[0].get('base_descuento', '')}", styles['SmallFont']),
            Paragraph(f"PEN {data.get('facturas_descuento', [{},{}])[0].get('interes_cobrado', '')}", styles['SmallFont']),
            Paragraph(f"PEN {data.get('facturas_descuento', [{},{}])[0].get('igv', '')}", styles['SmallFont']),
            Paragraph(f"PEN {data.get('facturas_descuento', [{},{}])[0].get('abono', '')}", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
        ],
        # Row 2: Data row 2
        [
            Paragraph(data.get('facturas_descuento', [{},{}])[1].get('nro_factura', ''), styles['SmallFont']),
            Paragraph(f"PEN {data.get('facturas_descuento', [{},{}])[1].get('base_descuento', '')}", styles['SmallFont']),
            Paragraph(f"PEN {data.get('facturas_descuento', [{},{}])[1].get('interes_cobrado', '')}", styles['SmallFont']),
            Paragraph(f"PEN {data.get('facturas_descuento', [{},{}])[1].get('igv', '')}", styles['SmallFont']),
            Paragraph(f"PEN {data.get('facturas_descuento', [{},{}])[1].get('abono', '')}", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
        ],
        # Row 3: Total row
        [
            Paragraph("", styles['SmallFont']),
            Paragraph(f"PEN {data.get('total_base_descuento', '')}", styles['BoldSmallFont']),
            Paragraph(f"PEN {data.get('total_interes_cobrado', '')}", styles['BoldSmallFont']),
            Paragraph(f"PEN {data.get('total_igv_descuento', '')}", styles['BoldSmallFont']),
            Paragraph(f"PEN {data.get('total_abono', '')}", styles['BoldSmallFont']),
            Paragraph("", styles['SmallFont']), # Column 6 (index 5) - empty
            Paragraph("Margen de Seguridad", styles['BoldSmallFont']), # Column 7 (index 6) - now contains label
            Paragraph(f"PEN {data.get('margen_seguridad', '')}", styles['BoldSmallFontRight']), # Column 8 (index 7) - now contains value
        ],
        # Row 4: Comision + IGV row
        [
            Paragraph("", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
            Paragraph("<b>Comisión + IGV</b>", styles['BoldSmallFont']),
            Paragraph(f"PEN {data.get('comision_mas_igv', '807.72')}", styles['BoldSmallFontRight']),
            Paragraph("", styles['SmallFont']), # Column 6 (index 5) - empty
            Paragraph("", styles['SmallFont']), # Column 7 (index 6) - empty
            Paragraph("", styles['SmallFont']), # Column 8 (index 7) - empty
        ],
        # Row 5: Total a Depositar row
        [
            Paragraph("", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
            Paragraph("<b>Total a Depositar:</b>", styles['BoldSmallFont']),
            Paragraph(f"PEN {data.get('total_a_depositar', '65,770.00')}", styles['BoldSmallFontRight']),
            Paragraph("", styles['SmallFont']),
            Paragraph("Se devuelve al final de la operación, sirve para cubrir intereses adicionales por atrasos del PAGADOR / ADQUIRIENTE", styles['SmallTinyFont']),
            Paragraph("", styles['SmallFont']),
        ],
    ]

    # Define column widths for table2 (keeping existing widths for now)
    col1_width_t2 = 0.9 * inch
    col2_width_t2 = 0.9 * inch
    col3_width_t2 = 0.9 * inch
    col4_width_t2 = 0.9 * inch
    col5_width_t2 = 0.9 * inch
    col6_width_t2 = 1.16 * inch
    col7_width_t2 = 1.1 * inch
    col8_width_t2 = 0.7 * inch

    table2 = Table(table2_data, colWidths=[col1_width_t2, col2_width_t2, col3_width_t2, col4_width_t2, col5_width_t2, col6_width_t2, col7_width_t2, col8_width_t2], hAlign='LEFT')
    # Initial basic styling for the new table. User will provide specific styling later.
    table2.setStyle(TableStyle([
    # Set entire table background to white first to ensure no grey halos
    ('BACKGROUND', (0, 0), (-1, -1), colors.white),

    # Header styling (Row 0)
    ('BACKGROUND', (0, 0), (4, 0), colors.lightgrey), # Header background for first 5 columns
    ('BACKGROUND', (5, 0), (7, 0), colors.white), # Header background for last 3 columns
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'), # Header text alignment
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
    ('TOPPADDING', (0, 0), (-1, 0), 6),
    ('GRID', (0, 0), (4, 0), 0.5, colors.black), # Grid for header (first 5 columns)

    # Main data grid for columns 0-4 (Rows 1-5)
    ('GRID', (0, 1), (4, 2), 0.5, colors.black), # Rows 1 and 2, columns 0-4
    ('GRID', (1, 3), (4, 3), 0.5, colors.black), # Row 3, columns 1-4 (Total row)
    ('GRID', (3, 4), (4, 5), 0.5, colors.black), # Rows 4 and 5, columns 3-4 (Comision + IGV and Total a Depositar)

    # Specific cell backgrounds (red, blue, and green) for merged cells
    ('BACKGROUND', (6, 3), (6, 4), colors.lightgrey), # Column 7 (index 6), rows 4 and 5 (indices 3 and 4) red
    ('GRID', (6, 3), (6, 4), 0.5, colors.black),
    ('BACKGROUND', (7, 3), (7, 4), colors.white), # Column 8 (index 7), rows 4 and 5 (indices 3 and 4) blue
    ('GRID', (7, 3), (7, 4), 0.5, colors.black),
    ('BACKGROUND', (6, 5), (7, 5), colors.white), # Merged green cell
    # ('GRID', (6, 5), (7, 5), 0.5, colors.black), # Merged green cell border

    # Vertical merges for columns 6, 7 and 8 across rows 4 and 5
    ('SPAN', (5, 3), (5, 4)), # Merge column 6 (index 5) for rows 4 and 5 (indices 3 and 4)
    ('SPAN', (6, 3), (6, 4)), # Merge column 7 (index 6) for rows 4 and 5 (indices 3 and 4)
    ('SPAN', (7, 3), (7, 4)), # Merge column 8 (index 7) for rows 4 and 5 (indices 3 and 4)

    # Horizontal merge for the last row, columns 7 and 8
    ('SPAN', (6, 5), (7, 5)), # Merge column 7 (index 6) and column 8 (index 7) in row 6 (index 5)

    # Specific alignment for the last two rows (Comision + IGV and Total a Depositar)
    ('ALIGN', (3, 4), (4, 5), 'RIGHT'), # Labels and values in columns 4 and 5, rows 5 and 6
    ('FONTNAME', (3, 4), (4, 5), 'Helvetica-Bold'),
    ('BOTTOMPADDING', (3, 4), (4, 5), 3),
    ('TOPPADDING', (3, 4), (4, 5), 3),

    # Specific alignment and background for the total row (row 3)
    ('ALIGN', (1, 3), (4, 3), 'RIGHT'), # Numeric cells in total row
    ('FONTNAME', (1, 3), (4, 3), 'Helvetica-Bold'),
    ('BACKGROUND', (1, 3), (4, 3), colors.lightgrey), # Shade filled cells in the total row
]))

    
    story.append(table2)
    story.append(Spacer(1, 0.1 * inch))

    

    

    # --- Three columns of tables at the bottom ---
    # FACTURAR A MILENIO CONSULTORES SAC POR INTERESES PACTADOS
    intereses_pactados_data = [
        [Paragraph("<b>FACTURAR A MILENIO CONSULTORES SAC POR INTERESES PACTADOS</b>", styles['BoldExtraSmallFontCenter'])],
        [Paragraph("<b>INTERES</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('intereses_pactados_interes', '1,587.52')}", styles['BoldSmallFontRight'])],
        [Paragraph("<b>IGV</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('intereses_pactados_igv', '285.75')}", styles['BoldSmallFontRight'])],
        [Paragraph("<b>TOTAL</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('intereses_pactados_total', '1,873.27')}", styles['BoldSmallFontRight'])],
    ]
    intereses_pactados_table = Table(intereses_pactados_data, colWidths=[1*inch, 1*inch])
    intereses_pactados_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (1,0), colors.blue),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('SPAN', (0,0), (1,0)),
    ]))

    # FACTURAR A MILENIO CONSULTORES SAC POR COMISION DE ESTRUCTURACIÓN
    comision_estructuracion_data = [
        [Paragraph("<b>FACTURAR A MILENIO CONSULTORES SAC POR COMISION DE ESTRUCTURACIÓN</b>", styles['BoldExtraSmallFontCenter'])],
        [Paragraph("<b>COMISION</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('comision_estructuracion_comision', '684.51')}", styles['BoldSmallFontRight'])],
        [Paragraph("<b>IGV</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('comision_estructuracion_igv', '123.21')}", styles['BoldSmallFontRight'])],
        [Paragraph("<b>TOTAL</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('comision_estructuracion_total', '807.72')}", styles['BoldSmallFontRight'])],
    ]
    comision_estructuracion_table = Table(comision_estructuracion_data, colWidths=[1*inch, 1*inch])
    comision_estructuracion_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (1,0), colors.blue),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('SPAN', (0,0), (1,0)),
    ]))

    # FACTURAR A MILENIO CONSULTORES SAC POR INTERESES ADICIONALES
    intereses_adicionales_data = [
        [Paragraph("<b>FACTURAR A MILENIO CONSULTORES SAC POR INTERESES ADICIONALES</b>", styles['BoldExtraSmallFontCenter'])],
        [Paragraph("<b>INT ADICIONALES</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('intereses_adicionales_int', '')}", styles['BoldSmallFontRight'])],
        [Paragraph("<b>IGV</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('intereses_adicionales_igv', '')}", styles['BoldSmallFontRight'])],
        [Paragraph("<b>TOTAL</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('intereses_adicionales_total', '')}", styles['BoldSmallFontRight'])],
    ]
    intereses_adicionales_table = Table(intereses_adicionales_data, colWidths=[1.2*inch, 0.8*inch])
    intereses_adicionales_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (1,0), colors.blue),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('SPAN', (0,0), (1,0)),
    ]))

    # Combine these three tables into one main table for layout
    bottom_tables_data = [
        [intereses_pactados_table, Spacer(1, 0.675*inch), comision_estructuracion_table, Spacer(1, 0.675*inch), intereses_adicionales_table]
    ]
    bottom_tables = Table(bottom_tables_data, colWidths=[2*inch, 0.675*inch, 2*inch, 0.675*inch, 2*inch])
    bottom_tables.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    bottom_tables.hAlign = 'LEFT'
    story.append(bottom_tables)
    story.append(Spacer(1, 0.2 * inch))

        # --- Signatures Section ---
    signature_line = Paragraph("_____________________________", styles['CenterAlign'])
    signature_blocks = []
    for sig_info in data.get('signatures', []):
        sig_content = [
            signature_line,
            Spacer(1, 0.05*inch),
            Paragraph(f"<b>{sig_info.get('name', '')}</b>", styles['BoldNormalCenter']),
            Paragraph(f"DNI {sig_info.get('dni', '')}", styles['SmallFontCenter']),
            Paragraph(sig_info.get('role', ''), styles['SmallFontCenter'])
        ]
        signature_blocks.append(sig_content)

    # Arrange signatures in a 3x2 grid (3 columns, 2 rows)
    # The middle cell of the first row is empty.
    # Ensure we have at least 5 signature blocks for the layout, padding with empty strings if needed.
    padded_signature_blocks = signature_blocks + [""] * (5 - len(signature_blocks))

    signatures_data = [
        [padded_signature_blocks[0], "", padded_signature_blocks[1]],
        [padded_signature_blocks[2], padded_signature_blocks[3], padded_signature_blocks[4]]
    ]

    # Total width is ~7.5 inches (letter page width - 1 inch margins)
    # Divide by 3 columns -> ~2.5 inches per column
    col_width = (doc.width) / 3.0
    signatures_table = Table(signatures_data, colWidths=[col_width, col_width, col_width])
    signatures_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(signatures_table)

    doc.build(story)

    # --- Open PDF with Foxit Reader (User must provide path) ---
    foxit_reader_path = "C:\\Program Files (x86)\\Foxit Software\\Foxit Reader\\FoxitReader.exe"  # <<< REPLACE WITH YOUR ACTUAL FOXIT READER PATH
    if os.path.exists(foxit_reader_path):
        try:
            import subprocess
            subprocess.Popen([foxit_reader_path, output_file], shell=False)
            print(f"Attempting to open PDF with Foxit Reader: {output_file}")
        except Exception as e:
            print(f"Error opening PDF with Foxit Reader: {e}")
    else:
        print(f"Foxit Reader not found at {foxit_reader_path}. Please update the path in pdf_generator.py or open the PDF manually.")

if __name__ == '__main__':
    # Example usage with dummy data
    dummy_pdf_data = {
        "contract_name": "CONTRATO DE FACTORING",
        "client_name": "MILENIO CONSULTORES SAC",
        "client_ruc": "20422894854",
        "relation_type": "FACTURA(S)",
        "anexo_number": "31",
        "document_date": "JUEVES 01, AGO, 2025", # Updated date for dummy data

        "facturas_comision": [
            {
                "nro_factura": "E001-00000202",
                "fecha_vencimiento": "11 julio, 2025",
                "fecha_desembolso": "29 mayo, 2025",
                "dias": 43,
                "girador": "MILENIO CONSULTORES SAC",
                "aceptante": "PAZ REAL ESTATE",
                "monto_neto": "41,868.22",
                "detraccion_retencion": "4.0",
            },
            {
                "nro_factura": "E001-00000203",
                "fecha_vencimiento": "11 julio, 2025",
                "fecha_desembolso": "29 mayo, 2025",
                "dias": 43,
                "girador": "MILENIO CONSULTORES SAC",
                "aceptante": "PAZ REAL ESTATE",
                "monto_neto": "30,900.19",
                "detraccion_retencion": "4.0",
            },
            # Adding an extra dummy row to show dynamic behavior
            {
                "nro_factura": "E001-00000204",
                "fecha_vencimiento": "15 agosto, 2025",
                "fecha_desembolso": "01 agosto, 2025",
                "dias": 14,
                "girador": "OTRA EMPRESA S.A.C.",
                "aceptante": "CLIENTE FICTICIO S.A.",
                "monto_neto": "10,000.00",
                "detraccion_retencion": "2.0",
            },
        ],
        "total_monto_neto": "82,768.41", # Sum of 41868.22 + 30900.19 + 10000.00
        "detracciones_total": "3,310.74", # 4% of 41868.22 + 4% of 30900.19 + 2% of 10000.00
        "total_neto": "79,457.67", # 82768.41 - 3310.74

        "facturas_descuento": [
            {
                "nro_factura": "E001-00000202",
                "base_descuento": "39,384.02",
                "interes_cobrado": "913.40",
                "igv": "164.41",
                "abono": "38,306.22",
            },
            {
                "nro_factura": "E001-00000203",
                "base_descuento": "29,066.97",
                "interes_cobrado": "674.12",
                "igv": "121.34",
                "abono": "28,271.51",
            },
            # Adding an extra dummy row for table2
            {
                "nro_factura": "E001-00000204",
                "base_descuento": "9,500.00",
                "interes_cobrado": "200.00",
                "igv": "36.00",
                "abono": "9,264.00",
            },
        ],
        "total_base_descuento": "77,950.99", # Sum of 39384.02 + 29066.97 + 9500.00
        "total_interes_cobrado": "1,787.52", # Sum of 913.40 + 674.12 + 200.00
        "total_igv_descuento": "321.75", # Sum of 164.41 + 121.34 + 36.00
        "total_abono": "75,841.73", # Sum of 38306.22 + 28271.51 + 9264.00
        "margen_seguridad": "1,500.00", # Dummy value
        "comision_mas_igv": "900.00", # Dummy value
        "total_a_depositar": "74,441.73", # Dummy value

        "intereses_pactados_interes": "1,787.52",
        "intereses_pactados_igv": "321.75",
        "intereses_pactados_total": "2,109.27",

        "comision_estructuracion_comision": "750.00",
        "comision_estructuracion_igv": "135.00",
        "comision_estructuracion_total": "885.00",

        "intereses_adicionales_int": "50.00", # Dummy value
        "intereses_adicionales_igv": "9.00", # Dummy value
        "intereses_adicionales_total": "59.00", # Dummy value

        "signatures": [
            {"name": "Harry Odar Mazza", "dni": "42411175", "role": "MILENIO CONSULTORES SAC"},
            {"name": "Juan Ricardo Gallo Pizarro", "dni": "02816271", "role": "INANDES CAPITAL FACTOR SAC"},
            {"name": "Harry Odar Mazza", "dni": "42411175", "role": "GARANTE / FIADOR SOLIDARIO"},
            {"name": "Harry Odar Mazza", "dni": "42411175", "role": "DEPOSITARIO"},
            {"name": "Guillermo Francisco Odar Cabrejos", "dni": "07723067", "role": "GARANTE / FIADOR SOLIDARIO"},
            # Adding an extra dummy signature to show dynamic behavior
            {"name": "Nuevo Firmante", "dni": "12345678", "role": "ROL ADICIONAL"},
        ]
    }
    output_dir = "C:/Users/rguti/Inandes.TECH/generated_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "generated_invoice.pdf")
    generate_pdf(output_file, dummy_pdf_data)
    print(f"Generated PDF: {output_file}")
