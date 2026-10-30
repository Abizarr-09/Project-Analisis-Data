import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="Dashboard Kualitas Udara Beijing",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# GAYA FONT DASAR
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD & CACHE DATA
# ============================================================
station_coords = {
    'Aotizhongxin':  {'latitude': 39.982, 'longitude': 116.397, 'zone': 'Urban Core'},
    'Changping':     {'latitude': 40.217, 'longitude': 116.230, 'zone': 'Sub-urban North'},
    'Dingling':      {'latitude': 40.292, 'longitude': 116.220, 'zone': 'Rural North'},
    'Dongsi':        {'latitude': 39.929, 'longitude': 116.417, 'zone': 'Urban Core'},
    'Guanyuan':      {'latitude': 39.929, 'longitude': 116.339, 'zone': 'Urban Core'},
    'Gucheng':       {'latitude': 39.914, 'longitude': 116.184, 'zone': 'Urban West'},
    'Huairou':       {'latitude': 40.328, 'longitude': 116.628, 'zone': 'Rural North'},
    'Nongzhanguan':  {'latitude': 39.937, 'longitude': 116.461, 'zone': 'Urban Core'},
    'Shunyi':        {'latitude': 40.127, 'longitude': 116.655, 'zone': 'Sub-urban Northeast'},
    'Tiantan':       {'latitude': 39.886, 'longitude': 116.407, 'zone': 'Urban Core'},
    'Wanliu':        {'latitude': 39.987, 'longitude': 116.287, 'zone': 'Urban Northwest'},
    'Wanshouxigong': {'latitude': 39.878, 'longitude': 116.352, 'zone': 'Urban Core'}
}

