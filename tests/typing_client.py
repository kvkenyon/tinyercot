from collections.abc import AsyncIterator, Iterator
from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal, assert_type

from tinyercot import (
    AncillaryServiceAdjustment,
    AncillaryServiceQuantity,
    AncillaryServiceRequirements,
    Archive,
    CapacityProject,
    CapacityTotals,
    Client,
    CoincidentPeakAllocation,
    CoincidentPeakDay,
    CrrTimeOfUse,
    DistributionLossCoefficient,
    Document,
    EnergyInterval,
    FuelMixArchive,
    FuelMixDay,
    FuelMixTotal,
    GenerationProfileHour,
    GenerationProfileKey,
    GenerationProfileKeySite,
    GenerationProfileKeySummary,
    GenerationProfileSite,
    HourlyLoadForecast,
    HourlyLoadScenario,
    IndicativeOrdcPrice,
    LegacyHourlyLoad,
    LoadArchive,
    LoadProfileAdjustment,
    LoadProfileCount,
    LoadProfileDay,
    LoadShedShare,
    LossFactorDay,
    MonthlyCoincidentPeak,
    MonthlyLoadForecast,
    MoraBalance,
    MoraBalanceMetric,
    MoraCapacity,
    MoraPercentile,
    MoraResource,
    MoraRiskPoint,
    MoraScenarioValue,
    Page,
    PeakDemandForecast,
    PolrUsage,
    Publication,
    PublicFile,
    ResponsiveReserveAllocation,
    RetailTransactionMonth,
    ScheduledGeneration,
    SeasonalPeakForecast,
    TransmissionLossCoefficient,
    WeatherDay,
    WeatherVariable,
    WeatherZone,
    WeatherZoneForecastValues,
    WeatherZoneLoad,
    WeatherZonePeakValues,
    WeeklyPeakForecast,
    WinterLoadForecast,
    ZonalEnergyDay,
    ZonalEnergyTotal,
    ZonalSourceNumber,
    np3_561_cd,
    np3_966_er,
    np3_988_er,
    np4_190_cd,
)

with Client() as client:
    assert_type(
        client.resource_outlook.risk_points(where=lambda r: r.event == "EEA"),
        Iterator[MoraRiskPoint],
    )
    assert_type(client.resource_outlook.read_risk_points(b""), Iterator[MoraRiskPoint])
    mora_risk_point = next(client.resource_outlook.risk_points())
    assert_type(mora_risk_point.probability, Decimal)
    assert_type(mora_risk_point.bessAvailabilityMW, Decimal | None)
    assert_type(mora_risk_point.chartHourEnding, time | None)
    assert_type(mora_risk_point.sourceFile, PublicFile | None)

with Client() as client:
    assert_type(client.zonal_energy.files(), list[PublicFile])
    assert_type(
        client.zonal_energy.rows(where=lambda r: r.kind == "load"),
        Iterator[ZonalEnergyDay],
    )
    assert_type(
        client.zonal_energy.read(b"", kind="generation"), Iterator[ZonalEnergyDay]
    )
    assert_type(
        client.zonal_energy.totals(where=lambda r: r.year == 2005),
        Iterator[ZonalEnergyTotal],
    )
    assert_type(
        client.zonal_energy.read_totals(b"", kind="load"), Iterator[ZonalEnergyTotal]
    )
    zonal_day = next(client.zonal_energy.rows())
    assert_type(zonal_day.sourceNumbers, list[ZonalSourceNumber])
    assert_type(zonal_day.intervals[0].sourceLabel, str | None)
    assert_type(zonal_day.totalMWh, Decimal | None)
    assert_type(zonal_day.sourceTimestamp, datetime | None)

with Client() as client:
    assert_type(client.distribution_loss_coefficients.files(), list[PublicFile])
    assert_type(
        client.distribution_loss_coefficients.read(b""),
        Iterator[DistributionLossCoefficient],
    )
    assert_type(
        client.distribution_loss_coefficients.rows(where=lambda r: r.year == 2026),
        Iterator[DistributionLossCoefficient],
    )
    distribution_coefficient = next(client.distribution_loss_coefficients.rows())
    assert_type(distribution_coefficient.f1, Decimal | None)
    assert_type(distribution_coefficient.kFactor, Decimal | None)
    assert_type(distribution_coefficient.baselineFrom, date | None)
    assert_type(distribution_coefficient.sourceFile, PublicFile | None)

