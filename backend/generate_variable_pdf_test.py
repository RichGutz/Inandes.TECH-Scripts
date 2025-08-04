import os
import datetime
from supabase_handler import get_proposal_details_by_id
from variable_data_pdf_generator import generate_variable_pdf

def run_variable_pdf_test():
    proposal_id = "TRANSPORTES_SANTA_FE_DEL_NORTE_SAC-E001-676-04-08-25"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filepath = f"C:/Users/rguti/Inandes.TECH/generated_pdfs/variables_log_{proposal_id}_{timestamp}.pdf"
    print(f"Attempting to generate PDF at: {output_filepath}")

    print(f"Fetching data for proposal_id: {proposal_id}")
    factoring_details = get_proposal_details_by_id(proposal_id)

    if not factoring_details:
        print("Could not retrieve factoring details. Aborting.")
        return

    print("Successfully fetched data. Generating variable PDF...")

    try:
        generate_variable_pdf(factoring_details, output_filepath)
        print(f"Variable PDF generated successfully at: {output_filepath}")
    except Exception as e:
        print(f"Error generating variable PDF: {e}")

if __name__ == "__main__":
    run_variable_pdf_test()
