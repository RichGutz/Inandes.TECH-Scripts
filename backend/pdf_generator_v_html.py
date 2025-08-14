
import json
import sys
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os

def format_currency(value, currency_symbol='PEN'):
    if currency_symbol == 'USD':
        return f"US$ {value:,.2f}"
    return f"S/ {value:,.2f}"

def generate_pdf_from_html(data, output_filepath):
    """
    Generates a PDF from an HTML template using Jinja2 and WeasyPrint.
    """
    try:
        # Configure Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'Adicionales.Inandes.HTML', 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        env.filters['format_currency'] = format_currency

        # Load the template
        template = env.get_template('plantilla_factura_V5.html')

        # Render the template with data
        html_out = template.render(data)

        # Generate PDF from HTML
        HTML(string=html_out, base_url=__file__).write_pdf(output_filepath)

        print(f"PDF successfully generated at {output_filepath}")

    except Exception as e:
        print(f"Error generating PDF: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        json_data_str = sys.argv[1]
        output_filepath = sys.argv[2]
        
        try:
            # Parse the JSON data
            final_data = json.loads(json_data_str)
            
            # Generate the PDF
            generate_pdf_from_html(final_data, output_filepath)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python pdf_generator_v_html.py <json_data> <output_filepath>", file=sys.stderr)
        sys.exit(1)
