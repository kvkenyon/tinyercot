from collections.abc import AsyncIterator, Iterator
from datetime import date, datetime
from decimal import Decimal
from typing import assert_type

from tinyercot import (
    Archive,
    Client,
    Document,
    FuelMixArchive,
    FuelMixDay,
    FuelMixTotal,
    LegacyHourlyLoad,
    LoadArchive,
    LoadProfileAdjustment,
    LoadProfileDay,
    Page,
    Publication,
    ScheduledGeneration,
    WeatherZoneLoad,
    np3_561_cd,
    np3_966_er,
    np3_988_er,
    np4_190_cd,
)

with Client() as client:
    assert_type(
        client.zonal_generation.rows(date_from=date(2001, 7, 31)),
        Iterator[ScheduledGeneration],
    )
    assert_type(client.zonal_generation.read(b""), Iterator[ScheduledGeneration])
    assert_type(client.zonal_generation.download(), bytes)

with Client() as client:
    assert_type(client.fuel_mix.archives(), list[FuelMixArchive])
    assert_type(client.fuel_mix.rows(date_from=date(2007, 1, 1)), Iterator[FuelMixDay])
    assert_type(client.fuel_mix.summaries(year_from=2007), Iterator[FuelMixTotal])
    assert_type(client.fuel_mix.read(b""), Iterator[FuelMixDay])

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

    for sced_curve in client.np3_906_ex._2day_agg_sced_as_offers_regdn_history.rows():
        assert_type(sced_curve.SCEDTimestamp, datetime | None)
        assert_type(sced_curve.MWOffered, Decimal | None)
        assert_type(sced_curve.REGDNOfferPrice, Decimal | None)
    for dam_curve in client.np3_907_ex._2d_agg_edc_north_history.rows():
        assert_type(dam_curve.deliveryDate, date | None)
        assert_type(dam_curve.MW, Decimal | None)
        assert_type(dam_curve.price, Decimal | None)

    for ptp_bid in client.np3_909_er._2d_ptp_obl_bids_history.rows():
        assert_type(ptp_bid.bidId, str | None)
        assert_type(ptp_bid.PTPBidAwardMW, Decimal | None)
    for gen_summary in client.np3_910_er._2d_agg_gen_summary_history.rows():
        assert_type(gen_summary.sumBasePointNonWGR, Decimal | None)
        assert_type(gen_summary.sumBasePointNonIRR, Decimal | None)

    for legacy_curve in client.np3_908_er._2d_agg_esc_non_wind_history.rows():
        assert_type(legacy_curve.MW, Decimal | None)
        assert_type(legacy_curve.price, Decimal | None)
    for demand_curve in client.np3_908_er._2d_agg_edc_clr_history.rows():
        assert_type(demand_curve.price, int | None)
        assert_type(demand_curve.SCEDTimestamp, datetime | None)
    for old_dam_curve in client.np3_908_er._2d_agg_dam_min_esc_history.rows():
        assert_type(old_dam_curve.deliveryDate, date | None)
        assert_type(old_dam_curve.MW, Decimal | None)

    for legacy_rrs in client.np3_911_er._2d_cleared_dam_as_rrsload_history.rows():
        assert_type(legacy_rrs.totalClearedASRRSLOAD, Decimal | None)
    for dam_rrs in client.np3_911_er._2d_agg_dam_as_offers_rrspfr_history.rows():
        assert_type(dam_rrs.RRSPFROfferPrice, Decimal | None)
    for aggregated_rrs in client.np3_911_er._2d_agg_as_offers_rrspfr_history.rows():
        assert_type(aggregated_rrs.RRSPFROfferPrice, Decimal | None)

    for cop_snapshot in client.np1_301._60_cop_adj_period_snapshot_history.rows():
        assert_type(cop_snapshot.hourEnding, str | None)
        assert_type(cop_snapshot.RRS, Decimal | None)
        assert_type(cop_snapshot.RRSPFR, Decimal | None)
    for obligation in client.np1_302.as_obligation_history.rows():
        assert_type(obligation.REGUPObligation, Decimal | None)
        assert_type(obligation.REGUPResponsibility, Decimal | None)
        assert_type(obligation.REGUPOblFinal, Decimal | None)

    for trigger in client.np3_987_ex._7d_trig_mcpc_50xfip_history.rows():
        assert_type(trigger.FIPx50, Decimal | None)
        assert_type(trigger.price1RRSPFR, Decimal | None)
    for sasm_award in client.np3_990_ex._60_sasm_gen_res_as_offer_awards_history.rows():
        assert_type(sasm_award.SASMId, datetime | None)
        assert_type(sasm_award.RRSAwarded, Decimal | None)
        assert_type(sasm_award.RRSPFRAwarded, Decimal | None)
    for sasm_offer in client.np3_990_ex._60_sasm_load_res_as_offers_history.rows():
        assert_type(sasm_offer.price1RRS, Decimal | None)
        assert_type(sasm_offer.price1RRSPFR, Decimal | None)

    for cop_update in client.np3_991_ex._60_cop_all_updates_history.rows():
        assert_type(cop_update.updateTime, datetime | None)
        assert_type(cop_update.submitTime, datetime | None)
        assert_type(cop_update.RRS, Decimal | None)
        assert_type(cop_update.cancelFlag, bool | None)

    for sced_resource in client.np3_965_er._60_sced_gen_res_data_history.rows():
        assert_type(sced_resource.resourceName, str | None)
        assert_type(sced_resource.SCED1CurveMW1, Decimal | None)
    for self_arranged in client.np3_965_er._60_sced_qse_self_arranged_as_history.rows():
        assert_type(self_arranged.RRSGN, Decimal | None)
        assert_type(self_arranged.RRSPFR, Decimal | None)
    for cap_override in client.np3_965_er._60d_sced_as_cap_man_override_history.rows():
        assert_type(cap_override.startTime, datetime | None)

    for sced_adder in client.np6_792_er.price_adders_history.rows():
        assert_type(sced_adder.SCEDTimestamp, datetime | None)
        assert_type(sced_adder.RTORPA, Decimal | None)
        assert_type(sced_adder.RTRDPA, Decimal | None)
        assert_type(sced_adder.RTRUCCST30HSL, Decimal | None)
        assert_type(sced_adder.RTNCLRNSCAP, Decimal | None)
    for interval_adder in client.np6_793_er.price_adders_history.rows():
        assert_type(interval_adder.deliveryDate, date | None)
        assert_type(interval_adder.RTRSVPOR, Decimal | None)

    for capability_row in client.np6_794_er.capability_history.rows():
        assert_type(capability_row.CapREGUP_RRS_ECRS_NSPINTotal, Decimal | None)
        assert_type(capability_row.SCEDTimestamp, datetime | None)
    for clearing_row in client.np6_795_er.clearing_prices_history.rows():
        assert_type(clearing_row.MCPC, Decimal | None)
        assert_type(clearing_row.cappedMCPC, Decimal | None)
        assert_type(clearing_row.uncappedMCPC, Decimal | None)
    for interval_clearing in client.np6_796_er.clearing_prices_history.rows():
        assert_type(interval_clearing.deliveryDate, date | None)

    for fuel_submission in client.np4_494_er.fuel_cost_submissions_history.rows():
        assert_type(fuel_submission.deliveryHour, int | None)
        assert_type(fuel_submission.resourceCount, int | None)
    for path_adder in client.np7_535_sg.path_adders_history.rows():
        assert_type(path_adder.source, str | None)
        assert_type(path_adder.startDate, date | None)
        assert_type(path_adder.ACI99, Decimal | None)

    for eia_hourly in client.eia_930_cd.hourly_operations_history.rows():
        assert_type(eia_hourly.dataDate, date | None)
        assert_type(eia_hourly.HR1, Decimal | datetime | None)

    for integration in client.np4_765_er.daily_values_history.rows():
        assert_type(integration.reportDate, date | None)
        assert_type(integration.installedDischargeCapacityMW, Decimal | None)
        assert_type(integration.sourceNotes, str | None)
    for record_power in client.np4_765_er.power_records_history.rows():
        assert_type(record_power.recordTime, datetime | None)
        assert_type(record_power.recordMW, Decimal | None)

    assert_type(
        client.np4_190_cd.dam_stlmnt_pnt_prices_history.rows(kind="bundle"),
        Iterator[np4_190_cd.DamStlmntPntPricesRow],
    )

    assert_type(
        client.np4_190_cd.dam_stlmnt_pnt_prices_history.backfill(
            where=lambda price: price.settlementPoint == "HB_HOUSTON"
        ),
        Iterator[np4_190_cd.DamStlmntPntPricesRow],
    )

    for percentages in client.np4_765_er.hourly_percentages_history.rows(kind="bundle"):
        assert_type(percentages.reportDate, date | None)
        assert_type(percentages.hourEnding, str | None)
        assert_type(percentages.netLoadPercent, Decimal | None)

    for legacy_load in client.np3_965_er._60_load_res_data_in_sced_history.rows():
        assert_type(legacy_load.SCEDBidCurveMW35, Decimal | None)
        assert_type(legacy_load.SCEDBidCurvePrice35, Decimal | None)
    for legacy_wind in client.np4_732_cd.wpp_hrly_avrg_actl_fcast_history.rows():
        assert_type(legacy_wind.actualLoadZoneWest, Decimal | None)
        assert_type(legacy_wind.actualLoadZoneNorth, Decimal | None)
        assert_type(legacy_wind.hourBeginningTimestamp, datetime | None)


