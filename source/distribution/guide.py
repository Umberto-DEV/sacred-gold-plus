#!/usr/bin/env python3
"""Render four illustrated player PDFs; requires reportlab 4.4.9."""
import argparse
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                               Image, KeepTogether, Table, TableStyle)
from pack import config, install_text, guide_names

HERE = Path(__file__).resolve().parent
IMAGES = HERE.parents[1] / 'images'
INK = colors.HexColor('#26343a')
TEAL = colors.HexColor('#16656b')
GOLD = colors.HexColor('#bc8d27')
PALE = colors.HexColor('#f8f3e7')
WIDTH = A4[0] - 88


def markup(text):
    lines = []
    for line in text.split('\n'):
        escaped = escape(line)
        escaped = re.sub(r'https://[^\s<>]+', lambda m: '<link href="' + m[0] + '" color="#16656b">' + m[0] + '</link>', escaped)
        if line.startswith('  '):
            escaped = '<font name="Courier" size="8">' + escaped.strip() + '</font>'
        lines.append(escaped)
    return '<br/>'.join(lines)


def styles():
    result = getSampleStyleSheet()
    result.add(ParagraphStyle(name='Text', fontName='Helvetica', fontSize=10.2,
                              leading=14.5, spaceAfter=10, textColor=INK))
    result.add(ParagraphStyle(name='Record', parent=result['Text'], fontName='Courier',
                              fontSize=8, leading=12, spaceAfter=11))
    result.add(ParagraphStyle(name='Caption', parent=result['Text'], fontSize=8.5,
                              leading=11, textColor=colors.HexColor('#617076')))
    result.add(ParagraphStyle(name='Label', parent=result['Text'], fontSize=9,
                              textColor=GOLD, spaceAfter=14, alignment=1))
    result['Title'].fontName = 'Helvetica-Bold'
    result['Title'].fontSize = 27
    result['Title'].leading = 32
    result['Title'].textColor = TEAL
    result['Title'].spaceAfter = 16
    result['Heading2'].fontName = 'Helvetica-Bold'
    result['Heading2'].textColor = TEAL
    result['Heading2'].spaceBefore = 12
    result['Heading2'].spaceAfter = 12
    result['Heading2'].keepWithNext = True
    return result


def paragraph(text, style):
    return Paragraph(markup(text), style)


def picture(name, width):
    shot = Image(str(IMAGES / name))
    shot.drawHeight *= width / shot.drawWidth
    shot.drawWidth = width
    shot.hAlign = 'CENTER'
    return shot


def callout(text, st):
    box = Table([[paragraph(text, st['Text'])]], colWidths=[WIDTH])
    box.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), PALE),
                             ('LINEBEFORE', (0, 0), (0, -1), 3, GOLD),
                             ('LEFTPADDING', (0, 0), (-1, -1), 13),
                             ('RIGHTPADDING', (0, 0), (-1, -1), 13),
                             ('TOPPADDING', (0, 0), (-1, -1), 10),
                             ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    return box


def folder_card(lang, cfg, st):
    names = guide_names(lang, cfg)
    rows = [[paragraph('Sacred Gold Plus ' + cfg['version'], st['Heading2']), '']]
    rows.extend([[paragraph(kind, st['Caption']), paragraph(name, st['Text'])]
                 for kind, name in [('PDF', names[0]), ('PDF', names[1]),
                                    ('DIR', 'Patch'), ('DIR', 'Manual'), ('DIR', 'Cheats')]])
    box = Table(rows, colWidths=[45, WIDTH-45])
    box.setStyle(TableStyle([('SPAN', (0, 0), (1, 0)),
                             ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#edf5f5')),
                             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                             ('LEFTPADDING', (0, 0), (-1, -1), 12),
                             ('TOPPADDING', (0, 0), (-1, -1), 4)]))
    return box


def render_document(path, story, label, st):
    if path.exists():
        raise FileExistsError(path)
    def frame(canvas, doc):
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(1)
        canvas.line(44, 39, A4[0]-44, 39)
        canvas.setFillColor(colors.HexColor('#617076'))
        canvas.setFont('Helvetica', 8)
        canvas.drawString(44, 25, 'SACRED GOLD PLUS 1.2.5  |  ' + label)
        canvas.drawRightString(A4[0]-44, 25, str(doc.page))
        if doc.page > 1:
            canvas.setFont('Helvetica-Bold', 8)
            canvas.setFillColor(GOLD)
            canvas.drawString(44, A4[1]-30, 'SACRED GOLD PLUS  /  1.2.5')
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=44, leftMargin=44,
                            topMargin=49, bottomMargin=53, invariant=1,
                            title='Sacred Gold Plus 1.2.5 - '+label,
                            author='Sacred Gold Plus contributors')
    doc.build(story, onFirstPage=frame, onLaterPages=frame)


