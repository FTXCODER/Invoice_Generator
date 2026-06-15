import streamlit as st
import pandas as pd
import gspread
import json
import os
import tempfile

from datetime import datetime

from google.oauth2.service_account import Credentials

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ----------------------
pdfmetrics.registerFont(
    TTFont(
        "DejaVuSans",
        "DejaVuSans.ttf"
    )
)
# ----------------------


# ==================================================
# CONFIGURATION
# ==================================================

# SPREADSHEET_ID = "1pjyogE1rwuKMkHA64g2SfwmgQIeFQEC7FcSEFEMaE38"

# DRIVE_FOLDER_ID = "1gimX8lZxLhQRvXbI-RlDAPOVK7MInhch"

SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]

DRIVE_FOLDER_ID = st.secrets["DRIVE_FOLDER_ID"]

# SERVICE_ACCOUNT_FILE = "service_account.json"
# credentials_info = dict(st.secrets["gcp_service_account"])

# credentials = Credentials.from_service_account_info(
#     credentials_info,
#     scopes=scopes
# )


# ==================================================
# STREAMLIT PAGE
# ==================================================

st.set_page_config(
    page_title="Invoice Generator",
    page_icon="🧾",
    layout="centered"
)

st.title("🧾 Invoice Generator")


# ==================================================
# SERVICE LIST
# ==================================================

SERVICES = [

"Graphic Design",
"Flex Design",
"Poster Design",
"Hand Bill DTP",
"Invitation Card Design",
"Business Card Design",
"Letter Head",
"Banner Design",
"Badge Design",
"Birth Day Design",
"Social Media Post Design",
"School Project",
"Brochure",
"Other Design",

"Digital Print",
"All GSM Digital Print",
"Gum Sheet Print",
"Vinyl Sheet Print",
"Photo Paper",
"Certificate",
"ID Card",
"Ribbon",
"Jacket",
"Card Holder",
"Lanyard",

"Flex",
"Normal Flex",
"Black Back Flex",
"Star Flex",
"Standee",
"Vinyl Print",
"Back Lit Flex",
"Canvas",
"One Way Vision",

"Offset Print",
"Single Colour Offset",
"Bi Colour Offset",
"4 Colour Offset",

"Screen Printing",
"Plastic Bag",
"Non woven Bag",
"Paper Bag",
"Halkhata Card",
"Calendar",
"Plastic Container",

"Jersey Name Number",
"Fees Card",
"Single Colour TShirt",

"Lamination",
"A4 Lamination",
"A3 Lamination",

"Pan card (new/correction)",
"Voter card (new/correction)",
"Ration card (new/correction)",
"Adhaar address update",
"Pan Adhaar Link"

]


UNITS = [
    "Pcs",
    "Nos",
    "Sqft",
    "Set",
    "Page",
    "Card",
    "Hour"
]



# ----------Part 2
# ==================================================
# GOOGLE CONNECTION
# ==================================================

# def get_credentials():

#     scopes = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive"
#     ]

#     credentials = Credentials.from_service_account_file(
#         SERVICE_ACCOUNT_FILE,
#         scopes=scopes
#     )

#     return credentials
def get_credentials():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials_info = dict(
        st.secrets["gcp_service_account"]
    )

    credentials = Credentials.from_service_account_info(
        credentials_info,
        scopes=scopes
    )

    return credentials


def get_sheet():

    credentials = get_credentials()

    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(
        SPREADSHEET_ID
    )

    return spreadsheet.sheet1


# ==================================================
# INVOICE NUMBER
# ==================================================

def generate_invoice_number():

    sheet = get_sheet()

    records = sheet.get_all_values()

    if len(records) <= 1:
        next_number = 1
    else:
        next_number = len(records)

    year = datetime.now().year

    return (
        f"INV-{year}-{next_number:04d}"
    )




# ----------Part 3
# ==================================================
# CUSTOMER DETAILS
# ==================================================

st.subheader("Customer Details")

customer_name = st.text_input(
    "Customer Name"
)

mobile = st.text_input(
    "Mobile Number"
)

address = st.text_area(
    "Address"
)


# ----------Part 4
# ==================================================
# MULTIPLE ITEM ENTRY
# ==================================================

st.subheader("Invoice Items")