with Client() as client:
    assert_type(client.hourly_load.archives(), list[LoadArchive])
    assert_type(
        client.hourly_load.weather_zones(date_from=date(2002, 1, 1)),
        Iterator[WeatherZoneLoad],
    )
    assert_type(client.hourly_load.read_weather_zones(b""), Iterator[WeatherZoneLoad])

with Client() as client:
    assert_type(
        client.hourly_load.legacy(date_from=date(1995, 1, 1)),
        Iterator[LegacyHourlyLoad],
    )
    assert_type(
        client.hourly_load.read_legacy(b"", filename="erceei95.txt"),
        Iterator[LegacyHourlyLoad],
    )

with Client() as client:
    forecast_publications = (
        client.np3_561_cd._7d_load_fcast_by_wzn_history.publications()
    )
    assert_type(
        forecast_publications,
        Iterator[Publication[np3_561_cd._7dLoadFcastByWznHistoryRow]],
    )
    forecast_publication = next(forecast_publications)
    assert_type(forecast_publication.document, Document)
    assert_type(
        forecast_publication.rows, Iterator[np3_561_cd._7dLoadFcastByWznHistoryRow]
    )


with Client() as client:
    sced_capacity = client.dashboards.sced_capacity()
    assert_type(sced_capacity.current.data[0].increaseGenResESRs, Decimal)
    assert_type(sced_capacity.previous.data[0].timestamp, datetime)
    ancillary_capacity = client.dashboards.ancillary_capacity()
    assert_type(
        ancillary_capacity.data.systemAvailableCapacityGroup.esrCapWEoIncreaseBp,
        Decimal,
    )
    assert_type(ancillary_capacity.data.regulationAwardsGroup.regUpAwd, Decimal)