def install_guide(output, lang, cfg):
    st = styles()
    name = guide_names(lang, cfg)[0]
    title = 'How to install 1.2.5' if lang == 'EN' else 'Come installare la 1.2.5'
    story = [paragraph('SACRED GOLD PLUS', st['Label']),
             picture('17-version-title-top.png', 285), Spacer(1, 16),
             paragraph(title, st['Title']),
             paragraph('WINDOWS + macOS  /  '+('ENGLISH EDITION' if lang == 'EN' else 'EDIZIONE ITALIANA'), st['Label'])]
    groups = install_text(lang, cfg).strip().split('\n\n')[1:]
    section = None
    body_count = 0
    for group in groups:
        heading = '\n' not in group and (group.isupper() or re.match(r'^[1-5]\. ', group))
        if heading:
            is_main = bool(re.match(r'^[1-5]\. ', group))
            starts_page = is_main or group.startswith(('REFERENCE A', 'RIFERIMENTO A',
                'TROUBLESHOOTING', 'RISOLUZIONE', 'OPTIONAL', 'FACOLTATIVO',
                'ABOUT THE OTHER', 'ALTRI FILE'))
            if starts_page:
                story.append(PageBreak())
            section = group[:1] if is_main else None
            body_count = 0
            story.append(paragraph(group, st['Heading2']))
            if section == '1':
                story.extend([folder_card(lang, cfg, st), Spacer(1, 15)])
            if section == '2':
                text = ('YOUR .nds  >  calculate SHA-256  >  match Reference A\nNEW .nds  >  calculate SHA-256  >  match Reference B' if lang == 'EN'
                        else 'IL TUO .nds  >  calcola SHA-256  >  confronta con A\nNUOVO .nds  >  calcola SHA-256  >  confronta con B')
                story.extend([callout(text, st), Spacer(1, 15)])
            continue
        body_count += 1
        if 'SHA-256: ' in group:
            story.append(KeepTogether([paragraph(group, st['Record'])]))
        elif group.startswith(('This ZIP always', 'Questo ZIP crea')):
            story.append(callout(group, st))
        else:
            story.append(paragraph(group, st['Text']))
        if section == '4' and body_count == 1:
            caption = ('ROM file = the starting .nds. Patch file = the one matching .xdelta.' if lang == 'EN'
                       else 'ROM file = il .nds iniziale. Patch file = il solo .xdelta corrispondente.')
            story.extend([picture('install-rom-patcher.jpg', 430), Spacer(1, 6),
                          paragraph(caption, st['Caption'])])
        if section == '4' and body_count == 2:
            caption = ('Settings: leave Fix ROM checksum OFF.\nReal Rom Patcher JS v3.5 captures, 27 October 2026. No ROM loaded; the file chooser uses the computer language.' if lang == 'EN'
                       else 'Settings: lascia Fix ROM checksum SPENTO.\nSchermate reali di Rom Patcher JS v3.5, 27 ottobre 2026. Nessuna ROM caricata; il pulsante file segue la lingua del computer.')
            box = Table([[picture('install-patcher-settings.jpg', 210), paragraph(caption, st['Caption'])]], colWidths=[230, WIDTH-230])
            box.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            story.extend([box, Spacer(1, 10)])
        if section == '5' and body_count == 1:
            caption = ('The version on the title screen helps you recognise the game. The complete output SHA-256 is the definitive file check.' if lang == 'EN'
                       else 'La versione nel titolo aiuta a riconoscere il gioco. Il controllo definitivo del file è lo SHA-256 completo del risultato.')
            box = Table([[picture('17-version-title-top.png', 205), paragraph(caption, st['Caption'])]], colWidths=[225, WIDTH-225])
            box.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
            story.extend([box, Spacer(1, 14)])
    render_document(output/name, story, 'INSTALL / '+lang, st)


def news_guide(output, lang, cfg):
    st = styles()
    text_name = 'NOVITA-1.2.5.txt' if lang == 'IT' else 'WHATS-NEW-1.2.5.txt'
    text = (HERE/'documents'/lang/text_name).read_text(encoding='utf-8')
    title = "What's New in 1.2.5" if lang == 'EN' else 'Novità della 1.2.5'
    story = [paragraph('SACRED GOLD PLUS', st['Label']),
             picture('17-version-title-top.png', 350), Spacer(1, 24),
             paragraph(title, st['Title']),
             paragraph('THE CURRENT GAME, AT A GLANCE' if lang == 'EN' else 'IL GIOCO ATTUALE, IN BREVE', st['Label'])]
    photographs = {
        '1': [('11-plus-options-english-bottom.png' if lang=='EN' else '12-plus-options-italian-bottom.png',
               'Options > SELECT > Plus' if lang=='EN' else 'Opzioni > SELECT > Plus')],
        '2': [('07-elms-lab.png', "Inside Professor Elm's lab" if lang=='EN' else 'Nel laboratorio del Prof. Elm'),
              ('18-goldenrod-city.png', 'Goldenrod City' if lang=='EN' else 'Fiordoropoli')],
        '3': [('13-ev-viewer-top.png', 'L: EV'), ('14-iv-viewer-top.png', 'R: IV')],
    }
    for group in text.strip().split('\n\n')[1:]:
        main = re.match(r'^([1-4])\. ', group) if '\n' not in group else None
        heading = '\n' not in group and (main or group.isupper())
        if heading:
            if main:
                story.append(PageBreak())
            story.append(paragraph(group, st['Heading2']))
            if main and main[1] in photographs:
                pics = photographs[main[1]]
                width = 260 if len(pics)==1 else 230
                cells = [[picture(filename, width), Spacer(1, 7), paragraph(caption, st['Caption'])]
                         for filename, caption in pics]
                box = Table([cells], colWidths=[WIDTH/len(cells)]*len(cells))
                box.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
                story.extend([box, Spacer(1, 14)])
        else:
            story.append(paragraph(group, st['Text']))
    render_document(output/guide_names(lang,cfg)[1], story, 'FEATURES / '+lang, st)


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    cfg = config()
    for lang in ('EN', 'IT'):
        install_guide(output, lang, cfg)
        news_guide(output, lang, cfg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    build(parser.parse_args().output)
