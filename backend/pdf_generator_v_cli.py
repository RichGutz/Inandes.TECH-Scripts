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
    print("--- [DEBUG] Inside generate_pdf function ---")
    print(f"--- [DEBUG] Output filepath: {output_filepath} ---")
    # print(f"--- [DEBUG] Received data: {json.dumps(data, indent=2)} ---") # Pretty print JSON
    
    doc = SimpleDocTemplate(output_filepath, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.375*inch, bottomMargin=0.375*inch)
    styles = getSampleStyleSheet()
    story = []
    
    print("--- [DEBUG] Doc and story initialized ---")

    # Custom styles
    styles.add(ParagraphStyle(name='RightAlign', alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='CenterAlign', alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='LeftAlign', alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='SmallFont', fontSize=7))
    styles.add(ParagraphStyle(name='BoldSmallFont', fontSize=6, fontName='Helvetica-Bold'))
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
    styles.add(ParagraphStyle(name='SmallTinyFont', fontSize=5, leading=5))
    logo_path = "C:/Users/rguti/Inandes.TECH/inputs_para_generated_pdfs/LOGO.png"
    inandes_logo = None
    if os.path.exists(logo_path):
        inandes_logo = Image(logo_path, width=1.5*inch, height=0.5*inch)
    else:
        print(f"Warning: Logo not found at {logo_path}. Using placeholder text.")
        inandes_logo = Paragraph("INANDES Logo Placeholder", styles['RightAlign'])

    # Left column content (Main Title + Client Info)
    left_column_content = []
    document_type = data.get('tipo_documento', '')
    main_title = "FONDO NSG MIPYME - INANDES FACTOR CAPITAL S.A.C."
    if document_type:
        main_title = f"{document_type.upper()} - {main_title}"
    left_column_content.append(Paragraph(f"<b>{main_title}</b>", styles['LeftAlign']))
    left_column_content.append(Spacer(1, 0.1 * inch))

    # Ensure values are strings before passing to Paragraph
    contract_name_str = str(data.get('contract_name', 'N/A'))
    emisor_nombre_str = str(data.get('emisor_nombre', 'N/A'))
    emisor_ruc_str = str(data.get('emisor_ruc', 'N/A'))
    relation_type_str = str(data.get('relation_type', 'N/A'))

    client_info_data = [
        [Paragraph("<b>CONTRATO</b>", styles['SmallFont']), Paragraph(contract_name_str, styles['BlueSmallFont'])],
        [Paragraph("<b>CLIENTE</b>", styles['SmallFont']), Paragraph(emisor_nombre_str, styles['BlueSmallFont'])],
        [Paragraph("<b>RUC</b>", styles['SmallFont']), Paragraph(emisor_ruc_str, styles['BlueSmallFont'])],
        [Paragraph("<b>RELACION DE</b>", styles['SmallFont']), Paragraph(relation_type_str, styles['BlueSmallFont'])],
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

    print("--- [DEBUG] Header and Anexo table added to story ---")

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
    for item in data.get('facturas', []):
        table1_data.append([
            Paragraph(item.get('invoice_series_and_number', ''), styles['ExtraSmallFont']),
            Paragraph(item.get('invoice_due_date', ''), styles['ExtraSmallFont']),
            Paragraph(item.get('invoice_issue_date', ''), styles['ExtraSmallFont']),
            Paragraph(str(item.get('financing_term_days', '')), styles['ExtraSmallFont']),
            Paragraph(item.get('invoice_issuer_name', ''), styles['ExtraSmallFont']),
            Paragraph(item.get('invoice_payer_name', ''), styles['ExtraSmallFont']),
            Paragraph(f"PEN {item.get('invoice_total_amount', 0.0):,.2f}", styles['ExtraSmallFont']),
            Paragraph(f"{item.get('detraccion_porcentaje', 0):.2f}%", styles['ExtraSmallFont']),
        ])
    table1_data.append([
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("<b>Total</b>", styles['BoldSmallFont']),
        Paragraph(f"PEN {data.get('total_monto_neto', 0.0):,.2f}", styles['BoldSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
    ])
    table1_data.append([
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("<b>(-) Detracciones</b>", styles['BoldSmallFont']),
        Paragraph(f"PEN {data.get('detracciones_total', 0.0):,.2f}", styles['BoldSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
    ])
    table1_data.append([
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
        Paragraph("<b>Total Neto</b>", styles['BoldSmallFont']),
        Paragraph(f"PEN {data.get('total_neto', 0.0):,.2f}", styles['BoldSmallFont']),
        Paragraph("", styles['ExtraSmallFont']),
    ])

    table1 = Table(table1_data, colWidths=[0.928*inch, 0.85*inch, 0.85*inch, 0.5*inch, 1.276*inch, 1.276*inch, 1.1*inch, 0.6*inch])
    table1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (7, 0), colors.lightgrey), # Header background for all columns
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('ALIGN', (1, 1), (4, 2), 'RIGHT'), # PEN values in rows 1 and 2
    ('ALIGN', (1, 3), (4, 3), 'RIGHT'), # PEN values in row 3
    ('ALIGN', (4, 4), (4, 5), 'RIGHT'), # PEN values in rows 4 and 5
    ('ALIGN', (7, 3), (7, 3), 'RIGHT'), # PEN value in row 3, col 7
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
        ('TOPPADDING', (0, 0), (-1, 0), 3),
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

    print("--- [DEBUG] First table (Facturas) added to story ---")

    # --- BASE DESCUENTO INTERES COBRADO Table ---
    table2_headers = [
        Paragraph("<b>Nro. Facturas</b>", styles['BoldSmallFont']),
        Paragraph("<b>BASE DESCUENTO</b>", styles['BoldSmallFont']),
        Paragraph("<b>INTERES COBRADO</b>", styles['BoldSmallFont']),
        Paragraph("<b>IGV</b>", styles['BoldSmallFont']),
        Paragraph("<b>ABONO</b>", styles['BoldSmallFont']),
        Paragraph("", styles['BoldSmallFont']),
        Paragraph("", styles['BoldSmallFont']),
        Paragraph("", styles['BoldSmallFont']),
    ]
    table2_data = [table2_headers]

    # Iterate over the correct data key 'facturas'
    for item in data.get('facturas', []):
        row = [
            Paragraph(item.get('invoice_series_and_number', ''), styles['SmallFont']),
            Paragraph(f"PEN {item.get('advance_amount', 0.0):,.2f}", styles['SmallFont']),
            Paragraph(f"PEN {item.get('commission_amount', 0.0):,.2f}", styles['SmallFont']),
            Paragraph(f"PEN {item.get('igv_interes_calculado', 0.0):,.2f}", styles['SmallFont']),
            Paragraph(f"PEN {item.get('initial_disbursement', 0.0):,.2f}", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
            Paragraph("", styles['SmallFont']),
        ]
        table2_data.append(row)

    # Add summary rows
    total_row = [
        Paragraph("", styles['SmallFont']),
        Paragraph(f"PEN {data.get('total_capital_calculado', 0.0):,.2f}", styles['BoldSmallFont']),
        Paragraph(f"PEN {data.get('total_interes_calculado', 0.0):,.2f}", styles['BoldSmallFont']),
        Paragraph(f"PEN {data.get('total_igv_interes_calculado', 0.0):,.2f}", styles['BoldSmallFont']),
        Paragraph(f"PEN {data.get('total_abono_real_calculado', 0.0):,.2f}", styles['BoldSmallFont']),
        Paragraph("", styles['SmallFont']),
        Paragraph("Margen de Seguridad", styles['BoldSmallFont']),
        Paragraph(f"PEN {data.get('total_margen_seguridad_calculado', 0.0):,.2f}", styles['BoldSmallFontRight']),
    ]
    table2_data.append(total_row)

    comision_row = [
        Paragraph("", styles['SmallFont']),
        Paragraph("", styles['SmallFont']),
        Paragraph("", styles['SmallFont']),
        Paragraph("<b>Comisión + IGV</b>", styles['BoldSmallFont']),
        Paragraph(f"PEN {data.get('total_comision_estructuracion_monto_calculado', 0.0):,.2f}", styles['BoldSmallFontRight']),
        Paragraph("", styles['SmallFont']),
        Paragraph("", styles['SmallFont']),
        Paragraph("", styles['SmallFont']),
    ]
    table2_data.append(comision_row)

    depositar_row = [
        Paragraph("", styles['SmallFont']),
        Paragraph("", styles['SmallFont']),
        Paragraph("", styles['SmallFont']),
        Paragraph("<b>Total a Depositar:</b>", styles['BoldSmallFont']),
        Paragraph(f"PEN {data.get('total_a_depositar', 0.0):,.2f}", styles['BoldSmallFontRight']),
        Paragraph("", styles['SmallFont']),
        Paragraph("Se devuelve al final de la operación, sirve para cubrir intereses adicionales por atrasos del PAGADOR / ADQUIRIENTE", styles['SmallTinyFont']),
        Paragraph("", styles['SmallFont']),
    ]
    table2_data.append(depositar_row)

    # Define column widths
    col_widths_t2 = [0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch, 1.16*inch, 1.0*inch, 0.7*inch]
    table2 = Table(table2_data, colWidths=col_widths_t2, hAlign='LEFT')

    # --- Dynamic Styling ---
    num_data_rows = len(data.get('facturas', []))
    last_data_row_idx = num_data_rows
    total_row_idx = last_data_row_idx + 1
    comision_row_idx = last_data_row_idx + 2
    depositar_row_idx = last_data_row_idx + 3
    
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 0), (4, 0), colors.lightgrey),
        ('BACKGROUND', (5, 0), (7, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (4, 0), 0.5, colors.black),
        
        # Grid for data rows
        ('GRID', (0, 1), (4, last_data_row_idx), 0.5, colors.black),
        
        # Grid for summary rows
        ('GRID', (1, total_row_idx), (4, total_row_idx), 0.5, colors.black),
        ('GRID', (3, comision_row_idx), (4, depositar_row_idx), 0.5, colors.black),
        
        # Backgrounds for summary rows
        ('BACKGROUND', (1, total_row_idx), (4, total_row_idx), colors.lightgrey),
        ('BACKGROUND', (3, depositar_row_idx), (4, depositar_row_idx), colors.lightgrey),
        ('BACKGROUND', (6, total_row_idx), (6, comision_row_idx), colors.lightgrey),
        ('GRID', (6, total_row_idx), (6, comision_row_idx), 0.5, colors.black),
        ('BACKGROUND', (7, total_row_idx), (7, comision_row_idx), colors.white),
        ('GRID', (7, total_row_idx), (7, comision_row_idx), 0.5, colors.black),
        ('BACKGROUND', (6, depositar_row_idx), (7, depositar_row_idx), colors.white),
        
        # SPAN commands
        ('SPAN', (5, total_row_idx), (5, comision_row_idx)),
        ('SPAN', (6, total_row_idx), (6, comision_row_idx)),
        ('SPAN', (7, total_row_idx), (7, comision_row_idx)),
        ('SPAN', (6, depositar_row_idx), (7, depositar_row_idx)),
        
        # Font for summary rows
        ('FONTNAME', (1, total_row_idx), (4, total_row_idx), 'Helvetica-Bold'),
        ('FONTNAME', (3, comision_row_idx), (4, depositar_row_idx), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (3, comision_row_idx), (4, depositar_row_idx), 3),
        ('TOPPADDING', (3, comision_row_idx), (4, depositar_row_idx), 3),
        
        # Padding for last row
        ('TOPPADDING', (0, depositar_row_idx), (-1, depositar_row_idx), 0),
        ('BOTTOMPADDING', (0, depositar_row_idx), (-1, depositar_row_idx), 0),
    ]
    
    table2.setStyle(TableStyle(style_commands))

    
    story.append(table2)
    story.append(Spacer(1, 0.1 * inch))

    print("--- [DEBUG] Second table (Descuento) added to story ---")

    

    

    # --- Conditional Bottom Tables ---
    if data.get('imprimir_comision_afiliacion', False):
        # --- Four columns of tables at the bottom ---
        # FACTURAR A MILENIO CONSULTORES SAC POR INTERESES PACTADOS
        intereses_pactados_data = [
            [Paragraph("<b>FACTURAR A MILENIO CONSULTORES SAC POR INTERESES PACTADOS</b>", styles['BoldExtraSmallFontCenter'])],
            [Paragraph("<b>INTERES</b>", styles['BoldSmallFont']), Paragraph(f"PEN {sum(inv.get('interes_calculado', 0) for inv in data.get('facturas', [])):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>IGV</b>", styles['BoldSmallFont']), Paragraph(f"PEN {sum(inv.get('igv_interes_calculado', 0) for inv in data.get('facturas', [])):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>TOTAL</b>", styles['BoldSmallFont']), Paragraph(f"PEN {sum(inv.get('interes_calculado', 0) for inv in data.get('facturas', [])) + sum(inv.get('igv_interes_calculado', 0) for inv in data.get('facturas', [])):,.2f}", styles['BoldSmallFontRight'])],
        ]
        intereses_pactados_table = Table(intereses_pactados_data, colWidths=[0.80625*inch, 0.80625*inch])
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
            [Paragraph("<b>COMISION</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_comision_estructuracion_monto_calculado', 0.0):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>IGV</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_igv_comision_estructuracion_calculado', 0.0):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>TOTAL</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_comision_estructuracion', 0.0):,.2f}", styles['BoldSmallFontRight'])],
        ]
        comision_estructuracion_table = Table(comision_estructuracion_data, colWidths=[0.80625*inch, 0.80625*inch])
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

        # FACTURAR A MILENIO CONSULTORES SAC POR COMISION DE AFILIACION
        comision_afiliacion_data = [
            [Paragraph("<b>FACTURAR A MILENIO CONSULTORES SAC POR COMISION DE AFILIACION</b>", styles['BoldExtraSmallFontCenter'])],
            [Paragraph("<b>COMISION</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_comision_afiliacion_monto_calculado', 0.0):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>IGV</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_igv_afiliacion_calculado', 0.0):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>TOTAL</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_comision_afiliacion', 0.0):,.2f}", styles['BoldSmallFontRight'])],
        ]
        comision_afiliacion_table = Table(comision_afiliacion_data, colWidths=[0.80625*inch, 0.80625*inch])
        comision_afiliacion_table.setStyle(TableStyle([
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
            [Paragraph("<b>INT ADICIONALES</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_intereses_adicionales_int', 0.0):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>IGV</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_intereses_adicionales_igv', 0.0):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>TOTAL</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_intereses_adicionales', 0.0):,.2f}", styles['BoldSmallFontRight'])],
        ]
        intereses_adicionales_table = Table(intereses_adicionales_data, colWidths=[0.9675*inch, 0.645*inch])
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

        # Combine these four tables into one main table for layout
        bottom_tables_data = [
            [intereses_pactados_table, Spacer(1, 0.3*inch), comision_estructuracion_table, Spacer(1, 0.3*inch), comision_afiliacion_table, Spacer(1, 0.3*inch), intereses_adicionales_table]
        ]
        bottom_tables = Table(bottom_tables_data, colWidths=[1.6125*inch, 0.3*inch, 1.6125*inch, 0.3*inch, 1.6125*inch, 0.3*inch, 1.6125*inch])
        bottom_tables.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        bottom_tables.hAlign = 'LEFT'
        story.append(bottom_tables)
        print("--- [DEBUG] Conditional bottom tables (4 columns) added to story ---")
    else:
        # --- Three columns of tables at the bottom ---
        # FACTURAR A MILENIO CONSULTORES SAC POR INTERESES PACTADOS
        intereses_pactados_data = [
            [Paragraph("<b>FACTURAR A MILENIO CONSULTORES SAC POR INTERESES PACTADOS</b>", styles['BoldExtraSmallFontCenter'])],
            [Paragraph("<b>INTERES</b>", styles['BoldSmallFont']), Paragraph(f"PEN {sum(inv.get('interes_calculado', 0) for inv in data.get('facturas', [])):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>IGV</b>", styles['BoldSmallFont']), Paragraph(f"PEN {sum(inv.get('igv_interes_calculado', 0) for inv in data.get('facturas', [])):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>TOTAL</b>", styles['BoldSmallFont']), Paragraph(f"PEN {sum(inv.get('interes_calculado', 0) for inv in data.get('facturas', [])) + sum(inv.get('igv_interes_calculado', 0) for inv in data.get('facturas', [])):,.2f}", styles['BoldSmallFontRight'])],
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
            [Paragraph("<b>COMISION</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_comision_estructuracion_monto_calculado', 0.0):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>IGV</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_igv_comision_estructuracion_calculado', 0.0):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>TOTAL</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_comision_estructuracion', 0.0):,.2f}", styles['BoldSmallFontRight'])],
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
            [Paragraph("<b>INT ADICIONALES</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_intereses_adicionales_int', 0.0):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>IGV</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_intereses_adicionales_igv', 0.0):,.2f}", styles['BoldSmallFontRight'])],
            [Paragraph("<b>TOTAL</b>", styles['BoldSmallFont']), Paragraph(f"PEN {data.get('total_intereses_adicionales', 0.0):,.2f}", styles['BoldSmallFontRight'])],
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
        print("--- [DEBUG] Conditional bottom tables (3 columns) added to story ---")
    story.append(Spacer(1, 0.1 * inch)) # Nueva fila adicional
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

    print("--- [DEBUG] All tables added to story. About to build the document. ---")
    doc.build(story)
    print("--- [DEBUG] doc.build(story) completed. ---")

    

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate a PDF from factoring details.")
    parser.add_argument("--output_filepath", required=True, help="The full path to save the output PDF.")
    parser.add_argument("--json_filepath", required=True, help="The full path to the JSON file containing the invoice data.")
    
    args = parser.parse_args()

    # Leer los datos desde el archivo JSON
    with open(args.json_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("--- [DEBUG] DATOS RECIBIDOS POR PDF_GENERATOR ---")
    print(json.dumps(data, indent=4, ensure_ascii=False))
    print("-------------------------------------------------")

    output_dir = os.path.dirname(args.output_filepath)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # Log the received data for debugging
    log_file_path = os.path.join(output_dir, 'pdf_generator_log.json')
    with open(log_file_path, 'w', encoding='utf-8') as log_f:
        json.dump(data, log_f, ensure_ascii=False, indent=4)
    print(f"Data for PDF generation logged to {log_file_path}")

    try:
        print("Starting PDF generation...")
        generate_pdf(args.output_filepath, data)
        print(f"PDF generated successfully at: {args.output_filepath}")
    except Exception as e:
        print(f"Error generating PDF: {e}")
    finally:
        print("pdf_generator_v_cli.py script finished.")

