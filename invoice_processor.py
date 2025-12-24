"""
JBridge Invoice Processor - PDF Invoice Analysis with Gemini AI
Extracts vendor, amounts, dates, line items from PDF invoices
"""
import os
import json
import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import google.generativeai as genai

load_dotenv()

# Configure Gemini
GEMINI_API = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API")
if GEMINI_API:
    genai.configure(api_key=GEMINI_API)

st.set_page_config(
    page_title="JBridge Invoice Processor",
    page_icon="📑",
    layout="wide"
)

st.title("📑 JBridge Invoice Processor")
st.markdown("*Powered by Gemini AI - Extract invoice data automatically*")

# Invoice extraction prompt
INVOICE_EXTRACTION_PROMPT = """Analyze this invoice/receipt text and extract the following information in JSON format:

{
    "vendor_name": "Company/business name",
    "vendor_address": "Full address if available",
    "invoice_number": "Invoice/receipt number",
    "invoice_date": "Date in YYYY-MM-DD format",
    "due_date": "Due date in YYYY-MM-DD format if available",
    "subtotal": "Subtotal amount as number",
    "tax": "Tax amount as number",
    "total": "Total amount as number",
    "currency": "Currency code (USD, EUR, etc.)",
    "payment_method": "Credit card, cash, check, etc. if mentioned",
    "line_items": [
        {
            "description": "Item description",
            "quantity": "Quantity as number",
            "unit_price": "Price per unit as number",
            "amount": "Line total as number"
        }
    ],
    "category_suggestion": "Suggested expense category (Office Supplies, Travel, Meals, Software, Professional Services, etc.)",
    "notes": "Any additional relevant information"
}

Be precise with numbers - extract them without currency symbols.
If a field is not found, use null.
For dates, convert to YYYY-MM-DD format.

INVOICE TEXT:
"""

def extract_text_from_pdf(pdf_file):
    """Extract text content from PDF"""
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def analyze_invoice_with_gemini(text):
    """Use Gemini to extract structured invoice data"""
    if not GEMINI_API:
        return {"error": "GEMINI_API_KEY not configured. Set in .env file."}

    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = INVOICE_EXTRACTION_PROMPT + text

    try:
        response = model.generate_content(prompt)
        response_text = response.text

        # Try to parse JSON from response
        # Handle markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        return {"error": "Failed to parse response", "raw_response": response.text}
    except Exception as e:
        return {"error": str(e)}

# Main UI
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Upload Invoice")
    pdf = st.file_uploader("Upload PDF invoice or receipt", type=["pdf"])

    if pdf is not None:
        with st.spinner("Extracting text from PDF..."):
            text = extract_text_from_pdf(pdf)

        with st.expander("📄 Raw PDF Text", expanded=False):
            st.text(text[:3000] + "..." if len(text) > 3000 else text)

        if st.button("🔍 Analyze Invoice", type="primary"):
            with st.spinner("Analyzing with Gemini AI..."):
                result = analyze_invoice_with_gemini(text)

            st.session_state.analysis_result = result

with col2:
    st.subheader("Extracted Data")

    if "analysis_result" in st.session_state:
        result = st.session_state.analysis_result

        if "error" in result:
            st.error(f"Error: {result['error']}")
            if "raw_response" in result:
                st.text(result["raw_response"])
        else:
            # Display key fields
            st.metric("Vendor", result.get("vendor_name", "N/A"))

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Total", f"${result.get('total', 0):.2f}" if result.get('total') else "N/A")
            with col_b:
                st.metric("Date", result.get("invoice_date", "N/A"))
            with col_c:
                st.metric("Category", result.get("category_suggestion", "N/A"))

            # Line items
            if result.get("line_items"):
                st.subheader("Line Items")
                for i, item in enumerate(result["line_items"]):
                    if item:
                        st.write(f"**{i+1}.** {item.get('description', 'N/A')} - ${item.get('amount', 0):.2f}" if item.get('amount') else f"**{i+1}.** {item.get('description', 'N/A')}")

            # Full JSON
            with st.expander("📋 Full JSON Output", expanded=False):
                st.json(result)

            # Export options
            st.subheader("Export")
            col_x, col_y = st.columns(2)
            with col_x:
                st.download_button(
                    "📥 Download JSON",
                    json.dumps(result, indent=2),
                    f"invoice_{result.get('invoice_number', 'data')}.json",
                    "application/json"
                )
            with col_y:
                # CSV-friendly format
                csv_line = f"{result.get('invoice_date','')},{result.get('vendor_name','')},{result.get('total','')},{result.get('category_suggestion','')}"
                st.download_button(
                    "📥 Download CSV Line",
                    f"date,vendor,total,category\n{csv_line}",
                    "invoice_data.csv",
                    "text/csv"
                )
    else:
        st.info("Upload a PDF and click 'Analyze Invoice' to extract data")

# Sidebar info
with st.sidebar:
    st.header("About")
    st.markdown("""
    **JBridge Invoice Processor** uses Gemini AI to automatically extract:
    - Vendor information
    - Invoice dates
    - Line items
    - Totals and taxes
    - Expense category suggestions

    Perfect for bookkeeping automation!
    """)

    st.header("Setup")
    if GEMINI_API:
        st.success("✅ Gemini API configured")
    else:
        st.warning("⚠️ Set GEMINI_API_KEY in .env file")
        st.code("GEMINI_API_KEY=your-key-here")

    st.header("Integration")
    st.markdown("""
    This tool can integrate with:
    - n8n workflows (webhook trigger)
    - Google Sheets (for expense tracking)
    - QuickBooks/Wave (via API)
    """)