with Client() as client:
    assert_type(client.transmission_loss_coefficients.files(), list[PublicFile])
    assert_type(
        client.transmission_loss_coefficients.read(b""),
        Iterator[TransmissionLossCoefficient],
    )
    assert_type(
        client.transmission_loss_coefficients.rows(
            where=lambda r: r.year == 2026 and r.area == "ERCOT"
        ),
        Iterator[TransmissionLossCoefficient],
    )
    coefficient = next(client.transmission_loss_coefficients.rows())
    assert_type(coefficient.slopePercentPerMW, Decimal | None)
    assert_type(coefficient.onPeakLossFactor, Decimal | None)
    assert_type(coefficient.effectiveFrom, date | None)
    assert_type(coefficient.sourceEffectivePeriod, str | None)
    assert_type(coefficient.sourceFile, PublicFile | None)
    assert_type(client.load_shed.files(), list[PublicFile])
    assert_type(client.load_shed.read(b""), Iterator[LoadShedShare])
    assert_type(
        client.load_shed.rows(where=lambda r: r.season == "winter"),
        Iterator[LoadShedShare],
    )
    operator_share = next(client.load_shed.rows())
    assert_type(operator_share.effectiveFrom, date)
    assert_type(operator_share.loadSharePercent, Decimal | None)

with Client() as client:
    assert_type(client.capacity_changes.files(), list[PublicFile])
    assert_type(
        client.capacity_changes.projects(where=lambda r: r.fuel == "Battery"),
        Iterator[CapacityProject],
    )
    assert_type(client.capacity_changes.read_projects(b""), Iterator[CapacityProject])
    assert_type(client.capacity_changes.totals(), Iterator[CapacityTotals])
    assert_type(client.capacity_changes.read_totals(b""), Iterator[CapacityTotals])
    capacity_project = next(client.capacity_changes.projects())
    assert_type(capacity_project.projectedCOD, date)
    assert_type(capacity_project.interconnectionAgreementSigned, date | str | None)
    assert_type(capacity_project.sourceFile, PublicFile | None)
    capacity_total = next(client.capacity_changes.totals())
    assert_type(capacity_total.period, int | date)
    assert_type(capacity_total.cumulativeOperationalMW, Decimal | None)

with Client() as client:
    assert_type(client.resource_outlook.files(), list[PublicFile])
    assert_type(client.resource_outlook.read_percentiles(b""), Iterator[MoraPercentile])
    assert_type(
        client.resource_outlook.percentiles(
            where=lambda r: r.metric == "wind_generation"
        ),
        Iterator[MoraPercentile],
    )
    mora_percentile = next(client.resource_outlook.percentiles())
    assert_type(mora_percentile.reportMonth, date)
    assert_type(mora_percentile.percentile, Decimal)
    assert_type(mora_percentile.hour, int | None)
    assert_type(mora_percentile.value, Decimal | None)
    assert_type(client.resource_outlook.read_resources(b""), Iterator[MoraResource])
    assert_type(
        client.resource_outlook.resources(where=lambda r: r.kind == "unit"),
        Iterator[MoraResource],
    )
    mora_resource = next(client.resource_outlook.resources())
    assert_type(mora_resource.category, str | None)
    assert_type(mora_resource.inService, int | date | str | None)
    assert_type(mora_resource.installedCapacityMW, Decimal | None)
    assert_type(mora_resource.reportedCapacityMW, Decimal | None)
    assert_type(client.resource_outlook.capacities(), Iterator[MoraCapacity])
    assert_type(client.resource_outlook.read_capacities(b""), Iterator[MoraCapacity])
    mora_capacity = next(client.resource_outlook.capacities())
    assert_type(mora_capacity.resourcePath, list[str])
    assert_type(mora_capacity.availableCapacity, list[MoraScenarioValue])
    assert_type(mora_capacity.availableCapacity[0].hourEnding, time)
    assert_type(mora_capacity.availableCapacity[0].valueMW, Decimal | None)
    assert_type(client.resource_outlook.balance(), Iterator[MoraBalance])
    assert_type(client.resource_outlook.read_balance(b""), Iterator[MoraBalance])
    mora_balance = next(client.resource_outlook.balance())
    assert_type(mora_balance.metric, MoraBalanceMetric)
    assert_type(mora_balance.values, list[MoraScenarioValue])

