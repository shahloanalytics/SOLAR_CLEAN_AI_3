"""SolarClean Research 3.0: an experimental decision aid, not a validated controller.

All values must be measured or explicitly marked as simulation. Two-reference
attribution requires matched instrument channels and clean-baseline calibration.
"""
from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd

REQUIRED = ['timestamp','power_dirty_w','power_clean_w','irradiance_poa_wm2','temp_dirty_c','temp_clean_c']

@dataclass(frozen=True)
class Assessment:
    status: str
    soiling_ratio: Optional[float]
    loss_fraction: Optional[float]
    samples_used: int
    diagnostics: str

def assess_paired_panels(df: pd.DataFrame, clean_baseline_ratio: Optional[float],
                          gamma_dirty: float = -0.004, gamma_clean: float = -0.004,
                          min_irradiance: float = 400.0, min_samples: int = 10) -> Assessment:
    """Compare calibrated, co-planar reference channels under simultaneous irradiance.

    clean_baseline_ratio: median(P_dirty_temp_corrected / P_clean_temp_corrected)
    measured while BOTH devices were clean, with independent meter channels.
    Gamma are module-relative STC power temperature coefficients, 1/deg C.
    This is a teaching estimator, NOT full IEC 61724-1 conformity.
    """
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return Assessment('INSUFFICIENT DATA',None,None,0,'Yetishmayotgan ustunlar: '+', '.join(missing))
    if clean_baseline_ratio is None or not np.isfinite(clean_baseline_ratio) or clean_baseline_ratio <= 0:
        return Assessment('INSUFFICIENT DATA',None,None,0,'Ikki panel toza bo‘lgan bazaviy kalibrlash nisbati talab qilinadi.')
    if not (-0.02 < gamma_dirty < 0 and -0.02 < gamma_clean < 0):
        return Assessment('INSUFFICIENT DATA',None,None,0,'Harorat koeffitsiyentlarini panel pasportidan kiriting.')
    d=df[REQUIRED].copy()
    d['timestamp']=pd.to_datetime(d['timestamp'], errors='coerce')
    for c in REQUIRED[1:]: d[c]=pd.to_numeric(d[c], errors='coerce')
    d=d.dropna().sort_values('timestamp')
    d=d[(d['irradiance_poa_wm2']>=min_irradiance)&(d['power_dirty_w']>0)&(d['power_clean_w']>0)]
    d=d[d['timestamp'].diff().dt.total_seconds().fillna(1)>0]  # discard duplicate timestamp
    # Equivalent power at 25C (linear-temperature model valid only within physical range).
    d=d[d['temp_dirty_c'].between(-20,85)&d['temp_clean_c'].between(-20,85)]
    f_dirty=1+gamma_dirty*(d['temp_dirty_c']-25)
    f_clean=1+gamma_clean*(d['temp_clean_c']-25)
    d=d[(f_dirty>0)&(f_clean>0)]
    f_dirty=1+gamma_dirty*(d['temp_dirty_c']-25)
    f_clean=1+gamma_clean*(d['temp_clean_c']-25)
    if len(d)<min_samples:
        return Assessment('INSUFFICIENT DATA',None,None,len(d),'Yetarli juft, yuqori nurlanishli kuzatuv yo‘q.')
    ratios=((d['power_dirty_w']/f_dirty)/(d['power_clean_w']/f_clean))/clean_baseline_ratio
    ratios=ratios.replace([np.inf,-np.inf],np.nan).dropna()
    # Sensor faults and shading should be investigated, never silently treated as soil.
    if (ratios<0.5).any() or (ratios>1.15).any():
        return Assessment('INSPECT SYSTEM',None,None,len(ratios),'Katta nomuvofiqlik: soya, sensor, invertor yoki kalibrlashni tekshiring.')
    sr=float(ratios.median())
    return Assessment('PROVISIONAL MEASUREMENT',sr,max(0.0,1-sr),len(ratios),
                      'Kalibrlangan juft panel bahosi; o‘lchov noaniqligi va oldin/keyin validatsiyasi zarur.')

def evaluate_cleaning(sr: Optional[float], sr_upper: Optional[float],
                      future_clean_energy_kwh: Optional[float], tariff_uzs_kwh: float,
                      cleaning_cost_uzs: float, water_liters: float,
                      water_budget_liters: float, verified_measurements: bool = False):
    """Conservative scenario: recovered energy=(1-SR)*clean-reference yield.

    Forecast Eclean and uncertainty are external inputs; do not claim trained ML.
    No cleaning command is permitted until the paired panel measurements are verified.
    """
    nums=[sr,sr_upper,future_clean_energy_kwh,tariff_uzs_kwh,cleaning_cost_uzs,water_liters,water_budget_liters]
    if any(x is None or not np.isfinite(x) for x in nums):
        return {'decision':'INSUFFICIENT DATA','reason':'Zarur parametrlar yoki noaniqlik chegarasi yo‘q.'}
    if not(0<sr<=1.05 and sr<=sr_upper<=1.05) or any(v<0 for v in nums[2:]):
        return {'decision':'INSPECT SYSTEM','reason':'Noto‘g‘ri yoki fizik jihatdan mos kelmaydigan parametrlar.'}
    low_recovery=max(0.,(1-sr_upper)*future_clean_energy_kwh)
    point_recovery=max(0.,(1-sr)*future_clean_energy_kwh)
    net_min=low_recovery*tariff_uzs_kwh-cleaning_cost_uzs
    result={'estimated_recovery_kwh':round(point_recovery,3),
            'conservative_recovery_kwh':round(low_recovery,3),
            'net_point_uzs':round(point_recovery*tariff_uzs_kwh-cleaning_cost_uzs,2),
            'net_min_uzs':round(net_min,2),
            'water_liters':water_liters}
    if not verified_measurements:
        result.update(decision='INSUFFICIENT DATA',reason='O‘lchovlar hali mustaqil tasdiqlanmagan.');return result
    if water_liters>water_budget_liters:
        result.update(decision='WAIT',reason='Suv byudjeti cheklovi bajarilmadi.');return result
    if net_min>0:
        result.update(decision='CLEAN NOW',reason='Konservativ iqtisodiy ssenariyda ham sof foyda musbat.');return result
    result.update(decision='WAIT',reason='Konservativ iqtisodiy ssenariyda sof foyda musbat emas.');return result
