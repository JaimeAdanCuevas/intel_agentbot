from jinja2 import Environment, FileSystemLoader
import pdfkit

def generate_html_report(report: dict, output_path: Path):
    env = Environment(loader=FileSystemLoader('reports/templates'))
    template = env.get_template('html_report.j2')
    html = template.render(**report)
    
    with open(output_path, 'w') as f:
        f.write(html)

def generate_pdf_report(report: dict, output_path: Path):
    html_path = output_path.with_suffix('.html')
    generate_html_report(report, html_path)
    pdfkit.from_file(html_path, output_path)