with Client() as client:
    assert_type(client.indicative_ordc.files(), list[PublicFile])
    assert_type(client.indicative_ordc.read(b""), Iterator[IndicativeOrdcPrice])
    assert_type(
        client.indicative_ordc.rows(where=lambda r: r.repeatedHourFlag == "Y"),
        Iterator[IndicativeOrdcPrice],
    )
    indicative_price = next(client.indicative_ordc.rows())
    assert_type(indicative_price.scedTimestamp, datetime)
    assert_type(indicative_price.sourceTimestamp, str)
    assert_type(indicative_price.rtorpa, Decimal | None)

with Client() as client:
    assert_type(client.retail_transactions.files(), list[PublicFile])
    assert_type(client.retail_transactions.read(b""), Iterator[RetailTransactionMonth])
    assert_type(
        client.retail_transactions.rows(where=lambda r: r.month.year == 2025),
        Iterator[RetailTransactionMonth],
    )
    retail_month = next(client.retail_transactions.rows())
    assert_type(retail_month.month, date)
    assert_type(retail_month.transactionCode, str | None)
    assert_type(retail_month.days[0].count, int | None)
    assert_type(retail_month.reportedTotal, int | None)
    assert_type(retail_month.reportedAveragePerDay, Decimal | None)

with Client() as client:
    assert_type(client.crr_hours.files(), list[PublicFile])
    assert_type(client.crr_hours.download(PublicFile(title="", url="")), bytes)
    assert_type(client.crr_hours.read(b""), Iterator[CrrTimeOfUse])
    assert_type(
        client.crr_hours.rows(where=lambda r: r.month.year == 2026),
        Iterator[CrrTimeOfUse],
    )
    crr_month = next(client.crr_hours.rows())
    assert_type(crr_month.month, date)
    assert_type(crr_month.peakWDHours, int)
    assert_type(client.polr.files(), list[PublicFile])
    assert_type(client.polr.read(b""), Iterator[PolrUsage])
    assert_type(
        client.polr.rows(where=lambda r: r.premiseType == "Residential"),
        Iterator[PolrUsage],
    )
    polr_usage = next(client.polr.rows())
    assert_type(polr_usage.snapshotDate, date)
    assert_type(polr_usage.energyPeriodStart, date)
    assert_type(polr_usage.activeEsiids, int)
    assert_type(polr_usage.energyKWh, Decimal | None)

with Client() as client:
    assert_type(client.loss_factors.archives(), list[LoadArchive])
    assert_type(client.loss_factors.read(b""), Iterator[LossFactorDay])
    assert_type(
        client.loss_factors.rows(where=lambda r: r.kind == "actual"),
        Iterator[LossFactorDay],
    )
    loss_day = next(client.loss_factors.rows())
    assert_type(loss_day.operatingDay, date)
    assert_type(loss_day.sourceStartTime, datetime)
    assert_type(loss_day.sourceLastTime, datetime)
    assert_type(loss_day.tdsp, str | None)
    assert_type(loss_day.intervals[0].factor, Decimal | None)
    assert_type(loss_day.intervals[0].sourceLabel, str | None)
    assert_type(loss_day.kind, Literal["actual", "forecast"] | None)
    assert_type(loss_day.recorder, str | None)
    assert_type(loss_day.sourceFile, LoadArchive | None)
    assert_type(loss_day.sourceSecondaryIdentifier, str | int | None)
    assert_type(loss_day.sourceMarker, str | None)
    assert_type(
        client.loss_factors.read(
            b"", source_file=LoadArchive(year=2001, title="", url="")
        ),
        Iterator[LossFactorDay],
    )

