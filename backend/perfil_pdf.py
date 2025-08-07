from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
import os
import datetime

def generate_perfil_pdf(output_filepath, invoice_data, print_date_str):
    doc = SimpleDocTemplate(output_filepath, pagesize=landscape(letter), leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=1.2*inch, bottomMargin=1*inch)
    styles = getSampleStyleSheet()
    story = []
    logo_path = "C:/Users/rguti/Inandes.TECH/inputs_para_generated_pdfs/LOGO.png"

    # Custom styles
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

    # Header and Footer callback function
    def header_and_footer(canvas, doc):
        # Save the state to not interfere with the rest of the document
        canvas.saveState()
        
        # Header
        if os.path.exists(logo_path):
            # Draw image on the top right. landscape(letter) is 11 x 8.5 inches.
            # Page width is doc.width + doc.leftMargin + doc.rightMargin
            page_width = doc.width + doc.leftMargin + doc.rightMargin
            # Draw on the right side of the page
            canvas.drawImage(logo_path, page_width - doc.rightMargin - 1*inch, doc.height + 0.5*inch, 
                           width=1*inch, height=1*inch, preserveAspectRatio=True, mask='auto')

        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.drawString(doc.leftMargin, 0.75 * inch, f"Fecha de Impresión: {print_date_str}")
        
        # Restore the canvas state
        canvas.restoreState()

    # Title
    story.append(Paragraph("Perfil de la Operación", styles['h2']))
    story.append(Spacer(1, 0.2 * inch))

    # Invoice Summary
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

    # Perfil de la Operación Table
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

    doc.build(story, onFirstPage=header_and_footer, onLaterPages=header_and_footer)

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--output_filepath", required=True, help="The full path to save the output PDF.")
    parser.add_argument("--invoice_json", required=True, help="JSON string of a single invoice's data.")
    parser.add_argument("--print_date", required=True, help="Date of printing in string format.")
    args = parser.parse_args()

    try:
        invoice_data = json.loads(args.invoice_json)
    except json.JSONDecodeError as e:
        print(f"Error decodificando JSON: {e}")
        print(f"JSON recibido: {args.invoice_json}")
        exit(1)
    print_date_str = args.print_date

    output_dir = os.path.dirname(args.output_filepath)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        generate_perfil_pdf(args.output_filepath, invoice_data, print_date_str)
        print(f"PDF de perfil generado exitosamente en: {args.output_filepath}")
    except Exception as e:
        print(f"Error al generar PDF de perfil: {e}")