@st.cache_data
def load_data():
    candidates = [
        os.path.join(os.path.dirname(__file__), "main_data.csv"),
        os.path.join(os.path.dirname(__file__), "dashboard", "main_data.csv"),
        "main_data.csv",
        os.path.join("dashboard", "main_data.csv")
    ]
    for path in candidates:
        if os.path.exists(path):
            df = pd.read_csv(path)
            if "datetime" in df.columns:
                df["datetime"] = pd.to_datetime(df["datetime"])
            if "zone" not in df.columns and "station" in df.columns:
                df["zone"] = df["station"].map(lambda s: station_coords.get(s, {}).get("zone", "Urban"))
            return df

    raw_candidates = [
        "PRSA_Data_20130301-20170228",
        os.path.join("data", "PRSA_Data_20130301-20170228"),
        os.path.join(os.path.dirname(__file__), "..", "data", "PRSA_Data_20130301-20170228"),
        os.path.join(os.path.dirname(__file__), "data", "PRSA_Data_20130301-20170228")
    ]
    DATA_FOLDER = None
    for folder in raw_candidates:
        if os.path.exists(folder):
            DATA_FOLDER = folder
            break

    if DATA_FOLDER is None:
        raise FileNotFoundError("Dataset tidak ditemukan.")

    csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
    df_list = [pd.read_csv(os.path.join(DATA_FOLDER, f)) for f in sorted(csv_files)]
    df = pd.concat(df_list, ignore_index=True)

    df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
    if "No" in df.columns:
        df.drop(columns=["No"], inplace=True)

    numeric_cols = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3",
                    "TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
    df[numeric_cols] = df.groupby("station")[numeric_cols].transform(
        lambda x: x.ffill().bfill()
    )
    df["wd"] = df.groupby("station")["wd"].transform(
        lambda x: x.fillna(x.mode()[0] if not x.mode().empty else "N")
    )

    df['latitude'] = df['station'].map(lambda s: station_coords[s]['latitude'])
    df['longitude'] = df['station'].map(lambda s: station_coords[s]['longitude'])
    df['zone'] = df['station'].map(lambda s: station_coords[s]['zone'])

    bins = [-np.inf, 35, 75, 115, 150, np.inf]
    labels = ['Baik', 'Sedang', 'Tidak Sehat', 'Sangat Tidak Sehat', 'Berbahaya']
    df['air_quality_category'] = pd.cut(df['PM2.5'], bins=bins, labels=labels)

    def get_season(m):
        if m in [12, 1, 2]: return "Musim Dingin"
        elif m in [3, 4, 5]: return "Musim Semi"
        elif m in [6, 7, 8]: return "Musim Panas"
        else: return "Musim Gugur"
    df["season"] = df["month"].apply(get_season)

    bulan = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"Mei",6:"Jun",
             7:"Jul",8:"Ags",9:"Sep",10:"Okt",11:"Nov",12:"Des"}
    df["month_name"] = df["month"].map(bulan)

    return df

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.subheader("Dashboard Kualitas Udara")
    st.caption("Beijing, China — 2013 s.d. 2017")
    st.divider()

    st.markdown("**Filter Data**")

    df_raw = load_data()

    all_stations = sorted(df_raw["station"].unique().tolist())
    selected_stations = st.multiselect(
        "Pilih Stasiun:",
        options=all_stations,
        default=all_stations,
        help="Pilih satu atau lebih stasiun pemantauan"
    )

    year_range = st.slider(
        "Rentang Tahun:",
        min_value=int(df_raw["year"].min()),
        max_value=int(df_raw["year"].max()),
        value=(int(df_raw["year"].min()), int(df_raw["year"].max())),
        help="Filter data berdasarkan rentang tahun"
    )

    pollutant = st.selectbox(
        "Pilih Polutan Utama:",
        options=["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"],
        index=0,
        help="Polutan yang akan dianalisis pada visualisasi"
    )

    st.divider()
    st.markdown("**Navigasi**")
    page = st.radio(
        "Pilih Halaman:",
        ["Overview", "Tren Bulanan", "Perbandingan Stasiun",
         "Faktor Meteorologi", "Analisis Lanjutan", "Kesimpulan"],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("**Abizar Algifari** | Proyek Analisis Data")

# ============================================================
# FILTER DATA
# ============================================================
df = df_raw[
    (df_raw["station"].isin(selected_stations)) &
    (df_raw["year"] >= year_range[0]) &
    (df_raw["year"] <= year_range[1])
].copy()

if df.empty:
    st.error("Tidak ada data untuk filter yang dipilih. Silakan ubah filter di sidebar.")
    st.stop()

# ============================================================
# PENGATURAN GAYA GRAFIK
# ============================================================
def set_chart_style(fig, ax_list):
    fig.patch.set_facecolor("#ffffff")
    axes = ax_list if isinstance(ax_list, (list, np.ndarray)) else [ax_list]
    for ax in axes:
        ax.set_facecolor("#ffffff")
        ax.tick_params(colors="#1e293b", labelsize=9)
        ax.xaxis.label.set_color("#1e293b")
        ax.yaxis.label.set_color("#1e293b")
        ax.title.set_color("#1e293b")
        for spine in ax.spines.values():
            spine.set_edgecolor("#cbd5e1")
            spine.set_linewidth(0.8)
        ax.grid(color="#e2e8f0", linewidth=0.8, linestyle="--", alpha=0.7)
    return fig

# ============================================================
# HALAMAN: OVERVIEW
# ============================================================
if page == "Overview":
    st.title("Dashboard Kualitas Udara Beijing")
    st.caption("Analisis data polutan udara dari 12 stasiun pemantauan periode 2013–2017")
    st.divider()

    # KPI Cards
    avg_pm25  = df["PM2.5"].mean()
    avg_pm10  = df["PM10"].mean()
    max_pm25  = df["PM2.5"].max()
    total_rec = len(df)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with st.container(border=True):
            st.metric("Total Rekaman", f"{total_rec:,.0f}", help="Jumlah data setelah filter")
    with c2:
        with st.container(border=True):
            st.metric("Rata-rata PM2.5", f"{avg_pm25:.1f} µg/m³",
                      delta=f"{avg_pm25 - 25:.1f} dari batas WHO",
                      delta_color="inverse")
    with c3:
        with st.container(border=True):
            st.metric("Rata-rata PM10", f"{avg_pm10:.1f} µg/m³",
                      delta=f"{avg_pm10 - 50:.1f} dari batas WHO",
                      delta_color="inverse")
    with c4:
        with st.container(border=True):
            st.metric("Puncak PM2.5", f"{max_pm25:.0f} µg/m³", help="Nilai PM2.5 tertinggi tercatat")

    st.subheader("Pertanyaan Bisnis")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("**Pertanyaan 1**")
            st.write(
                "Bagaimana tren konsentrasi polutan utama (PM2.5 dan PM10) berubah secara bulanan "
                "selama periode 2013–2017, dan pada bulan apa tingkat polusi udara paling tinggi "
                "dan paling rendah?"
            )
    with col2:
        with st.container(border=True):
            st.markdown("**Pertanyaan 2**")
            st.write(
                "Stasiun pemantauan mana yang memiliki rata-rata PM2.5 tertinggi dan terendah, "
                "dan apakah terdapat korelasi antara faktor meteorologi (suhu, angin, hujan, kelembaban) "
                "dengan tingkat polusi PM2.5?"
            )

    st.subheader("Informasi Dataset")
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.caption("Stasiun Aktif")
            st.subheader(f"{df['station'].nunique()}")
            st.caption("dari 12 stasiun pemantauan")
    with col2:
        with st.container(border=True):
            st.caption("Periode Data")
            st.subheader(f"{year_range[0]} – {year_range[1]}")
            st.caption("Data per jam (hourly)")
    with col3:
        with st.container(border=True):
            st.caption("Variabel")
            st.subheader("17 Kolom")
            st.caption("6 polutan + 6 parameter meteorologi")

    st.subheader("Preview Data")
    st.dataframe(
        df[["datetime", "station", "PM2.5", "PM10", "SO2", "NO2", "CO", "O3",
            "TEMP", "PRES", "WSPM", "RAIN"]].head(20),
        use_container_width=True,
        height=350
    )

# ============================================================
# HALAMAN: TREN BULANAN
# ============================================================
elif page == "Tren Bulanan":
    st.title("Pertanyaan 1: Tren Bulanan Polutan")
    st.caption("Analisis tren konsentrasi PM2.5 & PM10 secara bulanan selama 2013–2017")
    st.divider()

    # --- Plot 1: Time series ---
    st.subheader("Time Series Bulanan")

    df_monthly = df.groupby(["year", "month"])[[pollutant, "PM10"]].mean().reset_index()
    df_monthly["period"] = pd.to_datetime(df_monthly[["year", "month"]].assign(day=1))
    df_monthly = df_monthly.sort_values("period")

    fig, ax = plt.subplots(figsize=(14, 4.8))
    ax.plot(df_monthly["period"], df_monthly[pollutant],
            color="#e74c3c", linewidth=2.2, marker="o", markersize=3.5, label=pollutant)
    if pollutant != "PM10":
        ax.plot(df_monthly["period"], df_monthly["PM10"],
                color="#3498db", linewidth=1.8, linestyle="--", marker="s", markersize=3,
                alpha=0.85, label="PM10")
    ax.fill_between(df_monthly["period"], df_monthly[pollutant], alpha=0.15, color="#e74c3c")

    who_limits = {"PM2.5": 25, "PM10": 50, "SO2": 20, "NO2": 40, "CO": 4000, "O3": 100}
    if pollutant in who_limits:
        ax.axhline(y=who_limits[pollutant], color="#c0392b", linestyle=":",
                   linewidth=1.5, alpha=0.9, label=f"Batas WHO {pollutant} ({who_limits[pollutant]})")

    ax.set_xlabel("Periode", fontsize=10)
    ax.set_ylabel("Konsentrasi (µg/m³)", fontsize=10)
    ax.set_title(f"Tren Rata-rata Bulanan {pollutant} — Seluruh Stasiun Terpilih", fontsize=11, fontweight="bold")
    ax.legend(fontsize=9)
    ax.tick_params(axis="x", rotation=30)
    fig = set_chart_style(fig, ax)
    st.pyplot(fig, use_container_width=True)
    plt.close()

    # --- Plot 2: Bar per bulan ---
    st.subheader("Rata-rata per Bulan (Lintas Tahun)")

    bulan_order = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Ags","Sep","Okt","Nov","Des"]
    df_bulan = df.groupby("month_name")[pollutant].mean().reindex(bulan_order).reset_index()
    df_bulan.columns = ["month_name", pollutant]

    idx_max = df_bulan[pollutant].idxmax()
    idx_min = df_bulan[pollutant].idxmin()
    bulan_max = df_bulan.loc[idx_max, "month_name"]
    bulan_min = df_bulan.loc[idx_min, "month_name"]
    val_max   = df_bulan.loc[idx_max, pollutant]
    val_min   = df_bulan.loc[idx_min, pollutant]

    colors_bar = [
        "#e74c3c" if v == val_max
        else ("#2ecc71" if v == val_min else "#3498db")
        for v in df_bulan[pollutant]
    ]

    fig2, ax2 = plt.subplots(figsize=(14, 4.8))
    bars = ax2.bar(df_bulan["month_name"], df_bulan[pollutant],
                   color=colors_bar, alpha=0.85, edgecolor="#cbd5e1", linewidth=0.6)

    if pollutant in who_limits:
        ax2.axhline(y=who_limits[pollutant], color="#c0392b", linestyle=":",
                    linewidth=1.5, alpha=0.9, label=f"Batas Aman WHO ({who_limits[pollutant]} µg/m³)")

    ax2.annotate(f"Tertinggi\n{val_max:.1f}",
                 xy=(idx_max, val_max),
                 xytext=(idx_max, val_max + df_bulan[pollutant].max()*0.07),
                 ha="center", fontsize=9, color="#c0392b", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.2))
    ax2.annotate(f"Terendah\n{val_min:.1f}",
                 xy=(idx_min, val_min),
                 xytext=(idx_min, val_min + df_bulan[pollutant].max()*0.10),
                 ha="center", fontsize=9, color="#27ae60", fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color="#27ae60", lw=1.2))

    red_patch = mpatches.Patch(color="#e74c3c", label=f"Tertinggi ({bulan_max})")
    green_patch = mpatches.Patch(color="#2ecc71", label=f"Terendah ({bulan_min})")
    blue_patch = mpatches.Patch(color="#3498db", label="Bulan Lainnya")
    who_patch = plt.Line2D([0], [0], color="#c0392b", linestyle=":", label="Batas Aman WHO")
    ax2.legend(handles=[red_patch, green_patch, blue_patch, who_patch], fontsize=9)

    ax2.set_xlabel("Bulan", fontsize=10)
    ax2.set_ylabel(f"Rata-rata {pollutant} (µg/m³)", fontsize=10)
    ax2.set_title(f"Rata-rata {pollutant} per Bulan ({year_range[0]}–{year_range[1]})", fontsize=11, fontweight="bold")
    fig2 = set_chart_style(fig2, ax2)
    st.pyplot(fig2, use_container_width=True)
    plt.close()

    # Insight
    with st.container(border=True):
        st.markdown("**Insight Pertanyaan 1**")
        st.markdown(f"""
        - Konsentrasi **{pollutant}** paling tinggi terjadi pada bulan **{bulan_max}** dengan rata-rata **{val_max:.1f} µg/m³**.
        - Konsentrasi paling rendah terjadi pada bulan **{bulan_min}** dengan rata-rata **{val_min:.1f} µg/m³**.
        - Pola ini mencerminkan pengaruh musim: polusi meningkat di musim dingin akibat penggunaan pemanas berbahan bakar batu bara, dan menurun di musim panas/hujan karena dispersi dan curah hujan.
        """)

