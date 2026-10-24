#!/usr/bin/env python3
"""Render the current player guide; requires reportlab 4.4.9 (release tooling only)."""
import argparse
from functools import partial
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak


def build(output):
    output.mkdir(parents=True,exist_ok=True)
    here=Path(__file__).resolve().parent
    for lang in ['IT','EN']:
        path=output/f'Guide-1.2.5-{lang}.pdf'
        if path.exists():raise FileExistsError(path)
        styles=getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Text',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=10,textColor=colors.HexColor('#203443')))
        styles['Title'].textColor=colors.HexColor('#173c49')
        stories=[]
        names=['NOVITA-1.2.5.txt','COME-INSTALLARE.txt'] if lang=='IT' else ['WHATS-NEW-1.2.5.txt','HOW-TO-INSTALL.txt']
        for idx,name in enumerate(names):
            text=(here/'documents'/lang/name).read_text()
            # Complete fingerprint catalogue is shipped as plain text and JSON.
            text=text.split('INGRESSI SUPPORTATI' if lang=='IT' else 'SUPPORTED INPUTS')[0]
            if idx:stories.append(PageBreak())
            sections=text.strip().split('\n\n')
            stories.append(Paragraph(escape(sections[0]),styles['Title']));stories.append(Spacer(1,14))
            for section in sections[1:]:stories.append(Paragraph(escape(section).replace('\n','<br/>'),styles['Text']))
            if idx:
                msg=('Le 21 impronte di ingresso e i relativi nomi delle patch sono in COME-INSTALLARE.txt e Patch/manifest.json. Scegli la corrispondenza esatta prima di applicare una patch.' if lang=='IT' else 'The 21 input fingerprints and matching patch names are in HOW-TO-INSTALL.txt and Patch/manifest.json. Match the exact fingerprint before applying a patch.')
                stories.append(Paragraph(msg,styles['Text']))
        def footer(canvas,doc):
            canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#546875'))
            canvas.drawString(42,26,'Sacred Gold Plus 1.2.5 | 24 October 2026')
            canvas.drawRightString(A4[0]-42,26,str(doc.page))
        doc=SimpleDocTemplate(str(path),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=38,bottomMargin=42,title='Sacred Gold Plus 1.2.5 - '+lang,author='Sacred Gold Plus contributors')
        doc.build(stories,onFirstPage=footer,onLaterPages=footer,canvasmaker=partial(Canvas,invariant=1))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);build(p.parse_args().output)
