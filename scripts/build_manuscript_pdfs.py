#!/usr/bin/env python3
"""
build_manuscript_pdfs.py

Compiles high-precision, publication-grade academic PDFs from English and Urdu
Markdown files for the Al-Jassāsah study using Pandoc and WeasyPrint.

Typographic Specifications:
- Urdu Text: Alvi Nastaleeq (fallback: Jameel Noori Nastaleeq, serif)
- Arabic Words / Sentences: Amiri (Regular, Bold, Italic)
- English Body: Aptos Serif (fallback: Liberation Serif, DejaVu Serif, serif)
"""

import os
import re
import sys
import subprocess
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
JASSASA_DIR = REPO_ROOT / "jassasa"
EN_MD = JASSASA_DIR / "jassasah-academic-article.md"
EN_PDF = JASSASA_DIR / "jassasah-academic-article.pdf"
UR_MD = JASSASA_DIR / "jassasah-academic-article-urdu.md"
UR_PDF = JASSASA_DIR / "jassasah-academic-article-urdu.pdf"

WEASYPRINT_BIN = "/home/meer/.local/bin/weasyprint"

# Font paths
ALVI_FONT_PATH = "file:///home/meer/.local/share/fonts/alvi/Alvi_Nastaleeq.ttf"
AMIRI_REGULAR = "file:///usr/local/share/fonts/a/Amiri_Regular.ttf"
AMIRI_BOLD = "file:///usr/local/share/fonts/a/Amiri_Bold.ttf"
AMIRI_ITALIC = "file:///usr/local/share/fonts/a/Amiri_Italic.ttf"
AMIRI_BOLD_ITALIC = "file:///usr/local/share/fonts/a/Amiri_BoldItalic.ttf"
APTOS_SERIF_REG = "file:///usr/local/share/fonts/a/Aptos_Serif.ttf"
APTOS_SERIF_BOLD = "file:///usr/local/share/fonts/a/Aptos_Serif_Bold.ttf"
APTOS_SERIF_ITALIC = "file:///usr/local/share/fonts/a/Aptos_Serif_Italic.ttf"
APTOS_SERIF_BI = "file:///usr/local/share/fonts/a/Aptos_Serif_Bold_Italic.ttf"


def clean_math_markdown(text: str, is_urdu: bool = False) -> str:
    r"""
    Cleans inline math expressions like $P_1 \dots P_7$ into clean Unicode / HTML,
    preventing MathML bidi artifacts and duplicate annotation text.
    """
    # Replace arrow math
    text = text.replace(r"$\to$", "→")
    text = text.replace(r"\to", "→")

    # Replace pericope formulas
    if is_urdu:
        text = text.replace(r"$P_1 \dots P_7$", '<span class="latin" dir="ltr">P₁ … P₇</span>')
        text = text.replace(r"$P_1$", '<span class="latin" dir="ltr">P₁</span>')
        text = text.replace(r"$P_2$", '<span class="latin" dir="ltr">P₂</span>')
        text = text.replace(r"$P_3$", '<span class="latin" dir="ltr">P₃</span>')
        text = text.replace(r"$P_4$", '<span class="latin" dir="ltr">P₄</span>')
        text = text.replace(r"$P_5$", '<span class="latin" dir="ltr">P₅</span>')
        text = text.replace(r"$P_6$", '<span class="latin" dir="ltr">P₆</span>')
        text = text.replace(r"$P_7$", '<span class="latin" dir="ltr">P₇</span>')
        text = text.replace(r"$A = \sum \text{len}(P_i) / \text{len}(\text{Pericope Universe})$", 
                            '<span class="latin" dir="ltr">A = ∑ len(Pᵢ) / len(Pericope Universe)</span>')
    else:
        text = text.replace(r"$P_1 \dots P_7$", "<em>P</em>₁ … <em>P</em>₇")
        text = text.replace(r"$P_1$", "<em>P</em>₁")
        text = text.replace(r"$P_2$", "<em>P</em>₂")
        text = text.replace(r"$P_3$", "<em>P</em>₃")
        text = text.replace(r"$P_4$", "<em>P</em>₄")
        text = text.replace(r"$P_5$", "<em>P</em>₅")
        text = text.replace(r"$P_6$", "<em>P</em>₆")
        text = text.replace(r"$P_7$", "<em>P</em>₇")
        text = text.replace(r"$A = \sum \text{len}(P_i) / \text{len}(\text{Pericope Universe})$", 
                            "<em>A</em> = ∑ len(<em>P</em><sub><em>i</em></sub>) / len(Pericope Universe)")

    return text


