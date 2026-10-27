#!/usr/bin/env python3
import os
import re
import subprocess
import weasyprint

def build_pdf():
    # Read the Urdu markdown file
    md_path = 'docs/MASAR-CAPABILITIES-PAPER-URDU.md'
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Strip wrapper div if present
    md_clean = re.sub(r'<div dir="rtl"[^>]*>', '', md_content)
    md_clean = md_clean.replace('</div>', '')

    # Convert Markdown to HTML5 via pandoc
    p = subprocess.Popen(
        ['pandoc', '-f', 'markdown', '-t', 'html5'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    html_body, err = p.communicate(input=md_clean.encode('utf-8'))
    html_body = html_body.decode('utf-8')

    # Replace Metadata header with elegant publication box
    meta_pattern = r'<p><strong>مصنف:</strong>.*?<strong>مخاطبین:</strong>.*?</p>'
    meta_replacement = '''<div class="meta-container">
  <div class="meta-row"><strong>مصنف:</strong> مسار ریسرچ اینڈ ڈویلپمنٹ گروپ &nbsp; | &nbsp; <strong>تاریخِ اشاعت:</strong> ۲۰۲۶ء</div>
  <div class="meta-row"><strong>مخاطبین:</strong> علومِ اسلامیہ کے محققین، مؤرخین، ڈیجیٹل ہیومینٹیز کے ماہرین اور شائقینِ حدیث</div>
</div>'''
    html_body = re.sub(meta_pattern, meta_replacement, html_body, flags=re.DOTALL)

    # Replace <pre><code> diagrams with beautiful styled HTML cards
    # Diagram 1: Historical Takhrij
    d1_pattern = r'<pre><code>\s*تاریخی تخریج کا علمی سفر.*?</code></pre>'
    d1_replacement = '''<div class="diagram-card">
  <div class="diagram-title">تاریخی تخریج کا علمی سفر</div>
  <div class="main-node">مدینہ منورہ میں اصل واقعہ یا ارشادِ نبوی ﷺ</div>
  <div class="branch-connector">▼ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ▼</div>
  <div class="two-col">
    <div class="col-box">
      <div class="box-head">شام کی طرف منتقلی</div>
      <div class="box-sub">(الفاظ میں معمولی اختصار)</div>
      <div class="node-arrow">▼</div>
      <div class="pills-row">
        <span class="pill">کتاب الف (مکمل متن)</span>
        <span class="pill">کتاب ب (فقہی اقتباس)</span>
      </div>
    </div>
    <div class="col-box">
      <div class="box-head">عراق کی طرف منتقلی</div>
      <div class="box-sub">(روایت بالمعنیٰ / ہم معنی الفاظ)</div>
      <div class="node-arrow">▼</div>
      <div class="pills-row">
        <span class="pill">کتاب ج (سنی ذخیرہ)</span>
        <span class="pill">کتاب د (شیعی ذخیرہ)</span>
      </div>
    </div>
  </div>
  <div class="diagram-footer"><strong>تخریج کا ہدف:</strong> ان تمام بکھری ہوئی شاخوں کو تلاش کر کے ایک ہی اصل خاندان میں یکجا کرنا۔</div>
</div>'''
    html_body = re.sub(d1_pattern, d1_replacement, html_body, flags=re.DOTALL)

    # Diagram 2: Masar Architecture
    d2_pattern = r'<pre><code>\s*مسار کا علمی و تحقیقی نظام.*?</code></pre>'
    d2_replacement = '''<div class="diagram-card">
  <div class="diagram-title">مسار کا علمی و تحقیقی نظام</div>
  <div class="main-node">مطلوبہ کلام: حدیث کا متن، شناختی نمبر یا دستی نسخے کی عبارت</div>
  <div class="node-arrow">▼</div>
  <div class="flow-step step-blue">
    <div class="step-head">۱. چار رخی متوازن تلاش کا انجن</div>
    <div class="step-desc">ہو بہو الفاظ &bull; مشترک فقرے &bull; مجموعی مفہوم &bull; مشترک اساتذہ اور اسنادی کڑیاں</div>
  </div>
  <div class="node-arrow">▼</div>
  <div class="flow-step step-green">
    <div class="step-head">۲. شفاف اور مدلل نتائج (Explainability Receipts)</div>
    <div class="step-desc">بلند درجے کی متوازی روایات &bull; مقطوعہ فقہی ٹکڑوں کی پہچان &bull; موضوعاتی دھوکے کی چھان بین</div>
  </div>
  <div class="node-arrow">▼</div>
  <div class="flow-step step-amber">
    <div class="step-head">۳. درستی اور تدریجی ذخیرۂ علم (Accretive Flywheel)</div>
    <div class="step-desc">ایک کلک سے حد بندی کی درستی &bull; پائیدار کتب خانے (masar-curated.db) میں مستقل اندراج</div>
  </div>
  <div class="branch-connector">▼ &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; ▼</div>
  <div class="two-col">
    <div class="col-box outcome">
      <div class="box-head">خودمختارانہ استعمال</div>
      <div class="box-sub">مکمل تخریجی عمل اور تقابلِ الفاظ &bull; سنی و شیعی مصادر کی یکجا تلاش &bull; قلمی نسخوں کا اندراج</div>
    </div>
    <div class="col-box outcome">
      <div class="box-head">"رواق" کے لیے بنیادی سرچشمہ</div>
      <div class="box-sub">بے عیب اور تصدیق شدہ ڈیٹا &bull; شجرۂ اسناد (ICMA) کے لیے کڑے تصدیقی دربان</div>
    </div>
  </div>
</div>'''
    html_body = re.sub(d2_pattern, d2_replacement, html_body, flags=re.DOTALL)

    # Diagram 3: Two Modes
    d3_pattern = r'<pre><code>\s*┌─.*?پہلا رخ.*?</code></pre>'
    d3_replacement = '''<div class="diagram-card">
  <div class="two-col">
    <div class="col-box bordered">
      <div class="box-head-big color-primary">پہلا رخ: آزادانہ اور خودمختار استعمال</div>
      <div class="box-intro">حدیث کے محققین کے لیے ایک مکمل ڈیسک ٹاپ ورک بینچ:</div>
      <ul class="box-list">
        <li>نو لاکھ سے زائد روایات میں جملہ طرق کی جامع تلاش</li>
        <li>غیر مطبوعہ یا قلمی نسخوں کی عبارات کا براہِ راست اندراج</li>
        <li>مختلف مکاتبِ فکر (سنی، شیعی، زیدی) کے ذخائر کی بیک وقت چھان بین</li>
        <li>الفاظ کے اضافے، کمی اور تبدیلی کا آمنے سامنے تقابلی جائزہ</li>
      </ul>
    </div>
    <div class="col-box bordered">
      <div class="box-head-big color-accent">دوسرا رخ: "رواق" کے لیے بنیادی سرچشمہ</div>
      <div class="box-intro">تاریخی شجرۂ اسناد اور متن کے تجزیے (ICMA) کے لیے دربان:</div>
      <ul class="box-list">
        <li>چار خودکار تصدیقی دربان جو ناقص ڈیٹا کا راستہ روکتے ہیں</li>
        <li>سند اور متن کی بے عیب تفریق کی پختہ ضمانت</li>
        <li>شجرۂ اسناد اور تاریخی ارتقاء کے تجزیے کے لیے صاف ستھرا خام مال</li>
        <li>رواق کے امپورٹ بیچ معیار (schema_version: 1) سے سو فیصد مطابقت</li>
      </ul>
    </div>
  </div>
</div>'''
    html_body = re.sub(d3_pattern, d3_replacement, html_body, flags=re.DOTALL)

    # Add page-break class before Section 8
    html_body = re.sub(r'<h2 id="حرف-آخر[^"]*">', r'<div class="page-break"></div>\n\g<0>', html_body)

    full_html = f'''<!DOCTYPE html>
<html dir="rtl" lang="ur">
<head>
<meta charset="utf-8">
<title>حافظہ اور منہج کا سنگم: روایاتِ حدیث کے پیچیدہ تانے بانے کو سلجھانے میں مسار (Masar) کا کردار</title>
<style>
@page {{
    size: A4 portrait;
    margin: 22mm 18mm 22mm 18mm;
    @top-right {{
        content: "مسار (Masar) — مقالۂ تعارف و تحقیقی صلاحیت";
        font-family: 'Jameel Noori Nastaleeq';
        font-size: 11pt;
        color: #64748b;
        direction: rtl;
        border-bottom: 0.5px solid #cbd5e1;
        padding-bottom: 3px;
    }}
    @bottom-center {{
        content: counter(page);
        font-family: 'Jameel Noori Nastaleeq';
        font-size: 12pt;
        color: #475569;
    }}
}}

@font-face {{
    font-family: 'Jameel Noori Nastaleeq';
    src: url('file:///usr/local/share/fonts/j/Jameel_Noori_Nastaleeq.ttf') format('truetype');
}}

body {{
    font-family: 'Jameel Noori Nastaleeq', serif;
    font-size: 14pt;
    line-height: 2.15;
    color: #1e293b;
    direction: rtl;
    text-align: justify;
    orphans: 3;
    widows: 3;
}}

h1 {{
    font-size: 21pt;
    line-height: 1.7;
    color: #0f172a;
    text-align: center;
    margin-top: 5px;
    margin-bottom: 12px;
}}

.meta-container {{
    text-align: center;
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 10px 16px;
    margin: 0 auto 18px auto;
    font-size: 12.5pt;
    line-height: 1.9;
    color: #334155;
}}

.meta-row {{
    margin: 2px 0;
}}

h2 {{
    font-size: 17pt;
    color: #1e3a8a;
    border-bottom: 1.5px solid #cbd5e1;
    padding-bottom: 4px;
    margin-top: 22px;
    margin-bottom: 10px;
    page-break-after: avoid;
    break-after: avoid;
}}

h3 {{
    font-size: 15pt;
    color: #1e40af;
    margin-top: 15px;
    margin-bottom: 6px;
    page-break-after: avoid;
    break-after: avoid;
}}

p {{
    margin-top: 0;
    margin-bottom: 10px;
}}

strong {{
    color: #0f172a;
}}

.page-break {{
    page-break-before: always;
    break-before: page;
}}

/* Table styling */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 12.5pt;
    page-break-inside: avoid;
    break-inside: avoid;
}}

th {{
    background-color: #1e3a8a;
    color: #ffffff;
    padding: 8px 10px;
    border: 1px solid #1e3a8a;
    text-align: right;
    font-weight: normal;
    font-size: 13pt;
}}

td {{
    padding: 7px 10px;
    border: 1px solid #cbd5e1;
    text-align: right;
    line-height: 1.9;
}}

tr:nth-child(even) {{
    background-color: #f8fafc;
}}

/* Elegant Diagram Cards */
.diagram-card {{
    background: #f8fafc;
    border: 1.5px solid #cbd5e1;
    border-radius: 10px;
    padding: 12px 14px;
    margin: 16px 0;
    text-align: center;
    page-break-inside: avoid;
    break-inside: avoid;
}}

.diagram-title {{
    font-size: 15pt;
    font-weight: bold;
    color: #1e3a8a;
    margin-bottom: 6px;
    border-bottom: 1px dashed #cbd5e1;
    padding-bottom: 4px;
}}

.main-node {{
    display: inline-block;
    background: #ffffff;
    border: 1.5px solid #3b82f6;
    border-radius: 6px;
    padding: 3px 14px;
    font-size: 13pt;
    color: #1e3a8a;
    margin: 3px auto;
}}

.node-arrow {{
    font-size: 10pt;
    color: #64748b;
    margin: 2px 0;
    line-height: 1.2;
}}

.branch-connector {{
    font-size: 9.5pt;
    color: #64748b;
    margin: 2px 0;
    line-height: 1.2;
    text-align: center;
}}

.two-col {{
    display: flex;
    justify-content: space-between;
    gap: 10px;
    margin: 6px 0;
    direction: rtl;
}}

.col-box {{
    flex: 1;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 10px;
    text-align: center;
}}

.col-box.bordered {{
    border: 1.5px solid #cbd5e1;
    padding: 10px;
    text-align: right;
}}

.col-box.outcome {{
    border-top: 3px solid #10b981;
}}

.box-head {{
    font-size: 13.5pt;
    font-weight: bold;
    color: #1e3a8a;
}}

.box-head-big {{
    font-size: 14pt;
    font-weight: bold;
    margin-bottom: 4px;
}}

.color-primary {{
    color: #1e3a8a;
    border-bottom: 1px solid #93c5fd;
    padding-bottom: 2px;
}}

.color-accent {{
    color: #047857;
    border-bottom: 1px solid #6ee7b7;
    padding-bottom: 2px;
}}

.box-intro {{
    font-size: 12pt;
    color: #475569;
    margin-bottom: 4px;
    line-height: 1.6;
}}

.box-sub {{
    font-size: 11.5pt;
    color: #64748b;
    margin-top: 2px;
}}

.box-list {{
    margin: 4px 14px 4px 10px;
    padding: 0;
    font-size: 11.5pt;
    line-height: 1.7;
}}

.box-list li {{
    margin-bottom: 2px;
}}

.pills-row {{
    display: flex;
    justify-content: center;
    gap: 6px;
    margin-top: 4px;
}}

.pill {{
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 11pt;
    color: #334155;
}}

.diagram-footer {{
    margin-top: 6px;
    padding-top: 5px;
    border-top: 1px dashed #cbd5e1;
    font-size: 12pt;
    color: #334155;
}}

.flow-step {{
    background: #ffffff;
    border-radius: 6px;
    padding: 5px 12px;
    margin: 3px auto;
    width: 90%;
}}

.step-blue {{
    border: 1px solid #93c5fd;
    border-right: 4px solid #2563eb;
}}

.step-green {{
    border: 1px solid #a7f3d0;
    border-right: 4px solid #059669;
}}

.step-amber {{
    border: 1px solid #fde68a;
    border-right: 4px solid #d97706;
}}

.step-head {{
    font-size: 13.5pt;
    font-weight: bold;
    color: #0f172a;
}}

.step-desc {{
    font-size: 11.5pt;
    color: #475569;
}}

hr {{
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 16px 0;
}}
</style>
</head>
<body>
{html_body}
</body>
</html>'''

    output_html = 'docs/MASAR-CAPABILITIES-PAPER-URDU.html'
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(full_html)

    output_pdf = 'docs/MASAR-CAPABILITIES-PAPER-URDU.pdf'
    weasyprint.HTML(output_html).write_pdf(output_pdf)
    print(f"Successfully generated {output_pdf}")

if __name__ == '__main__':
    build_pdf()
