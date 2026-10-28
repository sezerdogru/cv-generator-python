"""
CV üretici (JobStep tarzı düzen) - veri cv_data.json'dan okunur

Gereksinimler:  pip install reportlab pillow
Klasör yapısı:  generate_cv.py
                cv_data.json
                photo.jpg (veya photo.jpeg / photo.png)   <- normal dikdörtgen fotoğraf, script ovale keser
                fonts/LiberationSerif-Regular.ttf
                fonts/LiberationSerif-Bold.ttf
                fonts/LiberationSerif-Italic.ttf
                fonts/LiberationSerif-BoldItalic.ttf
Çalıştır:       python generate_cv.py  ->  resume<DİL>.pdf
"""
import os, re, json
from PIL import Image as PILImage, ImageDraw
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, Image, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

BASE = os.path.dirname(os.path.abspath(__file__))

# ---------- Veri: cv_data.json ----------
with open(os.path.join(BASE, 'cv_data.json'), encoding='utf-8') as fh:
    DATA = json.load(fh)
LANG = DATA.get('language', 'tr')
OUT = os.path.join(BASE, f'resume_{LANG.upper()}.pdf')

# Bölüm başlıkları ve sabit etiketler (dile göre)
LABELS = {
    'tr': dict(summary='ÖZET', work='İŞ DENEYİMİ', edu='EĞİTİM', skills='TEKNİK YETKİNLİKLER',
               projects='PROJELER', langs='DİLLER', certs='SERTİFİKALAR VE KURSLAR',
               ref='REFERANS', now='Günümüz'),
    'en': dict(summary='SUMMARY', work='WORK EXPERIENCE', edu='EDUCATION', skills='TECHNICAL SKILLS',
               projects='PROJECTS', langs='LANGUAGES', certs='CERTIFICATIONS & COURSES',
               ref='REFERENCE', now='Present'),
}
LB = LABELS.get(LANG, LABELS['en'])

def esc(s):
    """JSON'daki çıplak & karakterlerini Paragraph için kaçır (<b> vb. etiketlere dokunmaz)."""
    return re.sub(r'&(?!amp;|lt;|gt;|#)', '&amp;', s)

# ---------- Fontlar: fonts/ klasöründen ----------
d = os.path.join(BASE, 'fonts', 'LiberationSerif-')
for n, f in [('S', 'Regular'), ('S-B', 'Bold'), ('S-I', 'Italic'), ('S-BI', 'BoldItalic')]:
    pdfmetrics.registerFont(TTFont(n, d + f + '.ttf'))
pdfmetrics.registerFontFamily('S', normal='S', bold='S-B', italic='S-I', boldItalic='S-BI')

# ---------- Sayfa ölçüleri ----------
MX, MY = 15 * mm, 13 * mm
W = A4[0] - 2 * MX
PHOTO_W = 27 * mm              # fotoğraf genişliği (büyütmek için artır)
PHOTO_H = PHOTO_W * 114 / 96   # dikey oval
PHOTO_ZOOM = 1.0               # 1.0 = tüm resim, büyüdükçe yüze yaklaşır
PHOTO_FACE_Y = 0.30            # yüzün dikey konumu (0 = üst, 1 = alt)

# ---------- Fotoğrafı oval kes ----------
def make_oval_photo(out='photo_oval.png', px=480):
    src = None
    for name in (DATA['header'].get('photo_path'), 'photo.jpg', 'photo.jpeg', 'photo.png'):
        if not name:
            continue
        p = os.path.join(BASE, name)
        if os.path.exists(p):
            src = p
            break
    if not src:
        print('UYARI: photo.jpg/jpeg/png bulunamadı, fotoğrafsız üretiliyor.')
        return None
    w, h = px, int(px * 114 / 96)
    im = PILImage.open(src).convert('RGB')
    # hedef orana göre kırp + yakınlaştır
    target = w / h
    iw, ih = im.size
    if iw / ih > target:
        ch = ih / PHOTO_ZOOM
        cw = ch * target
    else:
        cw = iw / PHOTO_ZOOM
        ch = cw / target
    left = (iw - cw) / 2
    top = (ih - ch) * PHOTO_FACE_Y
    im = im.crop((int(left), int(top), int(left + cw), int(top + ch)))
    im = im.resize((w, h), PILImage.LANCZOS)
    # oval maske (4x çiz, küçült -> pürüzsüz kenar)
    mask = PILImage.new('L', (w * 4, h * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, w * 4 - 1, h * 4 - 1), fill=255)
    mask = mask.resize((w, h), PILImage.LANCZOS)
    im.putalpha(mask)
    path = os.path.join(BASE, out)
    im.save(path)
    return path

