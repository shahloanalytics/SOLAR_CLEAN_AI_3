"""SolarClean AI Research 3.0 — o‘zbek tilidagi ilmiy-tajriba interfeysi.

Faylni research_engine.py bilan bitta papkaga joylashtiring.
Bu dastur haqiqiy changlanishni mustaqil tasdiqlamaydi.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from research_engine import assess_paired_panels, evaluate_cleaning

st.set_page_config(
    page_title="SolarClean AI Research 3.0",
    page_icon="☀️",
    layout="wide",
)

# Interfeys uslubi
st.markdown("""
<style>
.block-container {max-width: 1180px; padding-top: 1.5rem;}
h1, h2, h3 {letter-spacing: -.025em;}
[data-testid="stMetric"] {background: #f7fafb; padding: 1rem; border-radius: .8rem; border: 1px solid #dde7e9;}
</style>
""", unsafe_allow_html=True)

st.title("☀️ SolarClean AI Research 3.0")
st.subheader("Quyosh panellarining changlanishini ilmiy baholash")
st.caption(
    "Toza nazorat paneli va changlanadigan tajriba panelini taqqoslashga asoslangan "
    "tadqiqot prototipi. Sertifikatlangan boshqaruv tizimi emas."
)
st.warning(
    "**Ilmiy ogohlantirish:** sintetik ma’lumotlar real o‘lchov hisoblanmaydi. "
    "Kichik ishlab chiqarish farqi har doim changlanishni anglatmaydi."
)

with st.expander("📘 Dastur qanday ishlaydi?", expanded=False):
    st.markdown("""
    1. Bir vaqtda o‘lchangan **toza nazorat** va **tajriba** panellari ma’lumotlarini yuklaysiz.
    2. Ikkala panel toza bo‘lgan paytda aniqlangan **bazaviy quvvat nisbati**ni kiritasiz.
    3. Dastur harorat ta’sirini soddalashtirib hisobga olib, panellar nisbatini baholaydi.
    4. Natija va kiritilgan iqtisodiy farazlar asosida **shartli tozalash qarori** chiqariladi.

    **Eslatma:** statistik ishonch oralig‘i avtomatik hisoblanmaydi;
    yuqori chegara foydalanuvchi tomonidan kiritiladi.
    """)

st.markdown("### 1. Ma’lumotlarni yuklash")
yuklangan_fayl = st.file_uploader(
    "Ikkala panelning sinxron o‘lchovlari saqlangan CSV faylini tanlang",
    type=["csv"],
)

with st.expander("CSV fayl qanday tuzilgan bo‘lishi kerak?"):
    st.code(
        "timestamp,power_dirty_w,power_clean_w,irradiance_poa_wm2,temp_dirty_c,temp_clean_c\n"
        "2026-10-01 10:00:00,198,205,750,42,41\n"
        "2026-10-01 10:15:00,201,210,770,43,42",
        language="csv",
    )
    st.caption(
        "Quvvat — W, nurlanish — W/m², harorat — °C. "
        "Kamida 10 ta yaroqli sinxron kuzatuv kerak."
    )

ma_lumot_turi = st.radio(
    "Yuklanayotgan ma’lumot turi",
    ["Sintetik (sinov uchun)", "Haqiqiy o‘lchov (mustaqil tasdiqlanmagan)"],
    help="Ushbu belgi foydalanuvchi bayonoti; tizim ma’lumot manbasini avtomatik tasdiqlamaydi.",
)

bazaviy_nisbat = st.number_input(
    "Ikkala panel toza paytdagi bazaviy nisbat (tajriba / nazorat)",
    min_value=0.01, max_value=2.0, value=1.0, step=0.01, format="%.3f",
    help="Bu qiymat ikkala panel ham toza paytda alohida kalibrlashda olinishi kerak. "
         "1.0 — faqat sinov uchun taxminiy boshlang‘ich qiymat.",
)

if yuklangan_fayl is None:
    st.info("Davom etish uchun yuqoridagi maydonga CSV fayl yuklang.")
    st.stop()

try:
    jadval = pd.read_csv(yuklangan_fayl)
except Exception as xato:
    st.error(f"CSV faylni o‘qib bo‘lmadi: {xato}")
    st.stop()

st.caption(f"Yuklangan fayl: {yuklangan_fayl.name} · {len(jadval)} ta dastlabki qator")

with st.expander("📋 Yuklangan ma’lumotlarni ko‘rish", expanded=False):
    st.dataframe(jadval, use_container_width=True, hide_index=True)

# Asosiy diagnostika: research_engine.py dagi matematik hisoblash o‘zgarmaydi.
baho = assess_paired_panels(jadval, bazaviy_nisbat)

st.divider()
st.markdown("### 2. Changlanish diagnostikasi")

holat_tarjimasi = {
    "PROVISIONAL MEASUREMENT": "Dastlabki baho — mustaqil tasdiqlanmagan",
    "INSUFFICIENT DATA": "Ma’lumotlar yetarli emas",
    "INSPECT SYSTEM": "Uskuna yoki ma’lumotlarni tekshirish kerak",
    "VALIDATED": "Tasdiqlangan o‘lchov",
}

holat_matni = holat_tarjimasi.get(baho.status, baho.status)
if baho.status == "PROVISIONAL MEASUREMENT":
    st.info(f"**O‘lchov holati:** {holat_matni}")
elif baho.status == "INSUFFICIENT DATA":
    st.warning(f"**O‘lchov holati:** {holat_matni}")
else:
    st.warning(f"**O‘lchov holati:** {holat_matni}")

ustun1, ustun2, ustun3 = st.columns(3)
with ustun1:
    st.metric(
        "Changlanish nisbati (SR)",
        f"{baho.soiling_ratio:.4f}" if baho.soiling_ratio is not None else "Aniqlanmadi",
    )
with ustun2:
    st.metric(
        "Taxminiy energiya yo‘qotishi",
        f"{baho.loss_fraction * 100:.2f}%" if baho.loss_fraction is not None else "Aniqlanmadi",
    )
with ustun3:
    st.metric("Foydalanilgan kuzatuvlar", f"{baho.samples_used} ta")

if baho.loss_fraction is None:
    st.warning(
        "Changlanish yo‘qotishini baholash imkoni bo‘lmadi. "
        "CSV ustunlari, kalibrlash va sensordagi mumkin bo‘lgan xatolarni tekshiring."
    )
elif baho.loss_fraction < 0.01:
    st.success(
        "Ushbu kuzatuvlarda sezilarli musbat changlanish yo‘qotishi aniqlanmadi. "
        "Kichik tafovut o‘lchov shovqini bilan bog‘liq bo‘lishi mumkin."
    )
elif baho.loss_fraction < 0.10:
    st.info(
        "Changlanish bilan bog‘liq bo‘lishi mumkin bo‘lgan energiya yo‘qotishi baholandi. "
        "Sababni mustaqil tajribada tekshirish zarur."
    )
else:
    st.warning(
        "Nisbatan yuqori ehtimoliy yo‘qotish baholandi. "
        "Tozalashdan oldin soyalanish, panel nosozligi va sensor xatolarini tekshiring."
    )

st.caption(
    "Izoh: 1% va 10% chegaralar faqat tushuntirish uchun shartli tanlangan; "
    "ular ilmiy tasdiqlangan me’yorlar emas."
)

if baho.status == "PROVISIONAL MEASUREMENT":
    st.markdown(
        "**Diagnostika sharhi:** haroratga tuzatish kiritilgan juft panel nisbati "
        "hisoblangan. O‘lchov noaniqligi, bazaviy kalibrlash va tozalashdan oldingi/keyingi "
        "tajribalar bilan natija tasdiqlanishi kerak."
    )
else:
    st.markdown(f"**Diagnostika izohi:** {baho.diagnostics}")

if baho.soiling_ratio is None:
    st.stop()

st.divider()
st.markdown("### 3. Tozalashning iqtisodiy bahosi")
st.caption("Quyidagi hisoblashlar kelgusi davr uchun kiritilgan farazlarga asoslanadi.")

# Ushbu chegara statistik tahlildan chiqmaydi: uni foydalanuvchi belgilaydi.
minimal_chegara = float(baho.soiling_ratio)
if minimal_chegara > 1.05:
    st.error("Changlanish nisbati 1.05 dan yuqori. Kalibrlash va ma’lumotlarni tekshiring.")
    st.stop()

yuqori_chegara = st.number_input(
    "SR yuqori chegarasi (qo‘lda kiritiladigan taxmin)",
    min_value=minimal_chegara,
    max_value=1.05,
    value=min(1.05, minimal_chegara + 0.05),
    step=0.005,
    format="%.4f",
    help="Bu haqiqiy statistik ishonch chegarasi emas. "
         "Agar mustaqil hisoblangan noaniqlik bo‘lmasa, tavsiya ham shartli bo‘ladi.",
)

chap, ong = st.columns(2)
with chap:
    kelgusi_energiya = st.number_input(
        "Kelgusi davrda toza paneldan kutilayotgan energiya (kWh)",
        min_value=0.0, value=100.0, step=10.0,
    )
    tarif = st.number_input("Elektr energiyasi qiymati (so‘m/kWh)", min_value=0.0, value=1000.0, step=100.0)
    tozalash_xarajati = st.number_input("Bir martalik tozalash xarajati (so‘m)", min_value=0.0, value=25000.0, step=1000.0)
with ong:
    suv_sarfi = st.number_input("Bir martalik tozalashga suv sarfi (litr)", min_value=0.0, value=5.0, step=1.0)
    suv_limiti = st.number_input("Mavjud suv limiti (litr)", min_value=0.0, value=20.0, step=1.0)

if ma_lumot_turi.startswith("Sintetik"):
    st.info("Sintetik ma’lumot bilan haqiqiy tozalash topshirig‘i chiqarilmaydi.")
    tasdiqlangan = False
else:
    tasdiqlangan = st.checkbox(
        "Asboblar kalibrlangan va haqiqiy o‘lchovlar mustaqil tekshirilgan",
        value=False,
        help="Faqat hujjatlashtirilgan tekshiruv mavjud bo‘lsa belgilang.",
    )

qaror = evaluate_cleaning(
    baho.soiling_ratio,
    yuqori_chegara,
    kelgusi_energiya,
    tarif,
    tozalash_xarajati,
    suv_sarfi,
    suv_limiti,
    tasdiqlangan,
)

st.markdown("### 4. Iqtisodiy natijalar va qaror")
k1, k2, k3 = st.columns(3)
with k1:
    st.metric("Tiklanadigan energiya (taxmin)", f"{qaror.get('estimated_recovery_kwh', 0):,.3f} kWh")
with k2:
    st.metric("Taxminiy sof iqtisodiy natija", f"{qaror.get('net_point_uzs', 0):,.0f} so‘m")
with k3:
    st.metric("Konservativ sof natija", f"{qaror.get('net_min_uzs', 0):,.0f} so‘m")

qaror_tarjimasi = {
    "CLEAN NOW": "TOZALASH IQTISODIY JIHATDAN MAQBUL",
    "WAIT": "HOZIRCHA KUTISH TAVSIYA ETILADI",
    "INSPECT SYSTEM": "TIZIMNI TEKSHIRISH KERAK",
    "INSUFFICIENT DATA": "MA’LUMOTLAR YETARLI EMAS",
}
sabab_tarjimasi = {
    "O‘lchovlar hali mustaqil tasdiqlanmagan.": "O‘lchovlar mustaqil tasdiqlanmagan; bu hisob real tozalash buyrug‘i emas.",
    "Suv byudjeti cheklovi bajarilmadi.": "Mavjud suv limiti tozalash uchun yetarli emas.",
    "Konservativ iqtisodiy ssenariyda ham sof foyda musbat.": "Konservativ hisob bo‘yicha tiklanadigan energiya qiymati xarajatlarni qoplaydi.",
    "Konservativ iqtisodiy ssenariyda sof foyda musbat emas.": "Ehtiyotkor hisobda kutilgan foyda tozalash xarajatini qoplamaydi.",
    "Zarur parametrlar yoki noaniqlik chegarasi yo‘q.": "Hisoblash uchun zarur qiymatlar to‘liq emas.",
    "Noto‘g‘ri yoki fizik jihatdan mos kelmaydigan parametrlar.": "Kiritilgan qiymatlar fizik yoki hisoblash chegaralariga mos kelmaydi.",
}
qaror_kodi = qaror.get("decision", "INSUFFICIENT DATA")
qaror_matni = qaror_tarjimasi.get(qaror_kodi, qaror_kodi)
sabab = qaror.get("reason", "Izoh mavjud emas.")
sabab = sabab_tarjimasi.get(sabab, sabab)
if qaror_kodi == "CLEAN NOW":
    st.success(f"**{qaror_matni}** — {sabab}")
elif qaror_kodi == "WAIT":
    st.info(f"**{qaror_matni}** — {sabab}")
else:
    st.warning(f"**{qaror_matni}** — {sabab}")

st.caption(
    "Muhim: kelgusi energiya, SR yuqori chegarasi va boshqa qiymatlar tashqi farazlardir. "
    "Dastur statistik ishonch oralig‘ini yoki ML prognozini o‘zi yaratmaydi."
)

with st.expander("📄 Natijani CSV shaklida saqlash"):
    hisobot = pd.DataFrame([{
        "Ma’lumot turi": ma_lumot_turi,
        "O‘lchov holati": holat_matni,
        "Kuzatuvlar soni": baho.samples_used,
        "Changlanish nisbati": baho.soiling_ratio,
        "Taxminiy yo‘qotish (%)": None if baho.loss_fraction is None else baho.loss_fraction * 100,
        "SR yuqori taxminiy chegara": yuqori_chegara,
        "Tiklanadigan energiya (kWh)": qaror.get("estimated_recovery_kwh"),
        "Taxminiy sof foyda (so‘m)": qaror.get("net_point_uzs"),
        "Konservativ sof foyda (so‘m)": qaror.get("net_min_uzs"),
        "Qaror": qaror_matni,
        "Izoh": sabab,
    }])
    st.download_button(
        "Hisobot CSV faylini yuklab olish",
        data=hisobot.to_csv(index=False).encode("utf-8-sig"),
        file_name="solarclean_research_hisobot.csv",
        mime="text/csv",
    )

st.divider()
st.caption("SolarClean AI Research 3.0 · Ilmiy-tajriba prototipi · O‘zbekiston")
