"""Восстановить локальные статьи по версиям и SHA-256 из library/catalog.csv."""
from pathlib import Path
import csv
import hashlib
import urllib.request
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
for row in csv.DictReader((ROOT/'library/catalog.csv').open(encoding='utf-8')):
    pdf=ROOT/row['pdf_file']; txt=ROOT/row['text_file']
    if not pdf.exists():
        with urllib.request.urlopen(row['pdf_url'],timeout=60) as response:
            data=response.read()
        if hashlib.sha256(data).hexdigest()!=row['pdf_sha256']:
            raise ValueError(f"PDF {row['source_id']}: SHA-256 не совпадает с каталогом")
        pdf.write_bytes(data)
    if hashlib.sha256(pdf.read_bytes()).hexdigest()!=row['pdf_sha256']:
        raise ValueError(f"PDF {row['source_id']} изменён")
    if txt.exists() and hashlib.sha256(txt.read_bytes()).hexdigest()==row['text_sha256']:
        print(row['source_id'], 'PDF и текст совпадают с каталогом')
        continue
    reader=PdfReader(pdf)
    if len(reader.pages)!=int(row['pdf_pages']):
        raise ValueError(f"{row['source_id']}: изменилось число страниц")
    text='\n\n'.join(f'[с. {i}]\n'+(page.extract_text() or '') for i,page in enumerate(reader.pages,1))+'\n'
    if hashlib.sha256(text.encode()).hexdigest()!=row['text_sha256']:
        raise ValueError(f"{row['source_id']}: результат извлечения текста отличается; проверьте версию pypdf")
    txt.write_text(text,encoding='utf-8')
    print(row['source_id'], 'восстановлен')
