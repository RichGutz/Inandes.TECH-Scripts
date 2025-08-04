import subprocess
import sys
import os
import datetime
import json

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_handler import get_proposal_details_by_id

def run_test():
    proposal_id = "TRANSPORTES_SANTA_FE_DEL_NORTE_SAC-E001-676-04-08-25"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filepath = f"C:/Users/rguti/Inandes.TECH/generated_pdfs/{proposal_id}_{timestamp}.pdf"

    print(f"Fetching data for proposal_id: {proposal_id}")
    factoring_details = get_proposal_details_by_id(proposal_id)

    if not factoring_details:
        print("Could not retrieve factoring details. Aborting.")
        return

    print("Successfully fetched data.")

    # Duplicate the invoice to simulate a multi-invoice scenario
    invoices = [factoring_details, factoring_details]
    invoices_json = json.dumps(invoices)

    # Simulate affiliation commission
    aplicar_comision_afiliacion = True
    comision_afiliacion_monto = 200.0
    igv_afiliacion = 36.0

    # Construct the command to run the PDF generator CLI
    command = [
        "python",
        "C:/Users/rguti/Inandes.TECH/backend/pdf_generator_v_cli.py",
        f"--output_filepath={output_filepath}",
        f"--invoices_json={invoices_json}",
        "--aplicar_comision_afiliacion",
        f"--comision_afiliacion_monto_calculado={comision_afiliacion_monto}",
        f"--igv_afiliacion_calculado={igv_afiliacion}"
    ]

    print("\nRunning PDF generator command...")
    print(" ".join(command))

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("PDF Generator CLI executed successfully.")
        print("Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        # Verify that the file was created
        if os.path.exists(output_filepath):
            print(f"\nSUCCESS: PDF file found at {output_filepath}")
        else:
            print(f"\nFAILURE: PDF file was NOT found at {output_filepath}")

    except subprocess.CalledProcessError as e:
        print(f"Error executing PDF Generator CLI: {e}")
        print(f"Return code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
    except FileNotFoundError:
        print("Error: The pdf_generator_v_cli.py script was not found.")

if __name__ == "__main__":
    run_test()
