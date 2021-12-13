from typing import Dict, List, Optional, TypedDict, cast

from PyPDF2 import PdfFileReader
from PyPDF2.pdf import PageObject  # /PS-IGNORE

ParsedUKSBSPDF = TypedDict(  # /PS-IGNORE
    "ParsedUKSBSPDF",  # /PS-IGNORE
    {
        "Line Manager": str,
        "Line Manager's Email": str,
        "Line Manager's Oracle ID": str,
        "Line Manager's Employee Number": str,
        "Completed on": str,
        "Name": str,
        "Email": str,
        "Oracle ID": str,
        "Employee Number": str,
        "Paid or Unpaid?": str,
        "Reason for Leaving": str,
        "Last Day of Employment": str,
        "Unit of Measurement": str,  # /PS-IGNORE
        "Paid or Deducted?": str,
        "Number of Days to be Paid": str,
        "Number of Hours to be Paid": str,
        "Number of Days to be Deducted": str,
        "Number of Hours to be Deducted": str,
    },
)


def parse_leaver_pdf(*, filename: str) -> ParsedUKSBSPDF:
    fileReader = PdfFileReader(open(filename, "rb"))

    page: PageObject = fileReader.getPage(0)
    page_text = page.extractText()

    user_who_completed_title = "User who completed the form:"
    user_who_completed_labels = [
        "Line Manager",
        "Line Manager's Email",
        "Line Manager's Oracle ID",
        "Line Manager's Employee Number",
        "Completed on",
    ]

    leavers_details_title = "Leaver's details:"
    leavers_details_labels = [
        "Name",
        "Email",
        "Oracle ID",
        "Employee Number",
        "Paid or Unpaid?",
        "Reason for Leaving",
        "Last Day of Employment",
    ]

    annual_leave_title = "Annual Leave"  # /PS-IGNORE
    annual_leave_labels = [
        "Unit of Measurement",  # /PS-IGNORE
        "Paid or Deducted?",
        "Number of Days to be Paid",
        "Number of Hours to be Paid",
        "Number of Days to be Deducted",
        "Number of Hours to be Deducted",
    ]

    def get_table_data(
        *, title: str, labels: List[str], cut_off_text: str
    ) -> Dict[str, str]:
        """
        Gets the data from a table in the PDF
        """
        title_index = page_text.find(title)
        cut_off_index = page_text.find(cut_off_text)
        editing_text = page_text[title_index + len(title) : cut_off_index]

        table_data = {}

        for index, label in enumerate(labels):
            label_index = editing_text.find(label)
            row_value = editing_text[label_index + len(label) :]
            next_label: Optional[str] = None
            next_label_index = None
            try:
                next_label = labels[index + 1]
                next_label_index = row_value.find(next_label)
                row_value = row_value[:next_label_index]
            except IndexError:  # /PS-IGNORE
                pass

            table_data[label] = row_value

        return table_data

    user_who_completed_values = get_table_data(  # /PS-IGNORE
        title=user_who_completed_title,
        labels=user_who_completed_labels,
        cut_off_text=leavers_details_title,
    )

    leaver_details_values = get_table_data(
        title=leavers_details_title,
        labels=leavers_details_labels,
        cut_off_text=annual_leave_title,
    )

    annual_leave_values = get_table_data(
        title=annual_leave_title,
        labels=annual_leave_labels,
        cut_off_text=(
            "The Leaver does not have Flexi Impacting Pay to be "  # /PS-IGNORE
            "paid/deducted."
        ),
    )

    # Merge all the data
    parsed_pdf: Dict[str, str] = {}
    parsed_pdf.update(**user_who_completed_values)
    parsed_pdf.update(**leaver_details_values)
    parsed_pdf.update(**annual_leave_values)
    return cast(ParsedUKSBSPDF, parsed_pdf)