def run_pandoc(md_text: str) -> str:
    """Converts Markdown text to HTML5 using pandoc."""
    p = subprocess.Popen(
        ["pandoc", "-f", "markdown", "-t", "html5"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = p.communicate(input=md_text.encode("utf-8"))
    if p.returncode != 0:
        raise RuntimeError(f"Pandoc error: {stderr.decode('utf-8')}")
    return stdout.decode("utf-8")


def wrap_arabic_in_english_html(html: str) -> str:
    """
    Wraps all Arabic script sequences in English text with <span class="arabic" dir="rtl">...</span>
    Ensures that every Arabic word, quote, and sentence uses the Amiri font.
    """
    arabic_pattern = re.compile(
        r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]'
        r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\s\u060c\u061f\u061b\u0640«»"“”\(\)]*'
        r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF])'
    )
    
    tokens = re.split(r'(<[^>]+>)', html)
    for i in range(len(tokens)):
        if not tokens[i].startswith('<'):
            tokens[i] = arabic_pattern.sub(r'<span class="arabic" dir="rtl">\1</span>', tokens[i])
    return "".join(tokens)


def wrap_arabic_in_urdu_html(html: str) -> str:
    """
    In Urdu text, wraps Arabic Hadith quotes (enclosed in «...»), classical quotes,
    and specific Arabic matn terms in Table 1 & Table 2 with <span class="arabic" lang="ar" dir="rtl">...</span>
    so that all Arabic words and sentences strictly render in Amiri.
    """
    # 1. Anything inside guillemets «...»
    def replace_guillemets(match):
        content = match.group(1)
        return f'«<span class="arabic" lang="ar" dir="rtl">{content}</span>»'
    
    html = re.sub(r'«([^»]+)»', replace_guillemets, html)
    
    # 2. Specific Arabic quotes and phrases
    arabic_sayings = [
        r'ما كتبت سوداء في بيضاء قط[^\*<]*',
        r'ثَلاَثِينَ رَجُلاً مِنْ لَخْمٍ وَجُذَامَ',
        r'إن بني عم لتميم الداري ركبوا في البحر',
        r'أن بني عم له ركبوا البحر',
        r'ركب ناس من بني عم لتميم الداري',
        r'ابن عم لتميم',
        r'دابة أهلب كثير الشعر',
        r'بامرأة تجر شعرها',
        r'جارية تجر شعرها',
        r'رجل كبير أهلكه الغم',
        r'هل ظهر على فارس؟',
        r'دابة أهلب',
        r'أهلكه الغم',
        r'الجسّاس',
        r'بنو عم',
        r'دابة',
        r'امراة',
        r'ابن عم',
        r'جاریۃ',
    ]
    for saying in arabic_sayings:
        pattern = re.compile(rf'(?<!class="arabic" lang="ar" dir="rtl">)(?<!class="arabic">)({saying})')
        html = pattern.sub(r'<span class="arabic" lang="ar" dir="rtl">\1</span>', html)
        
    return html


