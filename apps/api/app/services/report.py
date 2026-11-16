import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime

def generate_pdf_forensic_report(analysis_data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )
    story.append(Paragraph("MINO Forensic Media Analysis Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", styles['Normal']))
    story.append(Spacer(1, 15))

    # Disclaimer banner
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#B45309'),
        backColor=colors.HexColor('#FEF3C7'),
        borderPadding=6,
        spaceAfter=15
    )
    story.append(Paragraph(
        "<b>CRITICAL FORENSIC DISCLAIMER:</b> MINO is a probabilistic deepfake screening tool. "
        "Estimated likelihood scores reflect model confidence on detected facial artifacts. "
        "This document is an investigative screening aid and does not constitute absolute proof of authenticity.",
        disclaimer_style
    ))

    # Metadata Table
    res = analysis_data.get("result", {})
    pred_class = res.get("predicted_class", "INCONCLUSIVE")
    score = res.get("manipulation_score", 0.0)

    summary_data = [
        ["Job Identifier:", str(analysis_data.get("id"))],
        ["Status:", str(analysis_data.get("status"))],
        ["Media Asset ID:", str(analysis_data.get("media_asset_id"))],
        ["Task Type:", str(analysis_data.get("task_type"))],
        ["Estimated Manipulation Score:", f"{score:.4f} (Scale: 0.0000 - 1.0000)"],
        ["Classification:", pred_class],
        ["Decision Thresholds:", f"Authentic ≤ {res.get('threshold_low', 0.35)} | Manipulated ≥ {res.get('threshold_high', 0.65)}"],
        ["Aggregation Policy:", str(res.get("aggregation_method"))],
        ["Sampled / Valid Frames:", f"{res.get('valid_frame_count')} / {res.get('face_frame_count')} face frames"],
        ["C2PA Provenance Status:", str(res.get("provenance_status"))]
    ]

    t = Table(summary_data, colWidths=[180, 350])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1E293B')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Methodology Summary
    story.append(Paragraph("<b>Analysis Summary & Findings:</b>", styles['Heading3']))
    summary_text = res.get("result_summary") or "Standard automated convolutional feature inspection executed."
    story.append(Paragraph(summary_text, styles['Normal']))

    doc.build(story)
    return buffer.getvalue()