# ---------- Stiller ----------
b = ParagraphStyle('b', fontName='S', fontSize=9.2, leading=11.8)
dt = ParagraphStyle('dt', parent=b, textColor=colors.HexColor('#333333'))
sec = ParagraphStyle('sec', parent=b, fontSize=8.5, textColor=colors.HexColor('#222222'), keepWithNext=1)
nm = ParagraphStyle('nm', fontName='S-B', fontSize=17, leading=20, alignment=TA_CENTER)
sub = ParagraphStyle('sub', fontName='S-I', fontSize=10.5, leading=13, alignment=TA_CENTER, textColor=colors.HexColor('#444444'))
ct = ParagraphStyle('ct', parent=b, alignment=TA_CENTER, fontSize=8.6)
bl = ParagraphStyle('bl', parent=b, leftIndent=8, firstLineIndent=-6)

COL = 38 * mm
CELL = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]

def sp(h):
    s = Spacer(1, h)
    s.keepWithNext = True      # başlık sayfa sonunda yalnız kalmasın
    return s

def hr():
    f = HRFlowable(width='100%', thickness=0.7, color=colors.black, spaceBefore=4, spaceAfter=5)
    f.keepWithNext = True
    return f

def section(title):
    return Paragraph(title, sec)

def row(date, title, bullets=None, desc=None):
    c = [Paragraph(f'<b>{esc(title)}</b>', b)]
    if desc:
        c.append(Paragraph(esc(desc), b))
    for x in bullets or []:
        c.append(Paragraph('• ' + esc(x), bl))
    t = Table([[Paragraph(esc(date), dt), c]], colWidths=[COL, W - COL], hAlign='LEFT')
    t.setStyle(TableStyle(CELL))
    return t

def kv(k, v):
    t = Table([[Paragraph(esc(k), dt), Paragraph(esc(v), b)]], colWidths=[COL, W - COL], hAlign='LEFT')
    t.setStyle(TableStyle(CELL))
    return t

def now(date):
    return LB['now'] if date == 'Present' else date

S=[]
H = DATA['header']
underline_email = lambda s: re.sub(r'\S+@\S+', lambda m: f'<u>{m.group(0)}</u>', esc(s))
hd=[Paragraph(esc(H['name']),nm),Paragraph(esc(H['title']),sub),sp(3),
 Paragraph(underline_email(H['contact_line_1']),ct),
 Paragraph(esc(H['contact_line_2']),ct)]
photo=make_oval_photo()
img=Image(photo,width=PHOTO_W,height=PHOTO_H) if photo else ''
t=Table([[hd,img]],colWidths=[W-PHOTO_W-4*mm,PHOTO_W+4*mm])
t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('LEFTPADDING',(0,0),(0,0),PHOTO_W+4*mm)]))
S+=[t,hr()]
S+=[section(LB['summary']),sp(3),Paragraph(esc(DATA['summary']),b),hr()]
S+=[section(LB['work']),sp(2)]
for e in DATA['work_experience']:
    S+=[row(e['date'],e['title'],e.get('bullets'))]
S[-1:]=[S[-1],hr()]
S+=[section(LB['edu']),sp(2)]
for e in DATA['education']:
    S+=[row(e['date'],e['title'],desc=e.get('desc'))]
S+=[hr()]
S+=[section(LB['skills']),sp(2)]
for k,v in DATA['technical_skills']: S.append(kv(k,v))
S.append(hr())
S+=[section(LB['projects']),sp(2)]
for e in DATA['projects']:
    S+=[row(now(e['date']),e['title'],desc=e.get('desc'))]
S+=[hr()]
S+=[section(LB['langs']),sp(2)]
cells=[]
for i in range(0,len(DATA['languages']),2):
    r=[]
    for l in DATA['languages'][i:i+2]:
        r+=[Paragraph(esc(l['name']),b),Paragraph(esc(l['level']),b)]
    r+=['']*(4-len(r))
    cells.append(r)
lt=Table(cells,colWidths=[28*mm,W/2-28*mm,40*mm,W/2-40*mm])
lt.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1)]))
S+=[lt,hr()]
S+=[section(LB['certs']),sp(2)]
for x in DATA['certifications']:
    S.append(row(LB['now'],x))
S+=[hr(),section(LB['ref']),sp(2)]
R=DATA['reference']
rt=Table([[Paragraph(esc(R['name_title']),b),Paragraph(esc(R['company']),ParagraphStyle('r',parent=b,alignment=2))]],colWidths=[W/2,W/2])
rt.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
S.append(rt)
doc=BaseDocTemplate(OUT,pagesize=A4,leftMargin=MX,rightMargin=MX,topMargin=MY,bottomMargin=MY,
                    title='resume',author='Lorem ipsum')
frame=Frame(MX,MY,A4[0]-2*MX,A4[1]-2*MY,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
doc.addPageTemplates([PageTemplate(id='main',frames=[frame])])
doc.build(S)
print('Yazıldı:',OUT)