with Client() as client:
    assert_type(client.historical_weather.download(), bytes)
    assert_type(
        client.historical_weather.rows(weather_zone="COAST", variable="DRYBULB TEMP"),
        Iterator[WeatherDay],
    )
    assert_type(client.historical_weather.read(b""), Iterator[WeatherDay])
    weather_day = next(client.historical_weather.rows())
    assert_type(weather_day.operatingDay, date)
    assert_type(weather_day.weatherZone, WeatherZone)
    assert_type(weather_day.variable, WeatherVariable)
    assert_type(weather_day.hours[0].value, Decimal | None)
    assert_type(weather_day.sourceUnit, str | None)

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
        assert_type(adder.RTORDPA, Decimal | None)
        assert_type(adder.RTRUCCST30HSL, Decimal | None)
        assert_type(adder.RTOLLASL, Decimal | None)
        assert_type(adder.RTOLHASL, Decimal | None)
        assert_type(adder.RTNCLRNSCAP, Decimal | None)
        assert_type(adder.RTNCLRECRS, Decimal | None)

    for quarter_hour in client.np6_324_cd.rt_15min_price_adders_history.rows():
        assert_type(quarter_hour.RTRDP, Decimal | None)
    for rtd_adder in client.np6_325_cd.rtd_price_adders_history.rows():
        assert_type(rtd_adder.RTORDPA, Decimal | None)
        assert_type(rtd_adder.RTDLRRRS, Decimal | None)
        assert_type(rtd_adder.RTOLLASL, Decimal | None)
        assert_type(rtd_adder.RTOLHASL, Decimal | None)
        assert_type(rtd_adder.RTNCLRECRS, Decimal | None)

    for forecast in client.np3_561_cd._7d_load_fcast_by_wzn_history.rows():
        assert_type(forecast.hourEnding, str | None)
        assert_type(forecast.coast, Decimal | None)
        assert_type(forecast.postedDatetime, datetime | None)
    for interval in client.np3_562_cd.ih_load_fcast_by_wzn_history.rows():
        assert_type(interval.intervalEnding, datetime | None)
        assert_type(interval.inUseFlag, bool | None)

    for capacity in client.np3_233_cd.hourly_res_outage_cap_history.rows():
        assert_type(capacity.totalResourceMW, int | None)
        assert_type(capacity.totalNewEquipResourceMW, int | None)
    for adequacy in client.np3_763_cd.st_sys_adequacy_history.rows():
        assert_type(adequacy.hourEnding, str | None)
        assert_type(adequacy.offAvailMW, Decimal | None)
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
    assert_type(lmps.data[0].lmpChange, Decimal | None)
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
    assert_type(
        client.load_profiles.counts(where=lambda row: row.weatherZone == "COAST"),
        Iterator[LoadProfileCount],
    )
    assert_type(client.load_profiles.read_counts(b""), Iterator[LoadProfileCount])
    profile_count = next(client.load_profiles.counts())
    assert_type(profile_count.snapshotDate, date | None)
    assert_type(profile_count.weatherZone, str | None)
    assert_type(profile_count.records, int)


with Client() as client:
    assert_type(
        client.coincident_peaks.allocations(year_from=1996),
        Iterator[CoincidentPeakAllocation],
    )
    assert_type(
        client.coincident_peaks.read_allocations(b""),
        Iterator[CoincidentPeakAllocation],
    )
    assert_type(client.coincident_peaks.daily_files(), list[PublicFile])
    assert_type(
        client.coincident_peaks.download(
            PublicFile(url="https://www.ercot.com/data.xlsx", title="Source")
        ),
        bytes,
    )
    assert_type(
        client.coincident_peaks.daily(where=lambda r: r.entity == "ERCOT"),
        Iterator[CoincidentPeakDay],
    )
    assert_type(client.coincident_peaks.read_daily(b""), Iterator[CoincidentPeakDay])
    cp_day = next(client.coincident_peaks.daily())
    assert_type(cp_day.operatingDay, date)
    assert_type(cp_day.intervals, list[EnergyInterval])
    assert_type(cp_day.intervals[0].energyMWh, Decimal | None)
    assert_type(cp_day.sourceFile, PublicFile | None)
    cp_allocation = next(client.coincident_peaks.allocations())
    assert_type(cp_allocation.averageLoad, Decimal | None)
    assert_type(cp_allocation.peaks[0].timestamp, datetime | None)
    assert_type(cp_allocation.duns, str | None)
    assert_type(client.coincident_peaks.monthly(), Iterator[MonthlyCoincidentPeak])
    assert_type(
        client.coincident_peaks.read_monthly(b""), Iterator[MonthlyCoincidentPeak]
    )
    cp_monthly = next(client.coincident_peaks.monthly())
    assert_type(cp_monthly.entity, str | None)
    assert_type(cp_monthly.timestamp, datetime)
    assert_type(cp_monthly.load, Decimal | None)
    assert_type(cp_monthly.energyMWh, Decimal | None)
    if cp_monthly.settlementRun:
        assert_type(cp_monthly.settlementRun.runDate, date | None)
        assert_type(cp_monthly.settlementRun.runTime, time | None)

