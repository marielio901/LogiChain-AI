from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from utils.helpers import brl


def _draw_wrapped_text(c: canvas.Canvas, text: str, x: float, y: float, width: float, line_height: float = 13):
    words = (text or "").split()
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if c.stringWidth(candidate, "Helvetica", 10) <= width:
            line = candidate
        else:
            c.drawString(x, y, line)
            y -= line_height
            line = word
    if line:
        c.drawString(x, y, line)
        y -= line_height
    return y


def generate_contract_pdf(contract: dict) -> str:
    pdf_dir = Path("storage/pdfs")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    file_path = pdf_dir / f"{contract['contract_number']}_v{contract.get('version', 1)}.pdf"

    c = canvas.Canvas(str(file_path), pagesize=A4)
    width, height = A4

    y = height - 2 * cm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, y, "Contrato - LogiChain AI")
    y -= 1 * cm

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Número: {contract['contract_number']}")
    c.drawString(9 * cm, y, f"Tipo: {contract['type']}")
    c.drawString(14 * cm, y, f"Status: {contract['status']}")
    y -= 0.7 * cm
    c.drawString(2 * cm, y, f"Título: {contract['title']}")
    c.drawString(11 * cm, y, f"Departamento: {contract['department']}")
    y -= 0.8 * cm

    contractor = contract.get("contractor", {})
    contracted = contract.get("contracted", {})

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Partes")
    y -= 0.5 * cm
    c.setFont("Helvetica", 10)
    y = _draw_wrapped_text(c, f"Contratante: {contractor.get('name', '')} | Doc: {contractor.get('doc', '')} | Endereço: {contractor.get('address', '')}", 2 * cm, y, width - 4 * cm)
    y = _draw_wrapped_text(c, f"Contratado: {contracted.get('name', '')} | Doc: {contracted.get('doc', '')} | Endereço: {contracted.get('address', '')}", 2 * cm, y, width - 4 * cm)

    y -= 0.3 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Objeto e Escopo")
    y -= 0.5 * cm
    c.setFont("Helvetica", 10)
    y = _draw_wrapped_text(c, contract.get("scope_text", ""), 2 * cm, y, width - 4 * cm)

    y -= 0.3 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Cláusulas")
    y -= 0.5 * cm
    c.setFont("Helvetica", 10)
    y = _draw_wrapped_text(c, contract.get("clauses_text", ""), 2 * cm, y, width - 4 * cm)

    y -= 0.3 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Valores e Vigência")
    y -= 0.5 * cm
    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, y, f"Valor contratado: {brl(contract.get('contract_value', 0))}")
    c.drawString(9 * cm, y, f"Valor executado: {brl(contract.get('executed_value', 0))}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Início: {contract.get('start_date')} | Fim: {contract.get('end_date')}")

    y -= 0.9 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Assinaturas")
    y -= 1.2 * cm

    signatures = contract.get("signatures", {})
    c.setFont("Helvetica", 10)
    c.line(2 * cm, y, 8 * cm, y)
    c.drawString(2 * cm, y - 0.4 * cm, signatures.get("contractor_sign", "Contratante"))

    c.line(11 * cm, y, 17 * cm, y)
    c.drawString(11 * cm, y - 0.4 * cm, signatures.get("contracted_sign", "Contratado"))

    y -= 1.3 * cm
    witnesses = signatures.get("witnesses", "")
    if witnesses:
        c.drawString(2 * cm, y, f"Testemunhas: {witnesses}")

    c.showPage()
    c.save()
    return str(file_path)