def build_english_pdf():
    print(f"Reading English Markdown: {EN_MD}...")
    with open(EN_MD, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Clean inline math before conversion
    md_text = clean_math_markdown(md_text, is_urdu=False)

    # Convert to HTML via pandoc
    html_body = run_pandoc(md_text)

    # Wrap Arabic phrases in Amiri
    html_body = wrap_arabic_in_english_html(html_body)

    # Enhance Metadata header into elegant academic card
    meta_pattern = r'<p>(<strong>(?:Author|Article type):</strong>.*?)</p>'
    def meta_repl(m):
        raw = m.group(1)
        lines = [line.strip() for line in raw.split('<br />') if line.strip()]
        if not lines:
            lines = [line.strip() for line in raw.split('\n') if line.strip()]
        meta_html = '<div class="article-meta-box">\n'
        for line in lines:
            meta_html += f'  <div class="meta-line">{line}</div>\n'
        meta_html += '</div>\n'
        return meta_html
    html_body = re.sub(meta_pattern, meta_repl, html_body, flags=re.DOTALL)

    # Style Abstract
    html_body = re.sub(
        r'<h2 id="abstract">Abstract</h2>\s*<p>(.*?)</p>',
        r'<div class="abstract-box"><div class="abstract-title">Abstract</div><p class="abstract-text">\1</p></div>',
        html_body,
        flags=re.DOTALL
    )

    # Make Table 1 avoid breaking inside
    html_body = html_body.replace(
        '<h3 id="table-1-cross-branch-attestation-of-the-kinsmen-voyage',
        '<div class="table1-container"><h3 id="table-1-cross-branch-attestation-of-the-kinsmen-voyage'
    )
    # Close container after table 1
    html_body = re.sub(
        r'(<div class="table1-container">.*?</table>)',
        r'\1</div>',
        html_body,
        flags=re.DOTALL
    )

    # Style AI Disclosure and Note of Caution as callout cards
    html_body = re.sub(
        r'<h2 id="ai-use-disclosure">AI Use Disclosure</h2>\s*<p>(.*?)</p>',
        r'<div class="callout-card ai-disclosure"><div class="callout-title">AI Use Disclosure</div><p>\1</p></div>',
        html_body,
        flags=re.DOTALL
    )

    html_body = re.sub(
        r'<h2 id="note-of-caution-and-methodological-disclaimer">Note of Caution and Methodological Disclaimer</h2>\s*<p>(.*?)</p>\s*<p>(.*?)</p>',
        r'<div class="callout-card disclaimer"><div class="callout-title">Note of Caution and Methodological Disclaimer</div><p>\1</p><p>\2</p></div>',
        html_body,
        flags=re.DOTALL
    )

    # Wrap Table 2 in a dedicated landscape section for perfect readability
    t2_heading = '<h3 id="table-2-pericope-alignment-and-witness-attestation-matrix'
    if t2_heading in html_body:
        parts = html_body.split(t2_heading, 1)
        # Find end of table 2 and its footnote
        t2_rest = parts[1]
        t2_end_marker = "This automated segmentation enables combinations"
        if t2_end_marker in t2_rest:
            t2_table_part, after_t2 = t2_rest.split(t2_end_marker, 1)
            html_body = (
                parts[0]
                + '<div class="landscape-section">'
                + t2_heading
                + t2_table_part
                + '</div>'
                + t2_end_marker
                + after_t2
            )

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Transmission, Narrative Variation, and the Limits of Reconstruction: An Isnād-cum-Matn Study of the Ḥadīth of al-Jassāsah</title>
<style>
@page {{
    size: A4 portrait;
    margin: 20mm 18mm 22mm 18mm;
    @top-right {{
        content: "Transmission, Narrative Variation, and Limits of Reconstruction: The Ḥadīth of al-Jassāsah";
        font-family: 'Aptos Serif', 'Liberation Serif', serif;
        font-size: 8.5pt;
        color: #64748b;
        font-style: italic;
        border-bottom: 0.5px solid #cbd5e1;
        padding-bottom: 4px;
    }}
    @bottom-center {{
        content: counter(page) " / " counter(pages);
        font-family: 'Aptos Serif', 'Liberation Serif', serif;
        font-size: 9pt;
        color: #64748b;
    }}
}}

@page:first {{
    @top-right {{
        content: normal;
    }}
}}

@page landscape-page {{
    size: A4 landscape;
    margin: 14mm 14mm 16mm 14mm;
    @top-right {{
        content: "Table 2: Pericope Alignment and Witness Attestation Matrix (P₁ … P₇)";
        font-family: 'Aptos Serif', 'Liberation Serif', serif;
        font-size: 8.5pt;
        color: #64748b;
        font-style: italic;
        border-bottom: 0.5px solid #cbd5e1;
        padding-bottom: 4px;
    }}
    @bottom-center {{
        content: counter(page) " / " counter(pages);
        font-family: 'Aptos Serif', 'Liberation Serif', serif;
        font-size: 8.5pt;
        color: #64748b;
    }}
}}

.landscape-section {{
    page: landscape-page;
    page-break-before: always;
    page-break-after: always;
}}

@font-face {{
    font-family: 'Amiri';
    src: url('{AMIRI_REGULAR}') format('truetype');
    font-weight: normal;
    font-style: normal;
}}
@font-face {{
    font-family: 'Amiri';
    src: url('{AMIRI_BOLD}') format('truetype');
    font-weight: bold;
    font-style: normal;
}}
@font-face {{
    font-family: 'Amiri';
    src: url('{AMIRI_ITALIC}') format('truetype');
    font-weight: normal;
    font-style: italic;
}}
@font-face {{
    font-family: 'Amiri';
    src: url('{AMIRI_BOLD_ITALIC}') format('truetype');
    font-weight: bold;
    font-style: italic;
}}

@font-face {{
    font-family: 'Aptos Serif';
    src: url('{APTOS_SERIF_REG}') format('truetype');
    font-weight: normal;
    font-style: normal;
}}
@font-face {{
    font-family: 'Aptos Serif';
    src: url('{APTOS_SERIF_BOLD}') format('truetype');
    font-weight: bold;
    font-style: normal;
}}
@font-face {{
    font-family: 'Aptos Serif';
    src: url('{APTOS_SERIF_ITALIC}') format('truetype');
    font-weight: normal;
    font-style: italic;
}}
@font-face {{
    font-family: 'Aptos Serif';
    src: url('{APTOS_SERIF_BI}') format('truetype');
    font-weight: bold;
    font-style: italic;
}}

body {{
    font-family: 'Aptos Serif', 'Liberation Serif', 'DejaVu Serif', serif;
    font-size: 9.8pt;
    line-height: 1.55;
    color: #1e293b;
    text-align: justify;
    orphans: 3;
    widows: 3;
}}

.arabic {{
    font-family: 'Amiri', serif !important;
    font-size: 1.18em;
    font-weight: normal;
    color: #1e3a8a;
    direction: rtl;
}}

h1 {{
    font-size: 18pt;
    line-height: 1.35;
    color: #0f172a;
    text-align: center;
    margin-top: 5px;
    margin-bottom: 12px;
    font-weight: bold;
}}

.article-meta-box {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 8px 14px;
    margin: 0 auto 14px auto;
    font-size: 8.8pt;
    line-height: 1.5;
    color: #334155;
    text-align: center;
}}
.article-meta-box .meta-line {{
    margin: 2px 0;
}}