# ============================================================
# HALAMAN: PERBANDINGAN STASIUN
# ============================================================
elif page == "Perbandingan Stasiun":
    st.title("Pertanyaan 2: Perbandingan Antar Stasiun")
    st.caption("Perbandingan tingkat polutan antar stasiun pemantauan di Beijing")
    st.divider()

    df_station = df.groupby("station")[["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"]].mean().reset_index()
    df_station = df_station.sort_values(pollutant, ascending=True).reset_index(drop=True)

    # --- Horizontal bar chart ---
    fig, ax = plt.subplots(figsize=(12, 6.5))
    n = len(df_station)
    cmap = plt.cm.RdYlGn_r
    bar_colors = [cmap(i / max(n - 1, 1)) for i in range(n)]

    bars = ax.barh(df_station["station"], df_station[pollutant],
                   color=bar_colors, edgecolor="#cbd5e1", linewidth=0.6, alpha=0.9)

    for bar, val in zip(bars, df_station[pollutant]):
        ax.text(bar.get_width() + df_station[pollutant].max()*0.01,
                bar.get_y() + bar.get_height()/2,
                f"{val:.1f}", va="center", fontsize=9, color="#1e293b", fontweight="bold")

    who_lim = {"PM2.5": 25, "PM10": 50, "SO2": 20, "NO2": 40, "CO": 4000, "O3": 100}
    if pollutant in who_lim:
        ax.axvline(x=who_lim[pollutant], color="#c0392b", linestyle=":",
                   linewidth=1.5, alpha=0.9, label=f"Batas Aman WHO ({who_lim[pollutant]})")

    ax.set_xlabel(f"Rata-rata {pollutant} (µg/m³)", fontsize=10)
    ax.set_title(f"Perbandingan Rata-rata {pollutant} per Stasiun (Merah = Tertinggi, Hijau = Terendah)",
                 fontsize=11, fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_xlim(0, df_station[pollutant].max() * 1.12)
    fig = set_chart_style(fig, ax)
    st.pyplot(fig, use_container_width=True)
    plt.close()

    # Ranking table
    st.subheader("Ranking Stasiun")

    df_rank = df_station.sort_values(pollutant, ascending=False).reset_index(drop=True)
    df_rank.index = df_rank.index + 1
    df_rank.index.name = "Rank"
    df_rank_show = df_rank[["station", "PM2.5", "PM10", "SO2", "NO2"]].rename(
        columns={"station": "Stasiun"}
    ).round(2)

    st.dataframe(df_rank_show, use_container_width=True)

    # Insight
    top_station    = df_station.iloc[-1]["station"]
    bottom_station = df_station.iloc[0]["station"]
    top_val        = df_station.iloc[-1][pollutant]
    bottom_val     = df_station.iloc[0][pollutant]

    with st.container(border=True):
        st.markdown("**Insight Pertanyaan 2: Perbandingan Stasiun**")
        st.markdown(f"""
        - Stasiun dengan rata-rata **{pollutant} tertinggi**: **{top_station}** ({top_val:.1f} µg/m³).
        - Stasiun dengan rata-rata **{pollutant} terendah**: **{bottom_station}** ({bottom_val:.1f} µg/m³).
        - Selisih antara stasiun tertinggi dan terendah: **{top_val - bottom_val:.1f} µg/m³**.
        - Stasiun di kawasan pusat kota dan lalu lintas padat cenderung mencatat polutan lebih tinggi dibandingkan stasiun suburban/perbukitan.
        """)

# ============================================================
# HALAMAN: FAKTOR METEOROLOGI
# ============================================================
elif page == "Faktor Meteorologi":
    st.title("Pertanyaan 2: Korelasi Faktor Meteorologi")
    st.caption("Analisis pengaruh parameter cuaca terhadap konsentrasi polutan udara")
    st.divider()

    col1, col2 = st.columns([1, 1])

    # --- Heatmap Korelasi ---
    with col1:
        st.subheader("Heatmap Korelasi")
        corr_cols = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
        corr_matrix = df[corr_cols].corr()

        mask = np.zeros_like(corr_matrix, dtype=bool)
        mask[np.triu_indices_from(mask)] = True

        fig, ax = plt.subplots(figsize=(8.5, 6.5))
        sns.heatmap(corr_matrix, ax=ax, annot=True, fmt=".2f",
                    cmap="coolwarm", center=0, vmin=-1, vmax=1,
                    linewidths=0.5, annot_kws={"size": 8, "weight": "bold"}, mask=mask,
                    cbar_kws={"shrink": 0.8})
        ax.set_title("Heatmap Korelasi Antar Variabel", fontsize=11, fontweight="bold")
        ax.tick_params(axis="x", rotation=45, colors="#1e293b")
        ax.tick_params(axis="y", rotation=0, colors="#1e293b")
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#ffffff")
        ax.title.set_color("#1e293b")
        st.pyplot(fig, use_container_width=True)
        plt.close()

    # --- Bar korelasi dengan PM2.5 ---
    with col2:
        st.subheader("Korelasi dengan PM2.5")
        corr_pm25 = df[corr_cols].corr()["PM2.5"].drop("PM2.5").sort_values()

        fig2, ax2 = plt.subplots(figsize=(8.5, 6.5))
        bar_colors2 = ["#e74c3c" if v > 0 else "#3498db" for v in corr_pm25.values]
        bars2 = ax2.barh(corr_pm25.index, corr_pm25.values,
                         color=bar_colors2, alpha=0.85, edgecolor="#cbd5e1", linewidth=0.6)
        ax2.axvline(x=0, color="#64748b", linewidth=1, linestyle="--")

        for bar, val in zip(bars2, corr_pm25.values):
            x_pos = bar.get_width() + 0.015 if val >= 0 else bar.get_width() - 0.015
            ha = "left" if val >= 0 else "right"
            ax2.text(x_pos, bar.get_y() + bar.get_height()/2,
                     f"{val:.3f}", va="center", ha=ha, fontsize=8.5, color="#1e293b", fontweight="bold")

        ax2.set_xlabel("Nilai Korelasi (r)", fontsize=10)
        ax2.set_title("Korelasi Setiap Variabel terhadap PM2.5", fontsize=11, fontweight="bold")

        pos_patch = mpatches.Patch(color="#e74c3c", label="Korelasi Positif")
        neg_patch = mpatches.Patch(color="#3498db", label="Korelasi Negatif")
        ax2.legend(handles=[pos_patch, neg_patch], fontsize=9)
        fig2 = set_chart_style(fig2, ax2)
        st.pyplot(fig2, use_container_width=True)
        plt.close()

    # --- Scatter plots ---
    st.subheader("Scatter Plot: PM2.5 vs Faktor Meteorologi")

    df_sample = df.sample(n=min(5000, len(df)), random_state=42)
    scatter_vars = [
        ("TEMP",  "Suhu (°C)",              "#e67e22"),
        ("WSPM",  "Kecepatan Angin (m/s)",  "#2980b9"),
        ("RAIN",  "Curah Hujan (mm)",        "#27ae60"),
        ("DEWP",  "Titik Embun (°C)",        "#8e44ad"),
    ]

    fig3, axes3 = plt.subplots(1, 4, figsize=(18, 4.5))

    for ax, (col, label, color) in zip(axes3, scatter_vars):
        ax.scatter(df_sample[col], df_sample["PM2.5"],
                   alpha=0.25, color=color, s=10, rasterized=True)
        valid = df_sample[[col, "PM2.5"]].dropna()
        z = np.polyfit(valid[col], valid["PM2.5"], 1)
        p = np.poly1d(z)
        x_line = np.linspace(valid[col].min(), valid[col].max(), 100)
        ax.plot(x_line, p(x_line), color="#c0392b", linestyle="--", linewidth=1.8, label="Regresi")
        r_val = df[[col, "PM2.5"]].corr().iloc[0, 1]
        ax.set_title(f"PM2.5 vs {label}\nr = {r_val:.3f}", fontsize=9.5, fontweight="bold")
        ax.set_xlabel(label, fontsize=9)
        ax.set_ylabel("PM2.5 (µg/m³)", fontsize=9)
        ax.legend(fontsize=8)

    fig3 = set_chart_style(fig3, list(axes3))
    plt.tight_layout()
    st.pyplot(fig3, use_container_width=True)
    plt.close()

    with st.container(border=True):
        st.markdown("**Insight Korelasi Meteorologi**")
        st.markdown("""
        - **Suhu (TEMP)**: Korelasi negatif — suhu tinggi memicu konveksi dan turbulensi atmosfer yang mempercepat dispersi polutan.
        - **Kecepatan Angin (WSPM)**: Korelasi negatif kuat — sirkulasi angin kencang meniup dan mengencerkan konsentrasi partikel udara.
        - **Titik Embun (DEWP)**: Korelasi positif — kelembaban tinggi menghambat dispersi polutan dan mempercepat reaksi pembentukan partikulat sekunder.
        - **Curah Hujan (RAIN)**: Korelasi negatif lemah — curah hujan berperan mencuci partikel di udara (wet scavenging), meski intensitasnya bervariasi.
        """)

# ============================================================
# HALAMAN: ANALISIS LANJUTAN (ADVANCED ANALYSIS)
# ============================================================
elif page == "Analisis Lanjutan":
    st.title("Analisis Lanjutan (Advanced Analysis)")
    st.caption("Penerapan teknik Clustering (Binning AQI), Geospatial Analysis, dan Analisis Temporal tanpa Machine Learning")
    st.divider()

    tab_geo, tab_cluster, tab_temporal = st.tabs([
        "Geospatial Analysis",
        "Clustering (Binning AQI)",
        "Pola Temporal (Jam & Musim)"
    ])

    # ------------------------------------------------------------
    # TAB 1: GEOSPATIAL ANALYSIS
    # ------------------------------------------------------------
    with tab_geo:
        st.subheader("Pemetaan Spasial 12 Stasiun Pemantauan di Beijing")
        st.caption("Menganalisis pola sebaran polusi berdasarkan lokasi koordinat geografis nyata (Latitude & Longitude)")

        geo_summary = df.groupby("station").agg({
            "PM2.5": "mean",
            "PM10": "mean",
            "latitude": "first",
            "longitude": "first",
            "zone": "first"
        }).reset_index().sort_values("PM2.5", ascending=False)

        col_map, col_table = st.columns([1.2, 1])

        with col_map:
            st.markdown("**Peta Interaktif Stasiun Pemantauan (OpenStreetMap)**")
            st.map(geo_summary[["latitude", "longitude"]], zoom=8)

        with col_table:
            st.markdown("**Ringkasan Konsentrasi per Lokasi Spasial**")
            geo_table_show = geo_summary[["station", "zone", "PM2.5", "PM10"]].rename(
                columns={
                    "station": "Stasiun",
                    "zone": "Zona Geografis",
                    "PM2.5": "Rata-rata PM2.5",
                    "PM10": "Rata-rata PM10"
                }
            ).round(1)
            st.dataframe(geo_table_show, use_container_width=True, height=360)

        # Plot Scatter Geografis
        st.markdown("**Visualisasi Gradien Spasial: Lintang vs Bujur**")
        fig_geo, ax_geo = plt.subplots(figsize=(11, 7))
        scatter = ax_geo.scatter(
            geo_summary['longitude'], geo_summary['latitude'],
            c=geo_summary['PM2.5'], cmap='RdYlGn_r', s=geo_summary['PM2.5']*10,
            edgecolor='#1e293b', linewidth=1.5, alpha=0.9
        )
        cbar = plt.colorbar(scatter, ax=ax_geo, shrink=0.8)
        cbar.set_label('Rata-rata PM2.5 (µg/m³)', fontsize=10)

        for _, row in geo_summary.iterrows():
            ax_geo.annotate(
                f"{row['station']}\n({row['PM2.5']:.1f})",
                (row['longitude'], row['latitude']),
                textcoords="offset points", xytext=(0, 12), ha='center',
                fontsize=8.5, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.85, edgecolor='#cbd5e1')
            )

        ax_geo.axhline(y=40.05, color='#7f8c8d', linestyle='--', linewidth=1.2, alpha=0.7)
        ax_geo.text(116.15, 40.07, 'Kawasan Utara (Sub-urban / Rural)', fontsize=9.5, fontstyle='italic', color='#2c3e50')
        ax_geo.text(116.15, 40.02, 'Kawasan Selatan & Tengah (Urban Core)', fontsize=9.5, fontstyle='italic', color='#c0392b')

        ax_geo.set_title('Distribusi Spasial Konsentrasi PM2.5 di 12 Stasiun Beijing', fontsize=11, fontweight='bold')
        ax_geo.set_xlabel('Garis Bujur (Longitude)', fontsize=10)
        ax_geo.set_ylabel('Garis Lintang (Latitude)', fontsize=10)
        fig_geo = set_chart_style(fig_geo, ax_geo)
        st.pyplot(fig_geo, use_container_width=True)
        plt.close()

        with st.container(border=True):
            st.markdown("**Insight Geospatial Analysis**")
            st.markdown("""
            - **Pola Gradien Spasial (North-South Gradient)**: Terdapat pola spasial yang nyata antara posisi lintang (latitude) dengan tingkat polusi PM2.5. Semakin ke arah utara (latitude > 40.1°), kualitas udara semakin bersih (Dingling: 66.8 µg/m³, Huairou: 70.3 µg/m³). Sebaliknya, stasiun di kawasan selatan dan pusat kota (Dongsi, Wanshouxigong, Nongzhanguan) mencatat PM2.5 di atas 85 µg/m³.
            - **Pengaruh Topografi Geografis**: Wilayah utara Beijing dikelilingi perbukitan dan pegunungan Yanshan yang memiliki tutupan vegetasi alami dan minim industri berat. Kawasan tengah dan selatan merupakan dataran rendah perkotaan padat yang juga terpapar akumulasi polusi dari koridor industri regional Hebei di sebelah selatan.
            """)

    # ------------------------------------------------------------
    # TAB 2: CLUSTERING (BINNING AQI)
    # ------------------------------------------------------------
    with tab_cluster:
        st.subheader("Clustering Kualitas Udara dengan Teknik Binning (Standar AQI)")
        st.caption("Pengelompokan non-machine learning menggunakan pd.cut berdasarkan standar ambang batas konsentrasi PM2.5")

        if "air_quality_category" not in df.columns:
            bins = [-np.inf, 35, 75, 115, 150, np.inf]
            labels = ['Baik', 'Sedang', 'Tidak Sehat', 'Sangat Tidak Sehat', 'Berbahaya']
            df['air_quality_category'] = pd.cut(df['PM2.5'], bins=bins, labels=labels)

        # Overview Metrics
        cat_counts = df['air_quality_category'].value_counts()
        total_cat = len(df)

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            with st.container(border=True):
                st.caption("Kategori Baik")
                st.subheader(f"{(cat_counts.get('Baik', 0)/total_cat*100):.1f}%")
                st.caption("0 – 35 µg/m³")
        with m2:
            with st.container(border=True):
                st.caption("Kategori Sedang")
                st.subheader(f"{(cat_counts.get('Sedang', 0)/total_cat*100):.1f}%")
                st.caption("35.1 – 75 µg/m³")
        with m3:
            with st.container(border=True):
                st.caption("Kategori Tidak Sehat")
                st.subheader(f"{(cat_counts.get('Tidak Sehat', 0)/total_cat*100):.1f}%")
                st.caption("75.1 – 115 µg/m³")
        with m4:
            with st.container(border=True):
                st.caption("Sangat Tidak Sehat")
                st.subheader(f"{(cat_counts.get('Sangat Tidak Sehat', 0)/total_cat*100):.1f}%")
                st.caption("115.1 – 150 µg/m³")
        with m5:
            with st.container(border=True):
                st.caption("Kategori Berbahaya")
                st.subheader(f"{(cat_counts.get('Berbahaya', 0)/total_cat*100):.1f}%")
                st.caption("> 150 µg/m³")

        # Stacked bar per station
        st.markdown("**Proporsi Kategori Kualitas Udara per Stasiun**")
        crosstab_station = pd.crosstab(df['station'], df['air_quality_category'], normalize='index') * 100
        colors_binning = ['#2ECC71', '#F1C40F', '#E67E22', '#E74C3C', '#8E44AD']

        fig_bin, ax_bin = plt.subplots(figsize=(12, 6))
        sorted_st = crosstab_station['Berbahaya'].sort_values().index
        crosstab_station.loc[sorted_st].plot(
            kind='barh', stacked=True, color=colors_binning, ax=ax_bin, edgecolor='#cbd5e1', linewidth=0.6
        )
        ax_bin.set_title('Distribusi Proporsi Kategori Kualitas Udara per Stasiun', fontsize=11, fontweight='bold')
        ax_bin.set_xlabel('Persentase Waktu Pemantauan (%)', fontsize=10)
        ax_bin.set_ylabel('Stasiun Pemantauan', fontsize=10)
        ax_bin.legend(title='Kategori PM2.5', bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=8.5)
        fig_bin = set_chart_style(fig_bin, ax_bin)
        st.pyplot(fig_bin, use_container_width=True)
        plt.close()

        with st.container(border=True):
            st.markdown("**Insight Clustering (Binning)**")
            st.markdown("""
            - **Stasiun Dingling** memiliki proporsi kategori **Baik** tertinggi mencapai **46.4%**, serta proporsi kategori **Berbahaya** terendah (**12.1%**).
            - Sebaliknya, stasiun di kawasan perkotaan seperti **Dongsi**, **Nongzhanguan**, dan **Wanshouxigong** mencatat proporsi kategori **Berbahaya** dan **Sangat Tidak Sehat** tertinggi (mencapai lebih dari **26%** dari total waktu pengamatan).
            - Disparitas ini menunjukkan bahwa penduduk di kawasan urban Beijing terpapar udara berbahaya dua kali lebih sering dibandingkan kawasan suburban utara.
            """)

    # ------------------------------------------------------------
    # TAB 3: POLA TEMPORAL (JAM & MUSIM)
    # ------------------------------------------------------------
    with tab_temporal:
        st.subheader("Analisis Pola Temporal (Harian & Musiman)")
        st.caption("Siklus diurnal jam dalam sehari dan variasi distribusi polutan antar musim")

        col_h, col_s = st.columns(2)

        with col_h:
            st.markdown("**Pola Harian per Jam (0–23)**")
            df_hourly = df.groupby("hour")[pollutant].mean().reset_index()

            fig_h, ax_h = plt.subplots(figsize=(8, 4.6))
            ax_h.plot(df_hourly["hour"], df_hourly[pollutant],
                      color="#e67e22", linewidth=2.2, marker="o", markersize=4)
            ax_h.fill_between(df_hourly["hour"], df_hourly[pollutant], alpha=0.15, color="#e67e22")
            who_lim = {"PM2.5": 25, "PM10": 50, "SO2": 20, "NO2": 40, "CO": 4000, "O3": 100}
            if pollutant in who_lim:
                ax_h.axhline(y=who_lim[pollutant], color="#c0392b", linestyle=":",
                             linewidth=1.2, alpha=0.9, label=f"Batas WHO ({who_lim[pollutant]})")
            ax_h.set_xticks(range(0, 24, 2))
            ax_h.set_xlabel("Jam (0–23)", fontsize=9.5)
            ax_h.set_ylabel(f"Rata-rata {pollutant} (µg/m³)", fontsize=9.5)
            ax_h.set_title(f"Pola {pollutant} per Jam dalam Sehari", fontsize=11, fontweight="bold")
            ax_h.legend(fontsize=8.5)
            fig_h = set_chart_style(fig_h, ax_h)
            st.pyplot(fig_h, use_container_width=True)
            plt.close()

        with col_s:
            st.markdown("**Distribusi Konsentrasi per Musim**")
            season_order = ["Musim Dingin", "Musim Semi", "Musim Panas", "Musim Gugur"]
            season_colors_map = {
                "Musim Dingin": "#3498db",
                "Musim Semi":   "#2ecc71",
                "Musim Panas":  "#e74c3c",
                "Musim Gugur":  "#f39c12",
            }
            df_plot = df[df[pollutant] < df[pollutant].quantile(0.99)]

            fig_s, ax_s = plt.subplots(figsize=(8, 4.6))
            existing = [s for s in season_order if s in df_plot["season"].unique()]
            sns.boxplot(data=df_plot, x="season", y=pollutant,
                        order=existing,
                        palette={k: v for k, v in season_colors_map.items() if k in existing},
                        ax=ax_s, width=0.5, fliersize=1.5)
            if pollutant in who_lim:
                ax_s.axhline(y=who_lim[pollutant], color="#c0392b", linestyle=":",
                             linewidth=1.2, alpha=0.9, label="Batas WHO")
            ax_s.set_xlabel("Musim", fontsize=9.5)
            ax_s.set_ylabel(f"{pollutant} (µg/m³)", fontsize=9.5)
            ax_s.set_title(f"Distribusi {pollutant} per Musim", fontsize=11, fontweight="bold")
            ax_s.legend(fontsize=8.5)
            fig_s = set_chart_style(fig_s, ax_s)
            st.pyplot(fig_s, use_container_width=True)
            plt.close()

        with st.container(border=True):
            st.markdown("**Insight Pola Temporal**")
            st.markdown("""
            - **Pola Jam Harian**: PM2.5 memuncak di pagi hari (07.00–09.00 waktu sibuk lalu lintas) dan malam hari (21.00–23.00 waktu memasak/pemanas gedung). Konsentrasi terendah berada di siang hari (14.00–16.00) saat radiasi matahari memicu percampuran udara secara vertikal.
            - **Pola Musiman**: Musim Dingin mencatat konsentrasi polutan tertinggi dengan rentang dispersi terlebar, sementara Musim Panas mencatat kualitas udara paling bersih.
            """)

