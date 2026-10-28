# CV Generator (Python & ReportLab)

JSON formatındaki verileri ve isteğe bağlı vesikalık fotoğrafı kullanarak JobStep tarzında, ATS uyumlu ve profesyonel PDF özgeçmişler (CV) üreten Python betiğidir.

---

## 📁 Proje Dosya Yapısı

Scriptin sorunsuz çalışması için dosyaların aynı dizinde şu şekilde yapılandırılması gerekir:

```text
├── generate_cv.py
├── cv_data.json
├── photo.jpg (veya photo.jpeg / photo.png)   # Opsiyonel: Otomatik dikey oval kırpılır
├── fonts/
│   ├── LiberationSerif-Regular.ttf
│   ├── LiberationSerif-Bold.ttf
│   ├── LiberationSerif-Italic.ttf
│   └── LiberationSerif-BoldItalic.ttf
├── requirements.txt
└── README.md
```