with Client() as client:
    assert_type(client.generation_profiles.read(b""), Iterator[GenerationProfileHour])
    assert_type(client.generation_profiles.sites(b""), Iterator[GenerationProfileSite])
    generation_profile_hour = next(client.generation_profiles.read(b""))
    assert_type(generation_profile_hour.generationMW, dict[str, Decimal | None])
    assert_type(generation_profile_hour.profileDate, date)

with Client() as client:
    assert_type(
        client.generation_profiles.read_keys(b""), Iterator[GenerationProfileKey]
    )
    generation_key = next(client.generation_profiles.read_keys(b""))
    assert_type(generation_key.sites, list[GenerationProfileKeySite])
    assert_type(generation_key.summaries, list[GenerationProfileKeySummary])
    assert_type(generation_key.sites[0].capacityMW, Decimal | None)
    assert_type(generation_key.sites[0].tilt, Decimal | Literal["Lat", "NA"] | None)
    assert_type(generation_key.sites[0].queuedModelFlag, bool | None)

with Client() as client:
    generation_block = next(client.generation_profiles.read(b""))
    assert_type(generation_block.sourceBlock, int)
    generation_site = next(client.generation_profiles.sites(b""))
    assert_type(generation_site.sourceBlock, int)
    assert_type(generation_site.tracking, str | None)

with Client() as client:
    legacy_profile_hour = next(client.generation_profiles.read(b""))
    assert_type(legacy_profile_hour.calendarDate, date | None)
    legacy_profile_site = next(client.generation_profiles.sites(b""))
    assert_type(legacy_profile_site.annualEnergyMWh, dict[int, Decimal | None])
    assert_type(legacy_profile_site.annualCapacityFactor, dict[int, Decimal | None])
    assert_type(legacy_profile_site.sourceCount, int | None)
    assert_type(legacy_profile_site.sourceSum, Decimal | None)


def peak_forecast_typing(client: Client) -> None:
    assert_type(client.peak_demand_forecasts.files(), list[PublicFile])
    assert_type(client.peak_demand_forecasts.read(b""), Iterator[PeakDemandForecast])
    rows = client.peak_demand_forecasts.rows(where=lambda r: r.forecastYear >= 2025)
    assert_type(rows, Iterator[PeakDemandForecast])
    row = next(rows)
    assert_type(row.weatherYearMW, dict[int, Decimal | None])
    assert_type(row.p90MW, Decimal | None)
    assert_type(row.sourceFile, PublicFile | None)


def monthly_forecast_typing(client: Client) -> None:
    assert_type(client.monthly_load_forecasts.files(), list[PublicFile])
    assert_type(client.monthly_load_forecasts.read(b""), Iterator[MonthlyLoadForecast])
    rows = client.monthly_load_forecasts.rows(where=lambda r: r.forecastYear == 2026)
    assert_type(rows, Iterator[MonthlyLoadForecast])
    row = next(rows)
    assert_type(row.forecastMonth, int | None)
    assert_type(row.energy, Decimal | None)
    assert_type(row.energyUnit, Literal["MWh"] | None)
    assert_type(row.sourceFile, PublicFile | None)


