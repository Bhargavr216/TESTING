# -*- coding: utf-8 -*-
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def escape(text):
    return text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

doc = SimpleDocTemplate('TECH_NARRATIVE.pdf', pagesize=letter,
                        leftMargin=0.75*inch,rightMargin=0.75*inch,
                        topMargin=0.75*inch,bottomMargin=0.75*inch)
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='CustomCode', fontName='Courier', fontSize=9, leading=12, leftIndent=12))
styles.add(ParagraphStyle(name='CustomBullet', leftIndent=12, bulletIndent=6, bulletFontName='Helvetica', bulletFontSize=10, leading=14))

story = []
with open('TECH_NARRATIVE.md', encoding='utf-8') as f:
    lines = f.readlines()

in_code = False
for raw in lines:
    line = raw.rstrip('\n')
    stripped = line.strip()
    if stripped.startswith('```'):
        in_code = not in_code
        continue
    if in_code:
        if stripped == '':
            story.append(Spacer(1, 0.08*inch))
        else:
            story.append(Paragraph(escape(line), styles['CustomCode']))
        continue
    if not stripped:
        story.append(Spacer(1, 0.08*inch))
        continue
    if stripped.startswith('### '):
        story.append(Paragraph(escape(stripped[4:]), styles['Heading3']))
    elif stripped.startswith('## '):
        story.append(Paragraph(escape(stripped[3:]), styles['Heading2']))
    elif stripped.startswith('# '):
        story.append(Paragraph(escape(stripped[2:]), styles['Heading1']))
    elif stripped.startswith('- '):
        story.append(Paragraph(escape(stripped[2:]), styles['CustomBullet'], bulletText='•'))
    elif stripped[0].isdigit() and len(stripped) > 1 and stripped[1] == '.':
        story.append(Paragraph(escape(stripped), styles['CustomBullet'], bulletText='•'))
    else:
        story.append(Paragraph(escape(stripped), styles['Normal']))
story.append(Spacer(1, 0.2*inch))
doc.build(story)
