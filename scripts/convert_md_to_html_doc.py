import re
import os

def convert_md_to_html_doc(md_path, doc_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Khai báo Header HTML với CSS tương thích MS Word
    html_header = """<html xmlns:o="urn:schemas-microsoft-com:office:office"
xmlns:w="urn:schemas-microsoft-com:office:word"
xmlns="http://www.w3.org/TR/REC-html40">
<head>
<meta charset="utf-8">
<title>Báo cáo Đồ án môn học CSDL Phân tán</title>
<!--[if gte mso 9]>
<xml>
<w:WordDocument>
<w:View>Print</w:View>
<w:Zoom>100</w:Zoom>
<w:DoNotOptimizeForBrowser/>
</w:WordDocument>
</xml>
<![endif]-->
<style>
@page {
    size: 21.0cm 29.7cm; /* A4 */
    margin-top: 2.0cm;
    margin-bottom: 2.0cm;
    margin-left: 3.0cm;
    margin-right: 2.0cm;
    mso-header-margin: 1.0cm;
    mso-footer-margin: 1.0cm;
}
body {
    font-family: "Times New Roman", Times, serif;
    font-size: 13.0pt;
    line-height: 1.5;
    text-align: justify;
    color: black;
}
h1 {
    font-size: 16.0pt;
    font-weight: bold;
    text-align: center;
    margin-top: 18.0pt;
    margin-bottom: 12.0pt;
    page-break-before: always;
    mso-line-height-rule: exactly;
    line-height: 1.5;
}
/* Trang bìa không ngắt trang ở đầu */
h1.title-first {
    page-break-before: avoid !important;
}
h2 {
    font-size: 14.0pt;
    font-weight: bold;
    margin-top: 12.0pt;
    margin-bottom: 6.0pt;
}
h3 {
    font-size: 13.0pt;
    font-weight: bold;
    margin-top: 6.0pt;
    margin-bottom: 4.0pt;
}
p {
    margin-top: 0cm;
    margin-bottom: 6.0pt;
    text-indent: 1.0cm; /* Thụt lề đầu dòng 1cm */
}
p.center {
    text-align: center;
    text-indent: 0cm;
}
p.no-indent {
    text-indent: 0cm;
}
ul, ol {
    margin-top: 0cm;
    margin-bottom: 6.0pt;
    padding-left: 20pt;
}
li {
    margin-bottom: 4.0pt;
    text-align: justify;
    text-indent: 0cm;
}
pre {
    font-family: "Courier New", Courier, monospace;
    font-size: 10.0pt;
    background-color: #F4F4F4;
    border: 1px solid #CCCCCC;
    padding: 6.0pt;
    margin-left: 1.0cm;
    white-space: pre-wrap;
    mso-line-height-rule: exactly;
    line-height: 1.15;
}
table {
    border-collapse: collapse;
    width: 100%%;
    margin-bottom: 12.0pt;
}
th, td {
    border: 1px solid black;
    padding: 6.0pt;
    text-align: left;
    font-size: 12.0pt;
}
th {
    background-color: #F2F2F2;
    font-weight: bold;
}
</style>
</head>
<body>
"""

    html_footer = """
</body>
</html>
"""

    # 2. Xử lý chuyển đổi Markdown sang HTML
    lines = content.split('\n')
    html_body = []
    
    in_code_block = False
    code_lines = []
    
    in_list = False
    
    is_first_h1 = True # Để đánh dấu h1 đầu tiên không bị ngắt trang
    
    for line in lines:
        line_strip = line.strip()
        
        # Xử lý code block
        if line_strip.startswith('```'):
            if in_code_block:
                in_code_block = False
                code_text = '\n'.join(code_lines)
                # Escaping HTML characters
                code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_body.append(f"<pre>{code_text}</pre>")
                code_lines = []
            else:
                in_code_block = True
            continue
            
        if in_code_block:
            code_lines.append(line)
            continue

        # Bỏ qua các dòng gạch ngang Markdown
        if line_strip == '---':
            continue
            
        # Đóng list nếu không còn phần tử danh sách
        if not (line_strip.startswith('* ') or line_strip.startswith('- ') or re.match(r'^\d+\.', line_strip)):
            if in_list:
                html_body.append("</ul>")
                in_list = False

        # Thao tác dòng trống
        if not line_strip:
            continue

        # Định dạng in đậm trong dòng
        def format_inline(text):
            # Convert **bold** to <strong>bold</strong>
            text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
            # Convert [text](link) to text
            text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
            return text

        # H1
        if line.startswith('# '):
            title = format_inline(line[2:].strip())
            if is_first_h1:
                html_body.append(f"<h1 class='title-first'>{title}</h1>")
                is_first_h1 = False
            else:
                html_body.append(f"<h1>{title}</h1>")
            continue

        # H2
        if line.startswith('## '):
            title = format_inline(line[3:].strip())
            html_body.append(f"<h2>{title}</h2>")
            continue

        # H3
        if line.startswith('### '):
            title = format_inline(line[4:].strip())
            html_body.append(f"<h3>{title}</h3>")
            continue

        # Bullet List
        if line_strip.startswith('* ') or line_strip.startswith('- '):
            if not in_list:
                html_body.append("<ul>")
                in_list = True
            item_text = format_inline(line_strip[2:].strip())
            html_body.append(f"<li>{item_text}</li>")
            continue

        # Bảng phân công (Xử lý các dòng bảng markdown | ... |)
        if line_strip.startswith('|'):
            # Đồ án đơn giản nên chúng ta có thể chuyển đổi bảng thô hoặc tạo bảng HTML thủ công
            # Để đơn giản, ta sẽ bọc văn bản bảng vào thẻ td
            parts = [p.strip() for p in line_strip.split('|')[1:-1]]
            if not parts:
                continue
            # Nếu là dòng gạch ngang phân cách bảng |---|---|
            if all(p.startswith('-') for p in parts):
                continue
            
            # Kiểm tra xem có phải là tiêu đề bảng (dòng đầu tiên chứa "MSSV", "HỌ VÀ TÊN", "NHIỆM VỤ")
            is_header = "MSSV" in parts or "NHIỆM VỤ" in parts or "STT" in parts
            row_html = "<tr>"
            for p in parts:
                p_fmt = format_inline(p)
                tag = "th" if is_header else "td"
                row_html += f"<{tag}>{p_fmt}</{tag}>"
            row_html += "</tr>"
            
            # Thêm table wrapper nếu chưa có
            if len(html_body) > 0 and not html_body[-1].endswith("</tr>") and not html_body[-1].startswith("<table"):
                html_body.append("<table>")
            html_body.append(row_html)
            continue
            
        # Đóng thẻ table khi hết dòng bảng
        if len(html_body) > 0 and html_body[-1].endswith("</tr>") and not line_strip.startswith('|'):
            html_body.append("</table>")

        # Căn giữa trang bìa
        line_fmt = format_inline(line_strip)
        if "HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG" in line_strip or "KHOA CÔNG NGHỆ THÔNG TIN" in line_strip or "BÁO CÁO ĐỒ ÁN MÔN HỌC" in line_strip or "ĐỀ TÀI" in line_strip or "MÔN:" in line_strip or "TP. HỒ CHÍ MINH" in line_strip:
            html_body.append(f"<p class='center'><strong>{line_fmt}</strong></p>")
        elif "Giảng viên hướng dẫn:" in line_strip or "Sinh viên thực hiện:" in line_strip or "Mã số sinh viên:" in line_strip or "Lớp:" in line_strip or "Nhóm đăng ký:" in line_strip:
            html_body.append(f"<p class='no-indent'>{line_fmt}</p>")
        else:
            html_body.append(f"<p>{line_fmt}</p>")

    if in_list:
        html_body.append("</ul>")

    # 3. Kết xuất file HTML
    full_html = html_header + '\n'.join(html_body) + html_footer
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    print(f"[+] DOC successfully created at {doc_path}")

if __name__ == '__main__':
    md = r'd:\CSDL_PhanTan\reports\final_report.md'
    # Lưu file dạng .doc để Word nhận diện cấu trúc trang và mở trực tiếp
    doc = r'd:\CSDL_PhanTan\reports\Bao_Cao_Do_An_CSDLPT_N23DCCN071.doc'
    convert_md_to_html_doc(md, doc)