.abstract-box {{
    background: #f1f5f9;
    border-left: 4px solid #1e3a8a;
    border-radius: 0 6px 6px 0;
    padding: 10px 14px;
    margin: 14px 0 18px 0;
    page-break-inside: avoid;
}}
.abstract-title {{
    font-size: 9.8pt;
    font-weight: bold;
    color: #1e3a8a;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}}
.abstract-text {{
    font-size: 9.2pt;
    line-height: 1.5;
    color: #334155;
    margin: 0;
    font-style: italic;
}}

h2 {{
    font-size: 12.5pt;
    color: #1e3a8a;
    border-bottom: 1.2px solid #cbd5e1;
    padding-bottom: 3px;
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
    break-after: avoid;
}}

h3 {{
    font-size: 10.8pt;
    color: #1e40af;
    margin-top: 13px;
    margin-bottom: 5px;
    page-break-after: avoid;
    break-after: avoid;
}}

p {{
    margin-top: 0;
    margin-bottom: 8px;
}}

strong {{
    color: #0f172a;
}}

.table1-container {{
    page-break-inside: avoid;
    break-inside: avoid;
    margin: 14px 0;
}}

/* Tables */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 8.5pt;
    line-height: 1.35;
    page-break-inside: auto;
}}

thead {{
    display: table-header-group;
}}

