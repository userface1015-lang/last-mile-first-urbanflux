from pypdf import PdfReader

reader = PdfReader('data/documents/Improving_metro_access_in_India_WRI.pdf')
print('Total pages in WRI paper:', len(reader.pages))

terms = ['20 minute', '20-minute', '7,200', '7200', 'threshold', 'mode share', 'walking']
for term in terms:
    matches = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ''
        if term.lower() in text.lower():
            matches.append(idx + 1)
    print(f"Term '{term}': Pages {matches[:10]}")
