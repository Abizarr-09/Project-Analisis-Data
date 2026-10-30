# Air Quality Beijing Dashboard ✨

Dashboard analisis kualitas udara untuk 12 stasiun pemantauan di Beijing, China (periode 2013 s.d. 2017). Proyek ini merupakan submission akhir untuk program Dicoding Academy.

---

## Setup Environment - Anaconda
```bash
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal
```bash
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Run Streamlit App
```bash
streamlit run dashboard/dashboard.py
```

---

## Tautan Dashboard (Streamlit Cloud)
Aplikasi dashboard yang telah dideploy dapat diakses pada tautan berikut (juga tercantum pada `url.txt`):
> **URL**: [https://dashboard-airquality-beijing.streamlit.app](https://dashboard-airquality-beijing.streamlit.app)

---

## Pertanyaan Bisnis
1. **Pertanyaan 1**: Bagaimana tren konsentrasi polutan utama (PM2.5 dan PM10) berubah secara bulanan selama periode 2013–2017, dan pada bulan apa tingkat polusi udara paling tinggi dan paling rendah?
2. **Pertanyaan 2**: Stasiun pemantauan mana yang memiliki rata-rata PM2.5 tertinggi dan terendah, dan apakah terdapat korelasi antara faktor meteorologi (suhu, kecepatan angin, curah hujan, titik embun) dengan tingkat polusi PM2.5?

---

## Ringkasan Temuan & Insight
- **Tren Musiman (Pertanyaan 1)**: Polusi tertinggi konsisten terjadi pada bulan **Desember dan Januari** (musim dingin) dengan rata-rata PM2.5 mencapai >100 µg/m³ (4x batas WHO). Polusi terendah terjadi pada bulan **Agustus** (musim panas/hujan).
- **Perbandingan Stasiun & Faktor Meteorologi (Pertanyaan 2)**: Stasiun pusat perkotaan (**Dongsi, Wanshouxigong, Nongzhanguan**) memiliki polusi tertinggi (>85 µg/m³), sedangkan stasiun pinggiran utara (**Dingling**) paling bersih (66.8 µg/m³). Suhu dan kecepatan angin berkorelasi negatif kuat dengan PM2.5 (membantu dispersi), sedangkan kelembaban (DEWP) berkorelasi positif.
- **Clustering (Binning AQI)**: Stasiun Dingling memiliki proporsi kategori Baik tertinggi (**46.4%**), sedangkan stasiun perkotaan mencatat lebih dari **26%** hari dalam kategori Berbahaya & Sangat Tidak Sehat.
- **Geospatial Analysis**: Terdapat gradien spasial Utara–Selatan (*North-South Gradient*) yang kuat akibat proteksi topografi pegunungan Yanshan di utara dan akumulasi emisi di cekungan urban selatan.

---

## Struktur Direktori Proyek

```text
submission/
├── dashboard/
│   ├── main_data.csv         # Data hasil pembersihan yang siap digunakan dashboard
│   └── dashboard.py          # Script utama visualisasi dashboard Streamlit
├── data/
│   ├── PRSA_Data_Aotizhongxin_20130301-20170228.csv
│   ├── PRSA_Data_Changping_20130301-20170228.csv
│   ├── ... (12 file CSV dataset mentah stasiun)
│   └── PRSA_Data_20130301-20170228/
├── notebook.ipynb            # Jupyter Notebook yang telah dieksekusi lengkap
├── README.md                 # Dokumentasi proyek & petunjuk menjalankan
├── requirements.txt          # Daftar dependencies library Python
└── url.txt                   # Berkas berisi tautan dashboard Streamlit Cloud
```
