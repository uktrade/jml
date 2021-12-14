from unittest import mock

from django.test import TestCase

from core.utils.pdf import parse_leaver_pdf


class ParseLeaverPDF(TestCase):
    """
    Test the PDF parser
    """

    def setUp(self):
        self.BLANK_PDF_TEXT = ""  # /PS-IGNORE
        # A Text representation of the Leaver Form's content /PS-IGNORE
        self.LEAVER_PDF_TEXT = (
            "Leaver's Notification Form "  # /PS-IGNORE
            "User who completed the form: "
            "Line Manager Joe Bloggs "  # /PS-IGNORE
            "Line Manager's Email joe.bloggs@example.com "  # /PS-IGNORE
            "Line Manager's Oracle ID ORACLE123 "
            "Line Manager's Employee Number 123321 "
            "Completed on 21/12/2021 13:34 "
            "Leaver's details: "
            "Name Jane Doe "
            "Email jane.doe@example.com "  # /PS-IGNORE
            "Oracle ID ORACLE321 "
            "Employee Number 321123 "
            "Paid or Unpaid? Paid - on UK SBS Payroll "
            "Reason for Leaving Resignation "  # /PS-IGNORE
            "Last Day of Employment 22/11/2021 "
            "Annual Leave: "  # /PS-IGNORE
            "The Leaver has Annual Leave to be paid/deducted: "
            "Unit of Measurement Hours "  # /PS-IGNORE
            "Paid or Deducted? Paid "
            "Number of Days to be Paid 0 "
            "Number of Hours to be Paid 1 "
            "Number of Days to be Deducted 0 "
            "Number of Hours to be Deducted 0 "
            "The Leaver does not have Flexi Impacting Pay to be paid/deducted. "  # /PS-IGNORE
        )

    @mock.patch("core.utils.pdf.get_pdf_text")
    def test_blank_pdf(self, mock_get_pdf_text):
        mock_get_pdf_text.return_value = self.BLANK_PDF_TEXT  # /PS-IGNORE
        parsed_value = parse_leaver_pdf(filename="")

        self.assertEqual(
            parsed_value,
            {
                "Completed on": "",
                "Email": "",
                "Employee Number": "",
                "Last Day of Employment": "",
                "Line Manager": "",
                "Line Manager's Email": "",
                "Line Manager's Employee Number": "",
                "Line Manager's Oracle ID": "",
                "Name": "",
                "Number of Days to be Deducted": "",
                "Number of Days to be Paid": "",
                "Number of Hours to be Deducted": "",
                "Number of Hours to be Paid": "",
                "Oracle ID": "",
                "Paid or Deducted?": "",
                "Paid or Unpaid?": "",
                "Reason for Leaving": "",
                "Unit of Measurement": "",  # /PS-IGNORE
            },
        )

    @mock.patch("core.utils.pdf.get_pdf_text")
    def test_leaver_pdf(self, mock_get_pdf_text):
        mock_get_pdf_text.return_value = self.LEAVER_PDF_TEXT
        parsed_value = parse_leaver_pdf(filename="")

        self.assertEqual(
            parsed_value,
            {
                "Completed on": "21/12/2021 13:34",
                "Email": "jane.doe@example.com",  # /PS-IGNORE
                "Employee Number": "321123",
                "Last Day of Employment": "22/11/2021",  # /PS-IGNORE
                "Line Manager": "Joe Bloggs",  # /PS-IGNORE
                "Line Manager's Email": "joe.bloggs@example.com",  # /PS-IGNORE
                "Line Manager's Employee Number": "123321",
                "Line Manager's Oracle ID": "ORACLE123",
                "Name": "Jane Doe",  # /PS-IGNORE
                "Number of Days to be Deducted": "0",
                "Number of Days to be Paid": "0",
                "Number of Hours to be Deducted": "0",
                "Number of Hours to be Paid": "1",
                "Oracle ID": "ORACLE321",
                "Paid or Deducted?": "Paid",
                "Paid or Unpaid?": "Paid - on UK SBS Payroll",
                "Reason for Leaving": "Resignation",  # /PS-IGNORE
                "Unit of Measurement": "Hours",  # /PS-IGNORE
            },
        )