if "items" not in st.session_state:

    st.session_state["items"] = [
        {
            "service": SERVICES[0],
            "unit": UNITS[0],
            "qty": 1,
            "rate": 0.0
        }
    ]


# ADD ITEM BUTTON

col1, col2 = st.columns(2)

with col1:

    if st.button(
        "➕ Add Item",
        use_container_width=True
    ):

        st.session_state["items"].append(
            {
                "service": SERVICES[0],
                "unit": UNITS[0],
                "qty": 1,
                "rate": 0.0
            }
        )


with col2:

    if st.button(
        "➖ Remove Last Item",
        use_container_width=True
    ):

        if len(st.session_state["items"]) > 1:

            st.session_state["items"].pop()


# ==================================================
# ITEM ROWS
# ==================================================

invoice_items = []

grand_total = 0

for i in range(
    len(st.session_state["items"])
):

    st.markdown(
        f"### Item {i+1}"
    )

    c1, c2 = st.columns(2)

    service = c1.selectbox(
        "Service",
        SERVICES,
        key=f"service_{i}"
    )

    unit = c2.selectbox(
        "Unit",
        UNITS,
        key=f"unit_{i}"
    )

    c3, c4 = st.columns(2)

    qty = c3.number_input(
        "Quantity",
        min_value=1.0,
        value=1.0,
        key=f"qty_{i}"
    )

    rate = c4.number_input(
        "Rate",
        min_value=0.0,
        value=0.0,
        key=f"rate_{i}"
    )

    amount = qty * rate

    grand_total += amount

    st.success(
        f"Amount : ₹ {amount:,.2f}"
    )

    invoice_items.append(
        {
            "service": service,
            "unit": unit,
            "qty": qty,
            "rate": rate,
            "amount": amount
        }
    )

    st.divider()


# ==================================================
# INVOICE PREVIEW TABLE
# ==================================================

st.subheader("Invoice Preview")

preview_data = []

for row in invoice_items:

    preview_data.append(
        [
            row["service"],
            row["unit"],
            row["qty"],
            row["rate"],
            row["amount"]
        ]
    )

preview_df = pd.DataFrame(
    preview_data,
    columns=[
        "Service",
        "Unit",
        "Qty",
        "Rate",
        "Amount"
    ]
)

st.dataframe(
    preview_df,
    use_container_width=True
)

st.markdown("---")

st.subheader(
    f"Grand Total : ₹ {grand_total:,.2f}"
)

# -----------Part 5
# ==================================================
# PDF GENERATOR
# ==================================================

