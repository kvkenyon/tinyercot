from collections.abc import AsyncIterator, Iterator
from datetime import date, datetime
from decimal import Decimal
from typing import assert_type

from tinyercot import Archive, Client, Page, np3_966_er, np3_988_er, np4_190_cd

with Client() as client:
    result = client.np4_190_cd.dam_stlmnt_pnt_prices(deliveryDateFrom=date(2026, 1, 1))
    assert_type(result, Page[np4_190_cd.DamStlmntPntPricesRow])
    assert_type(result.data[0].settlementPointPrice, Decimal | None)
    assert_type(
        client.np4_190_cd.dam_stlmnt_pnt_prices_iter(),
        Iterator[np4_190_cd.DamStlmntPntPricesRow],
    )
    assert_type(
        client.np4_190_cd.dam_stlmnt_pnt_prices_iter_async(),
        AsyncIterator[np4_190_cd.DamStlmntPntPricesRow],
    )

    assert_type(
        client.np4_190_cd.dam_stlmnt_pnt_prices_history,
        Archive[np4_190_cd.DamStlmntPntPricesRow],
    )
    assert_type(
        client.np4_190_cd.dam_stlmnt_pnt_prices_history.rows(
            where=lambda row: row.settlementPoint == "HB_HOUSTON"
        ),
        Iterator[np4_190_cd.DamStlmntPntPricesRow],
    )

    assert_type(
        client.np3_966_er._60_dam_load_res_data_history,
        Archive[np3_966_er._60DamLoadResDataHistoryRow],
    )

    assert_type(
        client.np3_988_er.resources_history,
        Archive[np3_988_er.ResourcesHistoryRow],
    )

    for row in client.eia_930_er.daily_operations_history.read(b""):
        assert_type(row.HR1, Decimal | datetime | None)

    for outage in client.np1_346_er.outages_history.rows():
        assert_type(outage.plannedEndDate, datetime | None)
        assert_type(outage.availableMWMaximum, Decimal | None)
    for response in client.np3_108.demand_response_history.rows():
        assert_type(response.month, date | None)
        assert_type(response.sourceSheet, str | None)

    for solar in client.np4_737_cd.spp_hrly_avrg_actl_fcast_history.rows():
        assert_type(solar.hourEndingTimestamp, datetime | None)
        assert_type(solar.genSystemWide, Decimal | None)
    for wind in client.np4_733_cd.wpp_actual_5min_avg_values_history.rows():
        assert_type(wind.LZWestNorth, Decimal | None)

    for price in client.np6_322_cd.sced_system_lambda_history.rows():
        assert_type(price.systemLambda, Decimal | None)
        assert_type(price.cappedSystemLambda, Decimal | None)
    for adder in client.np6_323_cd.rt_price_adder_sced_history.rows():
        assert_type(adder.RTORPA, Decimal | None)
        assert_type(adder.RTRDPA, Decimal | None)

    for forecast in client.np3_561_cd._7d_load_fcast_by_wzn_history.rows():
        assert_type(forecast.hourEnding, str | None)
        assert_type(forecast.coast, Decimal | None)
        assert_type(forecast.postedDatetime, datetime | None)
    for interval in client.np3_562_cd.ih_load_fcast_by_wzn_history.rows():
        assert_type(interval.intervalEnding, datetime | None)
        assert_type(interval.inUseFlag, bool | None)

    for capacity in client.np3_233_cd.hourly_res_outage_cap_history.rows():
        assert_type(capacity.totalResourceMW, int | None)
    for adequacy in client.np3_763_cd.st_sys_adequacy_history.rows():
        assert_type(adequacy.hourEnding, str | None)
    for ruc in client.np3_764_cd.hrly_ruc_online_sced_offline_cop_history.rows():
        assert_type(ruc.sumSCEDTotal, Decimal | None)

    for offers in client.np4_179_cd.total_as_service_offers_history.rows():
        assert_type(offers.RRS, Decimal | None)
        assert_type(offers.RRSPFR, Decimal | None)
    for cap in client.np4_791_cd.da_sw_offer_caps_history.rows():
        assert_type(cap.SWCAP, Decimal | None)

    for renewable in client.np4_442_cd.hrly_sys_reg_wind_fcast_model_history.rows():
        assert_type(renewable.region, str | None)
        assert_type(renewable.model, str | None)
        assert_type(renewable.inUseFlag, bool | None)
    for solar_interval in client.np4_752_cd.ih_solar_fcast_geo_history.rows():
        assert_type(solar_interval.intervalEnding, datetime | None)
        assert_type(solar_interval.value, Decimal | None)

    for factor in client.np5_527_cd.druc_as_deploy_factors_history.rows():
        assert_type(factor.RUCTimestamp, datetime | None)
        assert_type(factor.deliveryDate, date | None)
        assert_type(factor.deliveryHour, str | None)
        assert_type(factor.ASDeploymentFactors, Decimal | None)

    for point in client.np4_214_cd.druc_as_demand_curves_history.rows():
        assert_type(point.RUCTimestamp, datetime | None)
        assert_type(point.demandCurvePoint, Decimal | None)
        assert_type(point.quantity, Decimal | None)
        assert_type(point.price, Decimal | None)

    for indicative in client.np6_329_cd.rtd_ind_mcpc_history.rows():
        assert_type(indicative.RTDTimestamp, datetime | None)
        assert_type(indicative.intervalEnding, datetime | None)
        assert_type(indicative.intervalRepeatHourFlag, bool | None)
    for clearing in client.np6_332_cd.rt_clear_price_cap_sced_history.rows():
        assert_type(clearing.cappedMCPC, Decimal | None)
        assert_type(clearing.uncappedMCPC, Decimal | None)

    for constraint in client.np5_755_cd.hrly_ruc_act_and_bind_tran_const_history.rows():
        assert_type(constraint.RUCTimestamp, datetime | None)
        assert_type(constraint.constraintID, int | None)
        assert_type(constraint.fromStationkV, Decimal | None)
    for lmp in client.np6_970_cd.rtd_lmp_node_zone_hub_history.rows():
        assert_type(lmp.RTDTimestamp, datetime | None)
        assert_type(lmp.intervalEnding, datetime | None)
        assert_type(lmp.LMP, Decimal | None)

    for distribution in client.np4_159_cd.load_distribution_factors_history.rows():
        assert_type(distribution.loadId, str | None)
        assert_type(distribution.MRIDLoad, str | None)
        assert_type(distribution.distributionFactor, Decimal | None)
    for bus in client.np4_231_cd.electrical_bus_map_heur_price_history.rows():
        assert_type(bus.fromEBName, str | None)
        assert_type(bus.toEBName, str | None)

    for correction in client.np4_197_m.rtm_price_corrections_soglmp_history.rows():
        assert_type(correction.RTORDPAOriginal, Decimal | None)
        assert_type(correction.RTRDPAOriginal, Decimal | None)
    for bus_correction in client.np4_196_m.dam_price_corrections_eblmp_history.rows():
        assert_type(bus_correction.electricalBus, str | None)
        assert_type(bus_correction.LMPCorrected, Decimal | None)

    for sog_price in client.np6_327_cd.lmp_sog_price_adders_history.rows():
        assert_type(sog_price.meterName, str | None)
        assert_type(sog_price.RTORPA, Decimal | None)
        assert_type(sog_price.RTORDPA, Decimal | None)
        assert_type(sog_price.RTRDPA, Decimal | None)
    for assumption in client.np4_722_cd.weather_assumptions_history.rows():
        assert_type(assumption.deliveryDate, date | None)
        assert_type(assumption.coast, Decimal | None)

    for offer_point in client.np4_19_cd.dam_agg_as_offer_curve_history.rows():
        assert_type(offer_point.ancillaryType, str | None)
        assert_type(offer_point.price, Decimal | None)
        assert_type(offer_point.quantity, Decimal | None)

    for (
        highest_bid
    ) in client.np3_257_ex._3d_high_price_bids_sel_disp_sced_history.rows():
        assert_type(highest_bid.batchId, str | None)
        assert_type(highest_bid.highestPriceDispatched, Decimal | None)
    for highest_as in client.np3_914_ex._3d_sced_high_as_offers_history.rows():
        assert_type(highest_as.resourceName, str | None)
        assert_type(highest_as.price, Decimal | None)
    for highest_dam in client.np3_915_ex._3d_dam_high_as_offers_history.rows():
        assert_type(highest_dam.deliveryDate, date | None)
        assert_type(highest_dam.qseName, str | None)
    for highest_sced in client.np3_916_ex._3d_highest_price_offer_sced_history.rows():
        assert_type(highest_sced.batchId, str | None)
        assert_type(highest_sced.LMP, Decimal | None)