# ============================================================
# HALAMAN: KESIMPULAN
# ============================================================
elif page == "Kesimpulan":
    st.title("Kesimpulan & Rekomendasi")
    st.caption("Ringkasan temuan analisis dan rekomendasi tindakan")
    st.divider()

    st.subheader("Kesimpulan")

    with st.container(border=True):
        st.markdown("**Kesimpulan Pertanyaan 1: Tren Bulanan**")
        st.write(
            "Tren konsentrasi PM2.5 dan PM10 di Beijing menunjukkan pola musiman yang sangat jelas "
            "selama periode 2013–2017. Tingkat polusi udara paling tinggi terjadi pada bulan Desember dan "
            "Januari (musim dingin), dengan rata-rata PM2.5 mencapai lebih dari 100 µg/m³ — melampaui "
            "batas aman WHO sebesar 25 µg/m³ hingga empat kali lipat. Sebaliknya, bulan Agustus mencatat tingkat "
            "PM2.5 terendah yang bertepatan dengan musim panas dan periode curah hujan lebih tinggi. Faktor musiman "
            "sangat dominan, terutama didorong oleh aktivitas pemanas gedung berbahan bakar batu bara serta kondisi "
            "inversi atmosfer di musim dingin."
        )

    with st.container(border=True):
        st.markdown("**Kesimpulan Pertanyaan 2: Stasiun & Faktor Meteorologi**")
        st.write(
            "Terdapat perbedaan konsentrasi yang signifikan antar stasiun pemantauan. "
            "Stasiun perkotaan dan pusat aktivitas seperti Dongsi, Wanshouxigong, dan Nongzhanguan "
            "mencatat rata-rata PM2.5 tertinggi karena volume transportasi dan konsentrasi aktivitas yang padat, sedangkan "
            "Stasiun Dingling di kawasan pinggiran mencatat rata-rata terendah. Analisis korelasi "
            "menunjukkan bahwa suhu dan kecepatan angin berkorelasi negatif dengan PM2.5 "
            "(membantu dispersi polutan), sementara kelembaban (DEWP) berkorelasi positif dengan PM2.5."
        )

    with st.container(border=True):
        st.markdown("**Kesimpulan Analisis Lanjutan: Binning & Geospatial Analysis**")
        st.write(
            "1. Clustering (Binning AQI) membuktikan disparitas paparan polusi: Stasiun Dingling mencatat 46.4% waktu dalam kategori 'Baik', "
            "sementara stasiun pusat kota mencatat lebih dari 26% waktu dalam kategori 'Berbahaya' dan 'Sangat Tidak Sehat'.\n"
            "2. Geospatial Analysis mengidentifikasi gradien spasial Utara-Selatan yang tegas: wilayah utara terproteksi pegunungan Yanshan "
            "sehingga lebih bersih, sedangkan cekungan selatan-tengah menampung emisi urban serta limpasan industri dari provinsi Hebei."
        )

    st.subheader("Rekomendasi Tindakan")

    recs = [
        ("Kebijakan Pengendalian Musim Dingin",
         "Memperketat pengawasan emisi industri dan percepatan transisi pemanas batu bara ke energi yang lebih bersih, terutama menjelang bulan Oktober hingga Februari."),
        ("Pengelolaan Transportasi & Zonasi Emisi",
         "Penerapan zona emisi rendah (Low Emission Zone) di stasiun pusat kota dengan tingkat PM2.5 tertinggi, serta penguatan jaringan transportasi publik ramah lingkungan."),
        ("Sistem Peringatan Dini Berbasis Cuaca",
         "Pemanfaatan model prediksi kualitas udara berbasis parameter meteorologi (kecepatan angin, suhu, tekanan udara) untuk memberikan informasi preventif kepada masyarakat."),
        ("Optimalisasi Jaringan Pemantauan",
         "Mempertahankan pemantauan berkala dan memperluas integrasi sensor di titik-titik rawan polusi untuk mendukung evaluasi kebijakan secara akurat."),
    ]

    col_left, col_right = st.columns(2)
    for i, (title, desc) in enumerate(recs):
        col = col_left if i % 2 == 0 else col_right
        with col:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.write(desc)

    st.subheader("Perbandingan dengan Standar WHO")

    avg_vals = df[["PM2.5","PM10","SO2","NO2"]].mean()
    who_vals = {"PM2.5": 25, "PM10": 50, "SO2": 20, "NO2": 40}

    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(who_vals))
    w = 0.32
    ax.bar(x - w/2, [avg_vals[k] for k in who_vals], w,
           color="#e74c3c", alpha=0.85, edgecolor="#cbd5e1", linewidth=0.6, label="Rata-rata Beijing")
    ax.bar(x + w/2, list(who_vals.values()), w,
           color="#2ecc71", alpha=0.85, edgecolor="#cbd5e1", linewidth=0.6, label="Batas Aman WHO")
    ax.set_xticks(x)
    ax.set_xticklabels(list(who_vals.keys()), fontsize=10)
    ax.set_ylabel("Konsentrasi (µg/m³)", fontsize=10)
    ax.set_title("Rata-rata Polutan Beijing vs Batas Aman WHO", fontsize=11, fontweight="bold")
    ax.legend(fontsize=9)
    fig = set_chart_style(fig, ax)
    st.pyplot(fig, use_container_width=True)
    plt.close()