def zonal_peak_typing(client: Client) -> None:
    assert_type(client.seasonal_peak_forecasts.files(), list[PublicFile])
    assert_type(
        client.seasonal_peak_forecasts.read(b""), Iterator[SeasonalPeakForecast]
    )
    assert_type(client.weekly_peak_forecasts.rows(), Iterator[WeeklyPeakForecast])
    row = next(
        client.seasonal_peak_forecasts.rows(where=lambda r: r.kind == "historical")
    )
    assert_type(row.peaks, WeatherZonePeakValues)
    assert_type(row.peaks.northCentral, Decimal | None)
    assert_type(row.endYear, int | None)
    assert_type(row.percentile, int | None)
    weekly = next(client.weekly_peak_forecasts.rows())
    assert_type(weekly.peakDate, date)
    assert_type(weekly.peakHour, int)


def hourly_forecast_typing(client: Client) -> None:
    assert_type(client.hourly_load_forecasts.files(), list[PublicFile])
    assert_type(client.hourly_load_forecasts.read(b""), Iterator[HourlyLoadForecast])
    rows = client.hourly_load_forecasts.rows(
        where=lambda r: r.forecastDate.year == 2026
    )
    assert_type(rows, Iterator[HourlyLoadForecast])
    row = next(rows)
    assert_type(row.forecastDate, date)
    assert_type(row.hour, int)
    assert_type(row.net, WeatherZoneForecastValues | None)
    if row.net is not None:
        assert_type(row.net.coast, Decimal | None)
        assert_type(row.net.total, Decimal | None)
    assert_type(row.unit, Literal["MW"] | None)
    assert_type(row.scenario, Literal["tsp_provided", "ercot_adjusted"] | None)


def winter_forecast_typing(client: Client) -> None:
    assert_type(client.winter_load_forecasts.files(), list[PublicFile])
    rows = client.winter_load_forecasts.rows(where=lambda row: row.kind == "peak")
    assert_type(rows, Iterator[WinterLoadForecast])
    assert_type(next(rows).transmissionOperators, dict[str, Decimal | None])


def hourly_load_scenario_typing(client: Client) -> None:
    assert_type(client.hourly_load_scenarios.files(), list[PublicFile])
    assert_type(client.hourly_load_scenarios.read(b""), Iterator[HourlyLoadScenario])
    rows = client.hourly_load_scenarios.rows(where=lambda r: r.weatherZone == "COAST")
    assert_type(rows, Iterator[HourlyLoadScenario])
    row = next(rows)
    assert_type(row.forecastDate, date)
    assert_type(row.weatherZone, WeatherZone)
    assert_type(row.weatherYearPredictions, dict[int, Decimal | None])
    assert_type(row.sourceMarkers, dict[str, str])
    assert_type(row.electricVehicles, Decimal | None)
    assert_type(row.largeFlexibleLoad, Decimal | None)
    assert_type(row.sourceFile, PublicFile | None)


# ESR uses a separate subscription while retaining the generated typed surface.
from tinyercot import ESRClient, rptesr_m

with ESRClient() as esr:
    assert_type(
        esr.rptesr_m._4_sec_esr_charging_mw(
            AGCExecTimeUTCFrom=datetime.fromisoformat("2025-09-01T00:00:00")
        ),
        Page[rptesr_m._4SecEsrChargingMwRow],
    )
    assert_type(
        esr.rptesr_m._4_sec_esr_charging_mw_iter(),
        Iterator[rptesr_m._4SecEsrChargingMwRow],
    )
    assert_type(
        esr.rptesr_m._4_sec_esr_charging_mw_iter_async(),
        AsyncIterator[rptesr_m._4SecEsrChargingMwRow],
    )
    assert_type(
        esr.rptesr_m._4_sec_esr_charging_mw_history,
        Archive[rptesr_m._4SecEsrChargingMwRow],
    )
    esr_row = next(esr.rptesr_m._4_sec_esr_charging_mw_iter())
    assert_type(esr_row.ESRChargingMW, Decimal | None)
    assert_type(esr_row.AGCExecTimeUTC, datetime | None)