tr {{
    page-break-inside: avoid;
    break-inside: avoid;
}}

th {{
    background-color: #1e3a8a;
    color: #ffffff;
    padding: 6px 8px;
    border: 1px solid #1e3a8a;
    text-align: left;
    font-weight: bold;
    font-size: 8.5pt;
}}

td {{
    padding: 5px 8px;
    border: 1px solid #cbd5e1;
    text-align: left;
    vertical-align: top;
}}

tr:nth-child(even) {{
    background-color: #f8fafc;
}}

/* Landscape Table 2 specific */
.landscape-section table {{
    font-size: 8.8pt;
    line-height: 1.38;
}}
.landscape-section th {{
    font-size: 8.8pt;
    padding: 5px 6px;
}}
.landscape-section td {{
    padding: 4px 6px;
}}

/* Callouts */
.callout-card {{
    border-radius: 6px;
    padding: 10px 14px;
    margin: 14px 0;
    page-break-inside: avoid;
}}
.callout-card.ai-disclosure {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 4px solid #6366f1;
}}
.callout-card.disclaimer {{
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-left: 4px solid #d97706;
}}
.callout-title {{
    font-size: 10pt;
    font-weight: bold;
    margin-bottom: 4px;
}}
.ai-disclosure .callout-title {{
    color: #4338ca;
}}
.disclaimer .callout-title {{
    color: #b45309;
}}
.callout-card p {{
    font-size: 9pt;
    line-height: 1.48;
    color: #334155;
    margin-bottom: 6px;
}}
.callout-card p:last-child {{
    margin-bottom: 0;
}}

ol {{
    padding-left: 18px;
    margin-top: 4px;
    margin-bottom: 10px;
}}
ol li {{
    margin-bottom: 5px;
    line-height: 1.48;
    page-break-inside: avoid;
}}

code {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.2pt;
    background: #f1f5f9;
    padding: 1px 4px;
    border-radius: 3px;
    color: #0f172a;
}}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    html_out = JASSASA_DIR / "jassasah-academic-article.html"
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Wrote English HTML: {html_out}")

    print(f"Compiling PDF via WeasyPrint: {EN_PDF}...")
    subprocess.run([WEASYPRINT_BIN, str(html_out), str(EN_PDF)], check=True)
    print(f"Generated English PDF: {EN_PDF} ({EN_PDF.stat().st_size} bytes)")


