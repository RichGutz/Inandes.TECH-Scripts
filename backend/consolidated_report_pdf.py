from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas # Necesario para el footer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import json
import datetime
import os

# Custom styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='RightAlign', alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='CenterAlign', alignment=TA_CENTER))
styles.add(ParagraphStyle(name='LeftAlign', alignment=TA_LEFT))
styles.add(ParagraphStyle(name='SmallFont', fontSize=7))
styles.add(ParagraphStyle(name='BoldSmallFont', fontSize=6, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle(name='BoldNormal', fontName='Helvetica-Bold'))
styles.add(ParagraphStyle(name='BoldNormalRight', parent=styles['BoldNormal'], alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='BoldSmallFontRight', parent=styles['BoldSmallFont'], alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='BoldSmallFontCenter', parent=styles['BoldSmallFont'], alignment=TA_CENTER))
styles.add(ParagraphStyle(name='BoldExtraSmallFontCenter', parent=styles['BoldSmallFont'], alignment=TA_CENTER, fontSize=6, textColor=colors.blue))
styles.add(ParagraphStyle(name='BoldNormalCenter', parent=styles['BoldNormal'], alignment=TA_CENTER))
styles.add(ParagraphStyle(name='SmallFontCenter', parent=styles['SmallFont'], alignment=TA_CENTER))
styles.add(ParagraphStyle(name='BlueSmallFont', fontSize=7, fontName='Helvetica', textColor=colors.blue))
styles.add(ParagraphStyle(name='TinyFont', fontSize=5))
styles.add(ParagraphStyle(name='SmallTinyFont', fontSize=5, leading=5))
styles.add(ParagraphStyle(name='BoldExtraExtraSmallFontCenter', parent=styles['BoldSmallFont'], alignment=TA_CENTER, fontSize=5, textColor=colors.blue))

def generate_consolidated_report_pdf(output_filepath, all_invoices_data, print_date_str):
    doc = SimpleDocTemplate(output_filepath, pagesize=landscape(letter),
                            leftMargin=0.5*inch, rightMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []

    # Footer callback function
    def footer_callback(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.drawString(inch, 0.75 * inch, f"Fecha de Impresión: {print_date_str}")
        canvas_obj.restoreState()

    # --- Render Individual Invoice Profiles ---
    for idx, invoice_data in enumerate(all_invoices_data):
        if idx > 0:
            story.append(PageBreak()) # Start new page for each subsequent invoice

        story.append(Paragraph(f"Perfil de la Operación - Factura {invoice_data.get('numero_factura', 'N/A')}", styles['h2']))
        story.append(Spacer(1, 0.2 * inch))

        # Invoice Summary (copied from perfil_pdf.py)
        story.append(Paragraph(
            f"<b>Emisor:</b> {invoice_data.get('emisor_nombre', 'N/A')} | "
            f"<b>Aceptante:</b> {invoice_data.get('aceptante_nombre', 'N/A')} | "
            f"<b>Factura:</b> {invoice_data.get('numero_factura', 'N/A')} | "
            f"<b>F. Emisión:</b> {invoice_data.get('fecha_emision_factura', 'N/A')} | "
            f"<b>F. Pago:</b> {invoice_data.get('fecha_pago_calculada', 'N/A')} | "
            f"<b>Monto Total:</b> {invoice_data.get('moneda_factura', '')} {invoice_data.get('monto_total_factura', 0):,.2f} | "
            f"<b>Monto Neto:</b> {invoice_data.get('moneda_factura', '')} {invoice_data.get('monto_neto_factura', 0):,.2f}",
            styles['Normal']
        ))
        story.append(Spacer(1, 0.2 * inch))

        # Perfil de la Operación Table (copied and adapted from perfil_pdf.py)
        recalc_result = invoice_data['recalculate_result']
        desglose = recalc_result.get('desglose_final_detallado', {})
        calculos = recalc_result.get('calculo_con_tasa_encontrada', {})
        busqueda = recalc_result.get('resultado_busqueda', {})
        moneda = invoice_data.get('moneda_factura', 'PEN')

        tasa_avance_pct = busqueda.get('tasa_avance_encontrada', 0) * 100
        monto_neto = invoice_data.get('monto_neto_factura', 0)
        capital = calculos.get('capital', 0)
        
        abono = desglose.get('abono', {})
        interes = desglose.get('interes', {})
        com_est = desglose.get('comision_estructuracion', {})
        com_afi = desglose.get('comision_afiliacion', {})
        igv = desglose.get('igv_total', {})
        margen = desglose.get('margen_seguridad', {})

        costos_totales = interes.get('monto', 0) + com_est.get('monto', 0) + com_afi.get('monto', 0) + igv.get('monto', 0)
        tasa_diaria_pct = (invoice_data.get('interes_mensual', 0) / 30) 

        table_data = []
        table_data.append([Paragraph("<b>Item</b>", styles['BoldSmallFont']), Paragraph(f"<b>Monto ({moneda})</b>", styles['BoldSmallFont']), Paragraph("<b>% sobre Neto</b>", styles['BoldSmallFont']), Paragraph("<b>Fórmula de Cálculo</b>", styles['BoldSmallFont']), Paragraph("<b>Detalle del Cálculo</b>", styles['BoldSmallFont'])])

        table_data.append([Paragraph("Monto Neto de Factura", styles['SmallFont']), Paragraph(f"{monto_neto:,.2f}", styles['SmallFont']), Paragraph("100.00%", styles['SmallFont']), Paragraph("`Dato de entrada`", styles['SmallFont']), Paragraph("Monto total de la factura menos detraccion/retencion", styles['SmallFont'])])
        table_data.append([Paragraph("Margen de Seguridad", styles['SmallFont']), Paragraph(f"{margen.get('monto', 0):,.2f}", styles['SmallFont']), Paragraph(f"{margen.get('porcentaje', 0):.2f}%", styles['SmallFont']), Paragraph("`Monto Neto - Capital`", styles['SmallFont']), Paragraph(f"{monto_neto:,.2f} - {capital:,.2f} = {margen.get('monto', 0):,.2f}", styles['SmallFont'])])
        table_data.append([Paragraph("Tasa de Avance Aplicada", styles['SmallFont']), Paragraph("N/A", styles['SmallFont']), Paragraph(f"{tasa_avance_pct:.2f}%", styles['SmallFont']), Paragraph("`Tasa final de la operación`", styles['SmallFont']), Paragraph("N/A", styles['SmallFont'])])
        table_data.append([Paragraph("Capital", styles['SmallFont']), Paragraph(f"{capital:,.2f}", styles['SmallFont']), Paragraph(f"{((capital / monto_neto) * 100) if monto_neto else 0:.2f}%", styles['SmallFont']), Paragraph("`Monto Neto * (Tasa de Avance / 100)`", styles['SmallFont']), Paragraph(f"{monto_neto:,.2f} * ({tasa_avance_pct:.2f} / 100) = {capital:,.2f}", styles['SmallFont'])])
        table_data.append([Paragraph("Intereses", styles['SmallFont']), Paragraph(f"{interes.get('monto', 0):,.2f}", styles['SmallFont']), Paragraph(f"{interes.get('porcentaje', 0):.2f}%", styles['SmallFont']), Paragraph("`Capital * ((1 + Tasa Diaria)^Plazo - 1)`", styles['SmallFont']), Paragraph(f"Tasa Diaria: {invoice_data.get('interes_mensual', 0):.2f}% / 30 = {tasa_diaria_pct:.4f}%, Plazo: {calculos.get('plazo_operacion', 0)} días. Cálculo: {capital:,.2f} * ((1 + {tasa_diaria_pct/100:.6f})^{calculos.get('plazo_operacion', 0)} - 1) = {interes.get('monto', 0):,.2f}", styles['SmallFont'])])

        igv_interes_monto = calculos.get('igv_interes', 0)
        igv_interes_pct = (igv_interes_monto / monto_neto * 100) if monto_neto else 0
        table_data.append([Paragraph("IGV sobre Intereses", styles['SmallFont']), Paragraph(f"{igv_interes_monto:,.2f}", styles['SmallFont']), Paragraph(f"{igv_interes_pct:.2f}%", styles['SmallFont']), Paragraph("`Intereses * 18%`", styles['SmallFont']), Paragraph(f"{interes.get('monto', 0):,.2f} * 18% = {igv_interes_monto:,.2f}", styles['SmallFont'])])

        table_data.append([Paragraph("Comisión de Estructuración", styles['SmallFont']), Paragraph(f"{com_est.get('monto', 0):,.2f}", styles['SmallFont']), Paragraph(f"{com_est.get('porcentaje', 0):.2f}%", styles['SmallFont']), Paragraph("`MAX(Capital * %Comisión, Mínima)`", styles['SmallFont']), Paragraph(f"Base: {capital:,.2f} * {invoice_data.get('comision_de_estructuracion',0):.2f}% = {capital * (invoice_data.get('comision_de_estructuracion',0)/100):,.2f}, Mín: {invoice_data.get('comision_minima_pen',0) if moneda == 'PEN' else invoice_data.get('comision_minima_usd',0):,.2f}. Resultado: {com_est.get('monto', 0):,.2f}", styles['SmallFont'])])

        igv_com_est_monto = calculos.get('igv_comision_estructuracion', 0)
        igv_com_est_pct = (igv_com_est_monto / monto_neto * 100) if monto_neto else 0
        table_data.append([Paragraph("IGV sobre Com. de Estruct.", styles['SmallFont']), Paragraph(f"{igv_com_est_monto:,.2f}", styles['SmallFont']), Paragraph(f"{igv_com_est_pct:.2f}%", styles['SmallFont']), Paragraph("`Comisión * 18%`", styles['SmallFont']), Paragraph(f"{com_est.get('monto', 0):,.2f} * 18% = {igv_com_est_monto:,.2f}", styles['SmallFont'])])

        if com_afi.get('monto', 0) > 0:
            table_data.append([Paragraph("Comisión de Afiliación", styles['SmallFont']), Paragraph(f"{com_afi.get('monto', 0):,.2f}", styles['SmallFont']), Paragraph(f"{com_afi.get('porcentaje', 0):.2f}%", styles['SmallFont']), Paragraph("`Valor Fijo (si aplica)`", styles['SmallFont']), Paragraph(f"Monto fijo para la moneda {moneda}.", styles['SmallFont'])])
            igv_com_afi_monto = calculos.get('igv_afiliacion', 0)
            igv_com_afi_pct = (igv_com_afi_monto / monto_neto * 100) if monto_neto else 0
            table_data.append([Paragraph("IGV sobre Com. de Afiliación", styles['SmallFont']), Paragraph(f"{igv_com_afi_monto:,.2f}", styles['SmallFont']), Paragraph(f"{igv_com_afi_pct:.2f}%", styles['SmallFont']), Paragraph("`Comisión * 18%`", styles['SmallFont']), Paragraph(f"{com_afi.get('monto', 0):,.2f} * 18% = {igv_com_afi_monto:,.2f}", styles['SmallFont'])])

        table_data.append([Paragraph("", styles['SmallFont']), Paragraph("", styles['SmallFont']), Paragraph("", styles['SmallFont']), Paragraph("", styles['SmallFont']), Paragraph("", styles['SmallFont'])])
        table_data.append([Paragraph("<b>Monto a Desembolsar</b>", styles['BoldSmallFont']), Paragraph(f"<b>{abono.get('monto', 0):,.2f}</b>", styles['BoldSmallFont']), Paragraph(f"<b>{abono.get('porcentaje', 0):.2f}%</b>", styles['BoldSmallFont']), Paragraph("`Capital - Costos Totales`", styles['BoldSmallFont']), Paragraph(f"{capital:,.2f} - {costos_totales:,.2f} = {abono.get('monto', 0):,.2f}", styles['BoldSmallFont'])])
        table_data.append([Paragraph("", styles['SmallFont']), Paragraph("", styles['SmallFont']), Paragraph("", styles['SmallFont']), Paragraph("", styles['SmallFont']), Paragraph("", styles['SmallFont'])])
        table_data.append([Paragraph("<b>Total (Monto Neto Factura)</b>", styles['BoldSmallFont']), Paragraph(f"<b>{monto_neto:,.2f}</b>", styles['BoldSmallFont']), Paragraph("<b>100.00%</b>", styles['BoldSmallFont']), Paragraph("`Abono + Costos + Margen`", styles['BoldSmallFont']), Paragraph(f"{abono.get('monto', 0):,.2f} + {costos_totales:,.2f} + {margen.get('monto', 0):,.2f} = {monto_neto:,.2f}", styles['BoldSmallFont'])])

        table = Table(table_data, colWidths=[1.5*inch, 1*inch, 0.7*inch, 1.5*inch, 2.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('BACKGROUND', (0, -4), (-1, -4), colors.lightgrey),
        ]))
        story.append(table)

    # --- Consolidated Summary Table ---
    story.append(PageBreak()) # Start new page for the summary
    story.append(Paragraph("Resumen Consolidado de Operaciones", styles['h2']))
    story.append(Spacer(1, 0.2 * inch))

    summary_table_data = []
    # Build dynamic header for summary table
    header_row_1 = [Paragraph("<b>Item</b>", styles['BoldSmallFont'])]
    header_row_2 = [Paragraph("", styles['BoldSmallFont'])] # Empty for "Item" column
    
    # Collect all unique currencies
    currencies = sorted(list(set(inv.get('moneda_factura', 'PEN') for inv in all_invoices_data)))
    
    # Initialize totals
    total_net_amount_pen = 0
    total_net_amount_usd = 0
    total_capital_pen = 0
    total_capital_usd = 0
    total_interests_pen = 0
    total_interests_usd = 0
    total_structuring_commission_pen = 0
    total_structuring_commission_usd = 0
    total_affiliation_commission_pen = 0
    total_affiliation_commission_usd = 0
    total_igv_interests_pen = 0
    total_igv_interests_usd = 0
    total_igv_structuring_pen = 0
    total_igv_structuring_usd = 0
    total_igv_affiliation_pen = 0
    total_igv_affiliation_usd = 0
    total_disbursement_pen = 0
    total_disbursement_usd = 0

    # Data for each invoice
    invoice_columns_data = []
    for invoice_data in all_invoices_data:
        recalc_result = invoice_data['recalculate_result']
        desglose = recalc_result.get('desglose_final_detallado', {})
        calculos = recalc_result.get('calculo_con_tasa_encontrada', {})
        moneda = invoice_data.get('moneda_factura', 'PEN')
        
        invoice_num = invoice_data.get('numero_factura', 'N/A')
        header_row_1.extend([Paragraph(f"<b>Factura {invoice_num} ({moneda})</b>", styles['BoldSmallFontCenter']), Paragraph("", styles['BoldSmallFont'])])
        header_row_2.extend([Paragraph("<b>Monto</b>", styles['BoldSmallFontRight']), Paragraph("<b>%</b>", styles['BoldSmallFontRight'])])

        # Collect data for this invoice
        inv_net_amount = invoice_data.get('monto_neto_factura', 0)
        inv_capital = calculos.get('capital', 0)
        inv_interests = desglose.get('interes', {}).get('monto', 0)
        inv_com_est = desglose.get('comision_estructuracion', {}).get('monto', 0)
        inv_com_afi = desglose.get('comision_afiliacion', {}).get('monto', 0)
        inv_igv_interes = calculos.get('igv_interes', 0)
        inv_igv_com_est = calculos.get('igv_comision_estructuracion', 0)
        inv_igv_com_afi = calculos.get('igv_afiliacion', 0)
        inv_disbursement = desglose.get('abono', {}).get('monto', 0)

        invoice_columns_data.append({
            'net_amount': inv_net_amount,
            'capital': inv_capital,
            'interests': inv_interests,
            'com_est': inv_com_est,
            'com_afi': inv_com_afi,
            'igv_interes': inv_igv_interes,
            'igv_com_est': inv_igv_com_est,
            'igv_com_afi': inv_igv_com_afi,
            'disbursement': inv_disbursement,
            'moneda': moneda
        })

        # Accumulate totals
        if moneda == 'PEN':
            total_net_amount_pen += inv_net_amount
            total_capital_pen += inv_capital
            total_interests_pen += inv_interests
            total_structuring_commission_pen += inv_com_est
            total_affiliation_commission_pen += inv_com_afi
            total_igv_interests_pen += inv_igv_interes
            total_igv_structuring_pen += inv_igv_com_est
            total_igv_affiliation_pen += inv_igv_com_afi
            total_disbursement_pen += inv_disbursement
        elif moneda == 'USD':
            total_net_amount_usd += inv_net_amount
            total_capital_usd += inv_capital
            total_interests_usd += inv_interests
            total_structuring_commission_usd += inv_com_est
            total_affiliation_commission_usd += inv_com_afi
            total_igv_interests_usd += inv_igv_interes
            total_igv_structuring_usd += inv_igv_com_est
            total_igv_affiliation_usd += inv_igv_com_afi
            total_disbursement_usd += inv_disbursement

    # Add total columns to header
    if total_net_amount_pen > 0:
        header_row_1.extend([Paragraph("<b>Total (PEN)</b>", styles['BoldSmallFontCenter']), Paragraph("", styles['BoldSmallFont'])])
        header_row_2.extend([Paragraph("<b>Monto</b>", styles['BoldSmallFontRight']), Paragraph("<b>%</b>", styles['BoldSmallFontRight'])])
    if total_net_amount_usd > 0:
        header_row_1.extend([Paragraph("<b>Total (USD)</b>", styles['BoldSmallFontCenter']), Paragraph("", styles['BoldSmallFont'])])
        header_row_2.extend([Paragraph("<b>Monto</b>", styles['BoldSmallFontRight']), Paragraph("<b>%</b>", styles['BoldSmallFontRight'])])

    summary_table_data.append(header_row_1)
    summary_table_data.append(header_row_2)

    # Define rows for key metrics
    metrics = [
        ("Monto Neto de Factura", "net_amount"),
        ("Capital", "capital"),
        ("Intereses", "interests"),
        ("Comisión de Estructuración", "com_est"),
        ("Comisión de Afiliación", "com_afi"),
        ("IGV sobre Intereses", "igv_interes"),
        ("IGV sobre Com. de Estruct.", "igv_com_est"),
        ("IGV sobre Com. de Afiliación", "igv_com_afi"),
        ("Monto a Desembolsar", "disbursement")
    ]

    for item_name, key in metrics:
        row = [Paragraph(item_name, styles['SmallFont'])]
        for inv_data in invoice_columns_data:
            value = inv_data[key]
            net_amount_for_pct = inv_data['net_amount'] if inv_data['net_amount'] != 0 else 1 # Avoid division by zero
            percentage = (value / net_amount_for_pct * 100) if key != 'disbursement' else (value / inv_data['capital'] * 100) if inv_data['capital'] != 0 else 0 # Special case for disbursement %
            
            row.extend([Paragraph(f"{value:,.2f}", styles['SmallFontRight']), Paragraph(f"{percentage:.2f}%", styles['SmallFontRight'])])
        
        # Add totals for this metric
        total_pen = 0
        total_usd = 0
        for inv_data in invoice_columns_data:
            if inv_data['moneda'] == 'PEN':
                total_pen += inv_data[key]
            elif inv_data['moneda'] == 'USD':
                total_usd += inv_data[key]
        
        if total_net_amount_pen > 0: # Only add if PEN totals exist
            total_pen_net_amount_for_pct = total_net_amount_pen if total_net_amount_pen != 0 else 1
            total_pen_percentage = (total_pen / total_pen_net_amount_for_pct * 100) if key != 'disbursement' else (total_pen / total_capital_pen * 100) if total_capital_pen != 0 else 0
            row.extend([Paragraph(f"{total_pen:,.2f}", styles['BoldSmallFontRight']), Paragraph(f"{total_pen_percentage:.2f}%", styles['BoldSmallFontRight'])])
        
        if total_net_amount_usd > 0: # Only add if USD totals exist
            total_usd_net_amount_for_pct = total_net_amount_usd if total_net_amount_usd != 0 else 1
            total_usd_percentage = (total_usd / total_usd_net_amount_for_pct * 100) if key != 'disbursement' else (total_usd / total_capital_usd * 100) if total_capital_usd != 0 else 0
            row.extend([Paragraph(f"{total_usd:,.2f}", styles['BoldSmallFontRight']), Paragraph(f"{total_usd_percentage:.2f}%", styles['BoldSmallFontRight'])])
        
        summary_table_data.append(row)

    # Calculate column widths dynamically
    num_invoice_cols = len(all_invoices_data) * 2 # 2 columns per invoice (Monto, %)
    num_total_cols = 0
    if total_net_amount_pen > 0: num_total_cols += 2
    if total_net_amount_usd > 0: num_total_cols += 2

    col_widths = [1.5*inch] + [1*inch, 0.7*inch] * len(all_invoices_data) + [1*inch, 0.7*inch] * (num_total_cols // 2) # Adjust last part for actual total columns

    summary_table = Table(summary_table_data, colWidths=col_widths)
    
    # Apply TableStyle for merged cells and general formatting
    table_style_commands = [
        ('BACKGROUND', (0, 0), (-1, 1), colors.lightgrey), # Header rows
        ('TEXTCOLOR', (0, 0), (-1, 1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 1), 6),
        ('TOPPADDING', (0, 0), (-1, 1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]

    # Merge cells for invoice numbers in the first header row
    current_col = 1
    for i in range(len(all_invoices_data)):
        table_style_commands.append(('SPAN', (current_col, 0), (current_col + 1, 0)))
        current_col += 2
    
    # Merge cells for totals in the first header row
    if total_net_amount_pen > 0:
        table_style_commands.append(('SPAN', (current_col, 0), (current_col + 1, 0)))
        current_col += 2
    if total_net_amount_usd > 0:
        table_style_commands.append(('SPAN', (current_col, 0), (current_col + 1, 0)))

    summary_table.setStyle(TableStyle(table_style_commands))
    story.append(summary_table)

    doc.build(story, onFirstPage=footer_callback, onLaterPages=footer_callback)

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument("--output_filepath", required=True, help="The full path to save the output PDF.")
    parser.add_argument("--print_date", required=True, help="Date of printing in string format.")
    # --all_invoices_json is removed from arguments
    args = parser.parse_args()

    # Read the JSON data from stdin
    all_invoices_json = sys.stdin.read()
    all_invoices_data = json.loads(all_invoices_json)
    print_date_str = args.print_date

    output_dir = os.path.dirname(args.output_filepath)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        generate_consolidated_report_pdf(args.output_filepath, all_invoices_data, print_date_str)
        print(f"PDF consolidado generado exitosamente en: {args.output_filepath}")
    except Exception as e:
        print(f"Error al generar PDF consolidado: {e}")