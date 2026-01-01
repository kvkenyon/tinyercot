from datetime import date

import tinyercot

results = tinyercot.np4_190_cd.dam_stlmnt_pnt_prices(
    deliveryDateFrom=date(2025, 12, 29), settlementPoint="HB_HOUSTON"
)

print(results.head())


results = tinyercot.np3_233_cd.hourly_res_outage_cap(
    operatingDateFrom=date(2025, 12, 12), operatingDateTo=date(2025, 12, 13)
)
print(results.head())

results = tinyercot.np3_565_cd.lf_by_model_weather_zone(
    deliveryDateFrom=date(2025, 12, 22), deliveryDateTo=date(2025, 12, 23)
)
print(results.head())

results = tinyercot.np3_566_cd.lf_by_model_study_area(
    deliveryDateFrom=date(2025, 12, 22), deliveryDateTo=date(2025, 12, 23)
)
print(results.head())
