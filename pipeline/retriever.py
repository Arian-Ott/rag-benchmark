import os

from tqdm import tqdm

from pypdf import PdfReader


class Extractor:
    def __init__(self, input_path):
        self.cur = 0
        self.nex = 1
        self.input_path = input_path
        if not os.path.exists(self.input_path):
            raise RuntimeError("Given Path does not exist!")

        # Filter out only PDF files
        self.pdf_files = []
        for root, _, files in os.walk(self.input_path):
            pdfs = [f for f in files if f.lower().endswith(".pdf")]
            if pdfs:
                self.pdf_files.append((root, pdfs))

        self.extracted_pdfs = []
        self.paths_to_extract = []
        self.files = []

    def extract(self):
        if not self.pdf_files:
            raise RuntimeError("No PDF files found!")

        self.paths_to_extract = [
            os.path.join(pdf_file[0], pdf)
            for pdf_file in self.pdf_files
            for pdf in pdf_file[1]
        ]

        for path in tqdm(
            self.paths_to_extract,
            total=len(self.paths_to_extract),
            desc="Extracting PDFs...",
        ):
            try:
                extracted_text = self._extract_text_from_pdf(path)
                self.extracted_pdfs.append(extracted_text)
            except Exception as e:
                print(f"Failed to extract {path}: {e}")

    def _extract_text_from_pdf(self, pdf_path):
        text = ""
        try:
            with open(pdf_path, "rb") as file:
                reader = PdfReader(file)
                # Iterate over each page
                for page in reader.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            raise RuntimeError(f"Failed to read PDF {pdf_path}: {e}")
        self.files.append(
            (pdf_path, os.path.basename(pdf_path).replace(" ", "-"), text)
        )
        return text

    def to_txt(self):
        if not os.path.exists("../data/out"):
            os.mkdir("../data/out")

        for pdf_path, new_name, text in tqdm(
            self.files, desc="writing to " "text files..."
        ):
            new_name = new_name.replace(".pdf", "")
            with open(f"../data/out/{new_name}" + ".txt", "w") as file:
                file.write(text)

    def __iter__(self):
        return iter(self.extracted_pdfs)

    def __len__(self):
        return len(self.extracted_pdfs)

    def __next__(self):
        if self.cur >= len(self.extracted_pdfs):
            raise StopIteration
        self.cur += 1

        return self.extracted_pdfs[self.cur]
