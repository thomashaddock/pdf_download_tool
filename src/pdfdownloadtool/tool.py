import io
import re
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import requests
import PyPDF2


class PDFDownloadToolInput(BaseModel):
    """Input schema for PDFDownloadTool."""
    url: str = Field(..., description="Google Drive sharing URL to download PDF from")


class PDFDownloadTool(BaseTool):
    name: str = "PDF Download Tool"
    description: str = (
        "Downloads and extracts text from PDF files on Google Drive. "
        "Use for processing contract documents and legal agreements from cloud storage."
    )
    args_schema: Type[BaseModel] = PDFDownloadToolInput

    def _run(self, url: str) -> str:
        """Download PDF from Google Drive and extract text content."""
        try:
            # Validate URL
            if "drive.google.com" not in url:
                return "**Error:** Only Google Drive URLs are supported"
            
            # Extract file ID from Google Drive URL
            file_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
            if not file_id_match:
                return "**Error:** Invalid Google Drive URL format"
            
            file_id = file_id_match.group(1)
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            # Download PDF
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(download_url, headers=headers, allow_redirects=True, timeout=30)
            response.raise_for_status()
            
            # Extract text from PDF
            pdf_file = io.BytesIO(response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(f"## Page {page_num + 1}\n\n{text.strip()}")
                except Exception:
                    continue  # Skip problematic pages
            
            if not text_content:
                return "**Error:** Could not extract text from PDF. File might be image-based or corrupted."
            
            markdown_content = "# PDF Content\n\n" + "\n\n".join(text_content)
            return markdown_content
            
        except requests.RequestException as e:
            return f"**Network Error:** {str(e)}"
        except Exception as e:
            return f"**Processing Error:** {str(e)}"

    async def _arun(self, url: str) -> str:
        """Async version of _run - delegates to sync version since requests is thread-safe."""
        return self._run(url)