def create_invoice_pdf(
        invoice_no,
        customer_name,
        mobile,
        address,
        invoice_items,
        grand_total
):

    pdf_file = os.path.join(
        tempfile.gettempdir(),
        f"{invoice_no}.pdf"
    )

    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=A4
    )

    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "DejaVuSans"
    styles["Title"].fontName = "DejaVuSans"
    styles["Heading2"].fontName = "DejaVuSans"

    elements = []

    # ==========================================
    # HEADER
    # ==========================================

    title = Paragraph(
        "<b>INVOICE FOR ABC COMPANY</b>",
        styles["Title"]
    )

    elements.append(title)
    elements.append(Spacer(1, 15))

    # ==========================================
    # INVOICE DETAILS
    # ==========================================

    invoice_info = f"""
    <b>Invoice No:</b> {invoice_no}<br/>
    <b>Date:</b> {datetime.now().strftime('%d-%m-%Y')}<br/>
    """

    elements.append(
        Paragraph(
            invoice_info,
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    # ==========================================
    # CUSTOMER DETAILS
    # ==========================================

    customer_info = f"""
    <b>Customer Name:</b> {customer_name}<br/>
    <b>Mobile:</b> {mobile}<br/>
    <b>Address:</b> {address}
    """

    elements.append(
        Paragraph(
            customer_info,
            styles["Normal"]
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    # ==========================================
    # ITEM TABLE
    # ==========================================

    table_data = [
        [
            "Service",
            "Unit",
            "Qty",
            "Rate",
            "Amount"
        ]
    ]

    for item in invoice_items:

        table_data.append(
            [
                item["service"],
                item["unit"],
                str(item["qty"]),
                f"₹ {item['rate']:,.2f}",
                f"₹ {item['amount']:,.2f}"
            ]
        )

    table = Table(
        table_data,
        colWidths=[
            180,
            60,
            60,
            80,
            90
        ]
    )

    table.setStyle(
        TableStyle([

            ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),

            ('GRID',(0,0),(-1,-1),1,colors.black),

            # ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTNAME',(0,0),(-1,0),'DejaVuSans'),
            ('FONTNAME',(0,1),(-1,-1),'DejaVuSans'),

            ('ALIGN',(2,1),(-1,-1),'CENTER'),

            ('VALIGN',(0,0),(-1,-1),'MIDDLE')

        ])
    )

    elements.append(table)

    elements.append(
        Spacer(1, 20)
    )

    # ==========================================
    # GRAND TOTAL
    # ==========================================

    total_text = f"""
    <b>Grand Total : ₹ {grand_total:,.2f}</b>
    """

    elements.append(
        Paragraph(
            total_text,
            styles["Heading2"]
        )
    )

    elements.append(
        Spacer(1, 40)
    )

    # ==========================================
    # FOOTER
    # ==========================================

    footer = Paragraph(
        "Thank you for your business.",
        styles["Normal"]
    )

    elements.append(
        footer
    )

    # ==========================================
    # BUILD PDF
    # ==========================================

    doc.build(
        elements
    )

    return pdf_file



# ----------Part 6
# ==================================================
# GOOGLE DRIVE UPLOAD
# ==================================================

def upload_to_drive(pdf_path):

    credentials = get_credentials()

    drive_service = build(
        "drive",
        "v3",
        credentials=credentials
    )

    file_metadata = {
        "name": os.path.basename(pdf_path),
        "parents": [DRIVE_FOLDER_ID]
    }

    media = MediaFileUpload(
        pdf_path,
        mimetype="application/pdf"
    )

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id",
        supportsAllDrives=True
    ).execute()

    file_id = file.get("id")

    drive_service.permissions().create(
        fileId=file_id,
        body={
            "type": "anyone",
            "role": "reader"
        },
        supportsAllDrives=True
    ).execute()

    pdf_link = (
        f"https://drive.google.com/file/d/"
        f"{file_id}/view"
    )

    return pdf_link


# ==================================================
# SAVE TO GOOGLE SHEET
# ==================================================

def save_invoice_to_sheet(
        invoice_no,
        customer_name,
        mobile,
        address,
        invoice_items,
        grand_total,
        pdf_link
):

    sheet = get_sheet()

    sheet.append_row([

        invoice_no,

        datetime.now().strftime(
            "%d-%m-%Y"
        ),

        customer_name,

        mobile,

        address,

        json.dumps(
            invoice_items,
            default=str
        ),

        grand_total,

        pdf_link

    ])


# ==================================================
# GENERATE INVOICE BUTTON
# ==================================================

st.markdown("---")

if st.button(
    "🧾 Generate Invoice",
    use_container_width=True
):

    # =============================
    # VALIDATION
    # =============================

    if customer_name.strip() == "":

        st.error(
            "Customer Name Required"
        )

    elif len(invoice_items) == 0:

        st.error(
            "Add at least one item"
        )

    else:

        try:

            invoice_no = (
                generate_invoice_number()
            )

            # =====================
            # PDF
            # =====================

            pdf_file = create_invoice_pdf(
                invoice_no,
                customer_name,
                mobile,
                address,
                invoice_items,
                grand_total
            )

            # =====================
            # DRIVE UPLOAD
            # =====================

            # pdf_link = upload_to_drive(
            #     pdf_file
            # )
            pdf_link = "Drive Upload Disabled"

            # =====================
            # SHEET SAVE
            # =====================

            save_invoice_to_sheet(
                invoice_no,
                customer_name,
                mobile,
                address,
                invoice_items,
                grand_total,
                pdf_link
            )

            # =====================
            # SUCCESS
            # =====================

            st.success(
                f"Invoice {invoice_no} Created Successfully"
            )

            st.link_button(
                "📄 Open PDF",
                pdf_link
            )

            with open(
                pdf_file,
                "rb"
            ) as file:

                st.download_button(
                    label="⬇ Download PDF",
                    data=file,
                    file_name=f"{invoice_no}.pdf",
                    mime="application/pdf"
                )

        except Exception as e:

            st.error(
                str(e)
            )