from tinyercot import LoadForecastErrorSummary, LoadForecastPerformanceHour

with Client() as client:
    assert_type(
        client.load_forecast_performance.rows(), Iterator[LoadForecastPerformanceHour]
    )
    assert_type(
        client.load_forecast_performance.read(b""),
        Iterator[LoadForecastPerformanceHour],
    )
    assert_type(
        client.load_forecast_performance.summaries(), Iterator[LoadForecastErrorSummary]
    )
    assert_type(
        client.load_forecast_performance.read_summaries(b""),
        Iterator[LoadForecastErrorSummary],
    )
    performance = next(client.load_forecast_performance.rows())
    assert_type(performance.timestamp, datetime | None)
    assert_type(performance.selected, Decimal | None)
    assert_type(performance.X, Decimal | None)
    assert_type(performance.sourceMarkers, dict[str, str])
    summary = next(client.load_forecast_performance.summaries())
    assert_type(summary.hour, int | None)
    assert_type(summary.frequencyUnder, int | None)

from tinyercot import MonthlyLoadForecastPerformance

with Client() as client:
    assert_type(
        client.monthly_forecast_performance.rows(),
        Iterator[MonthlyLoadForecastPerformance],
    )
    assert_type(
        client.monthly_forecast_performance.read(b""),
        Iterator[MonthlyLoadForecastPerformance],
    )
    monthly_error = next(client.monthly_forecast_performance.rows())
    assert_type(monthly_error.month, date)
    assert_type(monthly_error.sourceDate, date | None)
    assert_type(monthly_error.value, Decimal | None)
    assert_type(monthly_error.percent, Decimal | None)
    assert_type(monthly_error.kind, Literal["forecast", "backcast", "target"])


with Client() as client:
    public_prices = client.dashboards.day_ahead_prices(date(2026, 9, 3))
    assert_type(public_prices.operatingDay, date)
    assert_type(public_prices.lastUpdated, datetime)
    assert_type(public_prices.data[0].periodEnding, str)
    assert_type(public_prices.data[0].values["HB_HOUSTON"], Decimal)
    assert_type(
        client.dashboards.real_time_prices().data[0].values["LZ_NORTH"], Decimal
    )
    assert_type(
        client.dashboards.day_ahead_ancillary_prices().data[0].values["ECRS"], Decimal
    )
    assert_type(
        client.dashboards.actual_forecast_zone_load().data[0].values["HOUSTON"], Decimal
    )
    assert_type(
        client.dashboards.actual_weather_zone_load().data[0].values["COAST"], Decimal
    )


with Client() as client:
    demand = client.dashboards.system_demand().nextDay.data[0]
    assert_type(demand.dayAheadForecast, Decimal | None)
    assert_type(demand.dayAheadHsl, Decimal | None)
    assert_type(demand.currentLoadForecast, Decimal)


with Client() as client:
    wind_solar = next(
        iter(client.dashboards.combined_wind_solar().nextDay.data.values())
    )
    assert_type(wind_solar.copHslWindDayAhead, Decimal | None)
    assert_type(wind_solar.stwpfDayAhead, Decimal | None)
    assert_type(wind_solar.wgrppDayAhead, Decimal | None)
    assert_type(wind_solar.copHslSolarDayAhead, Decimal | None)
    assert_type(wind_solar.stppfDayAhead, Decimal | None)
    assert_type(wind_solar.pvgrppDayAhead, Decimal | None)
    assert_type(wind_solar.stwpf, Decimal)


with Client() as client:
    assert_type(client.ancillary_requirements.files(), list[PublicFile])
    assert_type(
        client.ancillary_requirements.read(b""), Iterator[AncillaryServiceRequirements]
    )
    requirements = next(
        client.ancillary_requirements.rows(where=lambda d: d.year == 2026)
    )
    assert_type(requirements.effectiveDate, date | None)
    assert_type(requirements.quantities, list[AncillaryServiceQuantity])
    assert_type(requirements.rrsAllocations, list[ResponsiveReserveAllocation])
    assert_type(requirements.adjustments, list[AncillaryServiceAdjustment])
    assert_type(requirements.quantities[0].quantityMW, Decimal | None)
