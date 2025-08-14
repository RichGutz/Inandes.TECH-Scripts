import argparse
import json
import os
from jinja2 import Environment, FileSystemLoader

try:
    from weasyprint import HTML
except ImportError:
    print("Error: WeasyPrint is not installed. Please install it using 'pip install weasyprint'")
    exit(1)

def generate_pdf_from_invoices_data(output_filepath, invoices_data, print_date_str):
    template_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("perfil_template.html")

    template_data = {
        'invoices': invoices_data,
        'print_date': print_date_str
    }

    html_output = template.render(template_data)

    base_url = os.path.dirname(os.path.abspath(__file__))
    pdf_bytes = HTML(string=html_output, base_url=base_url).write_pdf()

    output_dir = os.path.dirname(output_filepath)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_filepath, "wb") as f:
        f.write(pdf_bytes)
    
    print(f"PDF profile successfully generated at: {output_filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a consolidated PDF profile from a list of invoices.")
    parser.add_argument("--output_filepath", required=True, help="The full path to save the output PDF file.")
    parser.add_argument("--invoices_json", required=True, help="JSON string of a list of invoice data.")
    parser.add_argument("--print_date", required=True, help="Date of printing in string format.")
    args = parser.parse_args()

    try:
        invoices_data = json.loads(args.invoices_json)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Received JSON string: {args.invoices_json}")
        exit(1)

    try:
        generate_pdf_from_invoices_data(args.output_filepath, invoices_data, args.print_date)
    except Exception as e:
        print(f"An error occurred during PDF generation: {e}")
        import traceback
        traceback.print_exc()
        exit(1)