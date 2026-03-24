# tests/test_pdf.py
import pytest
import sys
sys.path.insert(0, ".")
from providers.pdf import PDFBook


def test_pdf_open_missing_file():
    with pytest.raises(FileNotFoundError):
        PDFBook("/nonexistent/file.pdf")