def build_urdu_pdf():
    print(f"Reading Urdu Markdown: {UR_MD}...")
    with open(UR_MD, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Clean inline math before conversion
    md_text = clean_math_markdown(md_text, is_urdu=True)

    # Convert to HTML via pandoc
    html_body = run_pandoc(md_text)

    # Wrap Arabic phrases in Amiri
    html_body = wrap_arabic_in_urdu_html(html_body)

    # Enhance Metadata header into elegant academic card
    meta_pattern = r'<p>(<strong>(?:مصنف|مضمون کی نوعیت):</strong>.*?)</p>'
    def meta_repl(m):
        raw = m.group(1)
        lines = [line.strip() for line in raw.split('<br />') if line.strip()]
        if not lines:
            lines = [line.strip() for line in raw.split('\n') if line.strip()]
        meta_html = '<div class="article-meta-box-urdu">\n'
        for line in lines:
            meta_html += f'  <div class="meta-line">{line}</div>\n'
        meta_html += '</div>\n'
        return meta_html
    html_body = re.sub(meta_pattern, meta_repl, html_body, flags=re.DOTALL)

    # Style Abstract (خلاصہ)
    html_body = re.sub(
        r'<h2 id="خلاصہ">خلاصہ</h2>\s*<p>(.*?)</p>',
        r'<div class="abstract-box-urdu"><div class="abstract-title-urdu">خلاصۂ تحقیق</div><p class="abstract-text-urdu">\1</p></div>',
        html_body,
        flags=re.DOTALL
    )

    # Make Table 1 avoid breaking inside
    html_body = html_body.replace(
        '<h3 id="جدول-۱-عامر-شعبی-کے-تلامذہ-کے-مابین-رشتہ-داروں-کے-سفر',
        '<div class="table1-container-urdu"><h3 id="جدول-۱-عامر-شعبی-کے-تلامذہ-کے-مابین-رشتہ-داروں-کے-سفر'
    )
    html_body = re.sub(
        r'(<div class="table1-container-urdu">.*?</table>)',
        r'\1</div>',
        html_body,
        flags=re.DOTALL
    )

    # Style AI Disclosure and Note of Caution as callout cards
    html_body = re.sub(
        r'<h2 id="مصنوعی-ذہانت-کے-استعمال-کی-صراحت-ai-use-disclosure">مصنوعی ذہانت کے استعمال کی صراحت \(AI Use Disclosure\)</h2>\s*<p>(.*?)</p>',
        r'<div class="callout-card-urdu ai-disclosure-urdu"><div class="callout-title-urdu">مصنوعی ذہانت کے استعمال کی صراحت (AI Use Disclosure)</div><p>\1</p></div>',
        html_body,
        flags=re.DOTALL
    )

    html_body = re.sub(
        r'<h2 id="قارئین-کے-لیے-تنبیہ-اور-طریقہ-کار-کی-حدود-note-of-caution-and-methodological-disclaimer">قارئین کے لیے تنبیہ اور طریقہ کار کی حدود \(Note of Caution and Methodological Disclaimer\)</h2>\s*<p>(.*?)</p>\s*<p>(.*?)</p>',
        r'<div class="callout-card-urdu disclaimer-urdu"><div class="callout-title-urdu">قارئین کے لیے تنبیہ اور طریقہ کار کی حدود (Methodological Disclaimer)</div><p>\1</p><p>\2</p></div>',
        html_body,
        flags=re.DOTALL
    )

    # Wrap Table 2 in a dedicated landscape section for perfect readability
    t2_heading = '<h3 id="جدول-۲-بیس-روایات-پر-مشتمل-واقعاتی-تقسیم-کا-تقابلی-اشاریہ'
    if t2_heading in html_body:
        parts = html_body.split(t2_heading, 1)
        t2_rest = parts[1]
        t2_end_marker = "اس خودکار تقابل نے ثابت کیا کہ تمیم کے رشتہ داروں کی نسبت"
        if t2_end_marker in t2_rest:
            t2_table_part, after_t2 = t2_rest.split(t2_end_marker, 1)
            html_body = (
                parts[0]
                + '<div class="landscape-section-urdu">'
                + t2_heading
                + t2_table_part
                + '</div>'
                + t2_end_marker
                + after_t2
            )

    full_html = f"""<!DOCTYPE html>
<html lang="ur" dir="rtl">
<head>
<meta charset="utf-8">
<title>حدیثِ جسّاسہ کا اسناد و متون کی روشنی میں تحقیقی مطالعہ</title>
<style>
@page {{
    size: A4 portrait;
    margin: 22mm 18mm 25mm 18mm;
    @top-right {{
        content: "حدیثِ جسّاسہ کا اسناد و متون کی روشنی میں تحقیقی مطالعہ";
        font-family: 'Alvi Nastaleeq', 'Jameel Noori Nastaleeq', serif;
        font-size: 11pt;
        color: #64748b;
        direction: rtl;
        border-bottom: 0.5px solid #cbd5e1;
        padding-bottom: 3px;
    }}
    @bottom-center {{
        content: counter(page) " / " counter(pages);
        font-family: 'Aptos Serif', 'Liberation Serif', serif;
        font-size: 9.5pt;
        color: #64748b;
        direction: ltr;
    }}
}}

@page:first {{
    @top-right {{
        content: normal;
    }}
}}

@page landscape-page-urdu {{
    size: A4 landscape;
    margin: 14mm 14mm 16mm 14mm;
    @top-right {{
        content: "جدول ۲: بیس روایات پر مشتمل واقعاتی تقسیم کا تقابلی اشاریہ (P₁ … P₇)";
        font-family: 'Alvi Nastaleeq', 'Jameel Noori Nastaleeq', serif;
        font-size: 11pt;
        color: #64748b;
        direction: rtl;
        border-bottom: 0.5px solid #cbd5e1;
        padding-bottom: 3px;
    }}
    @bottom-center {{
        content: counter(page) " / " counter(pages);
        font-family: 'Aptos Serif', 'Liberation Serif', serif;
        font-size: 9pt;
        color: #64748b;
        direction: ltr;
    }}
}}

.landscape-section-urdu {{
    page: landscape-page-urdu;
    page-break-before: always;
    page-break-after: always;
}}

@font-face {{
    font-family: 'Alvi Nastaleeq';
    src: url('{ALVI_FONT_PATH}') format('truetype');
    font-weight: normal;
    font-style: normal;
}}

@font-face {{
    font-family: 'Amiri';
    src: url('{AMIRI_REGULAR}') format('truetype');
    font-weight: normal;
    font-style: normal;
}}
@font-face {{
    font-family: 'Amiri';
    src: url('{AMIRI_BOLD}') format('truetype');
    font-weight: bold;
    font-style: normal;
}}
@font-face {{
    font-family: 'Amiri';
    src: url('{AMIRI_ITALIC}') format('truetype');
    font-weight: normal;
    font-style: italic;
}}
@font-face {{
    font-family: 'Amiri';
    src: url('{AMIRI_BOLD_ITALIC}') format('truetype');
    font-weight: bold;
    font-style: italic;
}}

body {{
    font-family: 'Alvi Nastaleeq', 'Jameel Noori Nastaleeq', serif;
    font-size: 13.5pt;
    line-height: 2.18;
    color: #1e293b;
    direction: rtl;
    text-align: justify;
    orphans: 3;
    widows: 3;
}}

/* Arabic Text in Amiri */
.arabic {{
    font-family: 'Amiri', 'Traditional Arabic', serif !important;
    font-size: 1.25em;
    font-weight: normal;
    line-height: 1.5;
    color: #1e3a8a;
    direction: rtl;
}}

.latin {{
    font-family: 'Aptos Serif', 'Liberation Serif', serif;
    direction: ltr;
    unicode-bidi: embed;
    font-size: 0.95em;
}}

h1 {{
    font-size: 19pt;
    line-height: 1.8;
    color: #0f172a;
    text-align: center;
    margin-top: 5px;
    margin-bottom: 4px;
    font-weight: bold;
}}

.article-meta-box-urdu {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 14px;
    margin: 8px auto 16px auto;
    font-size: 11pt;
    line-height: 1.95;
    color: #334155;
    text-align: center;
}}
.article-meta-box-urdu .meta-line {{
    margin: 2px 0;
}}

.abstract-box-urdu {{
    background: #f1f5f9;
    border-right: 4px solid #1e3a8a;
    border-radius: 6px 0 0 6px;
    padding: 10px 14px;
    margin: 14px 0 18px 0;
    page-break-inside: avoid;
}}
.abstract-title-urdu {{
    font-size: 13pt;
    font-weight: bold;
    color: #1e3a8a;
    margin-bottom: 4px;
}}
.abstract-text-urdu {{
    font-size: 12.5pt;
    line-height: 2.1;
    color: #334155;
    margin: 0;
}}

h2 {{
    font-size: 15.5pt;
    line-height: 1.8;
    color: #1e3a8a;
    border-bottom: 1.5px solid #cbd5e1;
    padding-bottom: 3px;
    margin-top: 20px;
    margin-bottom: 8px;
    page-break-after: avoid;
    break-after: avoid;
}}

h3 {{
    font-size: 13.5pt;
    line-height: 1.7;
    color: #1e40af;
    margin-top: 14px;
    margin-bottom: 6px;
    page-break-after: avoid;
    break-after: avoid;
}}

p {{
    margin-top: 0;
    margin-bottom: 8px;
}}

strong {{
    color: #0f172a;
}}

.table1-container-urdu {{
    page-break-inside: avoid;
    break-inside: avoid;
    margin: 14px 0;
}}

/* Table Styling */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 10.5pt;
    line-height: 1.75;
    direction: rtl;
    page-break-inside: auto;
}}

thead {{
    display: table-header-group;
}}

tr {{
    page-break-inside: avoid;
    break-inside: avoid;
}}

th {{
    background-color: #1e3a8a;
    color: #ffffff;
    padding: 6px 8px;
    border: 1px solid #1e3a8a;
    text-align: right;
    font-weight: normal;
    font-size: 11pt;
}}

td {{
    padding: 5px 8px;
    border: 1px solid #cbd5e1;
    text-align: right;
    vertical-align: top;
}}

tr:nth-child(even) {{
    background-color: #f8fafc;
}}

/* Landscape Table 2 specific in Urdu */
.landscape-section-urdu table {{
    font-size: 10pt;
    line-height: 1.65;
}}
.landscape-section-urdu th {{
    font-size: 10.5pt;
    padding: 5px 6px;
}}
.landscape-section-urdu td {{
    padding: 4px 6px;
}}

/* Callouts in Urdu */
.callout-card-urdu {{
    border-radius: 8px;
    padding: 10px 14px;
    margin: 16px 0;
    page-break-inside: avoid;
}}
.callout-card-urdu.ai-disclosure-urdu {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-right: 4px solid #6366f1;
}}
.callout-card-urdu.disclaimer-urdu {{
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-right: 4px solid #d97706;
}}
.callout-title-urdu {{
    font-size: 13.5pt;
    font-weight: bold;
    margin-bottom: 4px;
}}
.ai-disclosure-urdu .callout-title-urdu {{
    color: #4338ca;
}}
.disclaimer-urdu .callout-title-urdu {{
    color: #b45309;
}}
.callout-card-urdu p {{
    font-size: 12.5pt;
    line-height: 2.1;
    color: #334155;
    margin-bottom: 6px;
}}
.callout-card-urdu p:last-child {{
    margin-bottom: 0;
}}

ol {{
    padding-right: 20px;
    margin-top: 4px;
    margin-bottom: 10px;
}}
ol li {{
    margin-bottom: 5px;
    line-height: 2.0;
    page-break-inside: avoid;
}}

code {{
    font-family: 'JetBrains Mono', 'Aptos Mono', monospace;
    font-size: 9.5pt;
    background: #f1f5f9;
    padding: 1px 4px;
    border-radius: 3px;
    color: #0f172a;
    direction: ltr;
    display: inline-block;
}}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    html_out = JASSASA_DIR / "jassasah-academic-article-urdu.html"
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Wrote Urdu HTML: {html_out}")

    print(f"Compiling PDF via WeasyPrint: {UR_PDF}...")
    subprocess.run([WEASYPRINT_BIN, str(html_out), str(UR_PDF)], check=True)
    print(f"Generated Urdu PDF: {UR_PDF} ({UR_PDF.stat().st_size} bytes)")


if __name__ == "__main__":
    build_english_pdf()
    build_urdu_pdf()
    print("ALL MANUSCRIPT PDFS BUILT AND REFINED SUCCESSFULLY!")