with Client() as client:
    conditions = client.dashboards.real_time_conditions()
    assert_type(conditions.lastUpdated, datetime)
    assert_type(conditions.instantaneousTimeError, Decimal)
    assert_type(conditions.consecutiveBaalExceedances, int)
    assert_type(conditions.dcS, Decimal)


with Client() as client:
    lmps = client.dashboards.real_time_lmps(hubs_and_zones=True)
    assert_type(lmps.lastUpdated, datetime)
    assert_type(lmps.RTRDPA, Decimal)
    assert_type(lmps.data[0].LMP, Decimal)
    assert_type(lmps.data[0].lmpWithAdderChange, Decimal)


with Client() as client:
    rtd_display = client.dashboards.indicative_prices("HB_HOUSTON")
    assert_type(rtd_display.lastSCEDTimestamp, datetime)
    assert_type(rtd_display.data[0].RTDTimestamp, datetime)
    assert_type(rtd_display.data[0].actualLMP, Decimal)
    assert_type(rtd_display.data[0].intervals[0].minutesAhead, int)
    assert_type(rtd_display.data[0].intervals[0].LMP, Decimal)


with Client() as client:
    assert_type(client.load_profiles.archives(), list[LoadArchive])
    assert_type(
        client.load_profiles.rows(profile="BUSHIDG_COAST"), Iterator[LoadProfileDay]
    )
    assert_type(
        client.load_profiles.read(b"", date_from=date(2026, 1, 1)),
        Iterator[LoadProfileDay],
    )
    profile_day = next(client.load_profiles.rows())
    assert_type(profile_day.intervals[0].energyKWh, Decimal | None)
    assert_type(profile_day.sourceAddTime, datetime | None)
    assert_type(profile_day.profileType, str)
    assert_type(profile_day.weatherZone, str)
    assert_type(client.load_profiles.adjustments(), Iterator[LoadProfileAdjustment])
    assert_type(
        client.load_profiles.read_adjustments(b""), Iterator[LoadProfileAdjustment]
    )
