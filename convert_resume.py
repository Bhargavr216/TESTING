
from fpdf import FPDF

class ResumePDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(input_file, output_file):
    pdf = ResumePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        # Replace special characters that cause issues with latin-1
        line = line.replace('\u2013', '-').replace('\u2014', '-').replace('\u2019', "'")
        
        if not line:
            pdf.ln(5)
            continue
            
        # Headers
        if line.startswith('# '):
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, line[2:], ln=True)
            pdf.ln(2)
        elif line.startswith('## '):
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, line[3:], ln=True)
            pdf.ln(2)
        elif line.startswith('### '):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, line[4:], ln=True)
            pdf.ln(1)
        # Horizontal rule
        elif line == '---':
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)
        # Bullet points
        elif line.startswith('- '):
            pdf.set_font('Arial', '', 10)
            text = line[2:]
            text = text.replace('**', '')
            # Using simple bullet char
            pdf.multi_cell(0, 6, "* " + text)
        # Bold text lines
        elif line.startswith('**') and line.endswith('**'):
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 7, line.replace('**', ''), ln=True)
        # Links and standard text
        else:
            pdf.set_font('Arial', '', 10)
            text = line.replace('**', '').replace('*', '')
            pdf.multi_cell(0, 6, text)

    pdf.output(output_file)

if __name__ == "__main__":
    create_pdf('Updated_Resume.md', 'Updated_Resume.pdf')
    print("PDF created successfully: Updated_Resume.pdf")
