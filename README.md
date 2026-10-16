# SolarClean AI Research 3.0 — mustaqil ilmiy modul

Bu loyiha mavjud SolarClean AI 2.0 dasturini o‘zgartirmaydi. Yangi `research_app.py` alohida ishlaydi.

```powershell
python -m pip install streamlit pandas numpy pytest
python -m streamlit run research_app.py
python -m pytest -q tests
```

CSV ustunlari: `timestamp`, `power_dirty_w`, `power_clean_w`, `irradiance_poa_wm2`, `temp_dirty_c`, `temp_clean_c`.

**Faqat haqiqiy ikkita mustaqil o‘lchangan, kalibrlangan panel bo‘lsa** `verified_measurements` belgilang. Oddiy simulyatsiyada qaror `INSUFFICIENT DATA` qolishi kerak.

Model prototype-level; verification flag self-declared; device/safety certification or scientific validation claim is not made.

`ILMIY_KONSEPSIYA.md`da manba maqola bilan farqlar, 3 ta muqobil model, asosiy formulalar, 12/36 oylik tajriba va novelty cheklovlari berilgan.
