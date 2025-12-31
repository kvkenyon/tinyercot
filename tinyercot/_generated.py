# AUTO-GENERATED — do not edit
from __future__ import annotations

import datetime
from decimal import Decimal
from typing import TypedDict

from tinyercot._client import _get

__all__ = [
    "np3_233_cd",
    "np3_565_cd",
    "np3_566_cd",
    "np3_910_er",
    "np3_911_er",
    "np3_965_er",
    "np3_966_er",
    "np3_990_ex",
    "np3_991_ex",
    "np4_159_cd",
    "np4_179_cd",
    "np4_183_cd",
    "np4_188_cd",
    "np4_190_cd",
    "np4_191_cd",
    "np4_196_m",
    "np4_197_m",
    "np4_33_cd",
    "np4_523_cd",
    "np4_732_cd",
    "np4_733_cd",
    "np4_737_cd",
    "np4_738_cd",
    "np4_742_cd",
    "np4_743_cd",
    "np4_745_cd",
    "np4_746_cd",
    "np6_322_cd",
    "np6_345_cd",
    "np6_346_cd",
    "np6_787_cd",
    "np6_788_cd",
    "np6_86_cd",
    "np6_905_cd",
    "np6_970_cd",
]


class np3_233_cd:
    """Hourly Resource Outage Capacity  This report includes all approved and accepted Planned, Forced and Maintenance Resource outages EXCEPT Resource outages for retirement of old equipment, seasonal mothballed (during the outaged season), and mothballed. The outage capacity in this report reflects aggregated ACTIVE resource outaged capacity by Load Zone sourced from the Outage Scheduler (OS) for the next 168 hours and is published every hour. Columns 'C\' - 'F' consists of the aggregated outaged capacity of ALL the ACTIVE resource outages by Load Zone in the OS for each hour excluding the outages stated above, IRR resource outages, and new equipment outages. Columns 'G' - 'J' consists of the aggregated outaged capacity of ALL the ACTIVE IRR resource outages by Load Zone in the OS for each hour excluding the outages stated above, outages in columns 'C' - 'F' and new equipment outages. Columns 'K' - 'N' consists of the aggregated outaged capacity of ALL the ACTIVE New Equipment Energization resource outages by Load Zone. Note that this report contains OS data only and does not look at telemetry. It includes both entire resource outage and de-rates."""

    class HourlyResOutageCapParams(TypedDict, total=False):
        operatingDateFrom: datetime.date
        operatingDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalResourceMWZoneSouthFrom: int
        totalResourceMWZoneSouthTo: int
        totalResourceMWZoneNorthFrom: int
        totalResourceMWZoneNorthTo: int
        totalResourceMWZoneWestFrom: int
        totalResourceMWZoneWestTo: int
        totalResourceMWZoneHoustonFrom: int
        totalResourceMWZoneHoustonTo: int
        totalIRRMWZoneSouthFrom: int
        totalIRRMWZoneSouthTo: int
        totalIRRMWZoneNorthFrom: int
        totalIRRMWZoneNorthTo: int
        totalIRRMWZoneWestFrom: int
        totalIRRMWZoneWestTo: int
        totalIRRMWZoneHoustonFrom: int
        totalIRRMWZoneHoustonTo: int
        totalNewEquipResourceMWZoneSouthFrom: int
        totalNewEquipResourceMWZoneSouthTo: int
        totalNewEquipResourceMWZoneNorthFrom: int
        totalNewEquipResourceMWZoneNorthTo: int
        totalNewEquipResourceMWZoneWestFrom: int
        totalNewEquipResourceMWZoneWestTo: int
        totalNewEquipResourceMWZoneHoustonFrom: int
        totalNewEquipResourceMWZoneHoustonTo: int
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def hourly_res_outage_cap(
        *,
        operatingDateFrom: datetime.date | None = None,
        operatingDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalResourceMWZoneSouthFrom: int | None = None,
        totalResourceMWZoneSouthTo: int | None = None,
        totalResourceMWZoneNorthFrom: int | None = None,
        totalResourceMWZoneNorthTo: int | None = None,
        totalResourceMWZoneWestFrom: int | None = None,
        totalResourceMWZoneWestTo: int | None = None,
        totalResourceMWZoneHoustonFrom: int | None = None,
        totalResourceMWZoneHoustonTo: int | None = None,
        totalIRRMWZoneSouthFrom: int | None = None,
        totalIRRMWZoneSouthTo: int | None = None,
        totalIRRMWZoneNorthFrom: int | None = None,
        totalIRRMWZoneNorthTo: int | None = None,
        totalIRRMWZoneWestFrom: int | None = None,
        totalIRRMWZoneWestTo: int | None = None,
        totalIRRMWZoneHoustonFrom: int | None = None,
        totalIRRMWZoneHoustonTo: int | None = None,
        totalNewEquipResourceMWZoneSouthFrom: int | None = None,
        totalNewEquipResourceMWZoneSouthTo: int | None = None,
        totalNewEquipResourceMWZoneNorthFrom: int | None = None,
        totalNewEquipResourceMWZoneNorthTo: int | None = None,
        totalNewEquipResourceMWZoneWestFrom: int | None = None,
        totalNewEquipResourceMWZoneWestTo: int | None = None,
        totalNewEquipResourceMWZoneHoustonFrom: int | None = None,
        totalNewEquipResourceMWZoneHoustonTo: int | None = None,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Hourly Resource Outage Capacity"""
        return _get(
            "np3-233-cd/hourly_res_outage_cap",
            operatingDateFrom=operatingDateFrom,
            operatingDateTo=operatingDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalResourceMWZoneSouthFrom=totalResourceMWZoneSouthFrom,
            totalResourceMWZoneSouthTo=totalResourceMWZoneSouthTo,
            totalResourceMWZoneNorthFrom=totalResourceMWZoneNorthFrom,
            totalResourceMWZoneNorthTo=totalResourceMWZoneNorthTo,
            totalResourceMWZoneWestFrom=totalResourceMWZoneWestFrom,
            totalResourceMWZoneWestTo=totalResourceMWZoneWestTo,
            totalResourceMWZoneHoustonFrom=totalResourceMWZoneHoustonFrom,
            totalResourceMWZoneHoustonTo=totalResourceMWZoneHoustonTo,
            totalIRRMWZoneSouthFrom=totalIRRMWZoneSouthFrom,
            totalIRRMWZoneSouthTo=totalIRRMWZoneSouthTo,
            totalIRRMWZoneNorthFrom=totalIRRMWZoneNorthFrom,
            totalIRRMWZoneNorthTo=totalIRRMWZoneNorthTo,
            totalIRRMWZoneWestFrom=totalIRRMWZoneWestFrom,
            totalIRRMWZoneWestTo=totalIRRMWZoneWestTo,
            totalIRRMWZoneHoustonFrom=totalIRRMWZoneHoustonFrom,
            totalIRRMWZoneHoustonTo=totalIRRMWZoneHoustonTo,
            totalNewEquipResourceMWZoneSouthFrom=totalNewEquipResourceMWZoneSouthFrom,
            totalNewEquipResourceMWZoneSouthTo=totalNewEquipResourceMWZoneSouthTo,
            totalNewEquipResourceMWZoneNorthFrom=totalNewEquipResourceMWZoneNorthFrom,
            totalNewEquipResourceMWZoneNorthTo=totalNewEquipResourceMWZoneNorthTo,
            totalNewEquipResourceMWZoneWestFrom=totalNewEquipResourceMWZoneWestFrom,
            totalNewEquipResourceMWZoneWestTo=totalNewEquipResourceMWZoneWestTo,
            totalNewEquipResourceMWZoneHoustonFrom=totalNewEquipResourceMWZoneHoustonFrom,
            totalNewEquipResourceMWZoneHoustonTo=totalNewEquipResourceMWZoneHoustonTo,
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np3_565_cd:
    """Seven-Day Load Forecast by Model and Weather Zone  Hourly system-wide Mid-Term Load Forecasts (MTLFs) for all forecast models with an indicator for which forecast was in use by ERCOT at the time of publication for current day plus the next 7."""

    class LfByModelWeatherZoneParams(TypedDict, total=False):
        DSTFlag: bool
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEnding: str
        coastFrom: Decimal
        coastTo: Decimal
        eastFrom: Decimal
        eastTo: Decimal
        farWestFrom: Decimal
        farWestTo: Decimal
        northFrom: Decimal
        northTo: Decimal
        northCentralFrom: Decimal
        northCentralTo: Decimal
        southCentralFrom: Decimal
        southCentralTo: Decimal
        southernFrom: Decimal
        southernTo: Decimal
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        westFrom: Decimal
        westTo: Decimal
        systemTotalFrom: Decimal
        systemTotalTo: Decimal
        model: str
        inUseFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def lf_by_model_weather_zone(
        *,
        DSTFlag: bool | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEnding: str | None = None,
        coastFrom: Decimal | None = None,
        coastTo: Decimal | None = None,
        eastFrom: Decimal | None = None,
        eastTo: Decimal | None = None,
        farWestFrom: Decimal | None = None,
        farWestTo: Decimal | None = None,
        northFrom: Decimal | None = None,
        northTo: Decimal | None = None,
        northCentralFrom: Decimal | None = None,
        northCentralTo: Decimal | None = None,
        southCentralFrom: Decimal | None = None,
        southCentralTo: Decimal | None = None,
        southernFrom: Decimal | None = None,
        southernTo: Decimal | None = None,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        westFrom: Decimal | None = None,
        westTo: Decimal | None = None,
        systemTotalFrom: Decimal | None = None,
        systemTotalTo: Decimal | None = None,
        model: str | None = None,
        inUseFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Seven-Day Load Forecast by Model and Weather Zone"""
        return _get(
            "np3-565-cd/lf_by_model_weather_zone",
            DSTFlag=DSTFlag,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEnding=hourEnding,
            coastFrom=coastFrom,
            coastTo=coastTo,
            eastFrom=eastFrom,
            eastTo=eastTo,
            farWestFrom=farWestFrom,
            farWestTo=farWestTo,
            northFrom=northFrom,
            northTo=northTo,
            northCentralFrom=northCentralFrom,
            northCentralTo=northCentralTo,
            southCentralFrom=southCentralFrom,
            southCentralTo=southCentralTo,
            southernFrom=southernFrom,
            southernTo=southernTo,
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            westFrom=westFrom,
            westTo=westTo,
            systemTotalFrom=systemTotalFrom,
            systemTotalTo=systemTotalTo,
            model=model,
            inUseFlag=inUseFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np3_566_cd:
    """Seven-Day Load Forecast by Model and Study Area  Forecasted hourly demands by Study Area, for the current day plus the next seven days."""

    class LfByModelStudyAreaParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEnding: str
        valleyFrom: Decimal
        valleyTo: Decimal
        model: str
        DSTFlag: bool
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def lf_by_model_study_area(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEnding: str | None = None,
        valleyFrom: Decimal | None = None,
        valleyTo: Decimal | None = None,
        model: str | None = None,
        DSTFlag: bool | None = None,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Seven-Day Load Forecast by Model and Study Area"""
        return _get(
            "np3-566-cd/lf_by_model_study_area",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEnding=hourEnding,
            valleyFrom=valleyFrom,
            valleyTo=valleyTo,
            model=model,
            DSTFlag=DSTFlag,
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np3_910_er:
    """2-Day Real Time Gen and Load Data Reports  This report will contain all 48 Hour disclosure data related to Real Time. The following individual files are included in the report:NP3-919-EX 48-hour Aggregate Output Schedules; NP3-920-EX 48-hour Aggregate Generation Summary; NP3-921-EX 48-hour Aggregate Load Summary; NP3-922-EX 48-hour Aggregate Dynamically Schedules Resources and Load; NP3-924-EX 48-hour Aggregate Load Summary by Disclosure Areas; NP3-931-EX 48-hour Aggregate Output Schedules by Disclosure Areas; NP3-935-EX 48-hour Aggregate Generation Summary by Disclosure Areas (previously 48 Hour Real Time Gen and Load Data Reports)."""

    class _2dAggOutSchedWestParams(TypedDict, total=False):
        repeatHourFlag: bool
        sumLSLOutputSchedFrom: Decimal
        sumLSLOutputSchedTo: Decimal
        sumHSLOutputSchedFrom: Decimal
        sumHSLOutputSchedTo: Decimal
        sumOutputSchedFrom: Decimal
        sumOutputSchedTo: Decimal
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_out_sched_west(
        *,
        repeatHourFlag: bool | None = None,
        sumLSLOutputSchedFrom: Decimal | None = None,
        sumLSLOutputSchedTo: Decimal | None = None,
        sumHSLOutputSchedFrom: Decimal | None = None,
        sumHSLOutputSchedTo: Decimal | None = None,
        sumOutputSchedFrom: Decimal | None = None,
        sumOutputSchedTo: Decimal | None = None,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Output Schedule West"""
        return _get(
            "np3-910-er/2d_agg_out_sched_west",
            repeatHourFlag=repeatHourFlag,
            sumLSLOutputSchedFrom=sumLSLOutputSchedFrom,
            sumLSLOutputSchedTo=sumLSLOutputSchedTo,
            sumHSLOutputSchedFrom=sumHSLOutputSchedFrom,
            sumHSLOutputSchedTo=sumHSLOutputSchedTo,
            sumOutputSchedFrom=sumOutputSchedFrom,
            sumOutputSchedTo=sumOutputSchedTo,
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggOutSchedSouthParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumLSLOutputSchedFrom: Decimal
        sumLSLOutputSchedTo: Decimal
        sumHSLOutputSchedFrom: Decimal
        sumHSLOutputSchedTo: Decimal
        sumOutputSchedFrom: Decimal
        sumOutputSchedTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_out_sched_south(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumLSLOutputSchedFrom: Decimal | None = None,
        sumLSLOutputSchedTo: Decimal | None = None,
        sumHSLOutputSchedFrom: Decimal | None = None,
        sumHSLOutputSchedTo: Decimal | None = None,
        sumOutputSchedFrom: Decimal | None = None,
        sumOutputSchedTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Output Schedule South"""
        return _get(
            "np3-910-er/2d_agg_out_sched_south",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumLSLOutputSchedFrom=sumLSLOutputSchedFrom,
            sumLSLOutputSchedTo=sumLSLOutputSchedTo,
            sumHSLOutputSchedFrom=sumHSLOutputSchedFrom,
            sumHSLOutputSchedTo=sumHSLOutputSchedTo,
            sumOutputSchedFrom=sumOutputSchedFrom,
            sumOutputSchedTo=sumOutputSchedTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggOutSchedNorthParams(TypedDict, total=False):
        sumHSLOutputSchedFrom: Decimal
        sumHSLOutputSchedTo: Decimal
        sumOutputSchedFrom: Decimal
        sumOutputSchedTo: Decimal
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumLSLOutputSchedFrom: Decimal
        sumLSLOutputSchedTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_out_sched_north(
        *,
        sumHSLOutputSchedFrom: Decimal | None = None,
        sumHSLOutputSchedTo: Decimal | None = None,
        sumOutputSchedFrom: Decimal | None = None,
        sumOutputSchedTo: Decimal | None = None,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumLSLOutputSchedFrom: Decimal | None = None,
        sumLSLOutputSchedTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Output Schedule North"""
        return _get(
            "np3-910-er/2d_agg_out_sched_north",
            sumHSLOutputSchedFrom=sumHSLOutputSchedFrom,
            sumHSLOutputSchedTo=sumHSLOutputSchedTo,
            sumOutputSchedFrom=sumOutputSchedFrom,
            sumOutputSchedTo=sumOutputSchedTo,
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumLSLOutputSchedFrom=sumLSLOutputSchedFrom,
            sumLSLOutputSchedTo=sumLSLOutputSchedTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggOutSchedHoustonParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumLSLOutputSchedFrom: Decimal
        sumLSLOutputSchedTo: Decimal
        sumHSLOutputSchedFrom: Decimal
        sumHSLOutputSchedTo: Decimal
        sumOutputSchedFrom: Decimal
        sumOutputSchedTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_out_sched_houston(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumLSLOutputSchedFrom: Decimal | None = None,
        sumLSLOutputSchedTo: Decimal | None = None,
        sumHSLOutputSchedFrom: Decimal | None = None,
        sumHSLOutputSchedTo: Decimal | None = None,
        sumOutputSchedFrom: Decimal | None = None,
        sumOutputSchedTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Output Schedule Houston"""
        return _get(
            "np3-910-er/2d_agg_out_sched_houston",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumLSLOutputSchedFrom=sumLSLOutputSchedFrom,
            sumLSLOutputSchedTo=sumLSLOutputSchedTo,
            sumHSLOutputSchedFrom=sumHSLOutputSchedFrom,
            sumHSLOutputSchedTo=sumHSLOutputSchedTo,
            sumOutputSchedFrom=sumOutputSchedFrom,
            sumOutputSchedTo=sumOutputSchedTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggOutSchedParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumLSLOutputSchedFrom: Decimal
        sumLSLOutputSchedTo: Decimal
        sumHSLOutputSchedFrom: Decimal
        sumHSLOutputSchedTo: Decimal
        sumOutputSchedFrom: Decimal
        sumOutputSchedTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_out_sched(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumLSLOutputSchedFrom: Decimal | None = None,
        sumLSLOutputSchedTo: Decimal | None = None,
        sumHSLOutputSchedFrom: Decimal | None = None,
        sumHSLOutputSchedTo: Decimal | None = None,
        sumOutputSchedFrom: Decimal | None = None,
        sumOutputSchedTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Output Schedule"""
        return _get(
            "np3-910-er/2d_agg_out_sched",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumLSLOutputSchedFrom=sumLSLOutputSchedFrom,
            sumLSLOutputSchedTo=sumLSLOutputSchedTo,
            sumHSLOutputSchedFrom=sumHSLOutputSchedFrom,
            sumHSLOutputSchedTo=sumHSLOutputSchedTo,
            sumOutputSchedFrom=sumOutputSchedFrom,
            sumOutputSchedTo=sumOutputSchedTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggLoadSummaryWestParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumTelemGenMWFrom: Decimal
        sumTelemGenMWTo: Decimal
        sumTelemDCtieMWFrom: Decimal
        sumTelemDCtieMWTo: Decimal
        aggLoadSummaryFrom: Decimal
        aggLoadSummaryTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_load_summary_west(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumTelemGenMWFrom: Decimal | None = None,
        sumTelemGenMWTo: Decimal | None = None,
        sumTelemDCtieMWFrom: Decimal | None = None,
        sumTelemDCtieMWTo: Decimal | None = None,
        aggLoadSummaryFrom: Decimal | None = None,
        aggLoadSummaryTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Load Summary West"""
        return _get(
            "np3-910-er/2d_agg_load_summary_west",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumTelemGenMWFrom=sumTelemGenMWFrom,
            sumTelemGenMWTo=sumTelemGenMWTo,
            sumTelemDCtieMWFrom=sumTelemDCtieMWFrom,
            sumTelemDCtieMWTo=sumTelemDCtieMWTo,
            aggLoadSummaryFrom=aggLoadSummaryFrom,
            aggLoadSummaryTo=aggLoadSummaryTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggLoadSummarySouthParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumTelemGenMWFrom: Decimal
        sumTelemGenMWTo: Decimal
        sumTelemDCtieMWFrom: Decimal
        sumTelemDCtieMWTo: Decimal
        aggLoadSummaryFrom: Decimal
        aggLoadSummaryTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_load_summary_south(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumTelemGenMWFrom: Decimal | None = None,
        sumTelemGenMWTo: Decimal | None = None,
        sumTelemDCtieMWFrom: Decimal | None = None,
        sumTelemDCtieMWTo: Decimal | None = None,
        aggLoadSummaryFrom: Decimal | None = None,
        aggLoadSummaryTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Load Summary South"""
        return _get(
            "np3-910-er/2d_agg_load_summary_south",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumTelemGenMWFrom=sumTelemGenMWFrom,
            sumTelemGenMWTo=sumTelemGenMWTo,
            sumTelemDCtieMWFrom=sumTelemDCtieMWFrom,
            sumTelemDCtieMWTo=sumTelemDCtieMWTo,
            aggLoadSummaryFrom=aggLoadSummaryFrom,
            aggLoadSummaryTo=aggLoadSummaryTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggLoadSummaryNorthParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumTelemGenMWFrom: Decimal
        sumTelemGenMWTo: Decimal
        sumTelemDCtieMWFrom: Decimal
        sumTelemDCtieMWTo: Decimal
        aggLoadSummaryFrom: Decimal
        aggLoadSummaryTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_load_summary_north(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumTelemGenMWFrom: Decimal | None = None,
        sumTelemGenMWTo: Decimal | None = None,
        sumTelemDCtieMWFrom: Decimal | None = None,
        sumTelemDCtieMWTo: Decimal | None = None,
        aggLoadSummaryFrom: Decimal | None = None,
        aggLoadSummaryTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Load Summary North"""
        return _get(
            "np3-910-er/2d_agg_load_summary_north",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumTelemGenMWFrom=sumTelemGenMWFrom,
            sumTelemGenMWTo=sumTelemGenMWTo,
            sumTelemDCtieMWFrom=sumTelemDCtieMWFrom,
            sumTelemDCtieMWTo=sumTelemDCtieMWTo,
            aggLoadSummaryFrom=aggLoadSummaryFrom,
            aggLoadSummaryTo=aggLoadSummaryTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggLoadSummaryHoustonParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumTelemGenMWFrom: Decimal
        sumTelemGenMWTo: Decimal
        sumTelemDCtieMWFrom: Decimal
        sumTelemDCtieMWTo: Decimal
        aggLoadSummaryFrom: Decimal
        aggLoadSummaryTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_load_summary_houston(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumTelemGenMWFrom: Decimal | None = None,
        sumTelemGenMWTo: Decimal | None = None,
        sumTelemDCtieMWFrom: Decimal | None = None,
        sumTelemDCtieMWTo: Decimal | None = None,
        aggLoadSummaryFrom: Decimal | None = None,
        aggLoadSummaryTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Load Summary Houston"""
        return _get(
            "np3-910-er/2d_agg_load_summary_houston",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumTelemGenMWFrom=sumTelemGenMWFrom,
            sumTelemGenMWTo=sumTelemGenMWTo,
            sumTelemDCtieMWFrom=sumTelemDCtieMWFrom,
            sumTelemDCtieMWTo=sumTelemDCtieMWTo,
            aggLoadSummaryFrom=aggLoadSummaryFrom,
            aggLoadSummaryTo=aggLoadSummaryTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggLoadSummaryParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumTelemGenMWFrom: Decimal
        sumTelemGenMWTo: Decimal
        sumTelemDCtieMWFrom: Decimal
        sumTelemDCtieMWTo: Decimal
        aggLoadSummaryFrom: Decimal
        aggLoadSummaryTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_load_summary(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumTelemGenMWFrom: Decimal | None = None,
        sumTelemGenMWTo: Decimal | None = None,
        sumTelemDCtieMWFrom: Decimal | None = None,
        sumTelemDCtieMWTo: Decimal | None = None,
        aggLoadSummaryFrom: Decimal | None = None,
        aggLoadSummaryTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Load Summary"""
        return _get(
            "np3-910-er/2d_agg_load_summary",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumTelemGenMWFrom=sumTelemGenMWFrom,
            sumTelemGenMWTo=sumTelemGenMWTo,
            sumTelemDCtieMWFrom=sumTelemDCtieMWFrom,
            sumTelemDCtieMWTo=sumTelemDCtieMWTo,
            aggLoadSummaryFrom=aggLoadSummaryFrom,
            aggLoadSummaryTo=aggLoadSummaryTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggGenSummaryWestParams(TypedDict, total=False):
        repeatHourFlag: bool
        sumBasePointNonWGRFrom: Decimal
        sumBasePointNonWGRTo: Decimal
        sumHaslNonWGRFrom: Decimal
        sumHaslNonWGRTo: Decimal
        sumLaslNonWGRFrom: Decimal
        sumLaslNonWGRTo: Decimal
        sumBasePointWGRFrom: Decimal
        sumBasePointWGRTo: Decimal
        sumHaslWGRFrom: Decimal
        sumHaslWGRTo: Decimal
        sumLaslWGRFrom: Decimal
        sumLaslWGRTo: Decimal
        sumBasePointRemResFrom: Decimal
        sumBasePointRemResTo: Decimal
        sumHaslRemResFrom: Decimal
        sumHaslRemResTo: Decimal
        sumLaslRemResFrom: Decimal
        sumLaslRemResTo: Decimal
        sumGenTelemMWFrom: Decimal
        sumGenTelemMWTo: Decimal
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_gen_summary_west(
        *,
        repeatHourFlag: bool | None = None,
        sumBasePointNonWGRFrom: Decimal | None = None,
        sumBasePointNonWGRTo: Decimal | None = None,
        sumHaslNonWGRFrom: Decimal | None = None,
        sumHaslNonWGRTo: Decimal | None = None,
        sumLaslNonWGRFrom: Decimal | None = None,
        sumLaslNonWGRTo: Decimal | None = None,
        sumBasePointWGRFrom: Decimal | None = None,
        sumBasePointWGRTo: Decimal | None = None,
        sumHaslWGRFrom: Decimal | None = None,
        sumHaslWGRTo: Decimal | None = None,
        sumLaslWGRFrom: Decimal | None = None,
        sumLaslWGRTo: Decimal | None = None,
        sumBasePointRemResFrom: Decimal | None = None,
        sumBasePointRemResTo: Decimal | None = None,
        sumHaslRemResFrom: Decimal | None = None,
        sumHaslRemResTo: Decimal | None = None,
        sumLaslRemResFrom: Decimal | None = None,
        sumLaslRemResTo: Decimal | None = None,
        sumGenTelemMWFrom: Decimal | None = None,
        sumGenTelemMWTo: Decimal | None = None,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Generation Summary West"""
        return _get(
            "np3-910-er/2d_agg_gen_summary_west",
            repeatHourFlag=repeatHourFlag,
            sumBasePointNonWGRFrom=sumBasePointNonWGRFrom,
            sumBasePointNonWGRTo=sumBasePointNonWGRTo,
            sumHaslNonWGRFrom=sumHaslNonWGRFrom,
            sumHaslNonWGRTo=sumHaslNonWGRTo,
            sumLaslNonWGRFrom=sumLaslNonWGRFrom,
            sumLaslNonWGRTo=sumLaslNonWGRTo,
            sumBasePointWGRFrom=sumBasePointWGRFrom,
            sumBasePointWGRTo=sumBasePointWGRTo,
            sumHaslWGRFrom=sumHaslWGRFrom,
            sumHaslWGRTo=sumHaslWGRTo,
            sumLaslWGRFrom=sumLaslWGRFrom,
            sumLaslWGRTo=sumLaslWGRTo,
            sumBasePointRemResFrom=sumBasePointRemResFrom,
            sumBasePointRemResTo=sumBasePointRemResTo,
            sumHaslRemResFrom=sumHaslRemResFrom,
            sumHaslRemResTo=sumHaslRemResTo,
            sumLaslRemResFrom=sumLaslRemResFrom,
            sumLaslRemResTo=sumLaslRemResTo,
            sumGenTelemMWFrom=sumGenTelemMWFrom,
            sumGenTelemMWTo=sumGenTelemMWTo,
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggGenSummarySouthParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumBasePointNonWGRFrom: Decimal
        sumBasePointNonWGRTo: Decimal
        sumHaslNonWGRFrom: Decimal
        sumHaslNonWGRTo: Decimal
        sumLaslNonWGRFrom: Decimal
        sumLaslNonWGRTo: Decimal
        sumBasePointWGRFrom: Decimal
        sumBasePointWGRTo: Decimal
        sumHaslWGRFrom: Decimal
        sumHaslWGRTo: Decimal
        sumLaslWGRFrom: Decimal
        sumLaslWGRTo: Decimal
        sumBasePointRemResFrom: Decimal
        sumBasePointRemResTo: Decimal
        sumHaslRemResFrom: Decimal
        sumHaslRemResTo: Decimal
        sumLaslRemResFrom: Decimal
        sumLaslRemResTo: Decimal
        sumGenTelemMWFrom: Decimal
        sumGenTelemMWTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_gen_summary_south(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumBasePointNonWGRFrom: Decimal | None = None,
        sumBasePointNonWGRTo: Decimal | None = None,
        sumHaslNonWGRFrom: Decimal | None = None,
        sumHaslNonWGRTo: Decimal | None = None,
        sumLaslNonWGRFrom: Decimal | None = None,
        sumLaslNonWGRTo: Decimal | None = None,
        sumBasePointWGRFrom: Decimal | None = None,
        sumBasePointWGRTo: Decimal | None = None,
        sumHaslWGRFrom: Decimal | None = None,
        sumHaslWGRTo: Decimal | None = None,
        sumLaslWGRFrom: Decimal | None = None,
        sumLaslWGRTo: Decimal | None = None,
        sumBasePointRemResFrom: Decimal | None = None,
        sumBasePointRemResTo: Decimal | None = None,
        sumHaslRemResFrom: Decimal | None = None,
        sumHaslRemResTo: Decimal | None = None,
        sumLaslRemResFrom: Decimal | None = None,
        sumLaslRemResTo: Decimal | None = None,
        sumGenTelemMWFrom: Decimal | None = None,
        sumGenTelemMWTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Generation Summary South"""
        return _get(
            "np3-910-er/2d_agg_gen_summary_south",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumBasePointNonWGRFrom=sumBasePointNonWGRFrom,
            sumBasePointNonWGRTo=sumBasePointNonWGRTo,
            sumHaslNonWGRFrom=sumHaslNonWGRFrom,
            sumHaslNonWGRTo=sumHaslNonWGRTo,
            sumLaslNonWGRFrom=sumLaslNonWGRFrom,
            sumLaslNonWGRTo=sumLaslNonWGRTo,
            sumBasePointWGRFrom=sumBasePointWGRFrom,
            sumBasePointWGRTo=sumBasePointWGRTo,
            sumHaslWGRFrom=sumHaslWGRFrom,
            sumHaslWGRTo=sumHaslWGRTo,
            sumLaslWGRFrom=sumLaslWGRFrom,
            sumLaslWGRTo=sumLaslWGRTo,
            sumBasePointRemResFrom=sumBasePointRemResFrom,
            sumBasePointRemResTo=sumBasePointRemResTo,
            sumHaslRemResFrom=sumHaslRemResFrom,
            sumHaslRemResTo=sumHaslRemResTo,
            sumLaslRemResFrom=sumLaslRemResFrom,
            sumLaslRemResTo=sumLaslRemResTo,
            sumGenTelemMWFrom=sumGenTelemMWFrom,
            sumGenTelemMWTo=sumGenTelemMWTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggGenSummaryNorthParams(TypedDict, total=False):
        sumBasePointWGRFrom: Decimal
        sumBasePointWGRTo: Decimal
        sumHaslWGRFrom: Decimal
        sumHaslWGRTo: Decimal
        sumLaslWGRFrom: Decimal
        sumLaslWGRTo: Decimal
        sumBasePointRemResFrom: Decimal
        sumBasePointRemResTo: Decimal
        sumHaslRemResFrom: Decimal
        sumHaslRemResTo: Decimal
        sumLaslRemResFrom: Decimal
        sumLaslRemResTo: Decimal
        sumGenTelemMWFrom: Decimal
        sumGenTelemMWTo: Decimal
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumBasePointNonWGRFrom: Decimal
        sumBasePointNonWGRTo: Decimal
        sumHaslNonWGRFrom: Decimal
        sumHaslNonWGRTo: Decimal
        sumLaslNonWGRFrom: Decimal
        sumLaslNonWGRTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_gen_summary_north(
        *,
        sumBasePointWGRFrom: Decimal | None = None,
        sumBasePointWGRTo: Decimal | None = None,
        sumHaslWGRFrom: Decimal | None = None,
        sumHaslWGRTo: Decimal | None = None,
        sumLaslWGRFrom: Decimal | None = None,
        sumLaslWGRTo: Decimal | None = None,
        sumBasePointRemResFrom: Decimal | None = None,
        sumBasePointRemResTo: Decimal | None = None,
        sumHaslRemResFrom: Decimal | None = None,
        sumHaslRemResTo: Decimal | None = None,
        sumLaslRemResFrom: Decimal | None = None,
        sumLaslRemResTo: Decimal | None = None,
        sumGenTelemMWFrom: Decimal | None = None,
        sumGenTelemMWTo: Decimal | None = None,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumBasePointNonWGRFrom: Decimal | None = None,
        sumBasePointNonWGRTo: Decimal | None = None,
        sumHaslNonWGRFrom: Decimal | None = None,
        sumHaslNonWGRTo: Decimal | None = None,
        sumLaslNonWGRFrom: Decimal | None = None,
        sumLaslNonWGRTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Generation Summary North"""
        return _get(
            "np3-910-er/2d_agg_gen_summary_north",
            sumBasePointWGRFrom=sumBasePointWGRFrom,
            sumBasePointWGRTo=sumBasePointWGRTo,
            sumHaslWGRFrom=sumHaslWGRFrom,
            sumHaslWGRTo=sumHaslWGRTo,
            sumLaslWGRFrom=sumLaslWGRFrom,
            sumLaslWGRTo=sumLaslWGRTo,
            sumBasePointRemResFrom=sumBasePointRemResFrom,
            sumBasePointRemResTo=sumBasePointRemResTo,
            sumHaslRemResFrom=sumHaslRemResFrom,
            sumHaslRemResTo=sumHaslRemResTo,
            sumLaslRemResFrom=sumLaslRemResFrom,
            sumLaslRemResTo=sumLaslRemResTo,
            sumGenTelemMWFrom=sumGenTelemMWFrom,
            sumGenTelemMWTo=sumGenTelemMWTo,
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumBasePointNonWGRFrom=sumBasePointNonWGRFrom,
            sumBasePointNonWGRTo=sumBasePointNonWGRTo,
            sumHaslNonWGRFrom=sumHaslNonWGRFrom,
            sumHaslNonWGRTo=sumHaslNonWGRTo,
            sumLaslNonWGRFrom=sumLaslNonWGRFrom,
            sumLaslNonWGRTo=sumLaslNonWGRTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggGenSummaryHoustonParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumBasePointNonWGRFrom: Decimal
        sumBasePointNonWGRTo: Decimal
        sumHaslNonWGRFrom: Decimal
        sumHaslNonWGRTo: Decimal
        sumLaslNonWGRFrom: Decimal
        sumLaslNonWGRTo: Decimal
        sumBasePointWGRFrom: Decimal
        sumBasePointWGRTo: Decimal
        sumHaslWGRFrom: Decimal
        sumHaslWGRTo: Decimal
        sumLaslWGRFrom: Decimal
        sumLaslWGRTo: Decimal
        sumBasePointRemResFrom: Decimal
        sumBasePointRemResTo: Decimal
        sumHaslRemResFrom: Decimal
        sumHaslRemResTo: Decimal
        sumLaslRemResFrom: Decimal
        sumLaslRemResTo: Decimal
        sumGenTelemMWFrom: Decimal
        sumGenTelemMWTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_gen_summary_houston(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumBasePointNonWGRFrom: Decimal | None = None,
        sumBasePointNonWGRTo: Decimal | None = None,
        sumHaslNonWGRFrom: Decimal | None = None,
        sumHaslNonWGRTo: Decimal | None = None,
        sumLaslNonWGRFrom: Decimal | None = None,
        sumLaslNonWGRTo: Decimal | None = None,
        sumBasePointWGRFrom: Decimal | None = None,
        sumBasePointWGRTo: Decimal | None = None,
        sumHaslWGRFrom: Decimal | None = None,
        sumHaslWGRTo: Decimal | None = None,
        sumLaslWGRFrom: Decimal | None = None,
        sumLaslWGRTo: Decimal | None = None,
        sumBasePointRemResFrom: Decimal | None = None,
        sumBasePointRemResTo: Decimal | None = None,
        sumHaslRemResFrom: Decimal | None = None,
        sumHaslRemResTo: Decimal | None = None,
        sumLaslRemResFrom: Decimal | None = None,
        sumLaslRemResTo: Decimal | None = None,
        sumGenTelemMWFrom: Decimal | None = None,
        sumGenTelemMWTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Generation Summary Houston"""
        return _get(
            "np3-910-er/2d_agg_gen_summary_houston",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumBasePointNonWGRFrom=sumBasePointNonWGRFrom,
            sumBasePointNonWGRTo=sumBasePointNonWGRTo,
            sumHaslNonWGRFrom=sumHaslNonWGRFrom,
            sumHaslNonWGRTo=sumHaslNonWGRTo,
            sumLaslNonWGRFrom=sumLaslNonWGRFrom,
            sumLaslNonWGRTo=sumLaslNonWGRTo,
            sumBasePointWGRFrom=sumBasePointWGRFrom,
            sumBasePointWGRTo=sumBasePointWGRTo,
            sumHaslWGRFrom=sumHaslWGRFrom,
            sumHaslWGRTo=sumHaslWGRTo,
            sumLaslWGRFrom=sumLaslWGRFrom,
            sumLaslWGRTo=sumLaslWGRTo,
            sumBasePointRemResFrom=sumBasePointRemResFrom,
            sumBasePointRemResTo=sumBasePointRemResTo,
            sumHaslRemResFrom=sumHaslRemResFrom,
            sumHaslRemResTo=sumHaslRemResTo,
            sumLaslRemResFrom=sumLaslRemResFrom,
            sumLaslRemResTo=sumLaslRemResTo,
            sumGenTelemMWFrom=sumGenTelemMWFrom,
            sumGenTelemMWTo=sumGenTelemMWTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggGenSummaryParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumBasePointNonIRRFrom: Decimal
        sumBasePointNonIRRTo: Decimal
        sumHASLNonIRRFrom: Decimal
        sumHASLNonIRRTo: Decimal
        sumLASLNonIRRFrom: Decimal
        sumLASLNonIRRTo: Decimal
        sumBasePointWGRFrom: Decimal
        sumBasePointWGRTo: Decimal
        sumHASLWGRFrom: Decimal
        sumHASLWGRTo: Decimal
        sumLASLWGRFrom: Decimal
        sumLASLWGRTo: Decimal
        sumBasePointPVGRFrom: Decimal
        sumBasePointPVGRTo: Decimal
        sumHASLPVGRFrom: Decimal
        sumHASLPVGRTo: Decimal
        sumLASLPVGRFrom: Decimal
        sumLASLPVGRTo: Decimal
        sumBasePointREMRESFrom: Decimal
        sumBasePointREMRESTo: Decimal
        sumHASLREMRESFrom: Decimal
        sumHASLREMRESTo: Decimal
        sumLASLREMRESFrom: Decimal
        sumLASLREMRESTo: Decimal
        sumGenTelemMWFrom: Decimal
        sumGenTelemMWTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_gen_summary(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumBasePointNonIRRFrom: Decimal | None = None,
        sumBasePointNonIRRTo: Decimal | None = None,
        sumHASLNonIRRFrom: Decimal | None = None,
        sumHASLNonIRRTo: Decimal | None = None,
        sumLASLNonIRRFrom: Decimal | None = None,
        sumLASLNonIRRTo: Decimal | None = None,
        sumBasePointWGRFrom: Decimal | None = None,
        sumBasePointWGRTo: Decimal | None = None,
        sumHASLWGRFrom: Decimal | None = None,
        sumHASLWGRTo: Decimal | None = None,
        sumLASLWGRFrom: Decimal | None = None,
        sumLASLWGRTo: Decimal | None = None,
        sumBasePointPVGRFrom: Decimal | None = None,
        sumBasePointPVGRTo: Decimal | None = None,
        sumHASLPVGRFrom: Decimal | None = None,
        sumHASLPVGRTo: Decimal | None = None,
        sumLASLPVGRFrom: Decimal | None = None,
        sumLASLPVGRTo: Decimal | None = None,
        sumBasePointREMRESFrom: Decimal | None = None,
        sumBasePointREMRESTo: Decimal | None = None,
        sumHASLREMRESFrom: Decimal | None = None,
        sumHASLREMRESTo: Decimal | None = None,
        sumLASLREMRESFrom: Decimal | None = None,
        sumLASLREMRESTo: Decimal | None = None,
        sumGenTelemMWFrom: Decimal | None = None,
        sumGenTelemMWTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Generation Summary"""
        return _get(
            "np3-910-er/2d_agg_gen_summary",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumBasePointNonIRRFrom=sumBasePointNonIRRFrom,
            sumBasePointNonIRRTo=sumBasePointNonIRRTo,
            sumHASLNonIRRFrom=sumHASLNonIRRFrom,
            sumHASLNonIRRTo=sumHASLNonIRRTo,
            sumLASLNonIRRFrom=sumLASLNonIRRFrom,
            sumLASLNonIRRTo=sumLASLNonIRRTo,
            sumBasePointWGRFrom=sumBasePointWGRFrom,
            sumBasePointWGRTo=sumBasePointWGRTo,
            sumHASLWGRFrom=sumHASLWGRFrom,
            sumHASLWGRTo=sumHASLWGRTo,
            sumLASLWGRFrom=sumLASLWGRFrom,
            sumLASLWGRTo=sumLASLWGRTo,
            sumBasePointPVGRFrom=sumBasePointPVGRFrom,
            sumBasePointPVGRTo=sumBasePointPVGRTo,
            sumHASLPVGRFrom=sumHASLPVGRFrom,
            sumHASLPVGRTo=sumHASLPVGRTo,
            sumLASLPVGRFrom=sumLASLPVGRFrom,
            sumLASLPVGRTo=sumLASLPVGRTo,
            sumBasePointREMRESFrom=sumBasePointREMRESFrom,
            sumBasePointREMRESTo=sumBasePointREMRESTo,
            sumHASLREMRESFrom=sumHASLREMRESFrom,
            sumHASLREMRESTo=sumHASLREMRESTo,
            sumLASLREMRESFrom=sumLASLREMRESFrom,
            sumLASLREMRESTo=sumLASLREMRESTo,
            sumGenTelemMWFrom=sumGenTelemMWFrom,
            sumGenTelemMWTo=sumGenTelemMWTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggDsrLoadsParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        sumTelemDSRLoadFrom: Decimal
        sumTelemDSRLoadTo: Decimal
        sumTelemDSRGenFrom: Decimal
        sumTelemDSRGenTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_dsr_loads(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        sumTelemDSRLoadFrom: Decimal | None = None,
        sumTelemDSRLoadTo: Decimal | None = None,
        sumTelemDSRGenFrom: Decimal | None = None,
        sumTelemDSRGenTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated DSR Loads"""
        return _get(
            "np3-910-er/2d_agg_dsr_loads",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            sumTelemDSRLoadFrom=sumTelemDSRLoadFrom,
            sumTelemDSRLoadTo=sumTelemDSRLoadTo,
            sumTelemDSRGenFrom=sumTelemDSRGenFrom,
            sumTelemDSRGenTo=sumTelemDSRGenTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np3_911_er:
    """2-Day Ancillary Services Reports  This report will contain all 48 Hour disclosure data related to DAM. The following individual files are included in the report:NP3-959-EX 48-hour Aggregate AS Offers; NP3-960-EX 48-hour Self-Arranged AS; NP3-961-EX 48-hour Cleared DAM AS (previously named 48 Hour Ancillary Services Reports)."""

    class _2dSelfArrangedAsRrsufrParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalSelfArrangedASRRSUFRFrom: Decimal
        totalSelfArrangedASRRSUFRTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_self_arranged_as_rrsufr(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalSelfArrangedASRRSUFRFrom: Decimal | None = None,
        totalSelfArrangedASRRSUFRTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Self Arranged Ancillary Service RRSUFR"""
        return _get(
            "np3-911-er/2d_self_arranged_as_rrsufr",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalSelfArrangedASRRSUFRFrom=totalSelfArrangedASRRSUFRFrom,
            totalSelfArrangedASRRSUFRTo=totalSelfArrangedASRRSUFRTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dSelfArrangedAsRrspfrParams(TypedDict, total=False):
        totalSelfArrangedASRRSPFRFrom: Decimal
        totalSelfArrangedASRRSPFRTo: Decimal
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_self_arranged_as_rrspfr(
        *,
        totalSelfArrangedASRRSPFRFrom: Decimal | None = None,
        totalSelfArrangedASRRSPFRTo: Decimal | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Self Arranged Ancillary Service RRSPFR"""
        return _get(
            "np3-911-er/2d_self_arranged_as_rrspfr",
            totalSelfArrangedASRRSPFRFrom=totalSelfArrangedASRRSPFRFrom,
            totalSelfArrangedASRRSPFRTo=totalSelfArrangedASRRSPFRTo,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dSelfArrangedAsRrsffrParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalSelfArrangedASRRSFFRFrom: Decimal
        totalSelfArrangedASRRSFFRTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_self_arranged_as_rrsffr(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalSelfArrangedASRRSFFRFrom: Decimal | None = None,
        totalSelfArrangedASRRSFFRTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Self Arranged Ancillary Service RRSFFR"""
        return _get(
            "np3-911-er/2d_self_arranged_as_rrsffr",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalSelfArrangedASRRSFFRFrom=totalSelfArrangedASRRSFFRFrom,
            totalSelfArrangedASRRSFFRTo=totalSelfArrangedASRRSFFRTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dSelfArrangedAsRegupParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalSelfArrangedASREGUPFrom: Decimal
        totalSelfArrangedASREGUPTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_self_arranged_as_regup(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalSelfArrangedASREGUPFrom: Decimal | None = None,
        totalSelfArrangedASREGUPTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Self Arranged Ancillary Service REGUP"""
        return _get(
            "np3-911-er/2d_self_arranged_as_regup",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalSelfArrangedASREGUPFrom=totalSelfArrangedASREGUPFrom,
            totalSelfArrangedASREGUPTo=totalSelfArrangedASREGUPTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dSelfArrangedAsRegdnParams(TypedDict, total=False):
        hourEndingFrom: int
        hourEndingTo: int
        totalSelfArrangedASREGDNFrom: Decimal
        totalSelfArrangedASREGDNTo: Decimal
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_self_arranged_as_regdn(
        *,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalSelfArrangedASREGDNFrom: Decimal | None = None,
        totalSelfArrangedASREGDNTo: Decimal | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Self Arranged Ancillary Service REGDN"""
        return _get(
            "np3-911-er/2d_self_arranged_as_regdn",
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalSelfArrangedASREGDNFrom=totalSelfArrangedASREGDNFrom,
            totalSelfArrangedASREGDNTo=totalSelfArrangedASREGDNTo,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dSelfArrangedAsNspnmParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalSelfArrangedASNSPNMFrom: Decimal
        totalSelfArrangedASNSPNMTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_self_arranged_as_nspnm(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalSelfArrangedASNSPNMFrom: Decimal | None = None,
        totalSelfArrangedASNSPNMTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Self Arranged Ancillary Service NSPNM"""
        return _get(
            "np3-911-er/2d_self_arranged_as_nspnm",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalSelfArrangedASNSPNMFrom=totalSelfArrangedASNSPNMFrom,
            totalSelfArrangedASNSPNMTo=totalSelfArrangedASNSPNMTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dSelfArrangedAsNspinParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalSelfArrangedASNSPINFrom: Decimal
        totalSelfArrangedASNSPINTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_self_arranged_as_nspin(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalSelfArrangedASNSPINFrom: Decimal | None = None,
        totalSelfArrangedASNSPINTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Self Arranged Ancillary Service NSPIN"""
        return _get(
            "np3-911-er/2d_self_arranged_as_nspin",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalSelfArrangedASNSPINFrom=totalSelfArrangedASNSPINFrom,
            totalSelfArrangedASNSPINTo=totalSelfArrangedASNSPINTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dSelfArrangedAsEcrssParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalSelfArrangedASECRSSFrom: Decimal
        totalSelfArrangedASECRSSTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_self_arranged_as_ecrss(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalSelfArrangedASECRSSFrom: Decimal | None = None,
        totalSelfArrangedASECRSSTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Self Arranged Ancillary Service ECRSS"""
        return _get(
            "np3-911-er/2d_self_arranged_as_ecrss",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalSelfArrangedASECRSSFrom=totalSelfArrangedASECRSSFrom,
            totalSelfArrangedASECRSSTo=totalSelfArrangedASECRSSTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dSelfArrangedAsEcrsmParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalSelfArrangedASECRSMFrom: Decimal
        totalSelfArrangedASECRSMTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_self_arranged_as_ecrsm(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalSelfArrangedASECRSMFrom: Decimal | None = None,
        totalSelfArrangedASECRSMTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Self Arranged Ancillary Service ECRSM"""
        return _get(
            "np3-911-er/2d_self_arranged_as_ecrsm",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalSelfArrangedASECRSMFrom=totalSelfArrangedASECRSMFrom,
            totalSelfArrangedASECRSMTo=totalSelfArrangedASECRSMTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dClearedDamAsRrsufrParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalClearedASRRSUFRFrom: Decimal
        totalClearedASRRSUFRTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_cleared_dam_as_rrsufr(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalClearedASRRSUFRFrom: Decimal | None = None,
        totalClearedASRRSUFRTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Cleared DAM Ancillary Service RRSUFR"""
        return _get(
            "np3-911-er/2d_cleared_dam_as_rrsufr",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalClearedASRRSUFRFrom=totalClearedASRRSUFRFrom,
            totalClearedASRRSUFRTo=totalClearedASRRSUFRTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dClearedDamAsRrspfrParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalClearedASRRSPFRFrom: Decimal
        totalClearedASRRSPFRTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_cleared_dam_as_rrspfr(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalClearedASRRSPFRFrom: Decimal | None = None,
        totalClearedASRRSPFRTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Cleared DAM Ancillary Service RRSPFR"""
        return _get(
            "np3-911-er/2d_cleared_dam_as_rrspfr",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalClearedASRRSPFRFrom=totalClearedASRRSPFRFrom,
            totalClearedASRRSPFRTo=totalClearedASRRSPFRTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dClearedDamAsRrsffrParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalClearedASRRSFFRFrom: Decimal
        totalClearedASRRSFFRTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_cleared_dam_as_rrsffr(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalClearedASRRSFFRFrom: Decimal | None = None,
        totalClearedASRRSFFRTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Cleared DAM Ancillary Service RRSFFR"""
        return _get(
            "np3-911-er/2d_cleared_dam_as_rrsffr",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalClearedASRRSFFRFrom=totalClearedASRRSFFRFrom,
            totalClearedASRRSFFRTo=totalClearedASRRSFFRTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dClearedDamAsRegupParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalClearedASREGUPFrom: Decimal
        totalClearedASREGUPTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_cleared_dam_as_regup(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalClearedASREGUPFrom: Decimal | None = None,
        totalClearedASREGUPTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Cleared DAM Ancillary Service REGUP"""
        return _get(
            "np3-911-er/2d_cleared_dam_as_regup",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalClearedASREGUPFrom=totalClearedASREGUPFrom,
            totalClearedASREGUPTo=totalClearedASREGUPTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dClearedDamAsRegdnParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalClearedASREGDNFrom: Decimal
        totalClearedASREGDNTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_cleared_dam_as_regdn(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalClearedASREGDNFrom: Decimal | None = None,
        totalClearedASREGDNTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Cleared DAM Ancillary Service REGDN"""
        return _get(
            "np3-911-er/2d_cleared_dam_as_regdn",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalClearedASREGDNFrom=totalClearedASREGDNFrom,
            totalClearedASREGDNTo=totalClearedASREGDNTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dClearedDamAsNspinParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalClearedASNSPINFrom: Decimal
        totalClearedASNSPINTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_cleared_dam_as_nspin(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalClearedASNSPINFrom: Decimal | None = None,
        totalClearedASNSPINTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Cleared DAM Ancillary Service NSPIN"""
        return _get(
            "np3-911-er/2d_cleared_dam_as_nspin",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalClearedASNSPINFrom=totalClearedASNSPINFrom,
            totalClearedASNSPINTo=totalClearedASNSPINTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dClearedDamAsEcrssParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalClearedASECRSSFrom: Decimal
        totalClearedASECRSSTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_cleared_dam_as_ecrss(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalClearedASECRSSFrom: Decimal | None = None,
        totalClearedASECRSSTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Cleared DAM Ancillary Service ECRSS"""
        return _get(
            "np3-911-er/2d_cleared_dam_as_ecrss",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalClearedASECRSSFrom=totalClearedASECRSSFrom,
            totalClearedASECRSSTo=totalClearedASECRSSTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dClearedDamAsEcrsmParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        totalClearedASECRSMFrom: Decimal
        totalClearedASECRSMTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_cleared_dam_as_ecrsm(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        totalClearedASECRSMFrom: Decimal | None = None,
        totalClearedASECRSMTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Cleared DAM Ancillary Service ECRSM"""
        return _get(
            "np3-911-er/2d_cleared_dam_as_ecrsm",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            totalClearedASECRSMFrom=totalClearedASECRSMFrom,
            totalClearedASECRSMTo=totalClearedASECRSMTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggAsOffersRrsufrParams(TypedDict, total=False):
        RRSUFROfferPriceFrom: Decimal
        RRSUFROfferPriceTo: Decimal
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        MWOfferedFrom: Decimal
        MWOfferedTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_as_offers_rrsufr(
        *,
        RRSUFROfferPriceFrom: Decimal | None = None,
        RRSUFROfferPriceTo: Decimal | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        MWOfferedFrom: Decimal | None = None,
        MWOfferedTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Ancillary Service Offers RRSUFR"""
        return _get(
            "np3-911-er/2d_agg_as_offers_rrsufr",
            RRSUFROfferPriceFrom=RRSUFROfferPriceFrom,
            RRSUFROfferPriceTo=RRSUFROfferPriceTo,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            MWOfferedFrom=MWOfferedFrom,
            MWOfferedTo=MWOfferedTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggAsOffersRrspfrParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        MWOfferedFrom: Decimal
        MWOfferedTo: Decimal
        RRSPFROfferPriceFrom: Decimal
        RRSPFROfferPriceTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_as_offers_rrspfr(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        MWOfferedFrom: Decimal | None = None,
        MWOfferedTo: Decimal | None = None,
        RRSPFROfferPriceFrom: Decimal | None = None,
        RRSPFROfferPriceTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Ancillary Service Offers RRSPFR"""
        return _get(
            "np3-911-er/2d_agg_as_offers_rrspfr",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            MWOfferedFrom=MWOfferedFrom,
            MWOfferedTo=MWOfferedTo,
            RRSPFROfferPriceFrom=RRSPFROfferPriceFrom,
            RRSPFROfferPriceTo=RRSPFROfferPriceTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggAsOffersRrsffrParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        MWOfferedFrom: Decimal
        MWOfferedTo: Decimal
        RRSFFROfferPriceFrom: Decimal
        RRSFFROfferPriceTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_as_offers_rrsffr(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        MWOfferedFrom: Decimal | None = None,
        MWOfferedTo: Decimal | None = None,
        RRSFFROfferPriceFrom: Decimal | None = None,
        RRSFFROfferPriceTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Ancillary Service Offers RRSFFR"""
        return _get(
            "np3-911-er/2d_agg_as_offers_rrsffr",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            MWOfferedFrom=MWOfferedFrom,
            MWOfferedTo=MWOfferedTo,
            RRSFFROfferPriceFrom=RRSFFROfferPriceFrom,
            RRSFFROfferPriceTo=RRSFFROfferPriceTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggAsOffersRegupParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        MWOfferedFrom: Decimal
        MWOfferedTo: Decimal
        REGUPOfferPriceFrom: Decimal
        REGUPOfferPriceTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_as_offers_regup(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        MWOfferedFrom: Decimal | None = None,
        MWOfferedTo: Decimal | None = None,
        REGUPOfferPriceFrom: Decimal | None = None,
        REGUPOfferPriceTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Ancillary Service Offers REGUP"""
        return _get(
            "np3-911-er/2d_agg_as_offers_regup",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            MWOfferedFrom=MWOfferedFrom,
            MWOfferedTo=MWOfferedTo,
            REGUPOfferPriceFrom=REGUPOfferPriceFrom,
            REGUPOfferPriceTo=REGUPOfferPriceTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggAsOffersRegdnParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        MWOfferedFrom: Decimal
        MWOfferedTo: Decimal
        REGDNOfferPriceFrom: Decimal
        REGDNOfferPriceTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_as_offers_regdn(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        MWOfferedFrom: Decimal | None = None,
        MWOfferedTo: Decimal | None = None,
        REGDNOfferPriceFrom: Decimal | None = None,
        REGDNOfferPriceTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Ancillary Service Offers REGDN"""
        return _get(
            "np3-911-er/2d_agg_as_offers_regdn",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            MWOfferedFrom=MWOfferedFrom,
            MWOfferedTo=MWOfferedTo,
            REGDNOfferPriceFrom=REGDNOfferPriceFrom,
            REGDNOfferPriceTo=REGDNOfferPriceTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggAsOffersOnnsParams(TypedDict, total=False):
        hourEndingFrom: int
        hourEndingTo: int
        MWOfferedFrom: Decimal
        MWOfferedTo: Decimal
        ONNSOfferPriceFrom: Decimal
        ONNSOfferPriceTo: Decimal
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_as_offers_onns(
        *,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        MWOfferedFrom: Decimal | None = None,
        MWOfferedTo: Decimal | None = None,
        ONNSOfferPriceFrom: Decimal | None = None,
        ONNSOfferPriceTo: Decimal | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Ancillary Service Offers ONNS"""
        return _get(
            "np3-911-er/2d_agg_as_offers_onns",
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            MWOfferedFrom=MWOfferedFrom,
            MWOfferedTo=MWOfferedTo,
            ONNSOfferPriceFrom=ONNSOfferPriceFrom,
            ONNSOfferPriceTo=ONNSOfferPriceTo,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggAsOffersOffnsParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        MWOfferedFrom: Decimal
        MWOfferedTo: Decimal
        OFFNSOfferPriceFrom: Decimal
        OFFNSOfferPriceTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_as_offers_offns(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        MWOfferedFrom: Decimal | None = None,
        MWOfferedTo: Decimal | None = None,
        OFFNSOfferPriceFrom: Decimal | None = None,
        OFFNSOfferPriceTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Ancillary Service Offers OFFNS"""
        return _get(
            "np3-911-er/2d_agg_as_offers_offns",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            MWOfferedFrom=MWOfferedFrom,
            MWOfferedTo=MWOfferedTo,
            OFFNSOfferPriceFrom=OFFNSOfferPriceFrom,
            OFFNSOfferPriceTo=OFFNSOfferPriceTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggAsOffersEcrssParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        MWOfferedFrom: Decimal
        MWOfferedTo: Decimal
        ECRSSOfferPriceFrom: Decimal
        ECRSSOfferPriceTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_as_offers_ecrss(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        MWOfferedFrom: Decimal | None = None,
        MWOfferedTo: Decimal | None = None,
        ECRSSOfferPriceFrom: Decimal | None = None,
        ECRSSOfferPriceTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Ancillary Service Offers ECRSS"""
        return _get(
            "np3-911-er/2d_agg_as_offers_ecrss",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            MWOfferedFrom=MWOfferedFrom,
            MWOfferedTo=MWOfferedTo,
            ECRSSOfferPriceFrom=ECRSSOfferPriceFrom,
            ECRSSOfferPriceTo=ECRSSOfferPriceTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _2dAggAsOffersEcrsmParams(TypedDict, total=False):
        ECRSMOfferPriceFrom: Decimal
        ECRSMOfferPriceTo: Decimal
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        MWOfferedFrom: Decimal
        MWOfferedTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _2d_agg_as_offers_ecrsm(
        *,
        ECRSMOfferPriceFrom: Decimal | None = None,
        ECRSMOfferPriceTo: Decimal | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        MWOfferedFrom: Decimal | None = None,
        MWOfferedTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """2 Day Aggregated Ancillary Service Offers ECRSM"""
        return _get(
            "np3-911-er/2d_agg_as_offers_ecrsm",
            ECRSMOfferPriceFrom=ECRSMOfferPriceFrom,
            ECRSMOfferPriceTo=ECRSMOfferPriceTo,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            MWOfferedFrom=MWOfferedFrom,
            MWOfferedTo=MWOfferedTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np3_965_er:
    """60-Day SCED Disclosure Reports  This report will contain all 60 day disclosure data related to SCED. The following individual files are included in the report: NP3-967-EX 61-day QSE-specific Self-Arranged AS in SCED NP3-968-EX 61-day Generation Resource data in SCED NP3-969-EX 61-day Load Resource data in SCED NP3-970-EX 61-day Dynamically Scheduled Resource and Loads in SCED NP3-971-EX 61-day Inc/Dec Offer Curves in SCED NP3-973-EX 61-day Settlement Metered Net Energy for Generation Resources and NP6-585-ER 60 Day HDL and LDL Manual Override Summary"""

    class _60ScedSmneGenResParams(TypedDict, total=False):
        intervalValueFrom: Decimal
        intervalValueTo: Decimal
        intervalTimeFrom: datetime.datetime
        intervalTimeTo: datetime.datetime
        intervalNumberFrom: int
        intervalNumberTo: int
        resourceCode: str
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_sced_smne_gen_res(
        *,
        intervalValueFrom: Decimal | None = None,
        intervalValueTo: Decimal | None = None,
        intervalTimeFrom: datetime.datetime | None = None,
        intervalTimeTo: datetime.datetime | None = None,
        intervalNumberFrom: int | None = None,
        intervalNumberTo: int | None = None,
        resourceCode: str | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day SCED Settlement Metered Net Energy for Generation Resources"""
        return _get(
            "np3-965-er/60_sced_smne_gen_res",
            intervalValueFrom=intervalValueFrom,
            intervalValueTo=intervalValueTo,
            intervalTimeFrom=intervalTimeFrom,
            intervalTimeTo=intervalTimeTo,
            intervalNumberFrom=intervalNumberFrom,
            intervalNumberTo=intervalNumberTo,
            resourceCode=resourceCode,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60ScedQseSelfArrangedAsParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        qseName: str
        REGUP: str
        REGDNFrom: Decimal
        REGDNTo: Decimal
        NSPINFrom: Decimal
        NSPINTo: Decimal
        NSPNMFrom: Decimal
        NSPNMTo: Decimal
        RRSPFRFrom: Decimal
        RRSPFRTo: Decimal
        RRSFFRFrom: Decimal
        RRSFFRTo: Decimal
        RRSUFRFrom: Decimal
        RRSUFRTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_sced_qse_self_arranged_as(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        qseName: str | None = None,
        REGUP: str | None = None,
        REGDNFrom: Decimal | None = None,
        REGDNTo: Decimal | None = None,
        NSPINFrom: Decimal | None = None,
        NSPINTo: Decimal | None = None,
        NSPNMFrom: Decimal | None = None,
        NSPNMTo: Decimal | None = None,
        RRSPFRFrom: Decimal | None = None,
        RRSPFRTo: Decimal | None = None,
        RRSFFRFrom: Decimal | None = None,
        RRSFFRTo: Decimal | None = None,
        RRSUFRFrom: Decimal | None = None,
        RRSUFRTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day QSE-specific Self-Arranged AS in SCED"""
        return _get(
            "np3-965-er/60_sced_qse_self_arranged_as",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            qseName=qseName,
            REGUP=REGUP,
            REGDNFrom=REGDNFrom,
            REGDNTo=REGDNTo,
            NSPINFrom=NSPINFrom,
            NSPINTo=NSPINTo,
            NSPNMFrom=NSPNMFrom,
            NSPNMTo=NSPNMTo,
            RRSPFRFrom=RRSPFRFrom,
            RRSPFRTo=RRSPFRTo,
            RRSFFRFrom=RRSFFRFrom,
            RRSFFRTo=RRSFFRTo,
            RRSUFRFrom=RRSUFRFrom,
            RRSUFRTo=RRSUFRTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60ScedGenResDataParams(TypedDict, total=False):
        SCED2CurveMW9From: Decimal
        SCED2CurveMW9To: Decimal
        SCED2CurvePrice9From: Decimal
        SCED2CurvePrice9To: Decimal
        SCED2CurveMW10From: Decimal
        SCED2CurveMW10To: Decimal
        SCED2CurvePrice10From: Decimal
        SCED2CurvePrice10To: Decimal
        SCED2CurveMW11From: Decimal
        SCED2CurveMW11To: Decimal
        SCED2CurvePrice11From: Decimal
        SCED2CurvePrice11To: Decimal
        SCED2CurveMW12From: Decimal
        SCED2CurveMW12To: Decimal
        SCED2CurvePrice12From: Decimal
        SCED2CurvePrice12To: Decimal
        SCED2CurveMW13From: Decimal
        SCED2CurveMW13To: Decimal
        SCED2CurvePrice13From: Decimal
        SCED2CurvePrice13To: Decimal
        SCED2CurveMW14From: Decimal
        SCED2CurveMW14To: Decimal
        SCED2CurvePrice14From: Decimal
        SCED2CurvePrice14To: Decimal
        SCED2CurveMW15From: Decimal
        SCED2CurveMW15To: Decimal
        SCED2CurvePrice15From: Decimal
        SCED2CurvePrice15To: Decimal
        SCED2CurveMW16From: Decimal
        SCED2CurveMW16To: Decimal
        SCED2CurvePrice16From: Decimal
        SCED2CurvePrice16To: Decimal
        SCED2CurveMW17From: Decimal
        SCED2CurveMW17To: Decimal
        SCED2CurvePrice17From: Decimal
        SCED2CurvePrice17To: Decimal
        SCED2CurveMW18From: Decimal
        SCED2CurveMW18To: Decimal
        SCED2CurvePrice18From: Decimal
        SCED2CurvePrice18To: Decimal
        SCED2CurveMW19From: Decimal
        SCED2CurveMW19To: Decimal
        SCED2CurvePrice19From: Decimal
        SCED2CurvePrice19To: Decimal
        SCED2CurveMW20From: Decimal
        SCED2CurveMW20To: Decimal
        SCED2CurvePrice20From: Decimal
        SCED2CurvePrice20To: Decimal
        SCED2CurveMW21From: Decimal
        SCED2CurveMW21To: Decimal
        SCED2CurvePrice21From: Decimal
        SCED2CurvePrice21To: Decimal
        SCED2CurveMW22From: Decimal
        SCED2CurveMW22To: Decimal
        SCED2CurvePrice22From: Decimal
        SCED2CurvePrice22To: Decimal
        SCED2CurveMW23From: Decimal
        SCED2CurveMW23To: Decimal
        SCED2CurvePrice23From: Decimal
        SCED2CurvePrice23To: Decimal
        SCED2CurveMW24From: Decimal
        SCED2CurveMW24To: Decimal
        SCED2CurvePrice24From: Decimal
        SCED2CurvePrice24To: Decimal
        SCED2CurveMW25From: Decimal
        SCED2CurveMW25To: Decimal
        SCED2CurvePrice25From: Decimal
        SCED2CurvePrice25To: Decimal
        SCED2CurveMW26From: Decimal
        SCED2CurveMW26To: Decimal
        SCED2CurvePrice26From: Decimal
        SCED2CurvePrice26To: Decimal
        SCED2CurveMW27From: Decimal
        SCED2CurveMW27To: Decimal
        SCED2CurvePrice27From: Decimal
        SCED2CurvePrice27To: Decimal
        SCED2CurveMW28From: Decimal
        SCED2CurveMW28To: Decimal
        SCED2CurvePrice28From: Decimal
        SCED2CurvePrice28To: Decimal
        SCED2CurveMW29From: Decimal
        SCED2CurveMW29To: Decimal
        SCED2CurvePrice29From: Decimal
        SCED2CurvePrice29To: Decimal
        SCED2CurveMW30From: Decimal
        SCED2CurveMW30To: Decimal
        SCED2CurvePrice30From: Decimal
        SCED2CurvePrice30To: Decimal
        SCED2CurveMW31From: Decimal
        SCED2CurveMW31To: Decimal
        SCED2CurvePrice31From: Decimal
        SCED2CurvePrice31To: Decimal
        SCED2CurveMW32From: Decimal
        SCED2CurveMW32To: Decimal
        SCED2CurvePrice32From: Decimal
        SCED2CurvePrice32To: Decimal
        SCED2CurveMW33From: Decimal
        SCED2CurveMW33To: Decimal
        SCED2CurvePrice33From: Decimal
        SCED2CurvePrice33To: Decimal
        SCED2CurveMW34From: Decimal
        SCED2CurveMW34To: Decimal
        SCED2CurvePrice34From: Decimal
        SCED2CurvePrice34To: Decimal
        SCED2CurveMW35From: Decimal
        SCED2CurveMW35To: Decimal
        SCED2CurvePrice35From: Decimal
        SCED2CurvePrice35To: Decimal
        outputScheduleFrom: Decimal
        outputScheduleTo: Decimal
        HSLFrom: Decimal
        HSLTo: Decimal
        HASLFrom: Decimal
        HASLTo: Decimal
        HDLFrom: Decimal
        HDLTo: Decimal
        LSLFrom: Decimal
        LSLTo: Decimal
        LASLFrom: Decimal
        LASLTo: Decimal
        LDLFrom: Decimal
        LDLTo: Decimal
        telemeteredResourceStatus: str
        basePointFrom: Decimal
        basePointTo: Decimal
        telemeteredNetOutputFrom: Decimal
        telemeteredNetOutputTo: Decimal
        ASREGUPFrom: Decimal
        ASREGUPTo: Decimal
        ASREGDNFrom: Decimal
        ASREGDNTo: Decimal
        ASRRSFrom: Decimal
        ASRRSTo: Decimal
        ASRRSFFRFrom: Decimal
        ASRRSFFRTo: Decimal
        ASNSRSFrom: Decimal
        ASNSRSTo: Decimal
        bidType: str
        startUpColdOfferFrom: Decimal
        startUpColdOfferTo: Decimal
        startUpHotOfferFrom: Decimal
        startUpHotOfferTo: Decimal
        startUpInterOfferFrom: Decimal
        startUpInterOfferTo: Decimal
        minGenCostFrom: Decimal
        minGenCostTo: Decimal
        submittedTPOMW1From: Decimal
        submittedTPOMW1To: Decimal
        submittedTPOPrice1From: Decimal
        submittedTPOPrice1To: Decimal
        submittedTPOMW2From: Decimal
        submittedTPOMW2To: Decimal
        submittedTPOPrice2From: Decimal
        submittedTPOPrice2To: Decimal
        submittedTPOMW3From: Decimal
        submittedTPOMW3To: Decimal
        submittedTPOPrice3From: Decimal
        submittedTPOPrice3To: Decimal
        submittedTPOMW4From: Decimal
        submittedTPOMW4To: Decimal
        submittedTPOPrice4From: Decimal
        submittedTPOPrice4To: Decimal
        submittedTPOMW5From: Decimal
        submittedTPOMW5To: Decimal
        submittedTPOPrice5From: Decimal
        submittedTPOPrice5To: Decimal
        submittedTPOMW6From: Decimal
        submittedTPOMW6To: Decimal
        submittedTPOPrice6From: Decimal
        submittedTPOPrice6To: Decimal
        submittedTPOMW7From: Decimal
        submittedTPOMW7To: Decimal
        submittedTPOPrice7From: Decimal
        submittedTPOPrice7To: Decimal
        submittedTPOMW8From: Decimal
        submittedTPOMW8To: Decimal
        submittedTPOPrice8From: Decimal
        submittedTPOPrice8To: Decimal
        submittedTPOMW9From: Decimal
        submittedTPOMW9To: Decimal
        submittedTPOPrice9From: Decimal
        submittedTPOPrice9To: Decimal
        submittedTPOMW10From: Decimal
        submittedTPOMW10To: Decimal
        submittedTPOPrice10From: Decimal
        submittedTPOPrice10To: Decimal
        proxyExtension: str
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        qseName: str
        dmeName: str
        resourceName: str
        resourceType: str
        SCED1CurveMW1From: Decimal
        SCED1CurveMW1To: Decimal
        SCED1CurvePrice1From: Decimal
        SCED1CurvePrice1To: Decimal
        SCED1CurveMW2From: Decimal
        SCED1CurveMW2To: Decimal
        SCED1CurvePrice2From: Decimal
        SCED1CurvePrice2To: Decimal
        SCED1CurveMW3From: Decimal
        SCED1CurveMW3To: Decimal
        SCED1CurvePrice3From: Decimal
        SCED1CurvePrice3To: Decimal
        SCED1CurveMW4From: Decimal
        SCED1CurveMW4To: Decimal
        SCED1CurvePrice4From: Decimal
        SCED1CurvePrice4To: Decimal
        SCED1CurveMW5From: Decimal
        SCED1CurveMW5To: Decimal
        SCED1CurvePrice5From: Decimal
        SCED1CurvePrice5To: Decimal
        SCED1CurveMW6From: Decimal
        SCED1CurveMW6To: Decimal
        SCED1CurvePrice6From: Decimal
        SCED1CurvePrice6To: Decimal
        SCED1CurveMW7From: Decimal
        SCED1CurveMW7To: Decimal
        SCED1CurvePrice7From: Decimal
        SCED1CurvePrice7To: Decimal
        SCED1CurveMW8From: Decimal
        SCED1CurveMW8To: Decimal
        SCED1CurvePrice8From: Decimal
        SCED1CurvePrice8To: Decimal
        SCED1CurveMW9From: Decimal
        SCED1CurveMW9To: Decimal
        SCED1CurvePrice9From: Decimal
        SCED1CurvePrice9To: Decimal
        SCED1CurveMW10From: Decimal
        SCED1CurveMW10To: Decimal
        SCED1CurvePrice10From: Decimal
        SCED1CurvePrice10To: Decimal
        SCED1CurveMW11From: Decimal
        SCED1CurveMW11To: Decimal
        SCED1CurvePrice11From: Decimal
        SCED1CurvePrice11To: Decimal
        SCED1CurveMW12From: Decimal
        SCED1CurveMW12To: Decimal
        SCED1CurvePrice12From: Decimal
        SCED1CurvePrice12To: Decimal
        SCED1CurveMW13From: Decimal
        SCED1CurveMW13To: Decimal
        SCED1CurvePrice13From: Decimal
        SCED1CurvePrice13To: Decimal
        SCED1CurveMW14From: Decimal
        SCED1CurveMW14To: Decimal
        SCED1CurvePrice14From: Decimal
        SCED1CurvePrice14To: Decimal
        SCED1CurveMW15From: Decimal
        SCED1CurveMW15To: Decimal
        SCED1CurvePrice15From: Decimal
        SCED1CurvePrice15To: Decimal
        SCED1CurveMW16From: Decimal
        SCED1CurveMW16To: Decimal
        SCED1CurvePrice16From: Decimal
        SCED1CurvePrice16To: Decimal
        SCED1CurveMW17From: Decimal
        SCED1CurveMW17To: Decimal
        SCED1CurvePrice17From: Decimal
        SCED1CurvePrice17To: Decimal
        SCED1CurveMW18From: Decimal
        SCED1CurveMW18To: Decimal
        SCED1CurvePrice18From: Decimal
        SCED1CurvePrice18To: Decimal
        SCED1CurveMW19From: Decimal
        SCED1CurveMW19To: Decimal
        SCED1CurvePrice19From: Decimal
        SCED1CurvePrice19To: Decimal
        SCED1CurveMW20From: Decimal
        SCED1CurveMW20To: Decimal
        SCED1CurvePrice20From: Decimal
        SCED1CurvePrice20To: Decimal
        SCED1CurveMW21From: Decimal
        SCED1CurveMW21To: Decimal
        SCED1CurvePrice21From: Decimal
        SCED1CurvePrice21To: Decimal
        SCED1CurveMW22From: Decimal
        SCED1CurveMW22To: Decimal
        SCED1CurvePrice22From: Decimal
        SCED1CurvePrice22To: Decimal
        SCED1CurveMW23From: Decimal
        SCED1CurveMW23To: Decimal
        SCED1CurvePrice23From: Decimal
        SCED1CurvePrice23To: Decimal
        SCED1CurveMW24From: Decimal
        SCED1CurveMW24To: Decimal
        SCED1CurvePrice24From: Decimal
        SCED1CurvePrice24To: Decimal
        SCED1CurveMW25From: Decimal
        SCED1CurveMW25To: Decimal
        SCED1CurvePrice25From: Decimal
        SCED1CurvePrice25To: Decimal
        SCED1CurveMW26From: Decimal
        SCED1CurveMW26To: Decimal
        SCED1CurvePrice26From: Decimal
        SCED1CurvePrice26To: Decimal
        SCED1CurveMW27From: Decimal
        SCED1CurveMW27To: Decimal
        SCED1CurvePrice27From: Decimal
        SCED1CurvePrice27To: Decimal
        SCED1CurveMW28From: Decimal
        SCED1CurveMW28To: Decimal
        SCED1CurvePrice28From: Decimal
        SCED1CurvePrice28To: Decimal
        SCED1CurveMW29From: Decimal
        SCED1CurveMW29To: Decimal
        SCED1CurvePrice29From: Decimal
        SCED1CurvePrice29To: Decimal
        SCED1CurveMW30From: Decimal
        SCED1CurveMW30To: Decimal
        SCED1CurvePrice30From: Decimal
        SCED1CurvePrice30To: Decimal
        SCED1CurveMW31From: Decimal
        SCED1CurveMW31To: Decimal
        SCED1CurvePrice31From: Decimal
        SCED1CurvePrice31To: Decimal
        SCED1CurveMW32From: Decimal
        SCED1CurveMW32To: Decimal
        SCED1CurvePrice32From: Decimal
        SCED1CurvePrice32To: Decimal
        SCED1CurveMW33From: Decimal
        SCED1CurveMW33To: Decimal
        SCED1CurvePrice33From: Decimal
        SCED1CurvePrice33To: Decimal
        SCED1CurveMW34From: Decimal
        SCED1CurveMW34To: Decimal
        SCED1CurvePrice34From: Decimal
        SCED1CurvePrice34To: Decimal
        SCED1CurveMW35From: Decimal
        SCED1CurveMW35To: Decimal
        SCED1CurvePrice35From: Decimal
        SCED1CurvePrice35To: Decimal
        SCED2CurveMW1From: Decimal
        SCED2CurveMW1To: Decimal
        SCED2CurvePrice1From: Decimal
        SCED2CurvePrice1To: Decimal
        SCED2CurveMW2From: Decimal
        SCED2CurveMW2To: Decimal
        SCED2CurvePrice2From: Decimal
        SCED2CurvePrice2To: Decimal
        SCED2CurveMW3From: Decimal
        SCED2CurveMW3To: Decimal
        SCED2CurvePrice3From: Decimal
        SCED2CurvePrice3To: Decimal
        SCED2CurveMW4From: Decimal
        SCED2CurveMW4To: Decimal
        SCED2CurvePrice4From: Decimal
        SCED2CurvePrice4To: Decimal
        SCED2CurveMW5From: Decimal
        SCED2CurveMW5To: Decimal
        SCED2CurvePrice5From: Decimal
        SCED2CurvePrice5To: Decimal
        SCED2CurveMW6From: Decimal
        SCED2CurveMW6To: Decimal
        SCED2CurvePrice6From: Decimal
        SCED2CurvePrice6To: Decimal
        SCED2CurveMW7From: Decimal
        SCED2CurveMW7To: Decimal
        SCED2CurvePrice7From: Decimal
        SCED2CurvePrice7To: Decimal
        SCED2CurveMW8From: Decimal
        SCED2CurveMW8To: Decimal
        SCED2CurvePrice8From: Decimal
        SCED2CurvePrice8To: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_sced_gen_res_data(
        *,
        SCED2CurveMW9From: Decimal | None = None,
        SCED2CurveMW9To: Decimal | None = None,
        SCED2CurvePrice9From: Decimal | None = None,
        SCED2CurvePrice9To: Decimal | None = None,
        SCED2CurveMW10From: Decimal | None = None,
        SCED2CurveMW10To: Decimal | None = None,
        SCED2CurvePrice10From: Decimal | None = None,
        SCED2CurvePrice10To: Decimal | None = None,
        SCED2CurveMW11From: Decimal | None = None,
        SCED2CurveMW11To: Decimal | None = None,
        SCED2CurvePrice11From: Decimal | None = None,
        SCED2CurvePrice11To: Decimal | None = None,
        SCED2CurveMW12From: Decimal | None = None,
        SCED2CurveMW12To: Decimal | None = None,
        SCED2CurvePrice12From: Decimal | None = None,
        SCED2CurvePrice12To: Decimal | None = None,
        SCED2CurveMW13From: Decimal | None = None,
        SCED2CurveMW13To: Decimal | None = None,
        SCED2CurvePrice13From: Decimal | None = None,
        SCED2CurvePrice13To: Decimal | None = None,
        SCED2CurveMW14From: Decimal | None = None,
        SCED2CurveMW14To: Decimal | None = None,
        SCED2CurvePrice14From: Decimal | None = None,
        SCED2CurvePrice14To: Decimal | None = None,
        SCED2CurveMW15From: Decimal | None = None,
        SCED2CurveMW15To: Decimal | None = None,
        SCED2CurvePrice15From: Decimal | None = None,
        SCED2CurvePrice15To: Decimal | None = None,
        SCED2CurveMW16From: Decimal | None = None,
        SCED2CurveMW16To: Decimal | None = None,
        SCED2CurvePrice16From: Decimal | None = None,
        SCED2CurvePrice16To: Decimal | None = None,
        SCED2CurveMW17From: Decimal | None = None,
        SCED2CurveMW17To: Decimal | None = None,
        SCED2CurvePrice17From: Decimal | None = None,
        SCED2CurvePrice17To: Decimal | None = None,
        SCED2CurveMW18From: Decimal | None = None,
        SCED2CurveMW18To: Decimal | None = None,
        SCED2CurvePrice18From: Decimal | None = None,
        SCED2CurvePrice18To: Decimal | None = None,
        SCED2CurveMW19From: Decimal | None = None,
        SCED2CurveMW19To: Decimal | None = None,
        SCED2CurvePrice19From: Decimal | None = None,
        SCED2CurvePrice19To: Decimal | None = None,
        SCED2CurveMW20From: Decimal | None = None,
        SCED2CurveMW20To: Decimal | None = None,
        SCED2CurvePrice20From: Decimal | None = None,
        SCED2CurvePrice20To: Decimal | None = None,
        SCED2CurveMW21From: Decimal | None = None,
        SCED2CurveMW21To: Decimal | None = None,
        SCED2CurvePrice21From: Decimal | None = None,
        SCED2CurvePrice21To: Decimal | None = None,
        SCED2CurveMW22From: Decimal | None = None,
        SCED2CurveMW22To: Decimal | None = None,
        SCED2CurvePrice22From: Decimal | None = None,
        SCED2CurvePrice22To: Decimal | None = None,
        SCED2CurveMW23From: Decimal | None = None,
        SCED2CurveMW23To: Decimal | None = None,
        SCED2CurvePrice23From: Decimal | None = None,
        SCED2CurvePrice23To: Decimal | None = None,
        SCED2CurveMW24From: Decimal | None = None,
        SCED2CurveMW24To: Decimal | None = None,
        SCED2CurvePrice24From: Decimal | None = None,
        SCED2CurvePrice24To: Decimal | None = None,
        SCED2CurveMW25From: Decimal | None = None,
        SCED2CurveMW25To: Decimal | None = None,
        SCED2CurvePrice25From: Decimal | None = None,
        SCED2CurvePrice25To: Decimal | None = None,
        SCED2CurveMW26From: Decimal | None = None,
        SCED2CurveMW26To: Decimal | None = None,
        SCED2CurvePrice26From: Decimal | None = None,
        SCED2CurvePrice26To: Decimal | None = None,
        SCED2CurveMW27From: Decimal | None = None,
        SCED2CurveMW27To: Decimal | None = None,
        SCED2CurvePrice27From: Decimal | None = None,
        SCED2CurvePrice27To: Decimal | None = None,
        SCED2CurveMW28From: Decimal | None = None,
        SCED2CurveMW28To: Decimal | None = None,
        SCED2CurvePrice28From: Decimal | None = None,
        SCED2CurvePrice28To: Decimal | None = None,
        SCED2CurveMW29From: Decimal | None = None,
        SCED2CurveMW29To: Decimal | None = None,
        SCED2CurvePrice29From: Decimal | None = None,
        SCED2CurvePrice29To: Decimal | None = None,
        SCED2CurveMW30From: Decimal | None = None,
        SCED2CurveMW30To: Decimal | None = None,
        SCED2CurvePrice30From: Decimal | None = None,
        SCED2CurvePrice30To: Decimal | None = None,
        SCED2CurveMW31From: Decimal | None = None,
        SCED2CurveMW31To: Decimal | None = None,
        SCED2CurvePrice31From: Decimal | None = None,
        SCED2CurvePrice31To: Decimal | None = None,
        SCED2CurveMW32From: Decimal | None = None,
        SCED2CurveMW32To: Decimal | None = None,
        SCED2CurvePrice32From: Decimal | None = None,
        SCED2CurvePrice32To: Decimal | None = None,
        SCED2CurveMW33From: Decimal | None = None,
        SCED2CurveMW33To: Decimal | None = None,
        SCED2CurvePrice33From: Decimal | None = None,
        SCED2CurvePrice33To: Decimal | None = None,
        SCED2CurveMW34From: Decimal | None = None,
        SCED2CurveMW34To: Decimal | None = None,
        SCED2CurvePrice34From: Decimal | None = None,
        SCED2CurvePrice34To: Decimal | None = None,
        SCED2CurveMW35From: Decimal | None = None,
        SCED2CurveMW35To: Decimal | None = None,
        SCED2CurvePrice35From: Decimal | None = None,
        SCED2CurvePrice35To: Decimal | None = None,
        outputScheduleFrom: Decimal | None = None,
        outputScheduleTo: Decimal | None = None,
        HSLFrom: Decimal | None = None,
        HSLTo: Decimal | None = None,
        HASLFrom: Decimal | None = None,
        HASLTo: Decimal | None = None,
        HDLFrom: Decimal | None = None,
        HDLTo: Decimal | None = None,
        LSLFrom: Decimal | None = None,
        LSLTo: Decimal | None = None,
        LASLFrom: Decimal | None = None,
        LASLTo: Decimal | None = None,
        LDLFrom: Decimal | None = None,
        LDLTo: Decimal | None = None,
        telemeteredResourceStatus: str | None = None,
        basePointFrom: Decimal | None = None,
        basePointTo: Decimal | None = None,
        telemeteredNetOutputFrom: Decimal | None = None,
        telemeteredNetOutputTo: Decimal | None = None,
        ASREGUPFrom: Decimal | None = None,
        ASREGUPTo: Decimal | None = None,
        ASREGDNFrom: Decimal | None = None,
        ASREGDNTo: Decimal | None = None,
        ASRRSFrom: Decimal | None = None,
        ASRRSTo: Decimal | None = None,
        ASRRSFFRFrom: Decimal | None = None,
        ASRRSFFRTo: Decimal | None = None,
        ASNSRSFrom: Decimal | None = None,
        ASNSRSTo: Decimal | None = None,
        bidType: str | None = None,
        startUpColdOfferFrom: Decimal | None = None,
        startUpColdOfferTo: Decimal | None = None,
        startUpHotOfferFrom: Decimal | None = None,
        startUpHotOfferTo: Decimal | None = None,
        startUpInterOfferFrom: Decimal | None = None,
        startUpInterOfferTo: Decimal | None = None,
        minGenCostFrom: Decimal | None = None,
        minGenCostTo: Decimal | None = None,
        submittedTPOMW1From: Decimal | None = None,
        submittedTPOMW1To: Decimal | None = None,
        submittedTPOPrice1From: Decimal | None = None,
        submittedTPOPrice1To: Decimal | None = None,
        submittedTPOMW2From: Decimal | None = None,
        submittedTPOMW2To: Decimal | None = None,
        submittedTPOPrice2From: Decimal | None = None,
        submittedTPOPrice2To: Decimal | None = None,
        submittedTPOMW3From: Decimal | None = None,
        submittedTPOMW3To: Decimal | None = None,
        submittedTPOPrice3From: Decimal | None = None,
        submittedTPOPrice3To: Decimal | None = None,
        submittedTPOMW4From: Decimal | None = None,
        submittedTPOMW4To: Decimal | None = None,
        submittedTPOPrice4From: Decimal | None = None,
        submittedTPOPrice4To: Decimal | None = None,
        submittedTPOMW5From: Decimal | None = None,
        submittedTPOMW5To: Decimal | None = None,
        submittedTPOPrice5From: Decimal | None = None,
        submittedTPOPrice5To: Decimal | None = None,
        submittedTPOMW6From: Decimal | None = None,
        submittedTPOMW6To: Decimal | None = None,
        submittedTPOPrice6From: Decimal | None = None,
        submittedTPOPrice6To: Decimal | None = None,
        submittedTPOMW7From: Decimal | None = None,
        submittedTPOMW7To: Decimal | None = None,
        submittedTPOPrice7From: Decimal | None = None,
        submittedTPOPrice7To: Decimal | None = None,
        submittedTPOMW8From: Decimal | None = None,
        submittedTPOMW8To: Decimal | None = None,
        submittedTPOPrice8From: Decimal | None = None,
        submittedTPOPrice8To: Decimal | None = None,
        submittedTPOMW9From: Decimal | None = None,
        submittedTPOMW9To: Decimal | None = None,
        submittedTPOPrice9From: Decimal | None = None,
        submittedTPOPrice9To: Decimal | None = None,
        submittedTPOMW10From: Decimal | None = None,
        submittedTPOMW10To: Decimal | None = None,
        submittedTPOPrice10From: Decimal | None = None,
        submittedTPOPrice10To: Decimal | None = None,
        proxyExtension: str | None = None,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        qseName: str | None = None,
        dmeName: str | None = None,
        resourceName: str | None = None,
        resourceType: str | None = None,
        SCED1CurveMW1From: Decimal | None = None,
        SCED1CurveMW1To: Decimal | None = None,
        SCED1CurvePrice1From: Decimal | None = None,
        SCED1CurvePrice1To: Decimal | None = None,
        SCED1CurveMW2From: Decimal | None = None,
        SCED1CurveMW2To: Decimal | None = None,
        SCED1CurvePrice2From: Decimal | None = None,
        SCED1CurvePrice2To: Decimal | None = None,
        SCED1CurveMW3From: Decimal | None = None,
        SCED1CurveMW3To: Decimal | None = None,
        SCED1CurvePrice3From: Decimal | None = None,
        SCED1CurvePrice3To: Decimal | None = None,
        SCED1CurveMW4From: Decimal | None = None,
        SCED1CurveMW4To: Decimal | None = None,
        SCED1CurvePrice4From: Decimal | None = None,
        SCED1CurvePrice4To: Decimal | None = None,
        SCED1CurveMW5From: Decimal | None = None,
        SCED1CurveMW5To: Decimal | None = None,
        SCED1CurvePrice5From: Decimal | None = None,
        SCED1CurvePrice5To: Decimal | None = None,
        SCED1CurveMW6From: Decimal | None = None,
        SCED1CurveMW6To: Decimal | None = None,
        SCED1CurvePrice6From: Decimal | None = None,
        SCED1CurvePrice6To: Decimal | None = None,
        SCED1CurveMW7From: Decimal | None = None,
        SCED1CurveMW7To: Decimal | None = None,
        SCED1CurvePrice7From: Decimal | None = None,
        SCED1CurvePrice7To: Decimal | None = None,
        SCED1CurveMW8From: Decimal | None = None,
        SCED1CurveMW8To: Decimal | None = None,
        SCED1CurvePrice8From: Decimal | None = None,
        SCED1CurvePrice8To: Decimal | None = None,
        SCED1CurveMW9From: Decimal | None = None,
        SCED1CurveMW9To: Decimal | None = None,
        SCED1CurvePrice9From: Decimal | None = None,
        SCED1CurvePrice9To: Decimal | None = None,
        SCED1CurveMW10From: Decimal | None = None,
        SCED1CurveMW10To: Decimal | None = None,
        SCED1CurvePrice10From: Decimal | None = None,
        SCED1CurvePrice10To: Decimal | None = None,
        SCED1CurveMW11From: Decimal | None = None,
        SCED1CurveMW11To: Decimal | None = None,
        SCED1CurvePrice11From: Decimal | None = None,
        SCED1CurvePrice11To: Decimal | None = None,
        SCED1CurveMW12From: Decimal | None = None,
        SCED1CurveMW12To: Decimal | None = None,
        SCED1CurvePrice12From: Decimal | None = None,
        SCED1CurvePrice12To: Decimal | None = None,
        SCED1CurveMW13From: Decimal | None = None,
        SCED1CurveMW13To: Decimal | None = None,
        SCED1CurvePrice13From: Decimal | None = None,
        SCED1CurvePrice13To: Decimal | None = None,
        SCED1CurveMW14From: Decimal | None = None,
        SCED1CurveMW14To: Decimal | None = None,
        SCED1CurvePrice14From: Decimal | None = None,
        SCED1CurvePrice14To: Decimal | None = None,
        SCED1CurveMW15From: Decimal | None = None,
        SCED1CurveMW15To: Decimal | None = None,
        SCED1CurvePrice15From: Decimal | None = None,
        SCED1CurvePrice15To: Decimal | None = None,
        SCED1CurveMW16From: Decimal | None = None,
        SCED1CurveMW16To: Decimal | None = None,
        SCED1CurvePrice16From: Decimal | None = None,
        SCED1CurvePrice16To: Decimal | None = None,
        SCED1CurveMW17From: Decimal | None = None,
        SCED1CurveMW17To: Decimal | None = None,
        SCED1CurvePrice17From: Decimal | None = None,
        SCED1CurvePrice17To: Decimal | None = None,
        SCED1CurveMW18From: Decimal | None = None,
        SCED1CurveMW18To: Decimal | None = None,
        SCED1CurvePrice18From: Decimal | None = None,
        SCED1CurvePrice18To: Decimal | None = None,
        SCED1CurveMW19From: Decimal | None = None,
        SCED1CurveMW19To: Decimal | None = None,
        SCED1CurvePrice19From: Decimal | None = None,
        SCED1CurvePrice19To: Decimal | None = None,
        SCED1CurveMW20From: Decimal | None = None,
        SCED1CurveMW20To: Decimal | None = None,
        SCED1CurvePrice20From: Decimal | None = None,
        SCED1CurvePrice20To: Decimal | None = None,
        SCED1CurveMW21From: Decimal | None = None,
        SCED1CurveMW21To: Decimal | None = None,
        SCED1CurvePrice21From: Decimal | None = None,
        SCED1CurvePrice21To: Decimal | None = None,
        SCED1CurveMW22From: Decimal | None = None,
        SCED1CurveMW22To: Decimal | None = None,
        SCED1CurvePrice22From: Decimal | None = None,
        SCED1CurvePrice22To: Decimal | None = None,
        SCED1CurveMW23From: Decimal | None = None,
        SCED1CurveMW23To: Decimal | None = None,
        SCED1CurvePrice23From: Decimal | None = None,
        SCED1CurvePrice23To: Decimal | None = None,
        SCED1CurveMW24From: Decimal | None = None,
        SCED1CurveMW24To: Decimal | None = None,
        SCED1CurvePrice24From: Decimal | None = None,
        SCED1CurvePrice24To: Decimal | None = None,
        SCED1CurveMW25From: Decimal | None = None,
        SCED1CurveMW25To: Decimal | None = None,
        SCED1CurvePrice25From: Decimal | None = None,
        SCED1CurvePrice25To: Decimal | None = None,
        SCED1CurveMW26From: Decimal | None = None,
        SCED1CurveMW26To: Decimal | None = None,
        SCED1CurvePrice26From: Decimal | None = None,
        SCED1CurvePrice26To: Decimal | None = None,
        SCED1CurveMW27From: Decimal | None = None,
        SCED1CurveMW27To: Decimal | None = None,
        SCED1CurvePrice27From: Decimal | None = None,
        SCED1CurvePrice27To: Decimal | None = None,
        SCED1CurveMW28From: Decimal | None = None,
        SCED1CurveMW28To: Decimal | None = None,
        SCED1CurvePrice28From: Decimal | None = None,
        SCED1CurvePrice28To: Decimal | None = None,
        SCED1CurveMW29From: Decimal | None = None,
        SCED1CurveMW29To: Decimal | None = None,
        SCED1CurvePrice29From: Decimal | None = None,
        SCED1CurvePrice29To: Decimal | None = None,
        SCED1CurveMW30From: Decimal | None = None,
        SCED1CurveMW30To: Decimal | None = None,
        SCED1CurvePrice30From: Decimal | None = None,
        SCED1CurvePrice30To: Decimal | None = None,
        SCED1CurveMW31From: Decimal | None = None,
        SCED1CurveMW31To: Decimal | None = None,
        SCED1CurvePrice31From: Decimal | None = None,
        SCED1CurvePrice31To: Decimal | None = None,
        SCED1CurveMW32From: Decimal | None = None,
        SCED1CurveMW32To: Decimal | None = None,
        SCED1CurvePrice32From: Decimal | None = None,
        SCED1CurvePrice32To: Decimal | None = None,
        SCED1CurveMW33From: Decimal | None = None,
        SCED1CurveMW33To: Decimal | None = None,
        SCED1CurvePrice33From: Decimal | None = None,
        SCED1CurvePrice33To: Decimal | None = None,
        SCED1CurveMW34From: Decimal | None = None,
        SCED1CurveMW34To: Decimal | None = None,
        SCED1CurvePrice34From: Decimal | None = None,
        SCED1CurvePrice34To: Decimal | None = None,
        SCED1CurveMW35From: Decimal | None = None,
        SCED1CurveMW35To: Decimal | None = None,
        SCED1CurvePrice35From: Decimal | None = None,
        SCED1CurvePrice35To: Decimal | None = None,
        SCED2CurveMW1From: Decimal | None = None,
        SCED2CurveMW1To: Decimal | None = None,
        SCED2CurvePrice1From: Decimal | None = None,
        SCED2CurvePrice1To: Decimal | None = None,
        SCED2CurveMW2From: Decimal | None = None,
        SCED2CurveMW2To: Decimal | None = None,
        SCED2CurvePrice2From: Decimal | None = None,
        SCED2CurvePrice2To: Decimal | None = None,
        SCED2CurveMW3From: Decimal | None = None,
        SCED2CurveMW3To: Decimal | None = None,
        SCED2CurvePrice3From: Decimal | None = None,
        SCED2CurvePrice3To: Decimal | None = None,
        SCED2CurveMW4From: Decimal | None = None,
        SCED2CurveMW4To: Decimal | None = None,
        SCED2CurvePrice4From: Decimal | None = None,
        SCED2CurvePrice4To: Decimal | None = None,
        SCED2CurveMW5From: Decimal | None = None,
        SCED2CurveMW5To: Decimal | None = None,
        SCED2CurvePrice5From: Decimal | None = None,
        SCED2CurvePrice5To: Decimal | None = None,
        SCED2CurveMW6From: Decimal | None = None,
        SCED2CurveMW6To: Decimal | None = None,
        SCED2CurvePrice6From: Decimal | None = None,
        SCED2CurvePrice6To: Decimal | None = None,
        SCED2CurveMW7From: Decimal | None = None,
        SCED2CurveMW7To: Decimal | None = None,
        SCED2CurvePrice7From: Decimal | None = None,
        SCED2CurvePrice7To: Decimal | None = None,
        SCED2CurveMW8From: Decimal | None = None,
        SCED2CurveMW8To: Decimal | None = None,
        SCED2CurvePrice8From: Decimal | None = None,
        SCED2CurvePrice8To: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day SCED Gen Resource Data"""
        return _get(
            "np3-965-er/60_sced_gen_res_data",
            SCED2CurveMW9From=SCED2CurveMW9From,
            SCED2CurveMW9To=SCED2CurveMW9To,
            SCED2CurvePrice9From=SCED2CurvePrice9From,
            SCED2CurvePrice9To=SCED2CurvePrice9To,
            SCED2CurveMW10From=SCED2CurveMW10From,
            SCED2CurveMW10To=SCED2CurveMW10To,
            SCED2CurvePrice10From=SCED2CurvePrice10From,
            SCED2CurvePrice10To=SCED2CurvePrice10To,
            SCED2CurveMW11From=SCED2CurveMW11From,
            SCED2CurveMW11To=SCED2CurveMW11To,
            SCED2CurvePrice11From=SCED2CurvePrice11From,
            SCED2CurvePrice11To=SCED2CurvePrice11To,
            SCED2CurveMW12From=SCED2CurveMW12From,
            SCED2CurveMW12To=SCED2CurveMW12To,
            SCED2CurvePrice12From=SCED2CurvePrice12From,
            SCED2CurvePrice12To=SCED2CurvePrice12To,
            SCED2CurveMW13From=SCED2CurveMW13From,
            SCED2CurveMW13To=SCED2CurveMW13To,
            SCED2CurvePrice13From=SCED2CurvePrice13From,
            SCED2CurvePrice13To=SCED2CurvePrice13To,
            SCED2CurveMW14From=SCED2CurveMW14From,
            SCED2CurveMW14To=SCED2CurveMW14To,
            SCED2CurvePrice14From=SCED2CurvePrice14From,
            SCED2CurvePrice14To=SCED2CurvePrice14To,
            SCED2CurveMW15From=SCED2CurveMW15From,
            SCED2CurveMW15To=SCED2CurveMW15To,
            SCED2CurvePrice15From=SCED2CurvePrice15From,
            SCED2CurvePrice15To=SCED2CurvePrice15To,
            SCED2CurveMW16From=SCED2CurveMW16From,
            SCED2CurveMW16To=SCED2CurveMW16To,
            SCED2CurvePrice16From=SCED2CurvePrice16From,
            SCED2CurvePrice16To=SCED2CurvePrice16To,
            SCED2CurveMW17From=SCED2CurveMW17From,
            SCED2CurveMW17To=SCED2CurveMW17To,
            SCED2CurvePrice17From=SCED2CurvePrice17From,
            SCED2CurvePrice17To=SCED2CurvePrice17To,
            SCED2CurveMW18From=SCED2CurveMW18From,
            SCED2CurveMW18To=SCED2CurveMW18To,
            SCED2CurvePrice18From=SCED2CurvePrice18From,
            SCED2CurvePrice18To=SCED2CurvePrice18To,
            SCED2CurveMW19From=SCED2CurveMW19From,
            SCED2CurveMW19To=SCED2CurveMW19To,
            SCED2CurvePrice19From=SCED2CurvePrice19From,
            SCED2CurvePrice19To=SCED2CurvePrice19To,
            SCED2CurveMW20From=SCED2CurveMW20From,
            SCED2CurveMW20To=SCED2CurveMW20To,
            SCED2CurvePrice20From=SCED2CurvePrice20From,
            SCED2CurvePrice20To=SCED2CurvePrice20To,
            SCED2CurveMW21From=SCED2CurveMW21From,
            SCED2CurveMW21To=SCED2CurveMW21To,
            SCED2CurvePrice21From=SCED2CurvePrice21From,
            SCED2CurvePrice21To=SCED2CurvePrice21To,
            SCED2CurveMW22From=SCED2CurveMW22From,
            SCED2CurveMW22To=SCED2CurveMW22To,
            SCED2CurvePrice22From=SCED2CurvePrice22From,
            SCED2CurvePrice22To=SCED2CurvePrice22To,
            SCED2CurveMW23From=SCED2CurveMW23From,
            SCED2CurveMW23To=SCED2CurveMW23To,
            SCED2CurvePrice23From=SCED2CurvePrice23From,
            SCED2CurvePrice23To=SCED2CurvePrice23To,
            SCED2CurveMW24From=SCED2CurveMW24From,
            SCED2CurveMW24To=SCED2CurveMW24To,
            SCED2CurvePrice24From=SCED2CurvePrice24From,
            SCED2CurvePrice24To=SCED2CurvePrice24To,
            SCED2CurveMW25From=SCED2CurveMW25From,
            SCED2CurveMW25To=SCED2CurveMW25To,
            SCED2CurvePrice25From=SCED2CurvePrice25From,
            SCED2CurvePrice25To=SCED2CurvePrice25To,
            SCED2CurveMW26From=SCED2CurveMW26From,
            SCED2CurveMW26To=SCED2CurveMW26To,
            SCED2CurvePrice26From=SCED2CurvePrice26From,
            SCED2CurvePrice26To=SCED2CurvePrice26To,
            SCED2CurveMW27From=SCED2CurveMW27From,
            SCED2CurveMW27To=SCED2CurveMW27To,
            SCED2CurvePrice27From=SCED2CurvePrice27From,
            SCED2CurvePrice27To=SCED2CurvePrice27To,
            SCED2CurveMW28From=SCED2CurveMW28From,
            SCED2CurveMW28To=SCED2CurveMW28To,
            SCED2CurvePrice28From=SCED2CurvePrice28From,
            SCED2CurvePrice28To=SCED2CurvePrice28To,
            SCED2CurveMW29From=SCED2CurveMW29From,
            SCED2CurveMW29To=SCED2CurveMW29To,
            SCED2CurvePrice29From=SCED2CurvePrice29From,
            SCED2CurvePrice29To=SCED2CurvePrice29To,
            SCED2CurveMW30From=SCED2CurveMW30From,
            SCED2CurveMW30To=SCED2CurveMW30To,
            SCED2CurvePrice30From=SCED2CurvePrice30From,
            SCED2CurvePrice30To=SCED2CurvePrice30To,
            SCED2CurveMW31From=SCED2CurveMW31From,
            SCED2CurveMW31To=SCED2CurveMW31To,
            SCED2CurvePrice31From=SCED2CurvePrice31From,
            SCED2CurvePrice31To=SCED2CurvePrice31To,
            SCED2CurveMW32From=SCED2CurveMW32From,
            SCED2CurveMW32To=SCED2CurveMW32To,
            SCED2CurvePrice32From=SCED2CurvePrice32From,
            SCED2CurvePrice32To=SCED2CurvePrice32To,
            SCED2CurveMW33From=SCED2CurveMW33From,
            SCED2CurveMW33To=SCED2CurveMW33To,
            SCED2CurvePrice33From=SCED2CurvePrice33From,
            SCED2CurvePrice33To=SCED2CurvePrice33To,
            SCED2CurveMW34From=SCED2CurveMW34From,
            SCED2CurveMW34To=SCED2CurveMW34To,
            SCED2CurvePrice34From=SCED2CurvePrice34From,
            SCED2CurvePrice34To=SCED2CurvePrice34To,
            SCED2CurveMW35From=SCED2CurveMW35From,
            SCED2CurveMW35To=SCED2CurveMW35To,
            SCED2CurvePrice35From=SCED2CurvePrice35From,
            SCED2CurvePrice35To=SCED2CurvePrice35To,
            outputScheduleFrom=outputScheduleFrom,
            outputScheduleTo=outputScheduleTo,
            HSLFrom=HSLFrom,
            HSLTo=HSLTo,
            HASLFrom=HASLFrom,
            HASLTo=HASLTo,
            HDLFrom=HDLFrom,
            HDLTo=HDLTo,
            LSLFrom=LSLFrom,
            LSLTo=LSLTo,
            LASLFrom=LASLFrom,
            LASLTo=LASLTo,
            LDLFrom=LDLFrom,
            LDLTo=LDLTo,
            telemeteredResourceStatus=telemeteredResourceStatus,
            basePointFrom=basePointFrom,
            basePointTo=basePointTo,
            telemeteredNetOutputFrom=telemeteredNetOutputFrom,
            telemeteredNetOutputTo=telemeteredNetOutputTo,
            ASREGUPFrom=ASREGUPFrom,
            ASREGUPTo=ASREGUPTo,
            ASREGDNFrom=ASREGDNFrom,
            ASREGDNTo=ASREGDNTo,
            ASRRSFrom=ASRRSFrom,
            ASRRSTo=ASRRSTo,
            ASRRSFFRFrom=ASRRSFFRFrom,
            ASRRSFFRTo=ASRRSFFRTo,
            ASNSRSFrom=ASNSRSFrom,
            ASNSRSTo=ASNSRSTo,
            bidType=bidType,
            startUpColdOfferFrom=startUpColdOfferFrom,
            startUpColdOfferTo=startUpColdOfferTo,
            startUpHotOfferFrom=startUpHotOfferFrom,
            startUpHotOfferTo=startUpHotOfferTo,
            startUpInterOfferFrom=startUpInterOfferFrom,
            startUpInterOfferTo=startUpInterOfferTo,
            minGenCostFrom=minGenCostFrom,
            minGenCostTo=minGenCostTo,
            submittedTPOMW1From=submittedTPOMW1From,
            submittedTPOMW1To=submittedTPOMW1To,
            submittedTPOPrice1From=submittedTPOPrice1From,
            submittedTPOPrice1To=submittedTPOPrice1To,
            submittedTPOMW2From=submittedTPOMW2From,
            submittedTPOMW2To=submittedTPOMW2To,
            submittedTPOPrice2From=submittedTPOPrice2From,
            submittedTPOPrice2To=submittedTPOPrice2To,
            submittedTPOMW3From=submittedTPOMW3From,
            submittedTPOMW3To=submittedTPOMW3To,
            submittedTPOPrice3From=submittedTPOPrice3From,
            submittedTPOPrice3To=submittedTPOPrice3To,
            submittedTPOMW4From=submittedTPOMW4From,
            submittedTPOMW4To=submittedTPOMW4To,
            submittedTPOPrice4From=submittedTPOPrice4From,
            submittedTPOPrice4To=submittedTPOPrice4To,
            submittedTPOMW5From=submittedTPOMW5From,
            submittedTPOMW5To=submittedTPOMW5To,
            submittedTPOPrice5From=submittedTPOPrice5From,
            submittedTPOPrice5To=submittedTPOPrice5To,
            submittedTPOMW6From=submittedTPOMW6From,
            submittedTPOMW6To=submittedTPOMW6To,
            submittedTPOPrice6From=submittedTPOPrice6From,
            submittedTPOPrice6To=submittedTPOPrice6To,
            submittedTPOMW7From=submittedTPOMW7From,
            submittedTPOMW7To=submittedTPOMW7To,
            submittedTPOPrice7From=submittedTPOPrice7From,
            submittedTPOPrice7To=submittedTPOPrice7To,
            submittedTPOMW8From=submittedTPOMW8From,
            submittedTPOMW8To=submittedTPOMW8To,
            submittedTPOPrice8From=submittedTPOPrice8From,
            submittedTPOPrice8To=submittedTPOPrice8To,
            submittedTPOMW9From=submittedTPOMW9From,
            submittedTPOMW9To=submittedTPOMW9To,
            submittedTPOPrice9From=submittedTPOPrice9From,
            submittedTPOPrice9To=submittedTPOPrice9To,
            submittedTPOMW10From=submittedTPOMW10From,
            submittedTPOMW10To=submittedTPOMW10To,
            submittedTPOPrice10From=submittedTPOPrice10From,
            submittedTPOPrice10To=submittedTPOPrice10To,
            proxyExtension=proxyExtension,
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            qseName=qseName,
            dmeName=dmeName,
            resourceName=resourceName,
            resourceType=resourceType,
            SCED1CurveMW1From=SCED1CurveMW1From,
            SCED1CurveMW1To=SCED1CurveMW1To,
            SCED1CurvePrice1From=SCED1CurvePrice1From,
            SCED1CurvePrice1To=SCED1CurvePrice1To,
            SCED1CurveMW2From=SCED1CurveMW2From,
            SCED1CurveMW2To=SCED1CurveMW2To,
            SCED1CurvePrice2From=SCED1CurvePrice2From,
            SCED1CurvePrice2To=SCED1CurvePrice2To,
            SCED1CurveMW3From=SCED1CurveMW3From,
            SCED1CurveMW3To=SCED1CurveMW3To,
            SCED1CurvePrice3From=SCED1CurvePrice3From,
            SCED1CurvePrice3To=SCED1CurvePrice3To,
            SCED1CurveMW4From=SCED1CurveMW4From,
            SCED1CurveMW4To=SCED1CurveMW4To,
            SCED1CurvePrice4From=SCED1CurvePrice4From,
            SCED1CurvePrice4To=SCED1CurvePrice4To,
            SCED1CurveMW5From=SCED1CurveMW5From,
            SCED1CurveMW5To=SCED1CurveMW5To,
            SCED1CurvePrice5From=SCED1CurvePrice5From,
            SCED1CurvePrice5To=SCED1CurvePrice5To,
            SCED1CurveMW6From=SCED1CurveMW6From,
            SCED1CurveMW6To=SCED1CurveMW6To,
            SCED1CurvePrice6From=SCED1CurvePrice6From,
            SCED1CurvePrice6To=SCED1CurvePrice6To,
            SCED1CurveMW7From=SCED1CurveMW7From,
            SCED1CurveMW7To=SCED1CurveMW7To,
            SCED1CurvePrice7From=SCED1CurvePrice7From,
            SCED1CurvePrice7To=SCED1CurvePrice7To,
            SCED1CurveMW8From=SCED1CurveMW8From,
            SCED1CurveMW8To=SCED1CurveMW8To,
            SCED1CurvePrice8From=SCED1CurvePrice8From,
            SCED1CurvePrice8To=SCED1CurvePrice8To,
            SCED1CurveMW9From=SCED1CurveMW9From,
            SCED1CurveMW9To=SCED1CurveMW9To,
            SCED1CurvePrice9From=SCED1CurvePrice9From,
            SCED1CurvePrice9To=SCED1CurvePrice9To,
            SCED1CurveMW10From=SCED1CurveMW10From,
            SCED1CurveMW10To=SCED1CurveMW10To,
            SCED1CurvePrice10From=SCED1CurvePrice10From,
            SCED1CurvePrice10To=SCED1CurvePrice10To,
            SCED1CurveMW11From=SCED1CurveMW11From,
            SCED1CurveMW11To=SCED1CurveMW11To,
            SCED1CurvePrice11From=SCED1CurvePrice11From,
            SCED1CurvePrice11To=SCED1CurvePrice11To,
            SCED1CurveMW12From=SCED1CurveMW12From,
            SCED1CurveMW12To=SCED1CurveMW12To,
            SCED1CurvePrice12From=SCED1CurvePrice12From,
            SCED1CurvePrice12To=SCED1CurvePrice12To,
            SCED1CurveMW13From=SCED1CurveMW13From,
            SCED1CurveMW13To=SCED1CurveMW13To,
            SCED1CurvePrice13From=SCED1CurvePrice13From,
            SCED1CurvePrice13To=SCED1CurvePrice13To,
            SCED1CurveMW14From=SCED1CurveMW14From,
            SCED1CurveMW14To=SCED1CurveMW14To,
            SCED1CurvePrice14From=SCED1CurvePrice14From,
            SCED1CurvePrice14To=SCED1CurvePrice14To,
            SCED1CurveMW15From=SCED1CurveMW15From,
            SCED1CurveMW15To=SCED1CurveMW15To,
            SCED1CurvePrice15From=SCED1CurvePrice15From,
            SCED1CurvePrice15To=SCED1CurvePrice15To,
            SCED1CurveMW16From=SCED1CurveMW16From,
            SCED1CurveMW16To=SCED1CurveMW16To,
            SCED1CurvePrice16From=SCED1CurvePrice16From,
            SCED1CurvePrice16To=SCED1CurvePrice16To,
            SCED1CurveMW17From=SCED1CurveMW17From,
            SCED1CurveMW17To=SCED1CurveMW17To,
            SCED1CurvePrice17From=SCED1CurvePrice17From,
            SCED1CurvePrice17To=SCED1CurvePrice17To,
            SCED1CurveMW18From=SCED1CurveMW18From,
            SCED1CurveMW18To=SCED1CurveMW18To,
            SCED1CurvePrice18From=SCED1CurvePrice18From,
            SCED1CurvePrice18To=SCED1CurvePrice18To,
            SCED1CurveMW19From=SCED1CurveMW19From,
            SCED1CurveMW19To=SCED1CurveMW19To,
            SCED1CurvePrice19From=SCED1CurvePrice19From,
            SCED1CurvePrice19To=SCED1CurvePrice19To,
            SCED1CurveMW20From=SCED1CurveMW20From,
            SCED1CurveMW20To=SCED1CurveMW20To,
            SCED1CurvePrice20From=SCED1CurvePrice20From,
            SCED1CurvePrice20To=SCED1CurvePrice20To,
            SCED1CurveMW21From=SCED1CurveMW21From,
            SCED1CurveMW21To=SCED1CurveMW21To,
            SCED1CurvePrice21From=SCED1CurvePrice21From,
            SCED1CurvePrice21To=SCED1CurvePrice21To,
            SCED1CurveMW22From=SCED1CurveMW22From,
            SCED1CurveMW22To=SCED1CurveMW22To,
            SCED1CurvePrice22From=SCED1CurvePrice22From,
            SCED1CurvePrice22To=SCED1CurvePrice22To,
            SCED1CurveMW23From=SCED1CurveMW23From,
            SCED1CurveMW23To=SCED1CurveMW23To,
            SCED1CurvePrice23From=SCED1CurvePrice23From,
            SCED1CurvePrice23To=SCED1CurvePrice23To,
            SCED1CurveMW24From=SCED1CurveMW24From,
            SCED1CurveMW24To=SCED1CurveMW24To,
            SCED1CurvePrice24From=SCED1CurvePrice24From,
            SCED1CurvePrice24To=SCED1CurvePrice24To,
            SCED1CurveMW25From=SCED1CurveMW25From,
            SCED1CurveMW25To=SCED1CurveMW25To,
            SCED1CurvePrice25From=SCED1CurvePrice25From,
            SCED1CurvePrice25To=SCED1CurvePrice25To,
            SCED1CurveMW26From=SCED1CurveMW26From,
            SCED1CurveMW26To=SCED1CurveMW26To,
            SCED1CurvePrice26From=SCED1CurvePrice26From,
            SCED1CurvePrice26To=SCED1CurvePrice26To,
            SCED1CurveMW27From=SCED1CurveMW27From,
            SCED1CurveMW27To=SCED1CurveMW27To,
            SCED1CurvePrice27From=SCED1CurvePrice27From,
            SCED1CurvePrice27To=SCED1CurvePrice27To,
            SCED1CurveMW28From=SCED1CurveMW28From,
            SCED1CurveMW28To=SCED1CurveMW28To,
            SCED1CurvePrice28From=SCED1CurvePrice28From,
            SCED1CurvePrice28To=SCED1CurvePrice28To,
            SCED1CurveMW29From=SCED1CurveMW29From,
            SCED1CurveMW29To=SCED1CurveMW29To,
            SCED1CurvePrice29From=SCED1CurvePrice29From,
            SCED1CurvePrice29To=SCED1CurvePrice29To,
            SCED1CurveMW30From=SCED1CurveMW30From,
            SCED1CurveMW30To=SCED1CurveMW30To,
            SCED1CurvePrice30From=SCED1CurvePrice30From,
            SCED1CurvePrice30To=SCED1CurvePrice30To,
            SCED1CurveMW31From=SCED1CurveMW31From,
            SCED1CurveMW31To=SCED1CurveMW31To,
            SCED1CurvePrice31From=SCED1CurvePrice31From,
            SCED1CurvePrice31To=SCED1CurvePrice31To,
            SCED1CurveMW32From=SCED1CurveMW32From,
            SCED1CurveMW32To=SCED1CurveMW32To,
            SCED1CurvePrice32From=SCED1CurvePrice32From,
            SCED1CurvePrice32To=SCED1CurvePrice32To,
            SCED1CurveMW33From=SCED1CurveMW33From,
            SCED1CurveMW33To=SCED1CurveMW33To,
            SCED1CurvePrice33From=SCED1CurvePrice33From,
            SCED1CurvePrice33To=SCED1CurvePrice33To,
            SCED1CurveMW34From=SCED1CurveMW34From,
            SCED1CurveMW34To=SCED1CurveMW34To,
            SCED1CurvePrice34From=SCED1CurvePrice34From,
            SCED1CurvePrice34To=SCED1CurvePrice34To,
            SCED1CurveMW35From=SCED1CurveMW35From,
            SCED1CurveMW35To=SCED1CurveMW35To,
            SCED1CurvePrice35From=SCED1CurvePrice35From,
            SCED1CurvePrice35To=SCED1CurvePrice35To,
            SCED2CurveMW1From=SCED2CurveMW1From,
            SCED2CurveMW1To=SCED2CurveMW1To,
            SCED2CurvePrice1From=SCED2CurvePrice1From,
            SCED2CurvePrice1To=SCED2CurvePrice1To,
            SCED2CurveMW2From=SCED2CurveMW2From,
            SCED2CurveMW2To=SCED2CurveMW2To,
            SCED2CurvePrice2From=SCED2CurvePrice2From,
            SCED2CurvePrice2To=SCED2CurvePrice2To,
            SCED2CurveMW3From=SCED2CurveMW3From,
            SCED2CurveMW3To=SCED2CurveMW3To,
            SCED2CurvePrice3From=SCED2CurvePrice3From,
            SCED2CurvePrice3To=SCED2CurvePrice3To,
            SCED2CurveMW4From=SCED2CurveMW4From,
            SCED2CurveMW4To=SCED2CurveMW4To,
            SCED2CurvePrice4From=SCED2CurvePrice4From,
            SCED2CurvePrice4To=SCED2CurvePrice4To,
            SCED2CurveMW5From=SCED2CurveMW5From,
            SCED2CurveMW5To=SCED2CurveMW5To,
            SCED2CurvePrice5From=SCED2CurvePrice5From,
            SCED2CurvePrice5To=SCED2CurvePrice5To,
            SCED2CurveMW6From=SCED2CurveMW6From,
            SCED2CurveMW6To=SCED2CurveMW6To,
            SCED2CurvePrice6From=SCED2CurvePrice6From,
            SCED2CurvePrice6To=SCED2CurvePrice6To,
            SCED2CurveMW7From=SCED2CurveMW7From,
            SCED2CurveMW7To=SCED2CurveMW7To,
            SCED2CurvePrice7From=SCED2CurvePrice7From,
            SCED2CurvePrice7To=SCED2CurvePrice7To,
            SCED2CurveMW8From=SCED2CurveMW8From,
            SCED2CurveMW8To=SCED2CurveMW8To,
            SCED2CurvePrice8From=SCED2CurvePrice8From,
            SCED2CurvePrice8To=SCED2CurvePrice8To,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60ScedDsrLoadDataParams(TypedDict, total=False):
        qseName: str
        totalTelemeteredDSRLoadsFrom: Decimal
        totalTelemeteredDSRLoadsTo: Decimal
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_sced_dsr_load_data(
        *,
        qseName: str | None = None,
        totalTelemeteredDSRLoadsFrom: Decimal | None = None,
        totalTelemeteredDSRLoadsTo: Decimal | None = None,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day SCED DSR Load Data"""
        return _get(
            "np3-965-er/60_sced_dsr_load_data",
            qseName=qseName,
            totalTelemeteredDSRLoadsFrom=totalTelemeteredDSRLoadsFrom,
            totalTelemeteredDSRLoadsTo=totalTelemeteredDSRLoadsTo,
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60LoadResDataInScedParams(TypedDict, total=False):
        ASRespForNSPINFrom: Decimal
        ASRespForNSPINTo: Decimal
        ASRespForREGUPFrom: Decimal
        ASRespForREGUPTo: Decimal
        ASRespForREGDNFrom: Decimal
        ASRespForREGDNTo: Decimal
        SCEDBidCurveMW1From: Decimal
        SCEDBidCurveMW1To: Decimal
        SCEDBidCurvePrice1From: Decimal
        SCEDBidCurvePrice1To: Decimal
        SCEDBidCurveMW2From: Decimal
        SCEDBidCurveMW2To: Decimal
        SCEDBidCurvePrice2From: Decimal
        SCEDBidCurvePrice2To: Decimal
        SCEDBidCurveMW3From: Decimal
        SCEDBidCurveMW3To: Decimal
        SCEDBidCurvePrice3From: Decimal
        SCEDBidCurvePrice3To: Decimal
        SCEDBidCurveMW4From: Decimal
        SCEDBidCurveMW4To: Decimal
        SCEDBidCurvePrice4From: Decimal
        SCEDBidCurvePrice4To: Decimal
        SCEDBidCurveMW5From: Decimal
        SCEDBidCurveMW5To: Decimal
        SCEDBidCurvePrice5From: Decimal
        SCEDBidCurvePrice5To: Decimal
        SCEDBidCurveMW6From: Decimal
        SCEDBidCurveMW6To: Decimal
        SCEDBidCurvePrice6From: Decimal
        SCEDBidCurvePrice6To: Decimal
        SCEDBidCurveMW7From: Decimal
        SCEDBidCurveMW7To: Decimal
        SCEDBidCurvePrice7From: Decimal
        SCEDBidCurvePrice7To: Decimal
        SCEDBidCurveMW8From: Decimal
        SCEDBidCurveMW8To: Decimal
        SCEDBidCurvePrice8From: Decimal
        SCEDBidCurvePrice8To: Decimal
        SCEDBidCurveMW9From: Decimal
        SCEDBidCurveMW9To: Decimal
        SCEDBidCurvePrice9From: Decimal
        SCEDBidCurvePrice9To: Decimal
        SCEDBidCurveMW10From: Decimal
        SCEDBidCurveMW10To: Decimal
        SCEDBidCurvePrice10From: Decimal
        SCEDBidCurvePrice10To: Decimal
        HASLFrom: Decimal
        HASLTo: Decimal
        HDLFrom: Decimal
        HDLTo: Decimal
        LASLFrom: Decimal
        LASLTo: Decimal
        LDLFrom: Decimal
        LDLTo: Decimal
        basePointFrom: Decimal
        basePointTo: Decimal
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        qseName: str
        dmeName: str
        resourceName: str
        telResStatus: str
        maxPowerConsumptionFrom: Decimal
        maxPowerConsumptionTo: Decimal
        lowPowerConsumptionFrom: Decimal
        lowPowerConsumptionTo: Decimal
        realPowerConsumptionFrom: Decimal
        realPowerConsumptionTo: Decimal
        ASRespForRRSFrom: Decimal
        ASRespForRRSTo: Decimal
        ASRespForRRSFFRFrom: Decimal
        ASRespForRRSFFRTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_load_res_data_in_sced(
        *,
        ASRespForNSPINFrom: Decimal | None = None,
        ASRespForNSPINTo: Decimal | None = None,
        ASRespForREGUPFrom: Decimal | None = None,
        ASRespForREGUPTo: Decimal | None = None,
        ASRespForREGDNFrom: Decimal | None = None,
        ASRespForREGDNTo: Decimal | None = None,
        SCEDBidCurveMW1From: Decimal | None = None,
        SCEDBidCurveMW1To: Decimal | None = None,
        SCEDBidCurvePrice1From: Decimal | None = None,
        SCEDBidCurvePrice1To: Decimal | None = None,
        SCEDBidCurveMW2From: Decimal | None = None,
        SCEDBidCurveMW2To: Decimal | None = None,
        SCEDBidCurvePrice2From: Decimal | None = None,
        SCEDBidCurvePrice2To: Decimal | None = None,
        SCEDBidCurveMW3From: Decimal | None = None,
        SCEDBidCurveMW3To: Decimal | None = None,
        SCEDBidCurvePrice3From: Decimal | None = None,
        SCEDBidCurvePrice3To: Decimal | None = None,
        SCEDBidCurveMW4From: Decimal | None = None,
        SCEDBidCurveMW4To: Decimal | None = None,
        SCEDBidCurvePrice4From: Decimal | None = None,
        SCEDBidCurvePrice4To: Decimal | None = None,
        SCEDBidCurveMW5From: Decimal | None = None,
        SCEDBidCurveMW5To: Decimal | None = None,
        SCEDBidCurvePrice5From: Decimal | None = None,
        SCEDBidCurvePrice5To: Decimal | None = None,
        SCEDBidCurveMW6From: Decimal | None = None,
        SCEDBidCurveMW6To: Decimal | None = None,
        SCEDBidCurvePrice6From: Decimal | None = None,
        SCEDBidCurvePrice6To: Decimal | None = None,
        SCEDBidCurveMW7From: Decimal | None = None,
        SCEDBidCurveMW7To: Decimal | None = None,
        SCEDBidCurvePrice7From: Decimal | None = None,
        SCEDBidCurvePrice7To: Decimal | None = None,
        SCEDBidCurveMW8From: Decimal | None = None,
        SCEDBidCurveMW8To: Decimal | None = None,
        SCEDBidCurvePrice8From: Decimal | None = None,
        SCEDBidCurvePrice8To: Decimal | None = None,
        SCEDBidCurveMW9From: Decimal | None = None,
        SCEDBidCurveMW9To: Decimal | None = None,
        SCEDBidCurvePrice9From: Decimal | None = None,
        SCEDBidCurvePrice9To: Decimal | None = None,
        SCEDBidCurveMW10From: Decimal | None = None,
        SCEDBidCurveMW10To: Decimal | None = None,
        SCEDBidCurvePrice10From: Decimal | None = None,
        SCEDBidCurvePrice10To: Decimal | None = None,
        HASLFrom: Decimal | None = None,
        HASLTo: Decimal | None = None,
        HDLFrom: Decimal | None = None,
        HDLTo: Decimal | None = None,
        LASLFrom: Decimal | None = None,
        LASLTo: Decimal | None = None,
        LDLFrom: Decimal | None = None,
        LDLTo: Decimal | None = None,
        basePointFrom: Decimal | None = None,
        basePointTo: Decimal | None = None,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        qseName: str | None = None,
        dmeName: str | None = None,
        resourceName: str | None = None,
        telResStatus: str | None = None,
        maxPowerConsumptionFrom: Decimal | None = None,
        maxPowerConsumptionTo: Decimal | None = None,
        lowPowerConsumptionFrom: Decimal | None = None,
        lowPowerConsumptionTo: Decimal | None = None,
        realPowerConsumptionFrom: Decimal | None = None,
        realPowerConsumptionTo: Decimal | None = None,
        ASRespForRRSFrom: Decimal | None = None,
        ASRespForRRSTo: Decimal | None = None,
        ASRespForRRSFFRFrom: Decimal | None = None,
        ASRespForRRSFFRTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day Load Resource Data in SCED"""
        return _get(
            "np3-965-er/60_load_res_data_in_sced",
            ASRespForNSPINFrom=ASRespForNSPINFrom,
            ASRespForNSPINTo=ASRespForNSPINTo,
            ASRespForREGUPFrom=ASRespForREGUPFrom,
            ASRespForREGUPTo=ASRespForREGUPTo,
            ASRespForREGDNFrom=ASRespForREGDNFrom,
            ASRespForREGDNTo=ASRespForREGDNTo,
            SCEDBidCurveMW1From=SCEDBidCurveMW1From,
            SCEDBidCurveMW1To=SCEDBidCurveMW1To,
            SCEDBidCurvePrice1From=SCEDBidCurvePrice1From,
            SCEDBidCurvePrice1To=SCEDBidCurvePrice1To,
            SCEDBidCurveMW2From=SCEDBidCurveMW2From,
            SCEDBidCurveMW2To=SCEDBidCurveMW2To,
            SCEDBidCurvePrice2From=SCEDBidCurvePrice2From,
            SCEDBidCurvePrice2To=SCEDBidCurvePrice2To,
            SCEDBidCurveMW3From=SCEDBidCurveMW3From,
            SCEDBidCurveMW3To=SCEDBidCurveMW3To,
            SCEDBidCurvePrice3From=SCEDBidCurvePrice3From,
            SCEDBidCurvePrice3To=SCEDBidCurvePrice3To,
            SCEDBidCurveMW4From=SCEDBidCurveMW4From,
            SCEDBidCurveMW4To=SCEDBidCurveMW4To,
            SCEDBidCurvePrice4From=SCEDBidCurvePrice4From,
            SCEDBidCurvePrice4To=SCEDBidCurvePrice4To,
            SCEDBidCurveMW5From=SCEDBidCurveMW5From,
            SCEDBidCurveMW5To=SCEDBidCurveMW5To,
            SCEDBidCurvePrice5From=SCEDBidCurvePrice5From,
            SCEDBidCurvePrice5To=SCEDBidCurvePrice5To,
            SCEDBidCurveMW6From=SCEDBidCurveMW6From,
            SCEDBidCurveMW6To=SCEDBidCurveMW6To,
            SCEDBidCurvePrice6From=SCEDBidCurvePrice6From,
            SCEDBidCurvePrice6To=SCEDBidCurvePrice6To,
            SCEDBidCurveMW7From=SCEDBidCurveMW7From,
            SCEDBidCurveMW7To=SCEDBidCurveMW7To,
            SCEDBidCurvePrice7From=SCEDBidCurvePrice7From,
            SCEDBidCurvePrice7To=SCEDBidCurvePrice7To,
            SCEDBidCurveMW8From=SCEDBidCurveMW8From,
            SCEDBidCurveMW8To=SCEDBidCurveMW8To,
            SCEDBidCurvePrice8From=SCEDBidCurvePrice8From,
            SCEDBidCurvePrice8To=SCEDBidCurvePrice8To,
            SCEDBidCurveMW9From=SCEDBidCurveMW9From,
            SCEDBidCurveMW9To=SCEDBidCurveMW9To,
            SCEDBidCurvePrice9From=SCEDBidCurvePrice9From,
            SCEDBidCurvePrice9To=SCEDBidCurvePrice9To,
            SCEDBidCurveMW10From=SCEDBidCurveMW10From,
            SCEDBidCurveMW10To=SCEDBidCurveMW10To,
            SCEDBidCurvePrice10From=SCEDBidCurvePrice10From,
            SCEDBidCurvePrice10To=SCEDBidCurvePrice10To,
            HASLFrom=HASLFrom,
            HASLTo=HASLTo,
            HDLFrom=HDLFrom,
            HDLTo=HDLTo,
            LASLFrom=LASLFrom,
            LASLTo=LASLTo,
            LDLFrom=LDLFrom,
            LDLTo=LDLTo,
            basePointFrom=basePointFrom,
            basePointTo=basePointTo,
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            qseName=qseName,
            dmeName=dmeName,
            resourceName=resourceName,
            telResStatus=telResStatus,
            maxPowerConsumptionFrom=maxPowerConsumptionFrom,
            maxPowerConsumptionTo=maxPowerConsumptionTo,
            lowPowerConsumptionFrom=lowPowerConsumptionFrom,
            lowPowerConsumptionTo=lowPowerConsumptionTo,
            realPowerConsumptionFrom=realPowerConsumptionFrom,
            realPowerConsumptionTo=realPowerConsumptionTo,
            ASRespForRRSFrom=ASRespForRRSFrom,
            ASRespForRRSTo=ASRespForRRSTo,
            ASRespForRRSFFRFrom=ASRespForRRSFFRFrom,
            ASRespForRRSFFRTo=ASRespForRRSFFRTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60HdlLdlManOverrideParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        participantName: str
        resourceName: str
        HDLOriginalFrom: Decimal
        HDLOriginalTo: Decimal
        HDLManualFrom: Decimal
        HDLManualTo: Decimal
        HDLFinalFrom: Decimal
        HDLFinalTo: Decimal
        LDLOriginalFrom: Decimal
        LDLOriginalTo: Decimal
        LDLManualFrom: Decimal
        LDLManualTo: Decimal
        LDLFinalFrom: Decimal
        LDLFinalTo: Decimal
        reasonCode: str
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_hdl_ldl_man_override(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        participantName: str | None = None,
        resourceName: str | None = None,
        HDLOriginalFrom: Decimal | None = None,
        HDLOriginalTo: Decimal | None = None,
        HDLManualFrom: Decimal | None = None,
        HDLManualTo: Decimal | None = None,
        HDLFinalFrom: Decimal | None = None,
        HDLFinalTo: Decimal | None = None,
        LDLOriginalFrom: Decimal | None = None,
        LDLOriginalTo: Decimal | None = None,
        LDLManualFrom: Decimal | None = None,
        LDLManualTo: Decimal | None = None,
        LDLFinalFrom: Decimal | None = None,
        LDLFinalTo: Decimal | None = None,
        reasonCode: str | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day HDL and LDL Manual Override Summary"""
        return _get(
            "np3-965-er/60_hdl_ldl_man_override",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            participantName=participantName,
            resourceName=resourceName,
            HDLOriginalFrom=HDLOriginalFrom,
            HDLOriginalTo=HDLOriginalTo,
            HDLManualFrom=HDLManualFrom,
            HDLManualTo=HDLManualTo,
            HDLFinalFrom=HDLFinalFrom,
            HDLFinalTo=HDLFinalTo,
            LDLOriginalFrom=LDLOriginalFrom,
            LDLOriginalTo=LDLOriginalTo,
            LDLManualFrom=LDLManualFrom,
            LDLManualTo=LDLManualTo,
            LDLFinalFrom=LDLFinalFrom,
            LDLFinalTo=LDLFinalTo,
            reasonCode=reasonCode,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np3_966_er:
    """60-Day DAM Disclosure Reports  This report will contain all 60 day disclosure data related to DAM. The following individual files are included in the report: NP3-974-EX 61-day QSE-specific Self-Arranged AS in DAM NP3-975-EX 61-day Generation Resource data in DAM NP3-976-EX 61-day Generation Resource AS Offers in DAM NP3-977-EX 61-day Load Resource data in DAM NP3-978-EX 61-day Load Resource AS Offers in DAM NP3-979-EX 61-day Settlement Point Data in DAM- Energy Only Offers NP3-980-EX 61-day Settlement Point Data in DAM- Energy Only Offer Award NP3-981-EX 61-day Settlement Point Data in DAM- Energy Bids NP3-982-EX 61-day Settlement Point Data in DAM- Bids Award NP3-983-EX 61-day Settlement Point Data in DAM- CRR Offers NP3-984-EX 61-day Settlement Point Data in DAM- CRR Awards NP3-985-EX 61-day Settlement Point Data Point-to-Point Obligation Bids NP3-986-EX 61-day Settlement Point Data Point-to-Point Obligation Bid Awards"""

    class _60DamQseSelfAsParams(TypedDict, total=False):
        totalSelfArrangedASRRSUFRFrom: Decimal
        totalSelfArrangedASRRSUFRTo: Decimal
        deliveryDateFrom: datetime.datetime
        deliveryDateTo: datetime.datetime
        hourEndingFrom: int
        hourEndingTo: int
        qseName: str
        totalSelfArrangedASREGUPFrom: Decimal
        totalSelfArrangedASREGUPTo: Decimal
        totalSelfArrangedASREGDNFrom: Decimal
        totalSelfArrangedASREGDNTo: Decimal
        totalSelfArrangedASNSPINFrom: Decimal
        totalSelfArrangedASNSPINTo: Decimal
        totalSelfArrangedASNSPNMFrom: Decimal
        totalSelfArrangedASNSPNMTo: Decimal
        totalSelfArrangedASRRSPFRFrom: Decimal
        totalSelfArrangedASRRSPFRTo: Decimal
        totalSelfArrangedASRRSFFRFrom: Decimal
        totalSelfArrangedASRRSFFRTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_qse_self_as(
        *,
        totalSelfArrangedASRRSUFRFrom: Decimal | None = None,
        totalSelfArrangedASRRSUFRTo: Decimal | None = None,
        deliveryDateFrom: datetime.datetime | None = None,
        deliveryDateTo: datetime.datetime | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        qseName: str | None = None,
        totalSelfArrangedASREGUPFrom: Decimal | None = None,
        totalSelfArrangedASREGUPTo: Decimal | None = None,
        totalSelfArrangedASREGDNFrom: Decimal | None = None,
        totalSelfArrangedASREGDNTo: Decimal | None = None,
        totalSelfArrangedASNSPINFrom: Decimal | None = None,
        totalSelfArrangedASNSPINTo: Decimal | None = None,
        totalSelfArrangedASNSPNMFrom: Decimal | None = None,
        totalSelfArrangedASNSPNMTo: Decimal | None = None,
        totalSelfArrangedASRRSPFRFrom: Decimal | None = None,
        totalSelfArrangedASRRSPFRTo: Decimal | None = None,
        totalSelfArrangedASRRSFFRFrom: Decimal | None = None,
        totalSelfArrangedASRRSFFRTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM QSE Self Arranged AS"""
        return _get(
            "np3-966-er/60_dam_qse_self_as",
            totalSelfArrangedASRRSUFRFrom=totalSelfArrangedASRRSUFRFrom,
            totalSelfArrangedASRRSUFRTo=totalSelfArrangedASRRSUFRTo,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            qseName=qseName,
            totalSelfArrangedASREGUPFrom=totalSelfArrangedASREGUPFrom,
            totalSelfArrangedASREGUPTo=totalSelfArrangedASREGUPTo,
            totalSelfArrangedASREGDNFrom=totalSelfArrangedASREGDNFrom,
            totalSelfArrangedASREGDNTo=totalSelfArrangedASREGDNTo,
            totalSelfArrangedASNSPINFrom=totalSelfArrangedASNSPINFrom,
            totalSelfArrangedASNSPINTo=totalSelfArrangedASNSPINTo,
            totalSelfArrangedASNSPNMFrom=totalSelfArrangedASNSPNMFrom,
            totalSelfArrangedASNSPNMTo=totalSelfArrangedASNSPNMTo,
            totalSelfArrangedASRRSPFRFrom=totalSelfArrangedASRRSPFRFrom,
            totalSelfArrangedASRRSPFRTo=totalSelfArrangedASRRSPFRTo,
            totalSelfArrangedASRRSFFRFrom=totalSelfArrangedASRRSFFRFrom,
            totalSelfArrangedASRRSFFRTo=totalSelfArrangedASRRSFFRTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60DamPtpOblOptAwardsParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: str
        hourEndingTo: str
        qseName: str
        settlementPointSource: str
        settlementPointSink: str
        MWFrom: Decimal
        MWTo: Decimal
        priceFrom: Decimal
        priceTo: Decimal
        offerId: str
        CRRId: str
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_ptp_obl_opt_awards(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: str | None = None,
        hourEndingTo: str | None = None,
        qseName: str | None = None,
        settlementPointSource: str | None = None,
        settlementPointSink: str | None = None,
        MWFrom: Decimal | None = None,
        MWTo: Decimal | None = None,
        priceFrom: Decimal | None = None,
        priceTo: Decimal | None = None,
        offerId: str | None = None,
        CRRId: str | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM PTP Obligation Option Awards"""
        return _get(
            "np3-966-er/60_dam_ptp_obl_opt_awards",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            qseName=qseName,
            settlementPointSource=settlementPointSource,
            settlementPointSink=settlementPointSink,
            MWFrom=MWFrom,
            MWTo=MWTo,
            priceFrom=priceFrom,
            priceTo=priceTo,
            offerId=offerId,
            CRRId=CRRId,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60DamPtpOblOptParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: str
        hourEndingTo: str
        qseName: str
        settlementPointSource: str
        settlementPointSink: str
        MWFrom: Decimal
        MWTo: Decimal
        priceFrom: int
        priceTo: int
        offerId: str
        multiHourBlock: bool
        CRRIdFrom: int
        CRRIdTo: int
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_ptp_obl_opt(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: str | None = None,
        hourEndingTo: str | None = None,
        qseName: str | None = None,
        settlementPointSource: str | None = None,
        settlementPointSink: str | None = None,
        MWFrom: Decimal | None = None,
        MWTo: Decimal | None = None,
        priceFrom: int | None = None,
        priceTo: int | None = None,
        offerId: str | None = None,
        multiHourBlock: bool | None = None,
        CRRIdFrom: int | None = None,
        CRRIdTo: int | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM PTP Obligation Option"""
        return _get(
            "np3-966-er/60_dam_ptp_obl_opt",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            qseName=qseName,
            settlementPointSource=settlementPointSource,
            settlementPointSink=settlementPointSink,
            MWFrom=MWFrom,
            MWTo=MWTo,
            priceFrom=priceFrom,
            priceTo=priceTo,
            offerId=offerId,
            multiHourBlock=multiHourBlock,
            CRRIdFrom=CRRIdFrom,
            CRRIdTo=CRRIdTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60DamPtpOblBidsParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: str
        hourEndingTo: str
        qseName: str
        settlementPointSource: str
        settlementPointSink: str
        PTPBidMWFrom: Decimal
        PTPBidMWTo: Decimal
        PTPBidPriceFrom: Decimal
        PTPBidPriceTo: Decimal
        bidId: str
        multiHourBlock: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_ptp_obl_bids(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: str | None = None,
        hourEndingTo: str | None = None,
        qseName: str | None = None,
        settlementPointSource: str | None = None,
        settlementPointSink: str | None = None,
        PTPBidMWFrom: Decimal | None = None,
        PTPBidMWTo: Decimal | None = None,
        PTPBidPriceFrom: Decimal | None = None,
        PTPBidPriceTo: Decimal | None = None,
        bidId: str | None = None,
        multiHourBlock: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM PTP Obligation Bids"""
        return _get(
            "np3-966-er/60_dam_ptp_obl_bids",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            qseName=qseName,
            settlementPointSource=settlementPointSource,
            settlementPointSink=settlementPointSink,
            PTPBidMWFrom=PTPBidMWFrom,
            PTPBidMWTo=PTPBidMWTo,
            PTPBidPriceFrom=PTPBidPriceFrom,
            PTPBidPriceTo=PTPBidPriceTo,
            bidId=bidId,
            multiHourBlock=multiHourBlock,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60DamPtpOblBidAwardsParams(TypedDict, total=False):
        settlementPointSource: str
        settlementPointSink: str
        PTPBidAwardMWFrom: Decimal
        PTPBidAwardMWTo: Decimal
        PTPBidPriceFrom: Decimal
        PTPBidPriceTo: Decimal
        bidId: str
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: str
        hourEndingTo: str
        qseName: str
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_ptp_obl_bid_awards(
        *,
        settlementPointSource: str | None = None,
        settlementPointSink: str | None = None,
        PTPBidAwardMWFrom: Decimal | None = None,
        PTPBidAwardMWTo: Decimal | None = None,
        PTPBidPriceFrom: Decimal | None = None,
        PTPBidPriceTo: Decimal | None = None,
        bidId: str | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: str | None = None,
        hourEndingTo: str | None = None,
        qseName: str | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM PTP Obligation Bid Awards"""
        return _get(
            "np3-966-er/60_dam_ptp_obl_bid_awards",
            settlementPointSource=settlementPointSource,
            settlementPointSink=settlementPointSink,
            PTPBidAwardMWFrom=PTPBidAwardMWFrom,
            PTPBidAwardMWTo=PTPBidAwardMWTo,
            PTPBidPriceFrom=PTPBidPriceFrom,
            PTPBidPriceTo=PTPBidPriceTo,
            bidId=bidId,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            qseName=qseName,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60DamLoadResDataParams(TypedDict, total=False):
        REGUPMCPCFrom: Decimal
        REGUPMCPCTo: Decimal
        REGDNAwardedFrom: Decimal
        REGDNAwardedTo: Decimal
        REGDNMCPCFrom: Decimal
        REGDNMCPCTo: Decimal
        RRSPFRAwardedFrom: Decimal
        RRSPFRAwardedTo: Decimal
        RRSFFRAwardedFrom: Decimal
        RRSFFRAwardedTo: Decimal
        RRSUFRAwardedFrom: Decimal
        RRSUFRAwardedTo: Decimal
        RRSMCPCFrom: Decimal
        RRSMCPCTo: Decimal
        NSPINAwardedFrom: Decimal
        NSPINAwardedTo: Decimal
        NSPINMCPCFrom: Decimal
        NSPINMCPCTo: Decimal
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: str
        hourEndingTo: str
        loadResourceName: str
        maxPowerConsumptionFrom: Decimal
        maxPowerConsumptionTo: Decimal
        lowPowerConsumptionFrom: Decimal
        lowPowerConsumptionTo: Decimal
        REGUPAwardedFrom: Decimal
        REGUPAwardedTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_load_res_data(
        *,
        REGUPMCPCFrom: Decimal | None = None,
        REGUPMCPCTo: Decimal | None = None,
        REGDNAwardedFrom: Decimal | None = None,
        REGDNAwardedTo: Decimal | None = None,
        REGDNMCPCFrom: Decimal | None = None,
        REGDNMCPCTo: Decimal | None = None,
        RRSPFRAwardedFrom: Decimal | None = None,
        RRSPFRAwardedTo: Decimal | None = None,
        RRSFFRAwardedFrom: Decimal | None = None,
        RRSFFRAwardedTo: Decimal | None = None,
        RRSUFRAwardedFrom: Decimal | None = None,
        RRSUFRAwardedTo: Decimal | None = None,
        RRSMCPCFrom: Decimal | None = None,
        RRSMCPCTo: Decimal | None = None,
        NSPINAwardedFrom: Decimal | None = None,
        NSPINAwardedTo: Decimal | None = None,
        NSPINMCPCFrom: Decimal | None = None,
        NSPINMCPCTo: Decimal | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: str | None = None,
        hourEndingTo: str | None = None,
        loadResourceName: str | None = None,
        maxPowerConsumptionFrom: Decimal | None = None,
        maxPowerConsumptionTo: Decimal | None = None,
        lowPowerConsumptionFrom: Decimal | None = None,
        lowPowerConsumptionTo: Decimal | None = None,
        REGUPAwardedFrom: Decimal | None = None,
        REGUPAwardedTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM Load Resource Data"""
        return _get(
            "np3-966-er/60_dam_load_res_data",
            REGUPMCPCFrom=REGUPMCPCFrom,
            REGUPMCPCTo=REGUPMCPCTo,
            REGDNAwardedFrom=REGDNAwardedFrom,
            REGDNAwardedTo=REGDNAwardedTo,
            REGDNMCPCFrom=REGDNMCPCFrom,
            REGDNMCPCTo=REGDNMCPCTo,
            RRSPFRAwardedFrom=RRSPFRAwardedFrom,
            RRSPFRAwardedTo=RRSPFRAwardedTo,
            RRSFFRAwardedFrom=RRSFFRAwardedFrom,
            RRSFFRAwardedTo=RRSFFRAwardedTo,
            RRSUFRAwardedFrom=RRSUFRAwardedFrom,
            RRSUFRAwardedTo=RRSUFRAwardedTo,
            RRSMCPCFrom=RRSMCPCFrom,
            RRSMCPCTo=RRSMCPCTo,
            NSPINAwardedFrom=NSPINAwardedFrom,
            NSPINAwardedTo=NSPINAwardedTo,
            NSPINMCPCFrom=NSPINMCPCFrom,
            NSPINMCPCTo=NSPINMCPCTo,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            loadResourceName=loadResourceName,
            maxPowerConsumptionFrom=maxPowerConsumptionFrom,
            maxPowerConsumptionTo=maxPowerConsumptionTo,
            lowPowerConsumptionFrom=lowPowerConsumptionFrom,
            lowPowerConsumptionTo=lowPowerConsumptionTo,
            REGUPAwardedFrom=REGUPAwardedFrom,
            REGUPAwardedTo=REGUPAwardedTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60DamLoadResAsOffersParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: str
        hourEndingTo: str
        qseName: str
        dmeName: str
        loadResourceName: str
        multiHourBlock: bool
        blockIndicator1: bool
        price1RRSPFRFrom: Decimal
        price1RRSPFRTo: Decimal
        price1RRSFFRFrom: Decimal
        price1RRSFFRTo: Decimal
        price1RRSUFRFrom: Decimal
        price1RRSUFRTo: Decimal
        price1OnlineNSPINFrom: Decimal
        price1OnlineNSPINTo: Decimal
        price1REGUPFrom: Decimal
        price1REGUPTo: Decimal
        price1REGDNFrom: Decimal
        price1REGDNTo: Decimal
        price1OfflineNSPINFrom: Decimal
        price1OfflineNSPINTo: Decimal
        quantityMW1From: int
        quantityMW1To: int
        blockIndicator2: bool
        price2RRSPFRFrom: Decimal
        price2RRSPFRTo: Decimal
        price2RRSFFRFrom: Decimal
        price2RRSFFRTo: Decimal
        price2RRSUFRFrom: Decimal
        price2RRSUFRTo: Decimal
        price2OnlineNSPINFrom: Decimal
        price2OnlineNSPINTo: Decimal
        price2REGUPFrom: Decimal
        price2REGUPTo: Decimal
        price2REGDNFrom: Decimal
        price2REGDNTo: Decimal
        price2OfflineNSPINFrom: Decimal
        price2OfflineNSPINTo: Decimal
        quantityMW2From: int
        quantityMW2To: int
        blockIndicator3: bool
        price3RRSPFRFrom: Decimal
        price3RRSPFRTo: Decimal
        price3RRSFFRFrom: Decimal
        price3RRSFFRTo: Decimal
        price3RRSUFRFrom: Decimal
        price3RRSUFRTo: Decimal
        price3OnlineNSPINFrom: Decimal
        price3OnlineNSPINTo: Decimal
        price3REGUPFrom: Decimal
        price3REGUPTo: Decimal
        price3REGDNFrom: Decimal
        price3REGDNTo: Decimal
        price3OfflineNSPINFrom: Decimal
        price3OfflineNSPINTo: Decimal
        quantityMW3From: int
        quantityMW3To: int
        blockIndicator4: bool
        price4RRSPFRFrom: Decimal
        price4RRSPFRTo: Decimal
        price4RRSFFRFrom: Decimal
        price4RRSFFRTo: Decimal
        price4RRSUFRFrom: Decimal
        price4RRSUFRTo: Decimal
        price4OnlineNSPINFrom: Decimal
        price4OnlineNSPINTo: Decimal
        price4REGUPFrom: Decimal
        price4REGUPTo: Decimal
        price4REGDNFrom: Decimal
        price4REGDNTo: Decimal
        price4OfflineNSPINFrom: Decimal
        price4OfflineNSPINTo: Decimal
        quantityMW4From: int
        quantityMW4To: int
        blockIndicator5: bool
        price5RRSPFRFrom: Decimal
        price5RRSPFRTo: Decimal
        price5RRSFFRFrom: Decimal
        price5RRSFFRTo: Decimal
        price5RRSUFRFrom: Decimal
        price5RRSUFRTo: Decimal
        price5OnlineNSPINFrom: Decimal
        price5OnlineNSPINTo: Decimal
        price5REGUPFrom: Decimal
        price5REGUPTo: Decimal
        price5REGDNFrom: Decimal
        price5REGDNTo: Decimal
        price5OfflineNSPINFrom: Decimal
        price5OfflineNSPINTo: Decimal
        quantityMW5From: int
        quantityMW5To: int
        NCLRFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_load_res_as_offers(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: str | None = None,
        hourEndingTo: str | None = None,
        qseName: str | None = None,
        dmeName: str | None = None,
        loadResourceName: str | None = None,
        multiHourBlock: bool | None = None,
        blockIndicator1: bool | None = None,
        price1RRSPFRFrom: Decimal | None = None,
        price1RRSPFRTo: Decimal | None = None,
        price1RRSFFRFrom: Decimal | None = None,
        price1RRSFFRTo: Decimal | None = None,
        price1RRSUFRFrom: Decimal | None = None,
        price1RRSUFRTo: Decimal | None = None,
        price1OnlineNSPINFrom: Decimal | None = None,
        price1OnlineNSPINTo: Decimal | None = None,
        price1REGUPFrom: Decimal | None = None,
        price1REGUPTo: Decimal | None = None,
        price1REGDNFrom: Decimal | None = None,
        price1REGDNTo: Decimal | None = None,
        price1OfflineNSPINFrom: Decimal | None = None,
        price1OfflineNSPINTo: Decimal | None = None,
        quantityMW1From: int | None = None,
        quantityMW1To: int | None = None,
        blockIndicator2: bool | None = None,
        price2RRSPFRFrom: Decimal | None = None,
        price2RRSPFRTo: Decimal | None = None,
        price2RRSFFRFrom: Decimal | None = None,
        price2RRSFFRTo: Decimal | None = None,
        price2RRSUFRFrom: Decimal | None = None,
        price2RRSUFRTo: Decimal | None = None,
        price2OnlineNSPINFrom: Decimal | None = None,
        price2OnlineNSPINTo: Decimal | None = None,
        price2REGUPFrom: Decimal | None = None,
        price2REGUPTo: Decimal | None = None,
        price2REGDNFrom: Decimal | None = None,
        price2REGDNTo: Decimal | None = None,
        price2OfflineNSPINFrom: Decimal | None = None,
        price2OfflineNSPINTo: Decimal | None = None,
        quantityMW2From: int | None = None,
        quantityMW2To: int | None = None,
        blockIndicator3: bool | None = None,
        price3RRSPFRFrom: Decimal | None = None,
        price3RRSPFRTo: Decimal | None = None,
        price3RRSFFRFrom: Decimal | None = None,
        price3RRSFFRTo: Decimal | None = None,
        price3RRSUFRFrom: Decimal | None = None,
        price3RRSUFRTo: Decimal | None = None,
        price3OnlineNSPINFrom: Decimal | None = None,
        price3OnlineNSPINTo: Decimal | None = None,
        price3REGUPFrom: Decimal | None = None,
        price3REGUPTo: Decimal | None = None,
        price3REGDNFrom: Decimal | None = None,
        price3REGDNTo: Decimal | None = None,
        price3OfflineNSPINFrom: Decimal | None = None,
        price3OfflineNSPINTo: Decimal | None = None,
        quantityMW3From: int | None = None,
        quantityMW3To: int | None = None,
        blockIndicator4: bool | None = None,
        price4RRSPFRFrom: Decimal | None = None,
        price4RRSPFRTo: Decimal | None = None,
        price4RRSFFRFrom: Decimal | None = None,
        price4RRSFFRTo: Decimal | None = None,
        price4RRSUFRFrom: Decimal | None = None,
        price4RRSUFRTo: Decimal | None = None,
        price4OnlineNSPINFrom: Decimal | None = None,
        price4OnlineNSPINTo: Decimal | None = None,
        price4REGUPFrom: Decimal | None = None,
        price4REGUPTo: Decimal | None = None,
        price4REGDNFrom: Decimal | None = None,
        price4REGDNTo: Decimal | None = None,
        price4OfflineNSPINFrom: Decimal | None = None,
        price4OfflineNSPINTo: Decimal | None = None,
        quantityMW4From: int | None = None,
        quantityMW4To: int | None = None,
        blockIndicator5: bool | None = None,
        price5RRSPFRFrom: Decimal | None = None,
        price5RRSPFRTo: Decimal | None = None,
        price5RRSFFRFrom: Decimal | None = None,
        price5RRSFFRTo: Decimal | None = None,
        price5RRSUFRFrom: Decimal | None = None,
        price5RRSUFRTo: Decimal | None = None,
        price5OnlineNSPINFrom: Decimal | None = None,
        price5OnlineNSPINTo: Decimal | None = None,
        price5REGUPFrom: Decimal | None = None,
        price5REGUPTo: Decimal | None = None,
        price5REGDNFrom: Decimal | None = None,
        price5REGDNTo: Decimal | None = None,
        price5OfflineNSPINFrom: Decimal | None = None,
        price5OfflineNSPINTo: Decimal | None = None,
        quantityMW5From: int | None = None,
        quantityMW5To: int | None = None,
        NCLRFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM Load Resources AS Offers"""
        return _get(
            "np3-966-er/60_dam_load_res_as_offers",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            qseName=qseName,
            dmeName=dmeName,
            loadResourceName=loadResourceName,
            multiHourBlock=multiHourBlock,
            blockIndicator1=blockIndicator1,
            price1RRSPFRFrom=price1RRSPFRFrom,
            price1RRSPFRTo=price1RRSPFRTo,
            price1RRSFFRFrom=price1RRSFFRFrom,
            price1RRSFFRTo=price1RRSFFRTo,
            price1RRSUFRFrom=price1RRSUFRFrom,
            price1RRSUFRTo=price1RRSUFRTo,
            price1OnlineNSPINFrom=price1OnlineNSPINFrom,
            price1OnlineNSPINTo=price1OnlineNSPINTo,
            price1REGUPFrom=price1REGUPFrom,
            price1REGUPTo=price1REGUPTo,
            price1REGDNFrom=price1REGDNFrom,
            price1REGDNTo=price1REGDNTo,
            price1OfflineNSPINFrom=price1OfflineNSPINFrom,
            price1OfflineNSPINTo=price1OfflineNSPINTo,
            quantityMW1From=quantityMW1From,
            quantityMW1To=quantityMW1To,
            blockIndicator2=blockIndicator2,
            price2RRSPFRFrom=price2RRSPFRFrom,
            price2RRSPFRTo=price2RRSPFRTo,
            price2RRSFFRFrom=price2RRSFFRFrom,
            price2RRSFFRTo=price2RRSFFRTo,
            price2RRSUFRFrom=price2RRSUFRFrom,
            price2RRSUFRTo=price2RRSUFRTo,
            price2OnlineNSPINFrom=price2OnlineNSPINFrom,
            price2OnlineNSPINTo=price2OnlineNSPINTo,
            price2REGUPFrom=price2REGUPFrom,
            price2REGUPTo=price2REGUPTo,
            price2REGDNFrom=price2REGDNFrom,
            price2REGDNTo=price2REGDNTo,
            price2OfflineNSPINFrom=price2OfflineNSPINFrom,
            price2OfflineNSPINTo=price2OfflineNSPINTo,
            quantityMW2From=quantityMW2From,
            quantityMW2To=quantityMW2To,
            blockIndicator3=blockIndicator3,
            price3RRSPFRFrom=price3RRSPFRFrom,
            price3RRSPFRTo=price3RRSPFRTo,
            price3RRSFFRFrom=price3RRSFFRFrom,
            price3RRSFFRTo=price3RRSFFRTo,
            price3RRSUFRFrom=price3RRSUFRFrom,
            price3RRSUFRTo=price3RRSUFRTo,
            price3OnlineNSPINFrom=price3OnlineNSPINFrom,
            price3OnlineNSPINTo=price3OnlineNSPINTo,
            price3REGUPFrom=price3REGUPFrom,
            price3REGUPTo=price3REGUPTo,
            price3REGDNFrom=price3REGDNFrom,
            price3REGDNTo=price3REGDNTo,
            price3OfflineNSPINFrom=price3OfflineNSPINFrom,
            price3OfflineNSPINTo=price3OfflineNSPINTo,
            quantityMW3From=quantityMW3From,
            quantityMW3To=quantityMW3To,
            blockIndicator4=blockIndicator4,
            price4RRSPFRFrom=price4RRSPFRFrom,
            price4RRSPFRTo=price4RRSPFRTo,
            price4RRSFFRFrom=price4RRSFFRFrom,
            price4RRSFFRTo=price4RRSFFRTo,
            price4RRSUFRFrom=price4RRSUFRFrom,
            price4RRSUFRTo=price4RRSUFRTo,
            price4OnlineNSPINFrom=price4OnlineNSPINFrom,
            price4OnlineNSPINTo=price4OnlineNSPINTo,
            price4REGUPFrom=price4REGUPFrom,
            price4REGUPTo=price4REGUPTo,
            price4REGDNFrom=price4REGDNFrom,
            price4REGDNTo=price4REGDNTo,
            price4OfflineNSPINFrom=price4OfflineNSPINFrom,
            price4OfflineNSPINTo=price4OfflineNSPINTo,
            quantityMW4From=quantityMW4From,
            quantityMW4To=quantityMW4To,
            blockIndicator5=blockIndicator5,
            price5RRSPFRFrom=price5RRSPFRFrom,
            price5RRSPFRTo=price5RRSPFRTo,
            price5RRSFFRFrom=price5RRSFFRFrom,
            price5RRSFFRTo=price5RRSFFRTo,
            price5RRSUFRFrom=price5RRSUFRFrom,
            price5RRSUFRTo=price5RRSUFRTo,
            price5OnlineNSPINFrom=price5OnlineNSPINFrom,
            price5OnlineNSPINTo=price5OnlineNSPINTo,
            price5REGUPFrom=price5REGUPFrom,
            price5REGUPTo=price5REGUPTo,
            price5REGDNFrom=price5REGDNFrom,
            price5REGDNTo=price5REGDNTo,
            price5OfflineNSPINFrom=price5OfflineNSPINFrom,
            price5OfflineNSPINTo=price5OfflineNSPINTo,
            quantityMW5From=quantityMW5From,
            quantityMW5To=quantityMW5To,
            NCLRFlag=NCLRFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60DamGenResDataParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: str
        hourEndingTo: str
        qseName: str
        dmeName: str
        resourceName: str
        resourceType: str
        qseSubmittedCurveMW1From: Decimal
        qseSubmittedCurveMW1To: Decimal
        qseSubmittedCurvePrice1From: Decimal
        qseSubmittedCurvePrice1To: Decimal
        qseSubmittedCurveMW2From: Decimal
        qseSubmittedCurveMW2To: Decimal
        qseSubmittedCurvePrice2From: Decimal
        qseSubmittedCurvePrice2To: Decimal
        qseSubmittedCurveMW3From: Decimal
        qseSubmittedCurveMW3To: Decimal
        qseSubmittedCurvePrice3From: Decimal
        qseSubmittedCurvePrice3To: Decimal
        qseSubmittedCurveMW4From: Decimal
        qseSubmittedCurveMW4To: Decimal
        qseSubmittedCurvePrice4From: Decimal
        qseSubmittedCurvePrice4To: Decimal
        qseSubmittedCurveMW5From: Decimal
        qseSubmittedCurveMW5To: Decimal
        qseSubmittedCurvePrice5From: Decimal
        qseSubmittedCurvePrice5To: Decimal
        qseSubmittedCurveMW6From: Decimal
        qseSubmittedCurveMW6To: Decimal
        qseSubmittedCurvePrice6From: Decimal
        qseSubmittedCurvePrice6To: Decimal
        qseSubmittedCurveMW7From: Decimal
        qseSubmittedCurveMW7To: Decimal
        qseSubmittedCurvePrice7From: Decimal
        qseSubmittedCurvePrice7To: Decimal
        qseSubmittedCurveMW8From: Decimal
        qseSubmittedCurveMW8To: Decimal
        qseSubmittedCurvePrice8From: Decimal
        qseSubmittedCurvePrice8To: Decimal
        qseSubmittedCurveMW9From: Decimal
        qseSubmittedCurveMW9To: Decimal
        qseSubmittedCurvePrice9From: Decimal
        qseSubmittedCurvePrice9To: Decimal
        qseSubmittedCurveMW10From: Decimal
        qseSubmittedCurveMW10To: Decimal
        qseSubmittedCurvePrice10From: Decimal
        qseSubmittedCurvePrice10To: Decimal
        startUpHotFrom: Decimal
        startUpHotTo: Decimal
        startUpInterFrom: Decimal
        startUpInterTo: Decimal
        startUpColdFrom: Decimal
        startUpColdTo: Decimal
        minGenCostFrom: Decimal
        minGenCostTo: Decimal
        HSLFrom: Decimal
        HSLTo: Decimal
        LSLFrom: Decimal
        LSLTo: Decimal
        resourceStatus: str
        awardedQuantityFrom: int
        awardedQuantityTo: int
        settlementPointName: str
        energySettlementPointPriceFrom: Decimal
        energySettlementPointPriceTo: Decimal
        REGUPAwardedFrom: Decimal
        REGUPAwardedTo: Decimal
        REGUPMCPCFrom: Decimal
        REGUPMCPCTo: Decimal
        REGDNAwardedFrom: Decimal
        REGDNAwardedTo: Decimal
        REGDNMCPCFrom: Decimal
        REGDNMCPCTo: Decimal
        RRSPFRAwardedFrom: Decimal
        RRSPFRAwardedTo: Decimal
        RRSFFRAwardedFrom: Decimal
        RRSFFRAwardedTo: Decimal
        RRSUFRAwardedFrom: Decimal
        RRSUFRAwardedTo: Decimal
        RRSMCPCFrom: Decimal
        RRSMCPCTo: Decimal
        NSPINAwardedFrom: Decimal
        NSPINAwardedTo: Decimal
        NSPINMCPCFrom: Decimal
        NSPINMCPCTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_gen_res_data(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: str | None = None,
        hourEndingTo: str | None = None,
        qseName: str | None = None,
        dmeName: str | None = None,
        resourceName: str | None = None,
        resourceType: str | None = None,
        qseSubmittedCurveMW1From: Decimal | None = None,
        qseSubmittedCurveMW1To: Decimal | None = None,
        qseSubmittedCurvePrice1From: Decimal | None = None,
        qseSubmittedCurvePrice1To: Decimal | None = None,
        qseSubmittedCurveMW2From: Decimal | None = None,
        qseSubmittedCurveMW2To: Decimal | None = None,
        qseSubmittedCurvePrice2From: Decimal | None = None,
        qseSubmittedCurvePrice2To: Decimal | None = None,
        qseSubmittedCurveMW3From: Decimal | None = None,
        qseSubmittedCurveMW3To: Decimal | None = None,
        qseSubmittedCurvePrice3From: Decimal | None = None,
        qseSubmittedCurvePrice3To: Decimal | None = None,
        qseSubmittedCurveMW4From: Decimal | None = None,
        qseSubmittedCurveMW4To: Decimal | None = None,
        qseSubmittedCurvePrice4From: Decimal | None = None,
        qseSubmittedCurvePrice4To: Decimal | None = None,
        qseSubmittedCurveMW5From: Decimal | None = None,
        qseSubmittedCurveMW5To: Decimal | None = None,
        qseSubmittedCurvePrice5From: Decimal | None = None,
        qseSubmittedCurvePrice5To: Decimal | None = None,
        qseSubmittedCurveMW6From: Decimal | None = None,
        qseSubmittedCurveMW6To: Decimal | None = None,
        qseSubmittedCurvePrice6From: Decimal | None = None,
        qseSubmittedCurvePrice6To: Decimal | None = None,
        qseSubmittedCurveMW7From: Decimal | None = None,
        qseSubmittedCurveMW7To: Decimal | None = None,
        qseSubmittedCurvePrice7From: Decimal | None = None,
        qseSubmittedCurvePrice7To: Decimal | None = None,
        qseSubmittedCurveMW8From: Decimal | None = None,
        qseSubmittedCurveMW8To: Decimal | None = None,
        qseSubmittedCurvePrice8From: Decimal | None = None,
        qseSubmittedCurvePrice8To: Decimal | None = None,
        qseSubmittedCurveMW9From: Decimal | None = None,
        qseSubmittedCurveMW9To: Decimal | None = None,
        qseSubmittedCurvePrice9From: Decimal | None = None,
        qseSubmittedCurvePrice9To: Decimal | None = None,
        qseSubmittedCurveMW10From: Decimal | None = None,
        qseSubmittedCurveMW10To: Decimal | None = None,
        qseSubmittedCurvePrice10From: Decimal | None = None,
        qseSubmittedCurvePrice10To: Decimal | None = None,
        startUpHotFrom: Decimal | None = None,
        startUpHotTo: Decimal | None = None,
        startUpInterFrom: Decimal | None = None,
        startUpInterTo: Decimal | None = None,
        startUpColdFrom: Decimal | None = None,
        startUpColdTo: Decimal | None = None,
        minGenCostFrom: Decimal | None = None,
        minGenCostTo: Decimal | None = None,
        HSLFrom: Decimal | None = None,
        HSLTo: Decimal | None = None,
        LSLFrom: Decimal | None = None,
        LSLTo: Decimal | None = None,
        resourceStatus: str | None = None,
        awardedQuantityFrom: int | None = None,
        awardedQuantityTo: int | None = None,
        settlementPointName: str | None = None,
        energySettlementPointPriceFrom: Decimal | None = None,
        energySettlementPointPriceTo: Decimal | None = None,
        REGUPAwardedFrom: Decimal | None = None,
        REGUPAwardedTo: Decimal | None = None,
        REGUPMCPCFrom: Decimal | None = None,
        REGUPMCPCTo: Decimal | None = None,
        REGDNAwardedFrom: Decimal | None = None,
        REGDNAwardedTo: Decimal | None = None,
        REGDNMCPCFrom: Decimal | None = None,
        REGDNMCPCTo: Decimal | None = None,
        RRSPFRAwardedFrom: Decimal | None = None,
        RRSPFRAwardedTo: Decimal | None = None,
        RRSFFRAwardedFrom: Decimal | None = None,
        RRSFFRAwardedTo: Decimal | None = None,
        RRSUFRAwardedFrom: Decimal | None = None,
        RRSUFRAwardedTo: Decimal | None = None,
        RRSMCPCFrom: Decimal | None = None,
        RRSMCPCTo: Decimal | None = None,
        NSPINAwardedFrom: Decimal | None = None,
        NSPINAwardedTo: Decimal | None = None,
        NSPINMCPCFrom: Decimal | None = None,
        NSPINMCPCTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM Generation Resource Data"""
        return _get(
            "np3-966-er/60_dam_gen_res_data",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            qseName=qseName,
            dmeName=dmeName,
            resourceName=resourceName,
            resourceType=resourceType,
            qseSubmittedCurveMW1From=qseSubmittedCurveMW1From,
            qseSubmittedCurveMW1To=qseSubmittedCurveMW1To,
            qseSubmittedCurvePrice1From=qseSubmittedCurvePrice1From,
            qseSubmittedCurvePrice1To=qseSubmittedCurvePrice1To,
            qseSubmittedCurveMW2From=qseSubmittedCurveMW2From,
            qseSubmittedCurveMW2To=qseSubmittedCurveMW2To,
            qseSubmittedCurvePrice2From=qseSubmittedCurvePrice2From,
            qseSubmittedCurvePrice2To=qseSubmittedCurvePrice2To,
            qseSubmittedCurveMW3From=qseSubmittedCurveMW3From,
            qseSubmittedCurveMW3To=qseSubmittedCurveMW3To,
            qseSubmittedCurvePrice3From=qseSubmittedCurvePrice3From,
            qseSubmittedCurvePrice3To=qseSubmittedCurvePrice3To,
            qseSubmittedCurveMW4From=qseSubmittedCurveMW4From,
            qseSubmittedCurveMW4To=qseSubmittedCurveMW4To,
            qseSubmittedCurvePrice4From=qseSubmittedCurvePrice4From,
            qseSubmittedCurvePrice4To=qseSubmittedCurvePrice4To,
            qseSubmittedCurveMW5From=qseSubmittedCurveMW5From,
            qseSubmittedCurveMW5To=qseSubmittedCurveMW5To,
            qseSubmittedCurvePrice5From=qseSubmittedCurvePrice5From,
            qseSubmittedCurvePrice5To=qseSubmittedCurvePrice5To,
            qseSubmittedCurveMW6From=qseSubmittedCurveMW6From,
            qseSubmittedCurveMW6To=qseSubmittedCurveMW6To,
            qseSubmittedCurvePrice6From=qseSubmittedCurvePrice6From,
            qseSubmittedCurvePrice6To=qseSubmittedCurvePrice6To,
            qseSubmittedCurveMW7From=qseSubmittedCurveMW7From,
            qseSubmittedCurveMW7To=qseSubmittedCurveMW7To,
            qseSubmittedCurvePrice7From=qseSubmittedCurvePrice7From,
            qseSubmittedCurvePrice7To=qseSubmittedCurvePrice7To,
            qseSubmittedCurveMW8From=qseSubmittedCurveMW8From,
            qseSubmittedCurveMW8To=qseSubmittedCurveMW8To,
            qseSubmittedCurvePrice8From=qseSubmittedCurvePrice8From,
            qseSubmittedCurvePrice8To=qseSubmittedCurvePrice8To,
            qseSubmittedCurveMW9From=qseSubmittedCurveMW9From,
            qseSubmittedCurveMW9To=qseSubmittedCurveMW9To,
            qseSubmittedCurvePrice9From=qseSubmittedCurvePrice9From,
            qseSubmittedCurvePrice9To=qseSubmittedCurvePrice9To,
            qseSubmittedCurveMW10From=qseSubmittedCurveMW10From,
            qseSubmittedCurveMW10To=qseSubmittedCurveMW10To,
            qseSubmittedCurvePrice10From=qseSubmittedCurvePrice10From,
            qseSubmittedCurvePrice10To=qseSubmittedCurvePrice10To,
            startUpHotFrom=startUpHotFrom,
            startUpHotTo=startUpHotTo,
            startUpInterFrom=startUpInterFrom,
            startUpInterTo=startUpInterTo,
            startUpColdFrom=startUpColdFrom,
            startUpColdTo=startUpColdTo,
            minGenCostFrom=minGenCostFrom,
            minGenCostTo=minGenCostTo,
            HSLFrom=HSLFrom,
            HSLTo=HSLTo,
            LSLFrom=LSLFrom,
            LSLTo=LSLTo,
            resourceStatus=resourceStatus,
            awardedQuantityFrom=awardedQuantityFrom,
            awardedQuantityTo=awardedQuantityTo,
            settlementPointName=settlementPointName,
            energySettlementPointPriceFrom=energySettlementPointPriceFrom,
            energySettlementPointPriceTo=energySettlementPointPriceTo,
            REGUPAwardedFrom=REGUPAwardedFrom,
            REGUPAwardedTo=REGUPAwardedTo,
            REGUPMCPCFrom=REGUPMCPCFrom,
            REGUPMCPCTo=REGUPMCPCTo,
            REGDNAwardedFrom=REGDNAwardedFrom,
            REGDNAwardedTo=REGDNAwardedTo,
            REGDNMCPCFrom=REGDNMCPCFrom,
            REGDNMCPCTo=REGDNMCPCTo,
            RRSPFRAwardedFrom=RRSPFRAwardedFrom,
            RRSPFRAwardedTo=RRSPFRAwardedTo,
            RRSFFRAwardedFrom=RRSFFRAwardedFrom,
            RRSFFRAwardedTo=RRSFFRAwardedTo,
            RRSUFRAwardedFrom=RRSUFRAwardedFrom,
            RRSUFRAwardedTo=RRSUFRAwardedTo,
            RRSMCPCFrom=RRSMCPCFrom,
            RRSMCPCTo=RRSMCPCTo,
            NSPINAwardedFrom=NSPINAwardedFrom,
            NSPINAwardedTo=NSPINAwardedTo,
            NSPINMCPCFrom=NSPINMCPCFrom,
            NSPINMCPCTo=NSPINMCPCTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60DamGenResAsOffersParams(TypedDict, total=False):
        price2RRSFFRFrom: Decimal
        price2RRSFFRTo: Decimal
        price2RRSUFRFrom: Decimal
        price2RRSUFRTo: Decimal
        price2OnlineNSPINFrom: Decimal
        price2OnlineNSPINTo: Decimal
        price2REGUPFrom: Decimal
        price2REGUPTo: Decimal
        price2REGDNFrom: Decimal
        price2REGDNTo: Decimal
        price2OfflineNSPINFrom: Decimal
        price2OfflineNSPINTo: Decimal
        quantityMW2From: int
        quantityMW2To: int
        blockIndicator3: bool
        price3RRSPFRFrom: Decimal
        price3RRSPFRTo: Decimal
        price3RRSFFRFrom: Decimal
        price3RRSFFRTo: Decimal
        price3RRSUFRFrom: Decimal
        price3RRSUFRTo: Decimal
        price3OnlineNSPINFrom: Decimal
        price3OnlineNSPINTo: Decimal
        price3REGUPFrom: Decimal
        price3REGUPTo: Decimal
        price3REGDNFrom: Decimal
        price3REGDNTo: Decimal
        price3OfflineNSPINFrom: Decimal
        price3OfflineNSPINTo: Decimal
        quantityMW3From: int
        quantityMW3To: int
        blockIndicator4: bool
        price4RRSPFRFrom: Decimal
        price4RRSPFRTo: Decimal
        price4RRSFFRFrom: Decimal
        price4RRSFFRTo: Decimal
        price4RRSUFRFrom: Decimal
        price4RRSUFRTo: Decimal
        price4OnlineNSPINFrom: Decimal
        price4OnlineNSPINTo: Decimal
        price4REGUPFrom: Decimal
        price4REGUPTo: Decimal
        price4REGDNFrom: Decimal
        price4REGDNTo: Decimal
        price4OfflineNSPINFrom: Decimal
        price4OfflineNSPINTo: Decimal
        quantityMW4From: int
        quantityMW4To: int
        blockIndicator5: bool
        price5RRSPFRFrom: Decimal
        price5RRSPFRTo: Decimal
        price5RRSFFRFrom: Decimal
        price5RRSFFRTo: Decimal
        price5RRSUFRFrom: Decimal
        price5RRSUFRTo: Decimal
        price5OnlineNSPINFrom: Decimal
        price5OnlineNSPINTo: Decimal
        price5REGUPFrom: Decimal
        price5REGUPTo: Decimal
        price5REGDNFrom: Decimal
        price5REGDNTo: Decimal
        price5OfflineNSPINFrom: Decimal
        price5OfflineNSPINTo: Decimal
        quantityMW5From: int
        quantityMW5To: int
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: str
        hourEndingTo: str
        qseName: str
        dmeName: str
        resourceName: str
        multiHourBlock: bool
        blockIndicator1: bool
        price1RRSPFRFrom: Decimal
        price1RRSPFRTo: Decimal
        price1RRSFFRFrom: Decimal
        price1RRSFFRTo: Decimal
        price1RRSUFRFrom: Decimal
        price1RRSUFRTo: Decimal
        price1OnlineNSPINFrom: Decimal
        price1OnlineNSPINTo: Decimal
        price1REGUPFrom: Decimal
        price1REGUPTo: Decimal
        price1REGDNFrom: Decimal
        price1REGDNTo: Decimal
        price1OfflineNSPINFrom: Decimal
        price1OfflineNSPINTo: Decimal
        quantityMW1From: int
        quantityMW1To: int
        blockIndicator2: bool
        price2RRSPFRFrom: Decimal
        price2RRSPFRTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_gen_res_as_offers(
        *,
        price2RRSFFRFrom: Decimal | None = None,
        price2RRSFFRTo: Decimal | None = None,
        price2RRSUFRFrom: Decimal | None = None,
        price2RRSUFRTo: Decimal | None = None,
        price2OnlineNSPINFrom: Decimal | None = None,
        price2OnlineNSPINTo: Decimal | None = None,
        price2REGUPFrom: Decimal | None = None,
        price2REGUPTo: Decimal | None = None,
        price2REGDNFrom: Decimal | None = None,
        price2REGDNTo: Decimal | None = None,
        price2OfflineNSPINFrom: Decimal | None = None,
        price2OfflineNSPINTo: Decimal | None = None,
        quantityMW2From: int | None = None,
        quantityMW2To: int | None = None,
        blockIndicator3: bool | None = None,
        price3RRSPFRFrom: Decimal | None = None,
        price3RRSPFRTo: Decimal | None = None,
        price3RRSFFRFrom: Decimal | None = None,
        price3RRSFFRTo: Decimal | None = None,
        price3RRSUFRFrom: Decimal | None = None,
        price3RRSUFRTo: Decimal | None = None,
        price3OnlineNSPINFrom: Decimal | None = None,
        price3OnlineNSPINTo: Decimal | None = None,
        price3REGUPFrom: Decimal | None = None,
        price3REGUPTo: Decimal | None = None,
        price3REGDNFrom: Decimal | None = None,
        price3REGDNTo: Decimal | None = None,
        price3OfflineNSPINFrom: Decimal | None = None,
        price3OfflineNSPINTo: Decimal | None = None,
        quantityMW3From: int | None = None,
        quantityMW3To: int | None = None,
        blockIndicator4: bool | None = None,
        price4RRSPFRFrom: Decimal | None = None,
        price4RRSPFRTo: Decimal | None = None,
        price4RRSFFRFrom: Decimal | None = None,
        price4RRSFFRTo: Decimal | None = None,
        price4RRSUFRFrom: Decimal | None = None,
        price4RRSUFRTo: Decimal | None = None,
        price4OnlineNSPINFrom: Decimal | None = None,
        price4OnlineNSPINTo: Decimal | None = None,
        price4REGUPFrom: Decimal | None = None,
        price4REGUPTo: Decimal | None = None,
        price4REGDNFrom: Decimal | None = None,
        price4REGDNTo: Decimal | None = None,
        price4OfflineNSPINFrom: Decimal | None = None,
        price4OfflineNSPINTo: Decimal | None = None,
        quantityMW4From: int | None = None,
        quantityMW4To: int | None = None,
        blockIndicator5: bool | None = None,
        price5RRSPFRFrom: Decimal | None = None,
        price5RRSPFRTo: Decimal | None = None,
        price5RRSFFRFrom: Decimal | None = None,
        price5RRSFFRTo: Decimal | None = None,
        price5RRSUFRFrom: Decimal | None = None,
        price5RRSUFRTo: Decimal | None = None,
        price5OnlineNSPINFrom: Decimal | None = None,
        price5OnlineNSPINTo: Decimal | None = None,
        price5REGUPFrom: Decimal | None = None,
        price5REGUPTo: Decimal | None = None,
        price5REGDNFrom: Decimal | None = None,
        price5REGDNTo: Decimal | None = None,
        price5OfflineNSPINFrom: Decimal | None = None,
        price5OfflineNSPINTo: Decimal | None = None,
        quantityMW5From: int | None = None,
        quantityMW5To: int | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: str | None = None,
        hourEndingTo: str | None = None,
        qseName: str | None = None,
        dmeName: str | None = None,
        resourceName: str | None = None,
        multiHourBlock: bool | None = None,
        blockIndicator1: bool | None = None,
        price1RRSPFRFrom: Decimal | None = None,
        price1RRSPFRTo: Decimal | None = None,
        price1RRSFFRFrom: Decimal | None = None,
        price1RRSFFRTo: Decimal | None = None,
        price1RRSUFRFrom: Decimal | None = None,
        price1RRSUFRTo: Decimal | None = None,
        price1OnlineNSPINFrom: Decimal | None = None,
        price1OnlineNSPINTo: Decimal | None = None,
        price1REGUPFrom: Decimal | None = None,
        price1REGUPTo: Decimal | None = None,
        price1REGDNFrom: Decimal | None = None,
        price1REGDNTo: Decimal | None = None,
        price1OfflineNSPINFrom: Decimal | None = None,
        price1OfflineNSPINTo: Decimal | None = None,
        quantityMW1From: int | None = None,
        quantityMW1To: int | None = None,
        blockIndicator2: bool | None = None,
        price2RRSPFRFrom: Decimal | None = None,
        price2RRSPFRTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM Generation Resources AS Offers"""
        return _get(
            "np3-966-er/60_dam_gen_res_as_offers",
            price2RRSFFRFrom=price2RRSFFRFrom,
            price2RRSFFRTo=price2RRSFFRTo,
            price2RRSUFRFrom=price2RRSUFRFrom,
            price2RRSUFRTo=price2RRSUFRTo,
            price2OnlineNSPINFrom=price2OnlineNSPINFrom,
            price2OnlineNSPINTo=price2OnlineNSPINTo,
            price2REGUPFrom=price2REGUPFrom,
            price2REGUPTo=price2REGUPTo,
            price2REGDNFrom=price2REGDNFrom,
            price2REGDNTo=price2REGDNTo,
            price2OfflineNSPINFrom=price2OfflineNSPINFrom,
            price2OfflineNSPINTo=price2OfflineNSPINTo,
            quantityMW2From=quantityMW2From,
            quantityMW2To=quantityMW2To,
            blockIndicator3=blockIndicator3,
            price3RRSPFRFrom=price3RRSPFRFrom,
            price3RRSPFRTo=price3RRSPFRTo,
            price3RRSFFRFrom=price3RRSFFRFrom,
            price3RRSFFRTo=price3RRSFFRTo,
            price3RRSUFRFrom=price3RRSUFRFrom,
            price3RRSUFRTo=price3RRSUFRTo,
            price3OnlineNSPINFrom=price3OnlineNSPINFrom,
            price3OnlineNSPINTo=price3OnlineNSPINTo,
            price3REGUPFrom=price3REGUPFrom,
            price3REGUPTo=price3REGUPTo,
            price3REGDNFrom=price3REGDNFrom,
            price3REGDNTo=price3REGDNTo,
            price3OfflineNSPINFrom=price3OfflineNSPINFrom,
            price3OfflineNSPINTo=price3OfflineNSPINTo,
            quantityMW3From=quantityMW3From,
            quantityMW3To=quantityMW3To,
            blockIndicator4=blockIndicator4,
            price4RRSPFRFrom=price4RRSPFRFrom,
            price4RRSPFRTo=price4RRSPFRTo,
            price4RRSFFRFrom=price4RRSFFRFrom,
            price4RRSFFRTo=price4RRSFFRTo,
            price4RRSUFRFrom=price4RRSUFRFrom,
            price4RRSUFRTo=price4RRSUFRTo,
            price4OnlineNSPINFrom=price4OnlineNSPINFrom,
            price4OnlineNSPINTo=price4OnlineNSPINTo,
            price4REGUPFrom=price4REGUPFrom,
            price4REGUPTo=price4REGUPTo,
            price4REGDNFrom=price4REGDNFrom,
            price4REGDNTo=price4REGDNTo,
            price4OfflineNSPINFrom=price4OfflineNSPINFrom,
            price4OfflineNSPINTo=price4OfflineNSPINTo,
            quantityMW4From=quantityMW4From,
            quantityMW4To=quantityMW4To,
            blockIndicator5=blockIndicator5,
            price5RRSPFRFrom=price5RRSPFRFrom,
            price5RRSPFRTo=price5RRSPFRTo,
            price5RRSFFRFrom=price5RRSFFRFrom,
            price5RRSFFRTo=price5RRSFFRTo,
            price5RRSUFRFrom=price5RRSUFRFrom,
            price5RRSUFRTo=price5RRSUFRTo,
            price5OnlineNSPINFrom=price5OnlineNSPINFrom,
            price5OnlineNSPINTo=price5OnlineNSPINTo,
            price5REGUPFrom=price5REGUPFrom,
            price5REGUPTo=price5REGUPTo,
            price5REGDNFrom=price5REGDNFrom,
            price5REGDNTo=price5REGDNTo,
            price5OfflineNSPINFrom=price5OfflineNSPINFrom,
            price5OfflineNSPINTo=price5OfflineNSPINTo,
            quantityMW5From=quantityMW5From,
            quantityMW5To=quantityMW5To,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            qseName=qseName,
            dmeName=dmeName,
            resourceName=resourceName,
            multiHourBlock=multiHourBlock,
            blockIndicator1=blockIndicator1,
            price1RRSPFRFrom=price1RRSPFRFrom,
            price1RRSPFRTo=price1RRSPFRTo,
            price1RRSFFRFrom=price1RRSFFRFrom,
            price1RRSFFRTo=price1RRSFFRTo,
            price1RRSUFRFrom=price1RRSUFRFrom,
            price1RRSUFRTo=price1RRSUFRTo,
            price1OnlineNSPINFrom=price1OnlineNSPINFrom,
            price1OnlineNSPINTo=price1OnlineNSPINTo,
            price1REGUPFrom=price1REGUPFrom,
            price1REGUPTo=price1REGUPTo,
            price1REGDNFrom=price1REGDNFrom,
            price1REGDNTo=price1REGDNTo,
            price1OfflineNSPINFrom=price1OfflineNSPINFrom,
            price1OfflineNSPINTo=price1OfflineNSPINTo,
            quantityMW1From=quantityMW1From,
            quantityMW1To=quantityMW1To,
            blockIndicator2=blockIndicator2,
            price2RRSPFRFrom=price2RRSPFRFrom,
            price2RRSPFRTo=price2RRSPFRTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60DamEnergyOnlyOffersParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: str
        hourEndingTo: str
        settlementPointName: str
        qseName: str
        energyOnlyOfferMW1From: Decimal
        energyOnlyOfferMW1To: Decimal
        energyOnlyOfferPrice1From: Decimal
        energyOnlyOfferPrice1To: Decimal
        energyOnlyOfferMW2From: Decimal
        energyOnlyOfferMW2To: Decimal
        energyOnlyOfferPrice2From: Decimal
        energyOnlyOfferPrice2To: Decimal
        energyOnlyOfferMW3From: Decimal
        energyOnlyOfferMW3To: Decimal
        energyOnlyOfferPrice3From: Decimal
        energyOnlyOfferPrice3To: Decimal
        energyOnlyOfferMW4From: Decimal
        energyOnlyOfferMW4To: Decimal
        energyOnlyOfferPrice4From: Decimal
        energyOnlyOfferPrice4To: Decimal
        energyOnlyOfferMW5From: Decimal
        energyOnlyOfferMW5To: Decimal
        energyOnlyOfferPrice5From: Decimal
        energyOnlyOfferPrice5To: Decimal
        energyOnlyOfferMW6From: Decimal
        energyOnlyOfferMW6To: Decimal
        energyOnlyOfferPrice6From: Decimal
        energyOnlyOfferPrice6To: Decimal
        energyOnlyOfferMW7From: Decimal
        energyOnlyOfferMW7To: Decimal
        energyOnlyOfferPrice7From: Decimal
        energyOnlyOfferPrice7To: Decimal
        energyOnlyOfferMW8From: Decimal
        energyOnlyOfferMW8To: Decimal
        energyOnlyOfferPrice8From: Decimal
        energyOnlyOfferPrice8To: Decimal
        energyOnlyOfferMW9From: Decimal
        energyOnlyOfferMW9To: Decimal
        energyOnlyOfferPrice9From: Decimal
        energyOnlyOfferPrice9To: Decimal
        energyOnlyOfferMW10From: Decimal
        energyOnlyOfferMW10To: Decimal
        energyOnlyOfferPrice10From: Decimal
        energyOnlyOfferPrice10To: Decimal
        offerIdFrom: Decimal
        offerIdTo: Decimal
        multiHourBlock: bool
        blockCurve: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_energy_only_offers(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: str | None = None,
        hourEndingTo: str | None = None,
        settlementPointName: str | None = None,
        qseName: str | None = None,
        energyOnlyOfferMW1From: Decimal | None = None,
        energyOnlyOfferMW1To: Decimal | None = None,
        energyOnlyOfferPrice1From: Decimal | None = None,
        energyOnlyOfferPrice1To: Decimal | None = None,
        energyOnlyOfferMW2From: Decimal | None = None,
        energyOnlyOfferMW2To: Decimal | None = None,
        energyOnlyOfferPrice2From: Decimal | None = None,
        energyOnlyOfferPrice2To: Decimal | None = None,
        energyOnlyOfferMW3From: Decimal | None = None,
        energyOnlyOfferMW3To: Decimal | None = None,
        energyOnlyOfferPrice3From: Decimal | None = None,
        energyOnlyOfferPrice3To: Decimal | None = None,
        energyOnlyOfferMW4From: Decimal | None = None,
        energyOnlyOfferMW4To: Decimal | None = None,
        energyOnlyOfferPrice4From: Decimal | None = None,
        energyOnlyOfferPrice4To: Decimal | None = None,
        energyOnlyOfferMW5From: Decimal | None = None,
        energyOnlyOfferMW5To: Decimal | None = None,
        energyOnlyOfferPrice5From: Decimal | None = None,
        energyOnlyOfferPrice5To: Decimal | None = None,
        energyOnlyOfferMW6From: Decimal | None = None,
        energyOnlyOfferMW6To: Decimal | None = None,
        energyOnlyOfferPrice6From: Decimal | None = None,
        energyOnlyOfferPrice6To: Decimal | None = None,
        energyOnlyOfferMW7From: Decimal | None = None,
        energyOnlyOfferMW7To: Decimal | None = None,
        energyOnlyOfferPrice7From: Decimal | None = None,
        energyOnlyOfferPrice7To: Decimal | None = None,
        energyOnlyOfferMW8From: Decimal | None = None,
        energyOnlyOfferMW8To: Decimal | None = None,
        energyOnlyOfferPrice8From: Decimal | None = None,
        energyOnlyOfferPrice8To: Decimal | None = None,
        energyOnlyOfferMW9From: Decimal | None = None,
        energyOnlyOfferMW9To: Decimal | None = None,
        energyOnlyOfferPrice9From: Decimal | None = None,
        energyOnlyOfferPrice9To: Decimal | None = None,
        energyOnlyOfferMW10From: Decimal | None = None,
        energyOnlyOfferMW10To: Decimal | None = None,
        energyOnlyOfferPrice10From: Decimal | None = None,
        energyOnlyOfferPrice10To: Decimal | None = None,
        offerIdFrom: Decimal | None = None,
        offerIdTo: Decimal | None = None,
        multiHourBlock: bool | None = None,
        blockCurve: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM Energy Only Offers"""
        return _get(
            "np3-966-er/60_dam_energy_only_offers",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            settlementPointName=settlementPointName,
            qseName=qseName,
            energyOnlyOfferMW1From=energyOnlyOfferMW1From,
            energyOnlyOfferMW1To=energyOnlyOfferMW1To,
            energyOnlyOfferPrice1From=energyOnlyOfferPrice1From,
            energyOnlyOfferPrice1To=energyOnlyOfferPrice1To,
            energyOnlyOfferMW2From=energyOnlyOfferMW2From,
            energyOnlyOfferMW2To=energyOnlyOfferMW2To,
            energyOnlyOfferPrice2From=energyOnlyOfferPrice2From,
            energyOnlyOfferPrice2To=energyOnlyOfferPrice2To,
            energyOnlyOfferMW3From=energyOnlyOfferMW3From,
            energyOnlyOfferMW3To=energyOnlyOfferMW3To,
            energyOnlyOfferPrice3From=energyOnlyOfferPrice3From,
            energyOnlyOfferPrice3To=energyOnlyOfferPrice3To,
            energyOnlyOfferMW4From=energyOnlyOfferMW4From,
            energyOnlyOfferMW4To=energyOnlyOfferMW4To,
            energyOnlyOfferPrice4From=energyOnlyOfferPrice4From,
            energyOnlyOfferPrice4To=energyOnlyOfferPrice4To,
            energyOnlyOfferMW5From=energyOnlyOfferMW5From,
            energyOnlyOfferMW5To=energyOnlyOfferMW5To,
            energyOnlyOfferPrice5From=energyOnlyOfferPrice5From,
            energyOnlyOfferPrice5To=energyOnlyOfferPrice5To,
            energyOnlyOfferMW6From=energyOnlyOfferMW6From,
            energyOnlyOfferMW6To=energyOnlyOfferMW6To,
            energyOnlyOfferPrice6From=energyOnlyOfferPrice6From,
            energyOnlyOfferPrice6To=energyOnlyOfferPrice6To,
            energyOnlyOfferMW7From=energyOnlyOfferMW7From,
            energyOnlyOfferMW7To=energyOnlyOfferMW7To,
            energyOnlyOfferPrice7From=energyOnlyOfferPrice7From,
            energyOnlyOfferPrice7To=energyOnlyOfferPrice7To,
            energyOnlyOfferMW8From=energyOnlyOfferMW8From,
            energyOnlyOfferMW8To=energyOnlyOfferMW8To,
            energyOnlyOfferPrice8From=energyOnlyOfferPrice8From,
            energyOnlyOfferPrice8To=energyOnlyOfferPrice8To,
            energyOnlyOfferMW9From=energyOnlyOfferMW9From,
            energyOnlyOfferMW9To=energyOnlyOfferMW9To,
            energyOnlyOfferPrice9From=energyOnlyOfferPrice9From,
            energyOnlyOfferPrice9To=energyOnlyOfferPrice9To,
            energyOnlyOfferMW10From=energyOnlyOfferMW10From,
            energyOnlyOfferMW10To=energyOnlyOfferMW10To,
            energyOnlyOfferPrice10From=energyOnlyOfferPrice10From,
            energyOnlyOfferPrice10To=energyOnlyOfferPrice10To,
            offerIdFrom=offerIdFrom,
            offerIdTo=offerIdTo,
            multiHourBlock=multiHourBlock,
            blockCurve=blockCurve,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60DamEnergyOnlyOfferAwardsParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: str
        hourEndingTo: str
        settlementPointName: str
        qseName: str
        energyOnlyOfferAwardInMWFrom: Decimal
        energyOnlyOfferAwardInMWTo: Decimal
        settlementPointPriceFrom: Decimal
        settlementPointPriceTo: Decimal
        offerId: str
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_energy_only_offer_awards(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: str | None = None,
        hourEndingTo: str | None = None,
        settlementPointName: str | None = None,
        qseName: str | None = None,
        energyOnlyOfferAwardInMWFrom: Decimal | None = None,
        energyOnlyOfferAwardInMWTo: Decimal | None = None,
        settlementPointPriceFrom: Decimal | None = None,
        settlementPointPriceTo: Decimal | None = None,
        offerId: str | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM Energy Offer Only Awards"""
        return _get(
            "np3-966-er/60_dam_energy_only_offer_awards",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            settlementPointName=settlementPointName,
            qseName=qseName,
            energyOnlyOfferAwardInMWFrom=energyOnlyOfferAwardInMWFrom,
            energyOnlyOfferAwardInMWTo=energyOnlyOfferAwardInMWTo,
            settlementPointPriceFrom=settlementPointPriceFrom,
            settlementPointPriceTo=settlementPointPriceTo,
            offerId=offerId,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60DamEnergyBidsParams(TypedDict, total=False):
        energyOnlyBidMw1From: Decimal
        energyOnlyBidMw1To: Decimal
        energyOnlyBidPrice1From: Decimal
        energyOnlyBidPrice1To: Decimal
        energyOnlyBidMw2From: Decimal
        energyOnlyBidMw2To: Decimal
        energyOnlyBidPrice2From: Decimal
        energyOnlyBidPrice2To: Decimal
        energyOnlyBidMw3From: Decimal
        energyOnlyBidMw3To: Decimal
        energyOnlyBidPrice3From: Decimal
        energyOnlyBidPrice3To: Decimal
        energyOnlyBidMw4From: Decimal
        energyOnlyBidMw4To: Decimal
        energyOnlyBidPrice4From: Decimal
        energyOnlyBidPrice4To: Decimal
        energyOnlyBidMw5From: Decimal
        energyOnlyBidMw5To: Decimal
        energyOnlyBidPrice5From: Decimal
        energyOnlyBidPrice5To: Decimal
        energyOnlyBidMw6From: Decimal
        energyOnlyBidMw6To: Decimal
        energyOnlyBidPrice6From: Decimal
        energyOnlyBidPrice6To: Decimal
        energyOnlyBidMw7From: Decimal
        energyOnlyBidMw7To: Decimal
        energyOnlyBidPrice7From: Decimal
        energyOnlyBidPrice7To: Decimal
        energyOnlyBidMw8From: Decimal
        energyOnlyBidMw8To: Decimal
        energyOnlyBidPrice8From: Decimal
        energyOnlyBidPrice8To: Decimal
        energyOnlyBidMw9From: Decimal
        energyOnlyBidMw9To: Decimal
        energyOnlyBidPrice9From: Decimal
        energyOnlyBidPrice9To: Decimal
        energyOnlyBidMw10From: Decimal
        energyOnlyBidMw10To: Decimal
        energyOnlyBidPrice10From: Decimal
        energyOnlyBidPrice10To: Decimal
        bidIdFrom: Decimal
        bidIdTo: Decimal
        multiHourBlock: bool
        blockCurve: bool
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: str
        hourEndingTo: str
        settlementPointName: str
        qseName: str
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_energy_bids(
        *,
        energyOnlyBidMw1From: Decimal | None = None,
        energyOnlyBidMw1To: Decimal | None = None,
        energyOnlyBidPrice1From: Decimal | None = None,
        energyOnlyBidPrice1To: Decimal | None = None,
        energyOnlyBidMw2From: Decimal | None = None,
        energyOnlyBidMw2To: Decimal | None = None,
        energyOnlyBidPrice2From: Decimal | None = None,
        energyOnlyBidPrice2To: Decimal | None = None,
        energyOnlyBidMw3From: Decimal | None = None,
        energyOnlyBidMw3To: Decimal | None = None,
        energyOnlyBidPrice3From: Decimal | None = None,
        energyOnlyBidPrice3To: Decimal | None = None,
        energyOnlyBidMw4From: Decimal | None = None,
        energyOnlyBidMw4To: Decimal | None = None,
        energyOnlyBidPrice4From: Decimal | None = None,
        energyOnlyBidPrice4To: Decimal | None = None,
        energyOnlyBidMw5From: Decimal | None = None,
        energyOnlyBidMw5To: Decimal | None = None,
        energyOnlyBidPrice5From: Decimal | None = None,
        energyOnlyBidPrice5To: Decimal | None = None,
        energyOnlyBidMw6From: Decimal | None = None,
        energyOnlyBidMw6To: Decimal | None = None,
        energyOnlyBidPrice6From: Decimal | None = None,
        energyOnlyBidPrice6To: Decimal | None = None,
        energyOnlyBidMw7From: Decimal | None = None,
        energyOnlyBidMw7To: Decimal | None = None,
        energyOnlyBidPrice7From: Decimal | None = None,
        energyOnlyBidPrice7To: Decimal | None = None,
        energyOnlyBidMw8From: Decimal | None = None,
        energyOnlyBidMw8To: Decimal | None = None,
        energyOnlyBidPrice8From: Decimal | None = None,
        energyOnlyBidPrice8To: Decimal | None = None,
        energyOnlyBidMw9From: Decimal | None = None,
        energyOnlyBidMw9To: Decimal | None = None,
        energyOnlyBidPrice9From: Decimal | None = None,
        energyOnlyBidPrice9To: Decimal | None = None,
        energyOnlyBidMw10From: Decimal | None = None,
        energyOnlyBidMw10To: Decimal | None = None,
        energyOnlyBidPrice10From: Decimal | None = None,
        energyOnlyBidPrice10To: Decimal | None = None,
        bidIdFrom: Decimal | None = None,
        bidIdTo: Decimal | None = None,
        multiHourBlock: bool | None = None,
        blockCurve: bool | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: str | None = None,
        hourEndingTo: str | None = None,
        settlementPointName: str | None = None,
        qseName: str | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM Energy Bids"""
        return _get(
            "np3-966-er/60_dam_energy_bids",
            energyOnlyBidMw1From=energyOnlyBidMw1From,
            energyOnlyBidMw1To=energyOnlyBidMw1To,
            energyOnlyBidPrice1From=energyOnlyBidPrice1From,
            energyOnlyBidPrice1To=energyOnlyBidPrice1To,
            energyOnlyBidMw2From=energyOnlyBidMw2From,
            energyOnlyBidMw2To=energyOnlyBidMw2To,
            energyOnlyBidPrice2From=energyOnlyBidPrice2From,
            energyOnlyBidPrice2To=energyOnlyBidPrice2To,
            energyOnlyBidMw3From=energyOnlyBidMw3From,
            energyOnlyBidMw3To=energyOnlyBidMw3To,
            energyOnlyBidPrice3From=energyOnlyBidPrice3From,
            energyOnlyBidPrice3To=energyOnlyBidPrice3To,
            energyOnlyBidMw4From=energyOnlyBidMw4From,
            energyOnlyBidMw4To=energyOnlyBidMw4To,
            energyOnlyBidPrice4From=energyOnlyBidPrice4From,
            energyOnlyBidPrice4To=energyOnlyBidPrice4To,
            energyOnlyBidMw5From=energyOnlyBidMw5From,
            energyOnlyBidMw5To=energyOnlyBidMw5To,
            energyOnlyBidPrice5From=energyOnlyBidPrice5From,
            energyOnlyBidPrice5To=energyOnlyBidPrice5To,
            energyOnlyBidMw6From=energyOnlyBidMw6From,
            energyOnlyBidMw6To=energyOnlyBidMw6To,
            energyOnlyBidPrice6From=energyOnlyBidPrice6From,
            energyOnlyBidPrice6To=energyOnlyBidPrice6To,
            energyOnlyBidMw7From=energyOnlyBidMw7From,
            energyOnlyBidMw7To=energyOnlyBidMw7To,
            energyOnlyBidPrice7From=energyOnlyBidPrice7From,
            energyOnlyBidPrice7To=energyOnlyBidPrice7To,
            energyOnlyBidMw8From=energyOnlyBidMw8From,
            energyOnlyBidMw8To=energyOnlyBidMw8To,
            energyOnlyBidPrice8From=energyOnlyBidPrice8From,
            energyOnlyBidPrice8To=energyOnlyBidPrice8To,
            energyOnlyBidMw9From=energyOnlyBidMw9From,
            energyOnlyBidMw9To=energyOnlyBidMw9To,
            energyOnlyBidPrice9From=energyOnlyBidPrice9From,
            energyOnlyBidPrice9To=energyOnlyBidPrice9To,
            energyOnlyBidMw10From=energyOnlyBidMw10From,
            energyOnlyBidMw10To=energyOnlyBidMw10To,
            energyOnlyBidPrice10From=energyOnlyBidPrice10From,
            energyOnlyBidPrice10To=energyOnlyBidPrice10To,
            bidIdFrom=bidIdFrom,
            bidIdTo=bidIdTo,
            multiHourBlock=multiHourBlock,
            blockCurve=blockCurve,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            settlementPointName=settlementPointName,
            qseName=qseName,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60DamEnergyBidAwardsParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: str
        hourEndingTo: str
        settlementPointName: str
        qseName: str
        energyOnlyBidAwardInMWFrom: Decimal
        energyOnlyBidAwardInMWTo: Decimal
        settlementPointPriceFrom: Decimal
        settlementPointPriceTo: Decimal
        bidId: str
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_dam_energy_bid_awards(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: str | None = None,
        hourEndingTo: str | None = None,
        settlementPointName: str | None = None,
        qseName: str | None = None,
        energyOnlyBidAwardInMWFrom: Decimal | None = None,
        energyOnlyBidAwardInMWTo: Decimal | None = None,
        settlementPointPriceFrom: Decimal | None = None,
        settlementPointPriceTo: Decimal | None = None,
        bidId: str | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day DAM Energy Bid Awards"""
        return _get(
            "np3-966-er/60_dam_energy_bid_awards",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            settlementPointName=settlementPointName,
            qseName=qseName,
            energyOnlyBidAwardInMWFrom=energyOnlyBidAwardInMWFrom,
            energyOnlyBidAwardInMWTo=energyOnlyBidAwardInMWTo,
            settlementPointPriceFrom=settlementPointPriceFrom,
            settlementPointPriceTo=settlementPointPriceTo,
            bidId=bidId,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np3_990_ex:
    """60-Day SASM Disclosure Reports  This report will contain all 60 day disclosure data related to SASM for Generation and Load Resources. The following individual files are included in the report: 60d_SASM_Generation_Resource_AS_Offers-YY-MMM-DD.csv60d_SASM_Load_Resource_AS_Offers-YY-MMM-DD.csv60d_SASM_Generation_Resource_AS_Offer Awards-YY-MMM-DD.csv60d_SASM_Load_Resource_AS_Offer_Awards-YY-MMM-DD.csv"""

    class _60SasmLoadResAsOffersParams(TypedDict, total=False):
        resourceName: str
        multiHourBlockFlag: bool
        blockIndicator1: str
        price1RRSPFRFrom: Decimal
        price1RRSPFRTo: Decimal
        price1RRSFFRFrom: Decimal
        price1RRSFFRTo: Decimal
        price1RRSUFRFrom: Decimal
        price1RRSUFRTo: Decimal
        price1OnlineNONSPINFrom: Decimal
        price1OnlineNONSPINTo: Decimal
        price1REGUPFrom: Decimal
        price1REGUPTo: Decimal
        price1REGDOWNFrom: Decimal
        price1REGDOWNTo: Decimal
        price1OfflineNONSPINFrom: Decimal
        price1OfflineNONSPINTo: Decimal
        quantityMW1From: int
        quantityMW1To: int
        blockIndicator2: str
        price2RRSPFRFrom: Decimal
        price2RRSPFRTo: Decimal
        price2RRSFFRFrom: Decimal
        price2RRSFFRTo: Decimal
        price2RRSUFRFrom: Decimal
        price2RRSUFRTo: Decimal
        price2OnlineNONSPINFrom: Decimal
        price2OnlineNONSPINTo: Decimal
        price2REGUPFrom: Decimal
        price2REGUPTo: Decimal
        price2REGDOWNFrom: Decimal
        price2REGDOWNTo: Decimal
        price2OfflineNONSPINFrom: Decimal
        price2OfflineNONSPINTo: Decimal
        quantityMW2From: int
        quantityMW2To: int
        blockIndicator3: str
        price3RRSPFRFrom: Decimal
        price3RRSPFRTo: Decimal
        price3RRSFFRFrom: Decimal
        price3RRSFFRTo: Decimal
        price3RRSUFRFrom: Decimal
        price3RRSUFRTo: Decimal
        price3OnlineNONSPINFrom: Decimal
        price3OnlineNONSPINTo: Decimal
        price3REGUPFrom: Decimal
        price3REGUPTo: Decimal
        price3REGDOWNFrom: Decimal
        price3REGDOWNTo: Decimal
        price3OfflineNONSPINFrom: Decimal
        price3OfflineNONSPINTo: Decimal
        quantityMW3From: int
        quantityMW3To: int
        blockIndicator4: str
        price4RRSPFRFrom: Decimal
        price4RRSPFRTo: Decimal
        price4RRSFFRFrom: Decimal
        price4RRSFFRTo: Decimal
        price4RRSUFRFrom: Decimal
        price4RRSUFRTo: Decimal
        price4OnlineNONSPINFrom: Decimal
        price4OnlineNONSPINTo: Decimal
        price4REGUPFrom: Decimal
        price4REGUPTo: Decimal
        price4REGDOWNFrom: Decimal
        price4REGDOWNTo: Decimal
        price4OfflineNONSPINFrom: Decimal
        price4OfflineNONSPINTo: Decimal
        quantityMW4From: int
        quantityMW4To: int
        blockIndicator5: str
        price5RRSPFRFrom: Decimal
        price5RRSPFRTo: Decimal
        price5RRSFFRFrom: Decimal
        price5RRSFFRTo: Decimal
        price5RRSUFRFrom: Decimal
        price5RRSUFRTo: Decimal
        price5OnlineNONSPINFrom: Decimal
        price5OnlineNONSPINTo: Decimal
        price5REGUP: bool
        price5REGDOWN: bool
        price5OfflineNONSPIN: bool
        quantityMW5From: int
        quantityMW5To: int
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        SASMIdFrom: datetime.datetime
        SASMIdTo: datetime.datetime
        hourEndingFrom: int
        hourEndingTo: int
        qseName: str
        dmeName: str
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_sasm_load_res_as_offers(
        *,
        resourceName: str | None = None,
        multiHourBlockFlag: bool | None = None,
        blockIndicator1: str | None = None,
        price1RRSPFRFrom: Decimal | None = None,
        price1RRSPFRTo: Decimal | None = None,
        price1RRSFFRFrom: Decimal | None = None,
        price1RRSFFRTo: Decimal | None = None,
        price1RRSUFRFrom: Decimal | None = None,
        price1RRSUFRTo: Decimal | None = None,
        price1OnlineNONSPINFrom: Decimal | None = None,
        price1OnlineNONSPINTo: Decimal | None = None,
        price1REGUPFrom: Decimal | None = None,
        price1REGUPTo: Decimal | None = None,
        price1REGDOWNFrom: Decimal | None = None,
        price1REGDOWNTo: Decimal | None = None,
        price1OfflineNONSPINFrom: Decimal | None = None,
        price1OfflineNONSPINTo: Decimal | None = None,
        quantityMW1From: int | None = None,
        quantityMW1To: int | None = None,
        blockIndicator2: str | None = None,
        price2RRSPFRFrom: Decimal | None = None,
        price2RRSPFRTo: Decimal | None = None,
        price2RRSFFRFrom: Decimal | None = None,
        price2RRSFFRTo: Decimal | None = None,
        price2RRSUFRFrom: Decimal | None = None,
        price2RRSUFRTo: Decimal | None = None,
        price2OnlineNONSPINFrom: Decimal | None = None,
        price2OnlineNONSPINTo: Decimal | None = None,
        price2REGUPFrom: Decimal | None = None,
        price2REGUPTo: Decimal | None = None,
        price2REGDOWNFrom: Decimal | None = None,
        price2REGDOWNTo: Decimal | None = None,
        price2OfflineNONSPINFrom: Decimal | None = None,
        price2OfflineNONSPINTo: Decimal | None = None,
        quantityMW2From: int | None = None,
        quantityMW2To: int | None = None,
        blockIndicator3: str | None = None,
        price3RRSPFRFrom: Decimal | None = None,
        price3RRSPFRTo: Decimal | None = None,
        price3RRSFFRFrom: Decimal | None = None,
        price3RRSFFRTo: Decimal | None = None,
        price3RRSUFRFrom: Decimal | None = None,
        price3RRSUFRTo: Decimal | None = None,
        price3OnlineNONSPINFrom: Decimal | None = None,
        price3OnlineNONSPINTo: Decimal | None = None,
        price3REGUPFrom: Decimal | None = None,
        price3REGUPTo: Decimal | None = None,
        price3REGDOWNFrom: Decimal | None = None,
        price3REGDOWNTo: Decimal | None = None,
        price3OfflineNONSPINFrom: Decimal | None = None,
        price3OfflineNONSPINTo: Decimal | None = None,
        quantityMW3From: int | None = None,
        quantityMW3To: int | None = None,
        blockIndicator4: str | None = None,
        price4RRSPFRFrom: Decimal | None = None,
        price4RRSPFRTo: Decimal | None = None,
        price4RRSFFRFrom: Decimal | None = None,
        price4RRSFFRTo: Decimal | None = None,
        price4RRSUFRFrom: Decimal | None = None,
        price4RRSUFRTo: Decimal | None = None,
        price4OnlineNONSPINFrom: Decimal | None = None,
        price4OnlineNONSPINTo: Decimal | None = None,
        price4REGUPFrom: Decimal | None = None,
        price4REGUPTo: Decimal | None = None,
        price4REGDOWNFrom: Decimal | None = None,
        price4REGDOWNTo: Decimal | None = None,
        price4OfflineNONSPINFrom: Decimal | None = None,
        price4OfflineNONSPINTo: Decimal | None = None,
        quantityMW4From: int | None = None,
        quantityMW4To: int | None = None,
        blockIndicator5: str | None = None,
        price5RRSPFRFrom: Decimal | None = None,
        price5RRSPFRTo: Decimal | None = None,
        price5RRSFFRFrom: Decimal | None = None,
        price5RRSFFRTo: Decimal | None = None,
        price5RRSUFRFrom: Decimal | None = None,
        price5RRSUFRTo: Decimal | None = None,
        price5OnlineNONSPINFrom: Decimal | None = None,
        price5OnlineNONSPINTo: Decimal | None = None,
        price5REGUP: bool | None = None,
        price5REGDOWN: bool | None = None,
        price5OfflineNONSPIN: bool | None = None,
        quantityMW5From: int | None = None,
        quantityMW5To: int | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        SASMIdFrom: datetime.datetime | None = None,
        SASMIdTo: datetime.datetime | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        qseName: str | None = None,
        dmeName: str | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day SASM Load Resource AS Offers"""
        return _get(
            "np3-990-ex/60_sasm_load_res_as_offers",
            resourceName=resourceName,
            multiHourBlockFlag=multiHourBlockFlag,
            blockIndicator1=blockIndicator1,
            price1RRSPFRFrom=price1RRSPFRFrom,
            price1RRSPFRTo=price1RRSPFRTo,
            price1RRSFFRFrom=price1RRSFFRFrom,
            price1RRSFFRTo=price1RRSFFRTo,
            price1RRSUFRFrom=price1RRSUFRFrom,
            price1RRSUFRTo=price1RRSUFRTo,
            price1OnlineNONSPINFrom=price1OnlineNONSPINFrom,
            price1OnlineNONSPINTo=price1OnlineNONSPINTo,
            price1REGUPFrom=price1REGUPFrom,
            price1REGUPTo=price1REGUPTo,
            price1REGDOWNFrom=price1REGDOWNFrom,
            price1REGDOWNTo=price1REGDOWNTo,
            price1OfflineNONSPINFrom=price1OfflineNONSPINFrom,
            price1OfflineNONSPINTo=price1OfflineNONSPINTo,
            quantityMW1From=quantityMW1From,
            quantityMW1To=quantityMW1To,
            blockIndicator2=blockIndicator2,
            price2RRSPFRFrom=price2RRSPFRFrom,
            price2RRSPFRTo=price2RRSPFRTo,
            price2RRSFFRFrom=price2RRSFFRFrom,
            price2RRSFFRTo=price2RRSFFRTo,
            price2RRSUFRFrom=price2RRSUFRFrom,
            price2RRSUFRTo=price2RRSUFRTo,
            price2OnlineNONSPINFrom=price2OnlineNONSPINFrom,
            price2OnlineNONSPINTo=price2OnlineNONSPINTo,
            price2REGUPFrom=price2REGUPFrom,
            price2REGUPTo=price2REGUPTo,
            price2REGDOWNFrom=price2REGDOWNFrom,
            price2REGDOWNTo=price2REGDOWNTo,
            price2OfflineNONSPINFrom=price2OfflineNONSPINFrom,
            price2OfflineNONSPINTo=price2OfflineNONSPINTo,
            quantityMW2From=quantityMW2From,
            quantityMW2To=quantityMW2To,
            blockIndicator3=blockIndicator3,
            price3RRSPFRFrom=price3RRSPFRFrom,
            price3RRSPFRTo=price3RRSPFRTo,
            price3RRSFFRFrom=price3RRSFFRFrom,
            price3RRSFFRTo=price3RRSFFRTo,
            price3RRSUFRFrom=price3RRSUFRFrom,
            price3RRSUFRTo=price3RRSUFRTo,
            price3OnlineNONSPINFrom=price3OnlineNONSPINFrom,
            price3OnlineNONSPINTo=price3OnlineNONSPINTo,
            price3REGUPFrom=price3REGUPFrom,
            price3REGUPTo=price3REGUPTo,
            price3REGDOWNFrom=price3REGDOWNFrom,
            price3REGDOWNTo=price3REGDOWNTo,
            price3OfflineNONSPINFrom=price3OfflineNONSPINFrom,
            price3OfflineNONSPINTo=price3OfflineNONSPINTo,
            quantityMW3From=quantityMW3From,
            quantityMW3To=quantityMW3To,
            blockIndicator4=blockIndicator4,
            price4RRSPFRFrom=price4RRSPFRFrom,
            price4RRSPFRTo=price4RRSPFRTo,
            price4RRSFFRFrom=price4RRSFFRFrom,
            price4RRSFFRTo=price4RRSFFRTo,
            price4RRSUFRFrom=price4RRSUFRFrom,
            price4RRSUFRTo=price4RRSUFRTo,
            price4OnlineNONSPINFrom=price4OnlineNONSPINFrom,
            price4OnlineNONSPINTo=price4OnlineNONSPINTo,
            price4REGUPFrom=price4REGUPFrom,
            price4REGUPTo=price4REGUPTo,
            price4REGDOWNFrom=price4REGDOWNFrom,
            price4REGDOWNTo=price4REGDOWNTo,
            price4OfflineNONSPINFrom=price4OfflineNONSPINFrom,
            price4OfflineNONSPINTo=price4OfflineNONSPINTo,
            quantityMW4From=quantityMW4From,
            quantityMW4To=quantityMW4To,
            blockIndicator5=blockIndicator5,
            price5RRSPFRFrom=price5RRSPFRFrom,
            price5RRSPFRTo=price5RRSPFRTo,
            price5RRSFFRFrom=price5RRSFFRFrom,
            price5RRSFFRTo=price5RRSFFRTo,
            price5RRSUFRFrom=price5RRSUFRFrom,
            price5RRSUFRTo=price5RRSUFRTo,
            price5OnlineNONSPINFrom=price5OnlineNONSPINFrom,
            price5OnlineNONSPINTo=price5OnlineNONSPINTo,
            price5REGUP=price5REGUP,
            price5REGDOWN=price5REGDOWN,
            price5OfflineNONSPIN=price5OfflineNONSPIN,
            quantityMW5From=quantityMW5From,
            quantityMW5To=quantityMW5To,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            SASMIdFrom=SASMIdFrom,
            SASMIdTo=SASMIdTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            qseName=qseName,
            dmeName=dmeName,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60SasmLoadResAsOfferAwardsParams(TypedDict, total=False):
        SASMIdFrom: datetime.datetime
        SASMIdTo: datetime.datetime
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        resourceName: str
        resourceType: str
        REGUPAawardedFrom: Decimal
        REGUPAawardedTo: Decimal
        REGUPMCPCFrom: Decimal
        REGUPMCPCTo: Decimal
        REGDNAwardedFrom: Decimal
        REGDNAwardedTo: Decimal
        REGDNMCPCFrom: Decimal
        REGDNMCPCTo: Decimal
        RRSPFRAwardedFrom: Decimal
        RRSPFRAwardedTo: Decimal
        RRSFFRAwardedFrom: Decimal
        RRSFFRAwardedTo: Decimal
        RRSUFRAwardedFrom: Decimal
        RRSUFRAwardedTo: Decimal
        RRSMCPCFrom: Decimal
        RRSMCPCTo: Decimal
        NSPINAwardedFrom: Decimal
        NSPINAwardedTo: Decimal
        NSPINMCPCFrom: Decimal
        NSPINMCPCTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_sasm_load_res_as_offer_awards(
        *,
        SASMIdFrom: datetime.datetime | None = None,
        SASMIdTo: datetime.datetime | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        resourceName: str | None = None,
        resourceType: str | None = None,
        REGUPAawardedFrom: Decimal | None = None,
        REGUPAawardedTo: Decimal | None = None,
        REGUPMCPCFrom: Decimal | None = None,
        REGUPMCPCTo: Decimal | None = None,
        REGDNAwardedFrom: Decimal | None = None,
        REGDNAwardedTo: Decimal | None = None,
        REGDNMCPCFrom: Decimal | None = None,
        REGDNMCPCTo: Decimal | None = None,
        RRSPFRAwardedFrom: Decimal | None = None,
        RRSPFRAwardedTo: Decimal | None = None,
        RRSFFRAwardedFrom: Decimal | None = None,
        RRSFFRAwardedTo: Decimal | None = None,
        RRSUFRAwardedFrom: Decimal | None = None,
        RRSUFRAwardedTo: Decimal | None = None,
        RRSMCPCFrom: Decimal | None = None,
        RRSMCPCTo: Decimal | None = None,
        NSPINAwardedFrom: Decimal | None = None,
        NSPINAwardedTo: Decimal | None = None,
        NSPINMCPCFrom: Decimal | None = None,
        NSPINMCPCTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day SASM Load Resource AS Offer Awards"""
        return _get(
            "np3-990-ex/60_sasm_load_res_as_offer_awards",
            SASMIdFrom=SASMIdFrom,
            SASMIdTo=SASMIdTo,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            resourceName=resourceName,
            resourceType=resourceType,
            REGUPAawardedFrom=REGUPAawardedFrom,
            REGUPAawardedTo=REGUPAawardedTo,
            REGUPMCPCFrom=REGUPMCPCFrom,
            REGUPMCPCTo=REGUPMCPCTo,
            REGDNAwardedFrom=REGDNAwardedFrom,
            REGDNAwardedTo=REGDNAwardedTo,
            REGDNMCPCFrom=REGDNMCPCFrom,
            REGDNMCPCTo=REGDNMCPCTo,
            RRSPFRAwardedFrom=RRSPFRAwardedFrom,
            RRSPFRAwardedTo=RRSPFRAwardedTo,
            RRSFFRAwardedFrom=RRSFFRAwardedFrom,
            RRSFFRAwardedTo=RRSFFRAwardedTo,
            RRSUFRAwardedFrom=RRSUFRAwardedFrom,
            RRSUFRAwardedTo=RRSUFRAwardedTo,
            RRSMCPCFrom=RRSMCPCFrom,
            RRSMCPCTo=RRSMCPCTo,
            NSPINAwardedFrom=NSPINAwardedFrom,
            NSPINAwardedTo=NSPINAwardedTo,
            NSPINMCPCFrom=NSPINMCPCFrom,
            NSPINMCPCTo=NSPINMCPCTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60SasmGenResAsOffersParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        SASMIdFrom: datetime.datetime
        SASMIdTo: datetime.datetime
        hourEndingFrom: int
        hourEndingTo: int
        qseName: str
        dmeName: str
        resourceName: str
        multiHourBlockFlag: bool
        blockIndicator1: str
        price1RRSPFRFrom: Decimal
        price1RRSPFRTo: Decimal
        price1RRSFFRFrom: Decimal
        price1RRSFFRTo: Decimal
        price1RRSUFRFrom: Decimal
        price1RRSUFRTo: Decimal
        price1OnlineNONSPINFrom: Decimal
        price1OnlineNONSPINTo: Decimal
        price1REGUPFrom: Decimal
        price1REGUPTo: Decimal
        price1REGDOWNFrom: Decimal
        price1REGDOWNTo: Decimal
        price1OfflineNONSPINFrom: Decimal
        price1OfflineNONSPINTo: Decimal
        quantityMW1From: int
        quantityMW1To: int
        blockIndicator2: str
        price2RRSPFRFrom: Decimal
        price2RRSPFRTo: Decimal
        price2RRSFFRFrom: Decimal
        price2RRSFFRTo: Decimal
        price2RRSUFRFrom: Decimal
        price2RRSUFRTo: Decimal
        price2OnlineNONSPINFrom: Decimal
        price2OnlineNONSPINTo: Decimal
        price2REGUPFrom: Decimal
        price2REGUPTo: Decimal
        price2REGDOWNFrom: Decimal
        price2REGDOWNTo: Decimal
        price2OfflineNONSPINFrom: Decimal
        price2OfflineNONSPINTo: Decimal
        quantityMW2From: int
        quantityMW2To: int
        blockIndicator3: str
        price3RRSPFRFrom: Decimal
        price3RRSPFRTo: Decimal
        price3RRSFFRFrom: Decimal
        price3RRSFFRTo: Decimal
        price3RRSUFRFrom: Decimal
        price3RRSUFRTo: Decimal
        price3OnlineNONSPINFrom: Decimal
        price3OnlineNONSPINTo: Decimal
        price3REGUPFrom: Decimal
        price3REGUPTo: Decimal
        price3REGDOWNFrom: Decimal
        price3REGDOWNTo: Decimal
        price3OfflineNONSPINFrom: Decimal
        price3OfflineNONSPINTo: Decimal
        quantityMW3From: int
        quantityMW3To: int
        blockIndicator4: str
        price4RRSPFRFrom: Decimal
        price4RRSPFRTo: Decimal
        price4RRSFFRFrom: Decimal
        price4RRSFFRTo: Decimal
        price4RRSUFRFrom: Decimal
        price4RRSUFRTo: Decimal
        price4OnlineNONSPINFrom: Decimal
        price4OnlineNONSPINTo: Decimal
        price4REGUPFrom: Decimal
        price4REGUPTo: Decimal
        price4REGDOWNFrom: Decimal
        price4REGDOWNTo: Decimal
        price4OfflineNONSPINFrom: Decimal
        price4OfflineNONSPINTo: Decimal
        quantityMW4From: int
        quantityMW4To: int
        blockIndicator5: str
        price5RRSPFRFrom: Decimal
        price5RRSPFRTo: Decimal
        price5RRSFFRFrom: Decimal
        price5RRSFFRTo: Decimal
        price5RRSUFRFrom: Decimal
        price5RRSUFRTo: Decimal
        price5OnlineNONSPINFrom: Decimal
        price5OnlineNONSPINTo: Decimal
        price5REGUP: bool
        price5REGDOWN: bool
        price5OfflineNONSPIN: bool
        quantityMW5From: int
        quantityMW5To: int
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_sasm_gen_res_as_offers(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        SASMIdFrom: datetime.datetime | None = None,
        SASMIdTo: datetime.datetime | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        qseName: str | None = None,
        dmeName: str | None = None,
        resourceName: str | None = None,
        multiHourBlockFlag: bool | None = None,
        blockIndicator1: str | None = None,
        price1RRSPFRFrom: Decimal | None = None,
        price1RRSPFRTo: Decimal | None = None,
        price1RRSFFRFrom: Decimal | None = None,
        price1RRSFFRTo: Decimal | None = None,
        price1RRSUFRFrom: Decimal | None = None,
        price1RRSUFRTo: Decimal | None = None,
        price1OnlineNONSPINFrom: Decimal | None = None,
        price1OnlineNONSPINTo: Decimal | None = None,
        price1REGUPFrom: Decimal | None = None,
        price1REGUPTo: Decimal | None = None,
        price1REGDOWNFrom: Decimal | None = None,
        price1REGDOWNTo: Decimal | None = None,
        price1OfflineNONSPINFrom: Decimal | None = None,
        price1OfflineNONSPINTo: Decimal | None = None,
        quantityMW1From: int | None = None,
        quantityMW1To: int | None = None,
        blockIndicator2: str | None = None,
        price2RRSPFRFrom: Decimal | None = None,
        price2RRSPFRTo: Decimal | None = None,
        price2RRSFFRFrom: Decimal | None = None,
        price2RRSFFRTo: Decimal | None = None,
        price2RRSUFRFrom: Decimal | None = None,
        price2RRSUFRTo: Decimal | None = None,
        price2OnlineNONSPINFrom: Decimal | None = None,
        price2OnlineNONSPINTo: Decimal | None = None,
        price2REGUPFrom: Decimal | None = None,
        price2REGUPTo: Decimal | None = None,
        price2REGDOWNFrom: Decimal | None = None,
        price2REGDOWNTo: Decimal | None = None,
        price2OfflineNONSPINFrom: Decimal | None = None,
        price2OfflineNONSPINTo: Decimal | None = None,
        quantityMW2From: int | None = None,
        quantityMW2To: int | None = None,
        blockIndicator3: str | None = None,
        price3RRSPFRFrom: Decimal | None = None,
        price3RRSPFRTo: Decimal | None = None,
        price3RRSFFRFrom: Decimal | None = None,
        price3RRSFFRTo: Decimal | None = None,
        price3RRSUFRFrom: Decimal | None = None,
        price3RRSUFRTo: Decimal | None = None,
        price3OnlineNONSPINFrom: Decimal | None = None,
        price3OnlineNONSPINTo: Decimal | None = None,
        price3REGUPFrom: Decimal | None = None,
        price3REGUPTo: Decimal | None = None,
        price3REGDOWNFrom: Decimal | None = None,
        price3REGDOWNTo: Decimal | None = None,
        price3OfflineNONSPINFrom: Decimal | None = None,
        price3OfflineNONSPINTo: Decimal | None = None,
        quantityMW3From: int | None = None,
        quantityMW3To: int | None = None,
        blockIndicator4: str | None = None,
        price4RRSPFRFrom: Decimal | None = None,
        price4RRSPFRTo: Decimal | None = None,
        price4RRSFFRFrom: Decimal | None = None,
        price4RRSFFRTo: Decimal | None = None,
        price4RRSUFRFrom: Decimal | None = None,
        price4RRSUFRTo: Decimal | None = None,
        price4OnlineNONSPINFrom: Decimal | None = None,
        price4OnlineNONSPINTo: Decimal | None = None,
        price4REGUPFrom: Decimal | None = None,
        price4REGUPTo: Decimal | None = None,
        price4REGDOWNFrom: Decimal | None = None,
        price4REGDOWNTo: Decimal | None = None,
        price4OfflineNONSPINFrom: Decimal | None = None,
        price4OfflineNONSPINTo: Decimal | None = None,
        quantityMW4From: int | None = None,
        quantityMW4To: int | None = None,
        blockIndicator5: str | None = None,
        price5RRSPFRFrom: Decimal | None = None,
        price5RRSPFRTo: Decimal | None = None,
        price5RRSFFRFrom: Decimal | None = None,
        price5RRSFFRTo: Decimal | None = None,
        price5RRSUFRFrom: Decimal | None = None,
        price5RRSUFRTo: Decimal | None = None,
        price5OnlineNONSPINFrom: Decimal | None = None,
        price5OnlineNONSPINTo: Decimal | None = None,
        price5REGUP: bool | None = None,
        price5REGDOWN: bool | None = None,
        price5OfflineNONSPIN: bool | None = None,
        quantityMW5From: int | None = None,
        quantityMW5To: int | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day SASM Generation Resource AS Offers"""
        return _get(
            "np3-990-ex/60_sasm_gen_res_as_offers",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            SASMIdFrom=SASMIdFrom,
            SASMIdTo=SASMIdTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            qseName=qseName,
            dmeName=dmeName,
            resourceName=resourceName,
            multiHourBlockFlag=multiHourBlockFlag,
            blockIndicator1=blockIndicator1,
            price1RRSPFRFrom=price1RRSPFRFrom,
            price1RRSPFRTo=price1RRSPFRTo,
            price1RRSFFRFrom=price1RRSFFRFrom,
            price1RRSFFRTo=price1RRSFFRTo,
            price1RRSUFRFrom=price1RRSUFRFrom,
            price1RRSUFRTo=price1RRSUFRTo,
            price1OnlineNONSPINFrom=price1OnlineNONSPINFrom,
            price1OnlineNONSPINTo=price1OnlineNONSPINTo,
            price1REGUPFrom=price1REGUPFrom,
            price1REGUPTo=price1REGUPTo,
            price1REGDOWNFrom=price1REGDOWNFrom,
            price1REGDOWNTo=price1REGDOWNTo,
            price1OfflineNONSPINFrom=price1OfflineNONSPINFrom,
            price1OfflineNONSPINTo=price1OfflineNONSPINTo,
            quantityMW1From=quantityMW1From,
            quantityMW1To=quantityMW1To,
            blockIndicator2=blockIndicator2,
            price2RRSPFRFrom=price2RRSPFRFrom,
            price2RRSPFRTo=price2RRSPFRTo,
            price2RRSFFRFrom=price2RRSFFRFrom,
            price2RRSFFRTo=price2RRSFFRTo,
            price2RRSUFRFrom=price2RRSUFRFrom,
            price2RRSUFRTo=price2RRSUFRTo,
            price2OnlineNONSPINFrom=price2OnlineNONSPINFrom,
            price2OnlineNONSPINTo=price2OnlineNONSPINTo,
            price2REGUPFrom=price2REGUPFrom,
            price2REGUPTo=price2REGUPTo,
            price2REGDOWNFrom=price2REGDOWNFrom,
            price2REGDOWNTo=price2REGDOWNTo,
            price2OfflineNONSPINFrom=price2OfflineNONSPINFrom,
            price2OfflineNONSPINTo=price2OfflineNONSPINTo,
            quantityMW2From=quantityMW2From,
            quantityMW2To=quantityMW2To,
            blockIndicator3=blockIndicator3,
            price3RRSPFRFrom=price3RRSPFRFrom,
            price3RRSPFRTo=price3RRSPFRTo,
            price3RRSFFRFrom=price3RRSFFRFrom,
            price3RRSFFRTo=price3RRSFFRTo,
            price3RRSUFRFrom=price3RRSUFRFrom,
            price3RRSUFRTo=price3RRSUFRTo,
            price3OnlineNONSPINFrom=price3OnlineNONSPINFrom,
            price3OnlineNONSPINTo=price3OnlineNONSPINTo,
            price3REGUPFrom=price3REGUPFrom,
            price3REGUPTo=price3REGUPTo,
            price3REGDOWNFrom=price3REGDOWNFrom,
            price3REGDOWNTo=price3REGDOWNTo,
            price3OfflineNONSPINFrom=price3OfflineNONSPINFrom,
            price3OfflineNONSPINTo=price3OfflineNONSPINTo,
            quantityMW3From=quantityMW3From,
            quantityMW3To=quantityMW3To,
            blockIndicator4=blockIndicator4,
            price4RRSPFRFrom=price4RRSPFRFrom,
            price4RRSPFRTo=price4RRSPFRTo,
            price4RRSFFRFrom=price4RRSFFRFrom,
            price4RRSFFRTo=price4RRSFFRTo,
            price4RRSUFRFrom=price4RRSUFRFrom,
            price4RRSUFRTo=price4RRSUFRTo,
            price4OnlineNONSPINFrom=price4OnlineNONSPINFrom,
            price4OnlineNONSPINTo=price4OnlineNONSPINTo,
            price4REGUPFrom=price4REGUPFrom,
            price4REGUPTo=price4REGUPTo,
            price4REGDOWNFrom=price4REGDOWNFrom,
            price4REGDOWNTo=price4REGDOWNTo,
            price4OfflineNONSPINFrom=price4OfflineNONSPINFrom,
            price4OfflineNONSPINTo=price4OfflineNONSPINTo,
            quantityMW4From=quantityMW4From,
            quantityMW4To=quantityMW4To,
            blockIndicator5=blockIndicator5,
            price5RRSPFRFrom=price5RRSPFRFrom,
            price5RRSPFRTo=price5RRSPFRTo,
            price5RRSFFRFrom=price5RRSFFRFrom,
            price5RRSFFRTo=price5RRSFFRTo,
            price5RRSUFRFrom=price5RRSUFRFrom,
            price5RRSUFRTo=price5RRSUFRTo,
            price5OnlineNONSPINFrom=price5OnlineNONSPINFrom,
            price5OnlineNONSPINTo=price5OnlineNONSPINTo,
            price5REGUP=price5REGUP,
            price5REGDOWN=price5REGDOWN,
            price5OfflineNONSPIN=price5OfflineNONSPIN,
            quantityMW5From=quantityMW5From,
            quantityMW5To=quantityMW5To,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class _60SasmGenResAsOfferAwardsParams(TypedDict, total=False):
        SASMIdFrom: datetime.datetime
        SASMIdTo: datetime.datetime
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        resourceName: str
        resourceType: str
        REGUPAawardedFrom: Decimal
        REGUPAawardedTo: Decimal
        REGUPMCPCFrom: Decimal
        REGUPMCPCTo: Decimal
        REGDNAwardedFrom: Decimal
        REGDNAwardedTo: Decimal
        REGDNMCPCFrom: Decimal
        REGDNMCPCTo: Decimal
        RRSPFRAwardedFrom: Decimal
        RRSPFRAwardedTo: Decimal
        RRSFFRAwardedFrom: Decimal
        RRSFFRAwardedTo: Decimal
        RRSUFRAwardedFrom: Decimal
        RRSUFRAwardedTo: Decimal
        RRSMCPCFrom: Decimal
        RRSMCPCTo: Decimal
        NSPINAwardedFrom: Decimal
        NSPINAwardedTo: Decimal
        NSPINMCPCFrom: Decimal
        NSPINMCPCTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_sasm_gen_res_as_offer_awards(
        *,
        SASMIdFrom: datetime.datetime | None = None,
        SASMIdTo: datetime.datetime | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        resourceName: str | None = None,
        resourceType: str | None = None,
        REGUPAawardedFrom: Decimal | None = None,
        REGUPAawardedTo: Decimal | None = None,
        REGUPMCPCFrom: Decimal | None = None,
        REGUPMCPCTo: Decimal | None = None,
        REGDNAwardedFrom: Decimal | None = None,
        REGDNAwardedTo: Decimal | None = None,
        REGDNMCPCFrom: Decimal | None = None,
        REGDNMCPCTo: Decimal | None = None,
        RRSPFRAwardedFrom: Decimal | None = None,
        RRSPFRAwardedTo: Decimal | None = None,
        RRSFFRAwardedFrom: Decimal | None = None,
        RRSFFRAwardedTo: Decimal | None = None,
        RRSUFRAwardedFrom: Decimal | None = None,
        RRSUFRAwardedTo: Decimal | None = None,
        RRSMCPCFrom: Decimal | None = None,
        RRSMCPCTo: Decimal | None = None,
        NSPINAwardedFrom: Decimal | None = None,
        NSPINAwardedTo: Decimal | None = None,
        NSPINMCPCFrom: Decimal | None = None,
        NSPINMCPCTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60 Day SASM Generation Resource AS Offer Awards"""
        return _get(
            "np3-990-ex/60_sasm_gen_res_as_offer_awards",
            SASMIdFrom=SASMIdFrom,
            SASMIdTo=SASMIdTo,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            resourceName=resourceName,
            resourceType=resourceType,
            REGUPAawardedFrom=REGUPAawardedFrom,
            REGUPAawardedTo=REGUPAawardedTo,
            REGUPMCPCFrom=REGUPMCPCFrom,
            REGUPMCPCTo=REGUPMCPCTo,
            REGDNAwardedFrom=REGDNAwardedFrom,
            REGDNAwardedTo=REGDNAwardedTo,
            REGDNMCPCFrom=REGDNMCPCFrom,
            REGDNMCPCTo=REGDNMCPCTo,
            RRSPFRAwardedFrom=RRSPFRAwardedFrom,
            RRSPFRAwardedTo=RRSPFRAwardedTo,
            RRSFFRAwardedFrom=RRSFFRAwardedFrom,
            RRSFFRAwardedTo=RRSFFRAwardedTo,
            RRSUFRAwardedFrom=RRSUFRAwardedFrom,
            RRSUFRAwardedTo=RRSUFRAwardedTo,
            RRSMCPCFrom=RRSMCPCFrom,
            RRSMCPCTo=RRSMCPCTo,
            NSPINAwardedFrom=NSPINAwardedFrom,
            NSPINAwardedTo=NSPINAwardedTo,
            NSPINMCPCFrom=NSPINMCPCFrom,
            NSPINMCPCTo=NSPINMCPCTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np3_991_ex:
    """60-Day COP All Updates  This report will contain all iterative Current Operating Plan (COP) submissions where a change has occurred for the operating day. Previously named 60-Day Current Operating Plan."""

    class _60CopAllUpdatesParams(TypedDict, total=False):
        cancelFlag: bool
        updateTimeFrom: datetime.datetime
        updateTimeTo: datetime.datetime
        submitTimeFrom: datetime.datetime
        submitTimeTo: datetime.datetime
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        qseName: str
        resourceName: str
        hourEnding: str
        status: str
        highSustainedLimitFrom: Decimal
        highSustainedLimitTo: Decimal
        lowSustainedLimitFrom: Decimal
        lowSustainedLimitTo: Decimal
        highEmergencyLimitFrom: Decimal
        highEmergencyLimitTo: Decimal
        lowEmergencyLimitFrom: Decimal
        lowEmergencyLimitTo: Decimal
        REGUPFrom: Decimal
        REGUPTo: Decimal
        REGDNFrom: Decimal
        REGDNTo: Decimal
        RRSPFRFrom: Decimal
        RRSPFRTo: Decimal
        RRSFFRFrom: Decimal
        RRSFFRTo: Decimal
        RRSUFRFrom: Decimal
        RRSUFRTo: Decimal
        NSPINFrom: Decimal
        NSPINTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def _60_cop_all_updates(
        *,
        cancelFlag: bool | None = None,
        updateTimeFrom: datetime.datetime | None = None,
        updateTimeTo: datetime.datetime | None = None,
        submitTimeFrom: datetime.datetime | None = None,
        submitTimeTo: datetime.datetime | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        qseName: str | None = None,
        resourceName: str | None = None,
        hourEnding: str | None = None,
        status: str | None = None,
        highSustainedLimitFrom: Decimal | None = None,
        highSustainedLimitTo: Decimal | None = None,
        lowSustainedLimitFrom: Decimal | None = None,
        lowSustainedLimitTo: Decimal | None = None,
        highEmergencyLimitFrom: Decimal | None = None,
        highEmergencyLimitTo: Decimal | None = None,
        lowEmergencyLimitFrom: Decimal | None = None,
        lowEmergencyLimitTo: Decimal | None = None,
        REGUPFrom: Decimal | None = None,
        REGUPTo: Decimal | None = None,
        REGDNFrom: Decimal | None = None,
        REGDNTo: Decimal | None = None,
        RRSPFRFrom: Decimal | None = None,
        RRSPFRTo: Decimal | None = None,
        RRSFFRFrom: Decimal | None = None,
        RRSFFRTo: Decimal | None = None,
        RRSUFRFrom: Decimal | None = None,
        RRSUFRTo: Decimal | None = None,
        NSPINFrom: Decimal | None = None,
        NSPINTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """60-Day COP All Updates"""
        return _get(
            "np3-991-ex/60_cop_all_updates",
            cancelFlag=cancelFlag,
            updateTimeFrom=updateTimeFrom,
            updateTimeTo=updateTimeTo,
            submitTimeFrom=submitTimeFrom,
            submitTimeTo=submitTimeTo,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            qseName=qseName,
            resourceName=resourceName,
            hourEnding=hourEnding,
            status=status,
            highSustainedLimitFrom=highSustainedLimitFrom,
            highSustainedLimitTo=highSustainedLimitTo,
            lowSustainedLimitFrom=lowSustainedLimitFrom,
            lowSustainedLimitTo=lowSustainedLimitTo,
            highEmergencyLimitFrom=highEmergencyLimitFrom,
            highEmergencyLimitTo=highEmergencyLimitTo,
            lowEmergencyLimitFrom=lowEmergencyLimitFrom,
            lowEmergencyLimitTo=lowEmergencyLimitTo,
            REGUPFrom=REGUPFrom,
            REGUPTo=REGUPTo,
            REGDNFrom=REGDNFrom,
            REGDNTo=REGDNTo,
            RRSPFRFrom=RRSPFRFrom,
            RRSPFRTo=RRSPFRTo,
            RRSFFRFrom=RRSFFRFrom,
            RRSFFRTo=RRSFFRTo,
            RRSUFRFrom=RRSUFRFrom,
            RRSUFRTo=RRSUFRTo,
            NSPINFrom=NSPINFrom,
            NSPINTo=NSPINTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_159_cd:
    """Load Distribution Factors  Load forecast distribution factors from which Market Participants can calculate Load at the Electrical Bus level by hour for the next seven days."""

    class LoadDistributionFactorsParams(TypedDict, total=False):
        LDFDateFrom: datetime.date
        LDFDateTo: datetime.date
        LDFHour: str
        substation: str
        distributionFactorFrom: Decimal
        distributionFactorTo: Decimal
        loadId: str
        MVARDistributionFactorFrom: Decimal
        MVARDistributionFactorTo: Decimal
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        MRIDLoad: str
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def load_distribution_factors(
        *,
        LDFDateFrom: datetime.date | None = None,
        LDFDateTo: datetime.date | None = None,
        LDFHour: str | None = None,
        substation: str | None = None,
        distributionFactorFrom: Decimal | None = None,
        distributionFactorTo: Decimal | None = None,
        loadId: str | None = None,
        MVARDistributionFactorFrom: Decimal | None = None,
        MVARDistributionFactorTo: Decimal | None = None,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        MRIDLoad: str | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Load Distribution Factors"""
        return _get(
            "np4-159-cd/load_distribution_factors",
            LDFDateFrom=LDFDateFrom,
            LDFDateTo=LDFDateTo,
            LDFHour=LDFHour,
            substation=substation,
            distributionFactorFrom=distributionFactorFrom,
            distributionFactorTo=distributionFactorTo,
            loadId=loadId,
            MVARDistributionFactorFrom=MVARDistributionFactorFrom,
            MVARDistributionFactorTo=MVARDistributionFactorTo,
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            MRIDLoad=MRIDLoad,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_179_cd:
    """Total Ancillary Service Offers  The total quantity in MW of Offers per Ancillary Service per hour from the Day-Ahead Market for the last thirty days on a daily basis which includes the following AS types: REGDN, REGUP, RRSPFR, RRSFFR, RRSUFR, & NSPIN."""

    class TotalAsServiceOffersParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEnding: str
        REGDNFrom: Decimal
        REGDNTo: Decimal
        REGUPFrom: Decimal
        REGUPTo: Decimal
        RRSPFRFrom: Decimal
        RRSPFRTo: Decimal
        RRSFFRFrom: Decimal
        RRSFFRTo: Decimal
        RRSUFRFrom: Decimal
        RRSUFRTo: Decimal
        ECRSSDFrom: Decimal
        ECRSSDTo: Decimal
        ECRSMDFrom: Decimal
        ECRSMDTo: Decimal
        NSPINFrom: Decimal
        NSPINTo: Decimal
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def total_as_service_offers(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEnding: str | None = None,
        REGDNFrom: Decimal | None = None,
        REGDNTo: Decimal | None = None,
        REGUPFrom: Decimal | None = None,
        REGUPTo: Decimal | None = None,
        RRSPFRFrom: Decimal | None = None,
        RRSPFRTo: Decimal | None = None,
        RRSFFRFrom: Decimal | None = None,
        RRSFFRTo: Decimal | None = None,
        RRSUFRFrom: Decimal | None = None,
        RRSUFRTo: Decimal | None = None,
        ECRSSDFrom: Decimal | None = None,
        ECRSSDTo: Decimal | None = None,
        ECRSMDFrom: Decimal | None = None,
        ECRSMDTo: Decimal | None = None,
        NSPINFrom: Decimal | None = None,
        NSPINTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Total Ancillary Service Offers"""
        return _get(
            "np4-179-cd/total_as_service_offers",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEnding=hourEnding,
            REGDNFrom=REGDNFrom,
            REGDNTo=REGDNTo,
            REGUPFrom=REGUPFrom,
            REGUPTo=REGUPTo,
            RRSPFRFrom=RRSPFRFrom,
            RRSPFRTo=RRSPFRTo,
            RRSFFRFrom=RRSFFRFrom,
            RRSFFRTo=RRSFFRTo,
            RRSUFRFrom=RRSUFRFrom,
            RRSUFRTo=RRSUFRTo,
            ECRSSDFrom=ECRSSDFrom,
            ECRSSDTo=ECRSSDTo,
            ECRSMDFrom=ECRSMDFrom,
            ECRSMDTo=ECRSMDTo,
            NSPINFrom=NSPINFrom,
            NSPINTo=NSPINTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_183_cd:
    """DAM Hourly LMPs  The Hourly Locational Marginal Prices per electrical bus from the Day-Ahead Market for the last thirty days on a daily basis."""

    class DamHourlyLmpParams(TypedDict, total=False):
        DSTFlag: bool
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEnding: str
        busName: str
        LMPFrom: Decimal
        LMPTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def dam_hourly_lmp(
        *,
        DSTFlag: bool | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEnding: str | None = None,
        busName: str | None = None,
        LMPFrom: Decimal | None = None,
        LMPTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """DAM Hourly LMPs"""
        return _get(
            "np4-183-cd/dam_hourly_lmp",
            DSTFlag=DSTFlag,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEnding=hourEnding,
            busName=busName,
            LMPFrom=LMPFrom,
            LMPTo=LMPTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_188_cd:
    """DAM Clearing Prices for Capacity  The Market Clearing Prices for Capacity for all Ancillary Services from the Day-Ahead Market for the last thirty days on a daily basis."""

    class DamClearPriceForCapParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEnding: str
        ancillaryType: str
        MCPCFrom: Decimal
        MCPCTo: Decimal
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def dam_clear_price_for_cap(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEnding: str | None = None,
        ancillaryType: str | None = None,
        MCPCFrom: Decimal | None = None,
        MCPCTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """DAM Clearing Prices for Capacity"""
        return _get(
            "np4-188-cd/dam_clear_price_for_cap",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEnding=hourEnding,
            ancillaryType=ancillaryType,
            MCPCFrom=MCPCFrom,
            MCPCTo=MCPCTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_190_cd:
    """DAM Settlement Point Prices  The Settlement Point Prices for all Resource Nodes, Load Zones, and Trading Hubs from the Day-Ahead Market for the last thirty days on a daily basis."""

    class DamStlmntPntPricesParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEnding: str
        settlementPoint: str
        settlementPointPriceFrom: Decimal
        settlementPointPriceTo: Decimal
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def dam_stlmnt_pnt_prices(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEnding: str | None = None,
        settlementPoint: str | None = None,
        settlementPointPriceFrom: Decimal | None = None,
        settlementPointPriceTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """DAM Settlement Point Prices"""
        return _get(
            "np4-190-cd/dam_stlmnt_pnt_prices",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEnding=hourEnding,
            settlementPoint=settlementPoint,
            settlementPointPriceFrom=settlementPointPriceFrom,
            settlementPointPriceTo=settlementPointPriceTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_191_cd:
    """DAM Shadow Prices  The active and binding constraints as well as the associated shadow prices from the Day-Ahead Market for the last thirty days on a daily basis."""

    class DamShadowPricesParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEnding: str
        constraintIdFrom: int
        constraintIdTo: int
        constraintName: str
        contingencyName: str
        constraintLimitFrom: int
        constraintLimitTo: int
        constraintValueFrom: int
        constraintValueTo: int
        violationAmountFrom: int
        violationAmountTo: int
        shadowPriceFrom: Decimal
        shadowPriceTo: Decimal
        fromStation: str
        toStation: str
        fromStationkVFrom: Decimal
        fromStationkVTo: Decimal
        toStationkVFrom: Decimal
        toStationkVTo: Decimal
        deliveryTimeFrom: datetime.datetime
        deliveryTimeTo: datetime.datetime
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def dam_shadow_prices(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEnding: str | None = None,
        constraintIdFrom: int | None = None,
        constraintIdTo: int | None = None,
        constraintName: str | None = None,
        contingencyName: str | None = None,
        constraintLimitFrom: int | None = None,
        constraintLimitTo: int | None = None,
        constraintValueFrom: int | None = None,
        constraintValueTo: int | None = None,
        violationAmountFrom: int | None = None,
        violationAmountTo: int | None = None,
        shadowPriceFrom: Decimal | None = None,
        shadowPriceTo: Decimal | None = None,
        fromStation: str | None = None,
        toStation: str | None = None,
        fromStationkVFrom: Decimal | None = None,
        fromStationkVTo: Decimal | None = None,
        toStationkVFrom: Decimal | None = None,
        toStationkVTo: Decimal | None = None,
        deliveryTimeFrom: datetime.datetime | None = None,
        deliveryTimeTo: datetime.datetime | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """DAM Shadow Prices"""
        return _get(
            "np4-191-cd/dam_shadow_prices",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEnding=hourEnding,
            constraintIdFrom=constraintIdFrom,
            constraintIdTo=constraintIdTo,
            constraintName=constraintName,
            contingencyName=contingencyName,
            constraintLimitFrom=constraintLimitFrom,
            constraintLimitTo=constraintLimitTo,
            constraintValueFrom=constraintValueFrom,
            constraintValueTo=constraintValueTo,
            violationAmountFrom=violationAmountFrom,
            violationAmountTo=violationAmountTo,
            shadowPriceFrom=shadowPriceFrom,
            shadowPriceTo=shadowPriceTo,
            fromStation=fromStation,
            toStation=toStation,
            fromStationkVFrom=fromStationkVFrom,
            fromStationkVTo=fromStationkVTo,
            toStationkVFrom=toStationkVFrom,
            toStationkVTo=toStationkVTo,
            deliveryTimeFrom=deliveryTimeFrom,
            deliveryTimeTo=deliveryTimeTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_196_m:
    """DAM Price Corrections  Day-Ahead Market price corrections."""

    class DamPriceCorrectionsSppParams(TypedDict, total=False):
        priceCorrectionTimeFrom: str
        priceCorrectionTimeTo: str
        DSTFlag: bool
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        deliveryHourFrom: int
        deliveryHourTo: int
        settlementPoint: str
        SPPOriginalFrom: Decimal
        SPPOriginalTo: Decimal
        SPPCorrectedFrom: Decimal
        SPPCorrectedTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def dam_price_corrections_spp(
        *,
        priceCorrectionTimeFrom: str | None = None,
        priceCorrectionTimeTo: str | None = None,
        DSTFlag: bool | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        deliveryHourFrom: int | None = None,
        deliveryHourTo: int | None = None,
        settlementPoint: str | None = None,
        SPPOriginalFrom: Decimal | None = None,
        SPPOriginalTo: Decimal | None = None,
        SPPCorrectedFrom: Decimal | None = None,
        SPPCorrectedTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """DAM Price Corrections for SPP"""
        return _get(
            "np4-196-m/dam_price_corrections_spp",
            priceCorrectionTimeFrom=priceCorrectionTimeFrom,
            priceCorrectionTimeTo=priceCorrectionTimeTo,
            DSTFlag=DSTFlag,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            deliveryHourFrom=deliveryHourFrom,
            deliveryHourTo=deliveryHourTo,
            settlementPoint=settlementPoint,
            SPPOriginalFrom=SPPOriginalFrom,
            SPPOriginalTo=SPPOriginalTo,
            SPPCorrectedFrom=SPPCorrectedFrom,
            SPPCorrectedTo=SPPCorrectedTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class DamPriceCorrectionsMcpcParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        deliveryHourFrom: int
        deliveryHourTo: int
        ASType: str
        MCPCOriginalFrom: Decimal
        MCPCOriginalTo: Decimal
        MCPCCorrectedFrom: Decimal
        MCPCCorrectedTo: Decimal
        priceCorrectionTimeFrom: datetime.datetime
        priceCorrectionTimeTo: datetime.datetime
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def dam_price_corrections_mcpc(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        deliveryHourFrom: int | None = None,
        deliveryHourTo: int | None = None,
        ASType: str | None = None,
        MCPCOriginalFrom: Decimal | None = None,
        MCPCOriginalTo: Decimal | None = None,
        MCPCCorrectedFrom: Decimal | None = None,
        MCPCCorrectedTo: Decimal | None = None,
        priceCorrectionTimeFrom: datetime.datetime | None = None,
        priceCorrectionTimeTo: datetime.datetime | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """DAM Price Corrections for MCPC"""
        return _get(
            "np4-196-m/dam_price_corrections_mcpc",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            deliveryHourFrom=deliveryHourFrom,
            deliveryHourTo=deliveryHourTo,
            ASType=ASType,
            MCPCOriginalFrom=MCPCOriginalFrom,
            MCPCOriginalTo=MCPCOriginalTo,
            MCPCCorrectedFrom=MCPCCorrectedFrom,
            MCPCCorrectedTo=MCPCCorrectedTo,
            priceCorrectionTimeFrom=priceCorrectionTimeFrom,
            priceCorrectionTimeTo=priceCorrectionTimeTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class DamPriceCorrectionsEblmpParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        deliveryHourFrom: int
        deliveryHourTo: int
        electricalBus: str
        LMPOriginalFrom: Decimal
        LMPOriginalTo: Decimal
        LMPCorrectedFrom: Decimal
        LMPCorrectedTo: Decimal
        priceCorrectionTimeFrom: datetime.datetime
        priceCorrectionTimeTo: datetime.datetime
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def dam_price_corrections_eblmp(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        deliveryHourFrom: int | None = None,
        deliveryHourTo: int | None = None,
        electricalBus: str | None = None,
        LMPOriginalFrom: Decimal | None = None,
        LMPOriginalTo: Decimal | None = None,
        LMPCorrectedFrom: Decimal | None = None,
        LMPCorrectedTo: Decimal | None = None,
        priceCorrectionTimeFrom: datetime.datetime | None = None,
        priceCorrectionTimeTo: datetime.datetime | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """DAM Price Corrections for EBLMP"""
        return _get(
            "np4-196-m/dam_price_corrections_eblmp",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            deliveryHourFrom=deliveryHourFrom,
            deliveryHourTo=deliveryHourTo,
            electricalBus=electricalBus,
            LMPOriginalFrom=LMPOriginalFrom,
            LMPOriginalTo=LMPOriginalTo,
            LMPCorrectedFrom=LMPCorrectedFrom,
            LMPCorrectedTo=LMPCorrectedTo,
            priceCorrectionTimeFrom=priceCorrectionTimeFrom,
            priceCorrectionTimeTo=priceCorrectionTimeTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_197_m:
    """RTM Price Corrections  Real-Time Market price corrections."""

    class RtmPriceCorrectionsSppParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        deliveryHourFrom: int
        deliveryHourTo: int
        deliveryIntervalFrom: int
        deliveryIntervalTo: int
        settlementPointName: str
        settlementPointType: str
        SPPOriginalFrom: Decimal
        SPPOriginalTo: Decimal
        SPPCorrectedFrom: Decimal
        SPPCorrectedTo: Decimal
        priceCorrectionTimeFrom: datetime.datetime
        priceCorrectionTimeTo: datetime.datetime
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def rtm_price_corrections_spp(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        deliveryHourFrom: int | None = None,
        deliveryHourTo: int | None = None,
        deliveryIntervalFrom: int | None = None,
        deliveryIntervalTo: int | None = None,
        settlementPointName: str | None = None,
        settlementPointType: str | None = None,
        SPPOriginalFrom: Decimal | None = None,
        SPPOriginalTo: Decimal | None = None,
        SPPCorrectedFrom: Decimal | None = None,
        SPPCorrectedTo: Decimal | None = None,
        priceCorrectionTimeFrom: datetime.datetime | None = None,
        priceCorrectionTimeTo: datetime.datetime | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """RTM Price Corrections for SPP"""
        return _get(
            "np4-197-m/rtm_price_corrections_spp",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            deliveryHourFrom=deliveryHourFrom,
            deliveryHourTo=deliveryHourTo,
            deliveryIntervalFrom=deliveryIntervalFrom,
            deliveryIntervalTo=deliveryIntervalTo,
            settlementPointName=settlementPointName,
            settlementPointType=settlementPointType,
            SPPOriginalFrom=SPPOriginalFrom,
            SPPOriginalTo=SPPOriginalTo,
            SPPCorrectedFrom=SPPCorrectedFrom,
            SPPCorrectedTo=SPPCorrectedTo,
            priceCorrectionTimeFrom=priceCorrectionTimeFrom,
            priceCorrectionTimeTo=priceCorrectionTimeTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class RtmPriceCorrectionsSplmpParams(TypedDict, total=False):
        settlementPointName: str
        LMPOriginalFrom: Decimal
        LMPOriginalTo: Decimal
        LMPCorrectedFrom: Decimal
        LMPCorrectedTo: Decimal
        priceCorrectionTimeFrom: datetime.datetime
        priceCorrectionTimeTo: datetime.datetime
        DSTFlag: bool
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def rtm_price_corrections_splmp(
        *,
        settlementPointName: str | None = None,
        LMPOriginalFrom: Decimal | None = None,
        LMPOriginalTo: Decimal | None = None,
        LMPCorrectedFrom: Decimal | None = None,
        LMPCorrectedTo: Decimal | None = None,
        priceCorrectionTimeFrom: datetime.datetime | None = None,
        priceCorrectionTimeTo: datetime.datetime | None = None,
        DSTFlag: bool | None = None,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """RTM Price Corrections SP LMP"""
        return _get(
            "np4-197-m/rtm_price_corrections_splmp",
            settlementPointName=settlementPointName,
            LMPOriginalFrom=LMPOriginalFrom,
            LMPOriginalTo=LMPOriginalTo,
            LMPCorrectedFrom=LMPCorrectedFrom,
            LMPCorrectedTo=LMPCorrectedTo,
            priceCorrectionTimeFrom=priceCorrectionTimeFrom,
            priceCorrectionTimeTo=priceCorrectionTimeTo,
            DSTFlag=DSTFlag,
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class RtmPriceCorrectionsSogpriceParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        deliveryHourFrom: int
        deliveryHourTo: int
        deliveryIntervalFrom: int
        deliveryIntervalTo: int
        resourceType: str
        resourceName: str
        meterName: str
        priceOriginalFrom: Decimal
        priceOriginalTo: Decimal
        priceCorrectedFrom: Decimal
        priceCorrectedTo: Decimal
        priceCorrectionTimeFrom: datetime.datetime
        priceCorrectionTimeTo: datetime.datetime
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def rtm_price_corrections_sogprice(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        deliveryHourFrom: int | None = None,
        deliveryHourTo: int | None = None,
        deliveryIntervalFrom: int | None = None,
        deliveryIntervalTo: int | None = None,
        resourceType: str | None = None,
        resourceName: str | None = None,
        meterName: str | None = None,
        priceOriginalFrom: Decimal | None = None,
        priceOriginalTo: Decimal | None = None,
        priceCorrectedFrom: Decimal | None = None,
        priceCorrectedTo: Decimal | None = None,
        priceCorrectionTimeFrom: datetime.datetime | None = None,
        priceCorrectionTimeTo: datetime.datetime | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """RTM Price Corrections for SOG Price"""
        return _get(
            "np4-197-m/rtm_price_corrections_sogprice",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            deliveryHourFrom=deliveryHourFrom,
            deliveryHourTo=deliveryHourTo,
            deliveryIntervalFrom=deliveryIntervalFrom,
            deliveryIntervalTo=deliveryIntervalTo,
            resourceType=resourceType,
            resourceName=resourceName,
            meterName=meterName,
            priceOriginalFrom=priceOriginalFrom,
            priceOriginalTo=priceOriginalTo,
            priceCorrectedFrom=priceCorrectedFrom,
            priceCorrectedTo=priceCorrectedTo,
            priceCorrectionTimeFrom=priceCorrectionTimeFrom,
            priceCorrectionTimeTo=priceCorrectionTimeTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class RtmPriceCorrectionsSoglmpParams(TypedDict, total=False):
        DSTFlag: bool
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        resourceType: str
        resourceName: str
        meterName: str
        meterLMPOriginalFrom: Decimal
        meterLMPOriginalTo: Decimal
        meterLMPCorrectedFrom: Decimal
        meterLMPCorrectedTo: Decimal
        RTORPAOriginalFrom: Decimal
        RTORPAOriginalTo: Decimal
        RTORPACorrectedFrom: Decimal
        RTORPACorrectedTo: Decimal
        RTORDPAOriginalFrom: Decimal
        RTORDPAOriginalTo: Decimal
        RTORDPACorrectedFrom: Decimal
        RTORDPACorrectedTo: Decimal
        finalLMPOriginalFrom: Decimal
        finalLMPOriginalTo: Decimal
        finalLMPCorrectedFrom: Decimal
        finalLMPCorrectedTo: Decimal
        priceCorrectionTimeFrom: datetime.datetime
        priceCorrectionTimeTo: datetime.datetime
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def rtm_price_corrections_soglmp(
        *,
        DSTFlag: bool | None = None,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        resourceType: str | None = None,
        resourceName: str | None = None,
        meterName: str | None = None,
        meterLMPOriginalFrom: Decimal | None = None,
        meterLMPOriginalTo: Decimal | None = None,
        meterLMPCorrectedFrom: Decimal | None = None,
        meterLMPCorrectedTo: Decimal | None = None,
        RTORPAOriginalFrom: Decimal | None = None,
        RTORPAOriginalTo: Decimal | None = None,
        RTORPACorrectedFrom: Decimal | None = None,
        RTORPACorrectedTo: Decimal | None = None,
        RTORDPAOriginalFrom: Decimal | None = None,
        RTORDPAOriginalTo: Decimal | None = None,
        RTORDPACorrectedFrom: Decimal | None = None,
        RTORDPACorrectedTo: Decimal | None = None,
        finalLMPOriginalFrom: Decimal | None = None,
        finalLMPOriginalTo: Decimal | None = None,
        finalLMPCorrectedFrom: Decimal | None = None,
        finalLMPCorrectedTo: Decimal | None = None,
        priceCorrectionTimeFrom: datetime.datetime | None = None,
        priceCorrectionTimeTo: datetime.datetime | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """RTM Price Corrections for SOG LMP"""
        return _get(
            "np4-197-m/rtm_price_corrections_soglmp",
            DSTFlag=DSTFlag,
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            resourceType=resourceType,
            resourceName=resourceName,
            meterName=meterName,
            meterLMPOriginalFrom=meterLMPOriginalFrom,
            meterLMPOriginalTo=meterLMPOriginalTo,
            meterLMPCorrectedFrom=meterLMPCorrectedFrom,
            meterLMPCorrectedTo=meterLMPCorrectedTo,
            RTORPAOriginalFrom=RTORPAOriginalFrom,
            RTORPAOriginalTo=RTORPAOriginalTo,
            RTORPACorrectedFrom=RTORPACorrectedFrom,
            RTORPACorrectedTo=RTORPACorrectedTo,
            RTORDPAOriginalFrom=RTORDPAOriginalFrom,
            RTORDPAOriginalTo=RTORDPAOriginalTo,
            RTORDPACorrectedFrom=RTORDPACorrectedFrom,
            RTORDPACorrectedTo=RTORDPACorrectedTo,
            finalLMPOriginalFrom=finalLMPOriginalFrom,
            finalLMPOriginalTo=finalLMPOriginalTo,
            finalLMPCorrectedFrom=finalLMPCorrectedFrom,
            finalLMPCorrectedTo=finalLMPCorrectedTo,
            priceCorrectionTimeFrom=priceCorrectionTimeFrom,
            priceCorrectionTimeTo=priceCorrectionTimeTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class RtmPriceCorrectionsShadowParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        constraintIdFrom: int
        constraintIdTo: int
        constraintName: str
        contingencyName: str
        shadowPriceOriginalFrom: Decimal
        shadowPriceOriginalTo: Decimal
        shadowPriceCorrectedFrom: Decimal
        shadowPriceCorrectedTo: Decimal
        limitOriginalFrom: Decimal
        limitOriginalTo: Decimal
        limitCorrectedFrom: Decimal
        limitCorrectedTo: Decimal
        valueOriginalFrom: Decimal
        valueOriginalTo: Decimal
        valueCorrectedFrom: Decimal
        valueCorrectedTo: Decimal
        priceCorrectionTimeFrom: datetime.datetime
        priceCorrectionTimeTo: datetime.datetime
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def rtm_price_corrections_shadow(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        constraintIdFrom: int | None = None,
        constraintIdTo: int | None = None,
        constraintName: str | None = None,
        contingencyName: str | None = None,
        shadowPriceOriginalFrom: Decimal | None = None,
        shadowPriceOriginalTo: Decimal | None = None,
        shadowPriceCorrectedFrom: Decimal | None = None,
        shadowPriceCorrectedTo: Decimal | None = None,
        limitOriginalFrom: Decimal | None = None,
        limitOriginalTo: Decimal | None = None,
        limitCorrectedFrom: Decimal | None = None,
        limitCorrectedTo: Decimal | None = None,
        valueOriginalFrom: Decimal | None = None,
        valueOriginalTo: Decimal | None = None,
        valueCorrectedFrom: Decimal | None = None,
        valueCorrectedTo: Decimal | None = None,
        priceCorrectionTimeFrom: datetime.datetime | None = None,
        priceCorrectionTimeTo: datetime.datetime | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """RTM Price Corrections for Shadow Prices"""
        return _get(
            "np4-197-m/rtm_price_corrections_shadow",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            constraintIdFrom=constraintIdFrom,
            constraintIdTo=constraintIdTo,
            constraintName=constraintName,
            contingencyName=contingencyName,
            shadowPriceOriginalFrom=shadowPriceOriginalFrom,
            shadowPriceOriginalTo=shadowPriceOriginalTo,
            shadowPriceCorrectedFrom=shadowPriceCorrectedFrom,
            shadowPriceCorrectedTo=shadowPriceCorrectedTo,
            limitOriginalFrom=limitOriginalFrom,
            limitOriginalTo=limitOriginalTo,
            limitCorrectedFrom=limitCorrectedFrom,
            limitCorrectedTo=limitCorrectedTo,
            valueOriginalFrom=valueOriginalFrom,
            valueOriginalTo=valueOriginalTo,
            valueCorrectedFrom=valueCorrectedFrom,
            valueCorrectedTo=valueCorrectedTo,
            priceCorrectionTimeFrom=priceCorrectionTimeFrom,
            priceCorrectionTimeTo=priceCorrectionTimeTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )

    class RtmPriceCorrectionsEblmpParams(TypedDict, total=False):
        LMPCorrectedFrom: Decimal
        LMPCorrectedTo: Decimal
        priceCorrectionTimeFrom: datetime.datetime
        priceCorrectionTimeTo: datetime.datetime
        DSTFlag: bool
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        electricalBus: str
        LMPOriginalFrom: Decimal
        LMPOriginalTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def rtm_price_corrections_eblmp(
        *,
        LMPCorrectedFrom: Decimal | None = None,
        LMPCorrectedTo: Decimal | None = None,
        priceCorrectionTimeFrom: datetime.datetime | None = None,
        priceCorrectionTimeTo: datetime.datetime | None = None,
        DSTFlag: bool | None = None,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        electricalBus: str | None = None,
        LMPOriginalFrom: Decimal | None = None,
        LMPOriginalTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """RTM Price Corrections for EB LMP"""
        return _get(
            "np4-197-m/rtm_price_corrections_eblmp",
            LMPCorrectedFrom=LMPCorrectedFrom,
            LMPCorrectedTo=LMPCorrectedTo,
            priceCorrectionTimeFrom=priceCorrectionTimeFrom,
            priceCorrectionTimeTo=priceCorrectionTimeTo,
            DSTFlag=DSTFlag,
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            electricalBus=electricalBus,
            LMPOriginalFrom=LMPOriginalFrom,
            LMPOriginalTo=LMPOriginalTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_33_cd:
    """DAM Ancillary Service Plan  Ancillary Service requirements by type and quantity for each hour of the current day plus the next 6 days."""

    class DamAsPlanParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEnding: str
        ancillaryType: str
        quantityFrom: int
        quantityTo: int
        DSTFlag: bool
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def dam_as_plan(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEnding: str | None = None,
        ancillaryType: str | None = None,
        quantityFrom: int | None = None,
        quantityTo: int | None = None,
        DSTFlag: bool | None = None,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """DAM Ancillary Service Plan"""
        return _get(
            "np4-33-cd/dam_as_plan",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEnding=hourEnding,
            ancillaryType=ancillaryType,
            quantityFrom=quantityFrom,
            quantityTo=quantityTo,
            DSTFlag=DSTFlag,
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_523_cd:
    """DAM System Lambda  System lambda of each successful DAM."""

    class DamSystemLambdaParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEnding: str
        systemLambdaFrom: Decimal
        systemLambdaTo: Decimal
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def dam_system_lambda(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEnding: str | None = None,
        systemLambdaFrom: Decimal | None = None,
        systemLambdaTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """DAM System Lambda"""
        return _get(
            "np4-523-cd/dam_system_lambda",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEnding=hourEnding,
            systemLambdaFrom=systemLambdaFrom,
            systemLambdaTo=systemLambdaTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_732_cd:
    """Wind Power Production - Hourly Averaged Actual and Forecasted Values  This report is posted every hour and includes System-wide and Regional actual hourly averaged wind power production, STWPF, WGRPP and COP HSLs for On-Line WGRs for a rolling historical 48-hour period as well as the System-wide and Regional STWPF, WGRPP and COP HSLs for On-Line WGRs for the rolling future 168-hour period. Our forecasts attempt to predict HSL, which is uncurtailed power generation potential. Actual system-wide generation, which is included in this report as "ACTUAL_SYSTEM_WIDE" or "SYSTEM_WIDE" is impacted by curtailments. Because of this, the data in this report should not be used to evaluate forecast performance. Steps will be taken to include Actual System-wide HSL in this report in the future."""

    class WppHrlyAvrgActlFcastParams(TypedDict, total=False):
        WGRPPLoadZoneNorthFrom: Decimal
        WGRPPLoadZoneNorthTo: Decimal
        DSTFlag: bool
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        actualSystemWideFrom: Decimal
        actualSystemWideTo: Decimal
        COPHSLSystemWideFrom: Decimal
        COPHSLSystemWideTo: Decimal
        STWPFSystemWideFrom: Decimal
        STWPFSystemWideTo: Decimal
        WGRPPSystemWideFrom: Decimal
        WGRPPSystemWideTo: Decimal
        actualLoadZoneSouthHoustonFrom: Decimal
        actualLoadZoneSouthHoustonTo: Decimal
        COPHSLLoadZoneSouthHoustonFrom: Decimal
        COPHSLLoadZoneSouthHoustonTo: Decimal
        STWPFLoadZoneSouthHoustonFrom: Decimal
        STWPFLoadZoneSouthHoustonTo: Decimal
        WGRPPLoadZoneSouthHoustonFrom: Decimal
        WGRPPLoadZoneSouthHoustonTo: Decimal
        actualLoadZoneWestFrom: Decimal
        actualLoadZoneWestTo: Decimal
        COPHSLLoadZoneWestFrom: Decimal
        COPHSLLoadZoneWestTo: Decimal
        STWPFLoadZoneWestFrom: Decimal
        STWPFLoadZoneWestTo: Decimal
        WGRPPLoadZoneWestFrom: Decimal
        WGRPPLoadZoneWestTo: Decimal
        actualLoadZoneNorthFrom: Decimal
        actualLoadZoneNorthTo: Decimal
        COPHSLLoadZoneNorthFrom: Decimal
        COPHSLLoadZoneNorthTo: Decimal
        STWPFLoadZoneNorthFrom: Decimal
        STWPFLoadZoneNorthTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def wpp_hrly_avrg_actl_fcast(
        *,
        WGRPPLoadZoneNorthFrom: Decimal | None = None,
        WGRPPLoadZoneNorthTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        actualSystemWideFrom: Decimal | None = None,
        actualSystemWideTo: Decimal | None = None,
        COPHSLSystemWideFrom: Decimal | None = None,
        COPHSLSystemWideTo: Decimal | None = None,
        STWPFSystemWideFrom: Decimal | None = None,
        STWPFSystemWideTo: Decimal | None = None,
        WGRPPSystemWideFrom: Decimal | None = None,
        WGRPPSystemWideTo: Decimal | None = None,
        actualLoadZoneSouthHoustonFrom: Decimal | None = None,
        actualLoadZoneSouthHoustonTo: Decimal | None = None,
        COPHSLLoadZoneSouthHoustonFrom: Decimal | None = None,
        COPHSLLoadZoneSouthHoustonTo: Decimal | None = None,
        STWPFLoadZoneSouthHoustonFrom: Decimal | None = None,
        STWPFLoadZoneSouthHoustonTo: Decimal | None = None,
        WGRPPLoadZoneSouthHoustonFrom: Decimal | None = None,
        WGRPPLoadZoneSouthHoustonTo: Decimal | None = None,
        actualLoadZoneWestFrom: Decimal | None = None,
        actualLoadZoneWestTo: Decimal | None = None,
        COPHSLLoadZoneWestFrom: Decimal | None = None,
        COPHSLLoadZoneWestTo: Decimal | None = None,
        STWPFLoadZoneWestFrom: Decimal | None = None,
        STWPFLoadZoneWestTo: Decimal | None = None,
        WGRPPLoadZoneWestFrom: Decimal | None = None,
        WGRPPLoadZoneWestTo: Decimal | None = None,
        actualLoadZoneNorthFrom: Decimal | None = None,
        actualLoadZoneNorthTo: Decimal | None = None,
        COPHSLLoadZoneNorthFrom: Decimal | None = None,
        COPHSLLoadZoneNorthTo: Decimal | None = None,
        STWPFLoadZoneNorthFrom: Decimal | None = None,
        STWPFLoadZoneNorthTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Wind Power Production - Hourly Averaged Actual and Forecasted Values"""
        return _get(
            "np4-732-cd/wpp_hrly_avrg_actl_fcast",
            WGRPPLoadZoneNorthFrom=WGRPPLoadZoneNorthFrom,
            WGRPPLoadZoneNorthTo=WGRPPLoadZoneNorthTo,
            DSTFlag=DSTFlag,
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            actualSystemWideFrom=actualSystemWideFrom,
            actualSystemWideTo=actualSystemWideTo,
            COPHSLSystemWideFrom=COPHSLSystemWideFrom,
            COPHSLSystemWideTo=COPHSLSystemWideTo,
            STWPFSystemWideFrom=STWPFSystemWideFrom,
            STWPFSystemWideTo=STWPFSystemWideTo,
            WGRPPSystemWideFrom=WGRPPSystemWideFrom,
            WGRPPSystemWideTo=WGRPPSystemWideTo,
            actualLoadZoneSouthHoustonFrom=actualLoadZoneSouthHoustonFrom,
            actualLoadZoneSouthHoustonTo=actualLoadZoneSouthHoustonTo,
            COPHSLLoadZoneSouthHoustonFrom=COPHSLLoadZoneSouthHoustonFrom,
            COPHSLLoadZoneSouthHoustonTo=COPHSLLoadZoneSouthHoustonTo,
            STWPFLoadZoneSouthHoustonFrom=STWPFLoadZoneSouthHoustonFrom,
            STWPFLoadZoneSouthHoustonTo=STWPFLoadZoneSouthHoustonTo,
            WGRPPLoadZoneSouthHoustonFrom=WGRPPLoadZoneSouthHoustonFrom,
            WGRPPLoadZoneSouthHoustonTo=WGRPPLoadZoneSouthHoustonTo,
            actualLoadZoneWestFrom=actualLoadZoneWestFrom,
            actualLoadZoneWestTo=actualLoadZoneWestTo,
            COPHSLLoadZoneWestFrom=COPHSLLoadZoneWestFrom,
            COPHSLLoadZoneWestTo=COPHSLLoadZoneWestTo,
            STWPFLoadZoneWestFrom=STWPFLoadZoneWestFrom,
            STWPFLoadZoneWestTo=STWPFLoadZoneWestTo,
            WGRPPLoadZoneWestFrom=WGRPPLoadZoneWestFrom,
            WGRPPLoadZoneWestTo=WGRPPLoadZoneWestTo,
            actualLoadZoneNorthFrom=actualLoadZoneNorthFrom,
            actualLoadZoneNorthTo=actualLoadZoneNorthTo,
            COPHSLLoadZoneNorthFrom=COPHSLLoadZoneNorthFrom,
            COPHSLLoadZoneNorthTo=COPHSLLoadZoneNorthTo,
            STWPFLoadZoneNorthFrom=STWPFLoadZoneNorthFrom,
            STWPFLoadZoneNorthTo=STWPFLoadZoneNorthTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_733_cd:
    """Wind Power Production - Actual 5-Minute Averaged Values  This report is posted every 5 minutes and includes System-wide and Regional actual 5-min averaged wind power production for a rolling historical 60-minute period."""

    class WppActual5minAvgValuesParams(TypedDict, total=False):
        intervalEndingFrom: datetime.datetime
        intervalEndingTo: datetime.datetime
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        systemWideFrom: Decimal
        systemWideTo: Decimal
        LZSouthHoustonFrom: Decimal
        LZSouthHoustonTo: Decimal
        LZWestFrom: Decimal
        LZWestTo: Decimal
        LZNorthFrom: Decimal
        LZNorthTo: Decimal
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def wpp_actual_5min_avg_values(
        *,
        intervalEndingFrom: datetime.datetime | None = None,
        intervalEndingTo: datetime.datetime | None = None,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        systemWideFrom: Decimal | None = None,
        systemWideTo: Decimal | None = None,
        LZSouthHoustonFrom: Decimal | None = None,
        LZSouthHoustonTo: Decimal | None = None,
        LZWestFrom: Decimal | None = None,
        LZWestTo: Decimal | None = None,
        LZNorthFrom: Decimal | None = None,
        LZNorthTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Wind Power Production - Actual 5-Minute Averaged Values"""
        return _get(
            "np4-733-cd/wpp_actual_5min_avg_values",
            intervalEndingFrom=intervalEndingFrom,
            intervalEndingTo=intervalEndingTo,
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            systemWideFrom=systemWideFrom,
            systemWideTo=systemWideTo,
            LZSouthHoustonFrom=LZSouthHoustonFrom,
            LZSouthHoustonTo=LZSouthHoustonTo,
            LZWestFrom=LZWestFrom,
            LZWestTo=LZWestTo,
            LZNorthFrom=LZNorthFrom,
            LZNorthTo=LZNorthTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_737_cd:
    """Solar Power Production - Hourly Averaged Actual and Forecasted Values  This report includes System-wide actual hourly averaged solar power production, STPPF, PVGRPP, and COP HSLs for On-Line PVGRs for a rolling historical 48-hour period as well as the System-wide STPPF, PVGRPP and COP HSLs for On-Line PVGRs for the rolling future 168-hour period. Our forecasts attempt to predict HSL, which is uncurtailed power generation potential. Actual system-wide generation, which is included in this report as "ACTUAL_SYSTEM_WIDE" or "SYSTEM_WIDE" is impacted by curtailments. Because of this, the data in this report should not be used to evaluate forecast performance. Steps will be taken to include Actual System-wide HSL in this report in the future."""

    class SppHrlyAvrgActlFcastParams(TypedDict, total=False):
        STPPFSystemWideFrom: Decimal
        STPPFSystemWideTo: Decimal
        PVGRPPSystemWideFrom: Decimal
        PVGRPPSystemWideTo: Decimal
        DSTFlag: bool
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        actualSystemWideFrom: Decimal
        actualSystemWideTo: Decimal
        COPHSLSystemWideFrom: Decimal
        COPHSLSystemWideTo: Decimal
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def spp_hrly_avrg_actl_fcast(
        *,
        STPPFSystemWideFrom: Decimal | None = None,
        STPPFSystemWideTo: Decimal | None = None,
        PVGRPPSystemWideFrom: Decimal | None = None,
        PVGRPPSystemWideTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        actualSystemWideFrom: Decimal | None = None,
        actualSystemWideTo: Decimal | None = None,
        COPHSLSystemWideFrom: Decimal | None = None,
        COPHSLSystemWideTo: Decimal | None = None,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Solar Power Production - Hourly Averaged Actual and Forecasted Values"""
        return _get(
            "np4-737-cd/spp_hrly_avrg_actl_fcast",
            STPPFSystemWideFrom=STPPFSystemWideFrom,
            STPPFSystemWideTo=STPPFSystemWideTo,
            PVGRPPSystemWideFrom=PVGRPPSystemWideFrom,
            PVGRPPSystemWideTo=PVGRPPSystemWideTo,
            DSTFlag=DSTFlag,
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            actualSystemWideFrom=actualSystemWideFrom,
            actualSystemWideTo=actualSystemWideTo,
            COPHSLSystemWideFrom=COPHSLSystemWideFrom,
            COPHSLSystemWideTo=COPHSLSystemWideTo,
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_738_cd:
    """Solar Power Production - Actual 5-Minute Averaged Values  This report is posted every 5 minutes and includes System-wide actual 5-minute averaged solar power production for On-Line PVGRs for a rolling historical 60-minute period."""

    class SppActual5minAvgValuesParams(TypedDict, total=False):
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        intervalEndingFrom: datetime.datetime
        intervalEndingTo: datetime.datetime
        systemWideFrom: Decimal
        systemWideTo: Decimal
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def spp_actual_5min_avg_values(
        *,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        intervalEndingFrom: datetime.datetime | None = None,
        intervalEndingTo: datetime.datetime | None = None,
        systemWideFrom: Decimal | None = None,
        systemWideTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Solar Power Production - Actual 5-Minute Averaged Values"""
        return _get(
            "np4-738-cd/spp_actual_5min_avg_values",
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            intervalEndingFrom=intervalEndingFrom,
            intervalEndingTo=intervalEndingTo,
            systemWideFrom=systemWideFrom,
            systemWideTo=systemWideTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_742_cd:
    """Wind Power Production - Hourly Averaged Actual and Forecasted Values by Geographical Region  This report is posted every hour and includes System-wide and Geographic Regional actual hourly averaged wind power production, STWPF, WGRPP and COP HSLs for On-Line WGRs for a rolling historical 48-hour period as well as the System-wide and Regional STWPF, WGRPP and COP HSLs for On-Line WGRs for the rolling future 168-hour period. Our forecasts attempt to predict HSL, which is uncurtailed power generation potential. Actual system-wide generation, which is included in this report as "ACTUAL_SYSTEM_WIDE" or "SYSTEM_WIDE" is impacted by curtailments. Because of this, the data in this report should not be used to evaluate forecast performance. Steps will be taken to include Actual System-wide HSL in this report in the future."""

    class WppHrlyActualFcastGeoParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        hourEndingFrom: int
        hourEndingTo: int
        actualSystemWideFrom: Decimal
        actualSystemWideTo: Decimal
        COPHSLSystemWideFrom: Decimal
        COPHSLSystemWideTo: Decimal
        STWPFSystemWideFrom: Decimal
        STWPFSystemWideTo: Decimal
        WGRPPSystemWideFrom: Decimal
        WGRPPSystemWideTo: Decimal
        actualPanhandleFrom: Decimal
        actualPanhandleTo: Decimal
        COPHSLPanhandleFrom: Decimal
        COPHSLPanhandleTo: Decimal
        STWPFPanhandleFrom: Decimal
        STWPFPanhandleTo: Decimal
        WGRPPPanhandleFrom: Decimal
        WGRPPPanhandleTo: Decimal
        actualCoastalFrom: Decimal
        actualCoastalTo: Decimal
        COPHSLCoastalFrom: Decimal
        COPHSLCoastalTo: Decimal
        STWPFCoastalFrom: Decimal
        STWPFCoastalTo: Decimal
        WGRPPCoastalFrom: Decimal
        WGRPPCoastalTo: Decimal
        actualSouthFrom: Decimal
        actualSouthTo: Decimal
        COPHSLSouthFrom: Decimal
        COPHSLSouthTo: Decimal
        STWPFSouthFrom: Decimal
        STWPFSouthTo: Decimal
        WGRPPSouthFrom: Decimal
        WGRPPSouthTo: Decimal
        actualWestFrom: Decimal
        actualWestTo: Decimal
        COPHSLWestFrom: Decimal
        COPHSLWestTo: Decimal
        STWPFWestFrom: Decimal
        STWPFWestTo: Decimal
        WGRPPWestFrom: Decimal
        WGRPPWestTo: Decimal
        actualNorthFrom: Decimal
        actualNorthTo: Decimal
        COPHSLNorthFrom: Decimal
        COPHSLNorthTo: Decimal
        STWPFNorthFrom: Decimal
        STWPFNorthTo: Decimal
        WGRPPNorthFrom: Decimal
        WGRPPNorthTo: Decimal
        DSTFlag: bool
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def wpp_hrly_actual_fcast_geo(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        actualSystemWideFrom: Decimal | None = None,
        actualSystemWideTo: Decimal | None = None,
        COPHSLSystemWideFrom: Decimal | None = None,
        COPHSLSystemWideTo: Decimal | None = None,
        STWPFSystemWideFrom: Decimal | None = None,
        STWPFSystemWideTo: Decimal | None = None,
        WGRPPSystemWideFrom: Decimal | None = None,
        WGRPPSystemWideTo: Decimal | None = None,
        actualPanhandleFrom: Decimal | None = None,
        actualPanhandleTo: Decimal | None = None,
        COPHSLPanhandleFrom: Decimal | None = None,
        COPHSLPanhandleTo: Decimal | None = None,
        STWPFPanhandleFrom: Decimal | None = None,
        STWPFPanhandleTo: Decimal | None = None,
        WGRPPPanhandleFrom: Decimal | None = None,
        WGRPPPanhandleTo: Decimal | None = None,
        actualCoastalFrom: Decimal | None = None,
        actualCoastalTo: Decimal | None = None,
        COPHSLCoastalFrom: Decimal | None = None,
        COPHSLCoastalTo: Decimal | None = None,
        STWPFCoastalFrom: Decimal | None = None,
        STWPFCoastalTo: Decimal | None = None,
        WGRPPCoastalFrom: Decimal | None = None,
        WGRPPCoastalTo: Decimal | None = None,
        actualSouthFrom: Decimal | None = None,
        actualSouthTo: Decimal | None = None,
        COPHSLSouthFrom: Decimal | None = None,
        COPHSLSouthTo: Decimal | None = None,
        STWPFSouthFrom: Decimal | None = None,
        STWPFSouthTo: Decimal | None = None,
        WGRPPSouthFrom: Decimal | None = None,
        WGRPPSouthTo: Decimal | None = None,
        actualWestFrom: Decimal | None = None,
        actualWestTo: Decimal | None = None,
        COPHSLWestFrom: Decimal | None = None,
        COPHSLWestTo: Decimal | None = None,
        STWPFWestFrom: Decimal | None = None,
        STWPFWestTo: Decimal | None = None,
        WGRPPWestFrom: Decimal | None = None,
        WGRPPWestTo: Decimal | None = None,
        actualNorthFrom: Decimal | None = None,
        actualNorthTo: Decimal | None = None,
        COPHSLNorthFrom: Decimal | None = None,
        COPHSLNorthTo: Decimal | None = None,
        STWPFNorthFrom: Decimal | None = None,
        STWPFNorthTo: Decimal | None = None,
        WGRPPNorthFrom: Decimal | None = None,
        WGRPPNorthTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Wind Power Production - Hourly Averaged Actual and Forecasted Values by Geographical Region"""
        return _get(
            "np4-742-cd/wpp_hrly_actual_fcast_geo",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            actualSystemWideFrom=actualSystemWideFrom,
            actualSystemWideTo=actualSystemWideTo,
            COPHSLSystemWideFrom=COPHSLSystemWideFrom,
            COPHSLSystemWideTo=COPHSLSystemWideTo,
            STWPFSystemWideFrom=STWPFSystemWideFrom,
            STWPFSystemWideTo=STWPFSystemWideTo,
            WGRPPSystemWideFrom=WGRPPSystemWideFrom,
            WGRPPSystemWideTo=WGRPPSystemWideTo,
            actualPanhandleFrom=actualPanhandleFrom,
            actualPanhandleTo=actualPanhandleTo,
            COPHSLPanhandleFrom=COPHSLPanhandleFrom,
            COPHSLPanhandleTo=COPHSLPanhandleTo,
            STWPFPanhandleFrom=STWPFPanhandleFrom,
            STWPFPanhandleTo=STWPFPanhandleTo,
            WGRPPPanhandleFrom=WGRPPPanhandleFrom,
            WGRPPPanhandleTo=WGRPPPanhandleTo,
            actualCoastalFrom=actualCoastalFrom,
            actualCoastalTo=actualCoastalTo,
            COPHSLCoastalFrom=COPHSLCoastalFrom,
            COPHSLCoastalTo=COPHSLCoastalTo,
            STWPFCoastalFrom=STWPFCoastalFrom,
            STWPFCoastalTo=STWPFCoastalTo,
            WGRPPCoastalFrom=WGRPPCoastalFrom,
            WGRPPCoastalTo=WGRPPCoastalTo,
            actualSouthFrom=actualSouthFrom,
            actualSouthTo=actualSouthTo,
            COPHSLSouthFrom=COPHSLSouthFrom,
            COPHSLSouthTo=COPHSLSouthTo,
            STWPFSouthFrom=STWPFSouthFrom,
            STWPFSouthTo=STWPFSouthTo,
            WGRPPSouthFrom=WGRPPSouthFrom,
            WGRPPSouthTo=WGRPPSouthTo,
            actualWestFrom=actualWestFrom,
            actualWestTo=actualWestTo,
            COPHSLWestFrom=COPHSLWestFrom,
            COPHSLWestTo=COPHSLWestTo,
            STWPFWestFrom=STWPFWestFrom,
            STWPFWestTo=STWPFWestTo,
            WGRPPWestFrom=WGRPPWestFrom,
            WGRPPWestTo=WGRPPWestTo,
            actualNorthFrom=actualNorthFrom,
            actualNorthTo=actualNorthTo,
            COPHSLNorthFrom=COPHSLNorthFrom,
            COPHSLNorthTo=COPHSLNorthTo,
            STWPFNorthFrom=STWPFNorthFrom,
            STWPFNorthTo=STWPFNorthTo,
            WGRPPNorthFrom=WGRPPNorthFrom,
            WGRPPNorthTo=WGRPPNorthTo,
            DSTFlag=DSTFlag,
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_743_cd:
    """Wind Power Production - Actual 5-Minute Averaged Values by Geographical Region  This report is posted every 5 minutes and includes System-wide and Geographic Regional actual 5-minute averaged wind power production for a rolling historical 60-minute period."""

    class WppActual5minAvgValuesGeoParams(TypedDict, total=False):
        intervalEndingFrom: datetime.datetime
        intervalEndingTo: datetime.datetime
        systemWideFrom: Decimal
        systemWideTo: Decimal
        panhandleFrom: Decimal
        panhandleTo: Decimal
        coastFrom: Decimal
        coastTo: Decimal
        southFrom: Decimal
        southTo: Decimal
        westFrom: Decimal
        westTo: Decimal
        northFrom: Decimal
        northTo: Decimal
        DSTFlag: bool
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def wpp_actual_5min_avg_values_geo(
        *,
        intervalEndingFrom: datetime.datetime | None = None,
        intervalEndingTo: datetime.datetime | None = None,
        systemWideFrom: Decimal | None = None,
        systemWideTo: Decimal | None = None,
        panhandleFrom: Decimal | None = None,
        panhandleTo: Decimal | None = None,
        coastFrom: Decimal | None = None,
        coastTo: Decimal | None = None,
        southFrom: Decimal | None = None,
        southTo: Decimal | None = None,
        westFrom: Decimal | None = None,
        westTo: Decimal | None = None,
        northFrom: Decimal | None = None,
        northTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Wind Power Production - Actual 5-Minute Averaged Values by Geographical Region"""
        return _get(
            "np4-743-cd/wpp_actual_5min_avg_values_geo",
            intervalEndingFrom=intervalEndingFrom,
            intervalEndingTo=intervalEndingTo,
            systemWideFrom=systemWideFrom,
            systemWideTo=systemWideTo,
            panhandleFrom=panhandleFrom,
            panhandleTo=panhandleTo,
            coastFrom=coastFrom,
            coastTo=coastTo,
            southFrom=southFrom,
            southTo=southTo,
            westFrom=westFrom,
            westTo=westTo,
            northFrom=northFrom,
            northTo=northTo,
            DSTFlag=DSTFlag,
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_745_cd:
    """Solar Power Production - Hourly Averaged Actual and Forecasted Values by Geographical Region  This report is posted every hour and includes System-wide and geographic regional hourly averaged solar power production, STPPF, PVGRPP, and COP HSL for On-Line PVGRs for a rolling historical 48-hour period as well as the system-wide and regional STPPF, PVGRPP, and COP HSL for On-Line PVGRs for the rolling future 168-hour period. System-wide and regional generation, are included in this report under column labels with "GEN_" prefixes. ERCOT's forecasts attempt to predict HSL, which is uncurtailed power generation potential. Since generation is impacted by curtailments, the data in this report should not be used to evaluate forecast performance. Steps will be taken to include HSL in this report in the future."""

    class SppHrlyActualFcastGeoParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        hourEndingFrom: int
        hourEndingTo: int
        genSystemWideFrom: Decimal
        genSystemWideTo: Decimal
        COPHSLSystemWideFrom: Decimal
        COPHSLSystemWideTo: Decimal
        STPPFSystemWideFrom: Decimal
        STPPFSystemWideTo: Decimal
        PVGRPPSystemWideFrom: Decimal
        PVGRPPSystemWideTo: Decimal
        genCenterWestFrom: Decimal
        genCenterWestTo: Decimal
        COPHSLCenterWestFrom: Decimal
        COPHSLCenterWestTo: Decimal
        STPPFCenterWestFrom: Decimal
        STPPFCenterWestTo: Decimal
        PVGRPPCenterWestFrom: Decimal
        PVGRPPCenterWestTo: Decimal
        genNorthWestFrom: Decimal
        genNorthWestTo: Decimal
        COPHSLNorthWestFrom: Decimal
        COPHSLNorthWestTo: Decimal
        STPPFNorthWestFrom: Decimal
        STPPFNorthWestTo: Decimal
        PVGRPPNorthWestFrom: Decimal
        PVGRPPNorthWestTo: Decimal
        genFarWestFrom: Decimal
        genFarWestTo: Decimal
        COPHSLFarWestFrom: Decimal
        COPHSLFarWestTo: Decimal
        STPPFFarWestFrom: Decimal
        STPPFFarWestTo: Decimal
        PVGRPPFarWestFrom: Decimal
        PVGRPPFarWestTo: Decimal
        genFarEastFrom: Decimal
        genFarEastTo: Decimal
        COPHSLFarEastFrom: Decimal
        COPHSLFarEastTo: Decimal
        STPPFFarEastFrom: Decimal
        STPPFFarEastTo: Decimal
        PVGRPPFarEastFrom: Decimal
        PVGRPPFarEastTo: Decimal
        genSouthEastFrom: Decimal
        genSouthEastTo: Decimal
        COPHSLSouthEastFrom: Decimal
        COPHSLSouthEastTo: Decimal
        STPPFSouthEastFrom: Decimal
        STPPFSouthEastTo: Decimal
        PVGRPPSouthEastFrom: Decimal
        PVGRPPSouthEastTo: Decimal
        genCenterEastFrom: Decimal
        genCenterEastTo: Decimal
        COPHSLCenterEastFrom: Decimal
        COPHSLCenterEastTo: Decimal
        STPPFCenterEastFrom: Decimal
        STPPFCenterEastTo: Decimal
        PVGRPPCenterEastFrom: Decimal
        PVGRPPCenterEastTo: Decimal
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def spp_hrly_actual_fcast_geo(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        hourEndingFrom: int | None = None,
        hourEndingTo: int | None = None,
        genSystemWideFrom: Decimal | None = None,
        genSystemWideTo: Decimal | None = None,
        COPHSLSystemWideFrom: Decimal | None = None,
        COPHSLSystemWideTo: Decimal | None = None,
        STPPFSystemWideFrom: Decimal | None = None,
        STPPFSystemWideTo: Decimal | None = None,
        PVGRPPSystemWideFrom: Decimal | None = None,
        PVGRPPSystemWideTo: Decimal | None = None,
        genCenterWestFrom: Decimal | None = None,
        genCenterWestTo: Decimal | None = None,
        COPHSLCenterWestFrom: Decimal | None = None,
        COPHSLCenterWestTo: Decimal | None = None,
        STPPFCenterWestFrom: Decimal | None = None,
        STPPFCenterWestTo: Decimal | None = None,
        PVGRPPCenterWestFrom: Decimal | None = None,
        PVGRPPCenterWestTo: Decimal | None = None,
        genNorthWestFrom: Decimal | None = None,
        genNorthWestTo: Decimal | None = None,
        COPHSLNorthWestFrom: Decimal | None = None,
        COPHSLNorthWestTo: Decimal | None = None,
        STPPFNorthWestFrom: Decimal | None = None,
        STPPFNorthWestTo: Decimal | None = None,
        PVGRPPNorthWestFrom: Decimal | None = None,
        PVGRPPNorthWestTo: Decimal | None = None,
        genFarWestFrom: Decimal | None = None,
        genFarWestTo: Decimal | None = None,
        COPHSLFarWestFrom: Decimal | None = None,
        COPHSLFarWestTo: Decimal | None = None,
        STPPFFarWestFrom: Decimal | None = None,
        STPPFFarWestTo: Decimal | None = None,
        PVGRPPFarWestFrom: Decimal | None = None,
        PVGRPPFarWestTo: Decimal | None = None,
        genFarEastFrom: Decimal | None = None,
        genFarEastTo: Decimal | None = None,
        COPHSLFarEastFrom: Decimal | None = None,
        COPHSLFarEastTo: Decimal | None = None,
        STPPFFarEastFrom: Decimal | None = None,
        STPPFFarEastTo: Decimal | None = None,
        PVGRPPFarEastFrom: Decimal | None = None,
        PVGRPPFarEastTo: Decimal | None = None,
        genSouthEastFrom: Decimal | None = None,
        genSouthEastTo: Decimal | None = None,
        COPHSLSouthEastFrom: Decimal | None = None,
        COPHSLSouthEastTo: Decimal | None = None,
        STPPFSouthEastFrom: Decimal | None = None,
        STPPFSouthEastTo: Decimal | None = None,
        PVGRPPSouthEastFrom: Decimal | None = None,
        PVGRPPSouthEastTo: Decimal | None = None,
        genCenterEastFrom: Decimal | None = None,
        genCenterEastTo: Decimal | None = None,
        COPHSLCenterEastFrom: Decimal | None = None,
        COPHSLCenterEastTo: Decimal | None = None,
        STPPFCenterEastFrom: Decimal | None = None,
        STPPFCenterEastTo: Decimal | None = None,
        PVGRPPCenterEastFrom: Decimal | None = None,
        PVGRPPCenterEastTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Solar Power Production - Hourly Averaged Actual and Forecasted Values by Geographical Region"""
        return _get(
            "np4-745-cd/spp_hrly_actual_fcast_geo",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            hourEndingFrom=hourEndingFrom,
            hourEndingTo=hourEndingTo,
            genSystemWideFrom=genSystemWideFrom,
            genSystemWideTo=genSystemWideTo,
            COPHSLSystemWideFrom=COPHSLSystemWideFrom,
            COPHSLSystemWideTo=COPHSLSystemWideTo,
            STPPFSystemWideFrom=STPPFSystemWideFrom,
            STPPFSystemWideTo=STPPFSystemWideTo,
            PVGRPPSystemWideFrom=PVGRPPSystemWideFrom,
            PVGRPPSystemWideTo=PVGRPPSystemWideTo,
            genCenterWestFrom=genCenterWestFrom,
            genCenterWestTo=genCenterWestTo,
            COPHSLCenterWestFrom=COPHSLCenterWestFrom,
            COPHSLCenterWestTo=COPHSLCenterWestTo,
            STPPFCenterWestFrom=STPPFCenterWestFrom,
            STPPFCenterWestTo=STPPFCenterWestTo,
            PVGRPPCenterWestFrom=PVGRPPCenterWestFrom,
            PVGRPPCenterWestTo=PVGRPPCenterWestTo,
            genNorthWestFrom=genNorthWestFrom,
            genNorthWestTo=genNorthWestTo,
            COPHSLNorthWestFrom=COPHSLNorthWestFrom,
            COPHSLNorthWestTo=COPHSLNorthWestTo,
            STPPFNorthWestFrom=STPPFNorthWestFrom,
            STPPFNorthWestTo=STPPFNorthWestTo,
            PVGRPPNorthWestFrom=PVGRPPNorthWestFrom,
            PVGRPPNorthWestTo=PVGRPPNorthWestTo,
            genFarWestFrom=genFarWestFrom,
            genFarWestTo=genFarWestTo,
            COPHSLFarWestFrom=COPHSLFarWestFrom,
            COPHSLFarWestTo=COPHSLFarWestTo,
            STPPFFarWestFrom=STPPFFarWestFrom,
            STPPFFarWestTo=STPPFFarWestTo,
            PVGRPPFarWestFrom=PVGRPPFarWestFrom,
            PVGRPPFarWestTo=PVGRPPFarWestTo,
            genFarEastFrom=genFarEastFrom,
            genFarEastTo=genFarEastTo,
            COPHSLFarEastFrom=COPHSLFarEastFrom,
            COPHSLFarEastTo=COPHSLFarEastTo,
            STPPFFarEastFrom=STPPFFarEastFrom,
            STPPFFarEastTo=STPPFFarEastTo,
            PVGRPPFarEastFrom=PVGRPPFarEastFrom,
            PVGRPPFarEastTo=PVGRPPFarEastTo,
            genSouthEastFrom=genSouthEastFrom,
            genSouthEastTo=genSouthEastTo,
            COPHSLSouthEastFrom=COPHSLSouthEastFrom,
            COPHSLSouthEastTo=COPHSLSouthEastTo,
            STPPFSouthEastFrom=STPPFSouthEastFrom,
            STPPFSouthEastTo=STPPFSouthEastTo,
            PVGRPPSouthEastFrom=PVGRPPSouthEastFrom,
            PVGRPPSouthEastTo=PVGRPPSouthEastTo,
            genCenterEastFrom=genCenterEastFrom,
            genCenterEastTo=genCenterEastTo,
            COPHSLCenterEastFrom=COPHSLCenterEastFrom,
            COPHSLCenterEastTo=COPHSLCenterEastTo,
            STPPFCenterEastFrom=STPPFCenterEastFrom,
            STPPFCenterEastTo=STPPFCenterEastTo,
            PVGRPPCenterEastFrom=PVGRPPCenterEastFrom,
            PVGRPPCenterEastTo=PVGRPPCenterEastTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np4_746_cd:
    """Solar Power Production - Actual 5-Minute Averaged Values by Geographical Region  This report is posted every 5 minutes and includes system-wide and geographic regional 5-minute averaged solar power production for a rolling historical 60-minute period."""

    class SppActual5minAvgValuesGeoParams(TypedDict, total=False):
        intervalEndingFrom: datetime.datetime
        intervalEndingTo: datetime.datetime
        postedDatetimeFrom: datetime.datetime
        postedDatetimeTo: datetime.datetime
        genSystemWideFrom: Decimal
        genSystemWideTo: Decimal
        genCenterWestFrom: Decimal
        genCenterWestTo: Decimal
        genNorthWestFrom: Decimal
        genNorthWestTo: Decimal
        genFarWestFrom: Decimal
        genFarWestTo: Decimal
        genFarEastFrom: Decimal
        genFarEastTo: Decimal
        genSouthEastFrom: Decimal
        genSouthEastTo: Decimal
        genCenterEastFrom: Decimal
        genCenterEastTo: Decimal
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def spp_actual_5min_avg_values_geo(
        *,
        intervalEndingFrom: datetime.datetime | None = None,
        intervalEndingTo: datetime.datetime | None = None,
        postedDatetimeFrom: datetime.datetime | None = None,
        postedDatetimeTo: datetime.datetime | None = None,
        genSystemWideFrom: Decimal | None = None,
        genSystemWideTo: Decimal | None = None,
        genCenterWestFrom: Decimal | None = None,
        genCenterWestTo: Decimal | None = None,
        genNorthWestFrom: Decimal | None = None,
        genNorthWestTo: Decimal | None = None,
        genFarWestFrom: Decimal | None = None,
        genFarWestTo: Decimal | None = None,
        genFarEastFrom: Decimal | None = None,
        genFarEastTo: Decimal | None = None,
        genSouthEastFrom: Decimal | None = None,
        genSouthEastTo: Decimal | None = None,
        genCenterEastFrom: Decimal | None = None,
        genCenterEastTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Solar Power Production - Actual 5-Minute Averaged Values by Geographical Region"""
        return _get(
            "np4-746-cd/spp_actual_5min_avg_values_geo",
            intervalEndingFrom=intervalEndingFrom,
            intervalEndingTo=intervalEndingTo,
            postedDatetimeFrom=postedDatetimeFrom,
            postedDatetimeTo=postedDatetimeTo,
            genSystemWideFrom=genSystemWideFrom,
            genSystemWideTo=genSystemWideTo,
            genCenterWestFrom=genCenterWestFrom,
            genCenterWestTo=genCenterWestTo,
            genNorthWestFrom=genNorthWestFrom,
            genNorthWestTo=genNorthWestTo,
            genFarWestFrom=genFarWestFrom,
            genFarWestTo=genFarWestTo,
            genFarEastFrom=genFarEastFrom,
            genFarEastTo=genFarEastTo,
            genSouthEastFrom=genSouthEastFrom,
            genSouthEastTo=genSouthEastTo,
            genCenterEastFrom=genCenterEastFrom,
            genCenterEastTo=genCenterEastTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np6_322_cd:
    """SCED System Lambda  System lambda of each successful SCED."""

    class ScedSystemLambdaParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        systemLambdaFrom: Decimal
        systemLambdaTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def sced_system_lambda(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        systemLambdaFrom: Decimal | None = None,
        systemLambdaTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """SCED System Lambda"""
        return _get(
            "np6-322-cd/sced_system_lambda",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            systemLambdaFrom=systemLambdaFrom,
            systemLambdaTo=systemLambdaTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np6_345_cd:
    """Actual System Load by Weather Zone  Report of Actual hourly load data by weather zone and ERCOT total."""

    class ActSysLoadByWznParams(TypedDict, total=False):
        operatingDayFrom: datetime.date
        operatingDayTo: datetime.date
        hourEnding: str
        coastFrom: Decimal
        coastTo: Decimal
        eastFrom: Decimal
        eastTo: Decimal
        farWestFrom: Decimal
        farWestTo: Decimal
        northFrom: Decimal
        northTo: Decimal
        northCFrom: Decimal
        northCTo: Decimal
        southernFrom: Decimal
        southernTo: Decimal
        southCFrom: Decimal
        southCTo: Decimal
        westFrom: Decimal
        westTo: Decimal
        totalFrom: Decimal
        totalTo: Decimal
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def act_sys_load_by_wzn(
        *,
        operatingDayFrom: datetime.date | None = None,
        operatingDayTo: datetime.date | None = None,
        hourEnding: str | None = None,
        coastFrom: Decimal | None = None,
        coastTo: Decimal | None = None,
        eastFrom: Decimal | None = None,
        eastTo: Decimal | None = None,
        farWestFrom: Decimal | None = None,
        farWestTo: Decimal | None = None,
        northFrom: Decimal | None = None,
        northTo: Decimal | None = None,
        northCFrom: Decimal | None = None,
        northCTo: Decimal | None = None,
        southernFrom: Decimal | None = None,
        southernTo: Decimal | None = None,
        southCFrom: Decimal | None = None,
        southCTo: Decimal | None = None,
        westFrom: Decimal | None = None,
        westTo: Decimal | None = None,
        totalFrom: Decimal | None = None,
        totalTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Actual System Load by Weather Zone"""
        return _get(
            "np6-345-cd/act_sys_load_by_wzn",
            operatingDayFrom=operatingDayFrom,
            operatingDayTo=operatingDayTo,
            hourEnding=hourEnding,
            coastFrom=coastFrom,
            coastTo=coastTo,
            eastFrom=eastFrom,
            eastTo=eastTo,
            farWestFrom=farWestFrom,
            farWestTo=farWestTo,
            northFrom=northFrom,
            northTo=northTo,
            northCFrom=northCFrom,
            northCTo=northCTo,
            southernFrom=southernFrom,
            southernTo=southernTo,
            southCFrom=southCFrom,
            southCTo=southCTo,
            westFrom=westFrom,
            westTo=westTo,
            totalFrom=totalFrom,
            totalTo=totalTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np6_346_cd:
    """Actual System Load by Forecast Zone  A daily report of Actual System Load by Forecast Zone for each hour of the previous operating day."""

    class ActSysLoadByFznParams(TypedDict, total=False):
        operatingDayFrom: datetime.date
        operatingDayTo: datetime.date
        hourEnding: str
        northFrom: Decimal
        northTo: Decimal
        southFrom: Decimal
        southTo: Decimal
        westFrom: Decimal
        westTo: Decimal
        houstonFrom: Decimal
        houstonTo: Decimal
        totalFrom: Decimal
        totalTo: Decimal
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def act_sys_load_by_fzn(
        *,
        operatingDayFrom: datetime.date | None = None,
        operatingDayTo: datetime.date | None = None,
        hourEnding: str | None = None,
        northFrom: Decimal | None = None,
        northTo: Decimal | None = None,
        southFrom: Decimal | None = None,
        southTo: Decimal | None = None,
        westFrom: Decimal | None = None,
        westTo: Decimal | None = None,
        houstonFrom: Decimal | None = None,
        houstonTo: Decimal | None = None,
        totalFrom: Decimal | None = None,
        totalTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Actual System Load by Forecast Zone"""
        return _get(
            "np6-346-cd/act_sys_load_by_fzn",
            operatingDayFrom=operatingDayFrom,
            operatingDayTo=operatingDayTo,
            hourEnding=hourEnding,
            northFrom=northFrom,
            northTo=northTo,
            southFrom=southFrom,
            southTo=southTo,
            westFrom=westFrom,
            westTo=westTo,
            houstonFrom=houstonFrom,
            houstonTo=houstonTo,
            totalFrom=totalFrom,
            totalTo=totalTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np6_787_cd:
    """LMPs by Electrical Bus  The Locational Marginal Price for each Electrical Bus, normally produced by SCED every five minutes."""

    class LmpElectricalBusParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        electricalBus: str
        LMPFrom: Decimal
        LMPTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def lmp_electrical_bus(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        electricalBus: str | None = None,
        LMPFrom: Decimal | None = None,
        LMPTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """LMP by Electrical Bus"""
        return _get(
            "np6-787-cd/lmp_electrical_bus",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            electricalBus=electricalBus,
            LMPFrom=LMPFrom,
            LMPTo=LMPTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np6_788_cd:
    """LMPs by Resource Nodes, Load Zones and Trading Hubs  The Locational Marginal Price for each Settlement Point, normally produced by SCED every five minutes."""

    class LmpNodeZoneHubParams(TypedDict, total=False):
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        settlementPoint: str
        LMPFrom: Decimal
        LMPTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def lmp_node_zone_hub(
        *,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        settlementPoint: str | None = None,
        LMPFrom: Decimal | None = None,
        LMPTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """LMPs by Resource Nodes, Load Zones and Trading Hubs"""
        return _get(
            "np6-788-cd/lmp_node_zone_hub",
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            settlementPoint=settlementPoint,
            LMPFrom=LMPFrom,
            LMPTo=LMPTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np6_86_cd:
    """SCED Shadow Prices and Binding Transmission Constraints  The report for Shadow Prices of binding/violated constraints in SCED. The report shows the contingency name, overloaded element details (element name, from/to station name and kV level), Shadow Price ( price for resolving one MW of the constraint), Penalty for violating the constraint (MaxShadow Price), overloaded element limit and flow (value)pairs that caused such constraint."""

    class ShdwPricesBndTrnsConstParams(TypedDict, total=False):
        fromStation: str
        toStation: str
        fromStationkVFrom: Decimal
        fromStationkVTo: Decimal
        toStationkVFrom: Decimal
        toStationkVTo: Decimal
        CCTStatus: str
        SCEDTimestampFrom: datetime.datetime
        SCEDTimestampTo: datetime.datetime
        repeatedHourFlag: bool
        constraintIDFrom: int
        constraintIDTo: int
        constraintName: str
        contingencyName: str
        shadowPriceFrom: Decimal
        shadowPriceTo: Decimal
        maxShadowPriceFrom: Decimal
        maxShadowPriceTo: Decimal
        limitFrom: Decimal
        limitTo: Decimal
        valueFrom: Decimal
        valueTo: Decimal
        violatedMWFrom: Decimal
        violatedMWTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def shdw_prices_bnd_trns_const(
        *,
        fromStation: str | None = None,
        toStation: str | None = None,
        fromStationkVFrom: Decimal | None = None,
        fromStationkVTo: Decimal | None = None,
        toStationkVFrom: Decimal | None = None,
        toStationkVTo: Decimal | None = None,
        CCTStatus: str | None = None,
        SCEDTimestampFrom: datetime.datetime | None = None,
        SCEDTimestampTo: datetime.datetime | None = None,
        repeatedHourFlag: bool | None = None,
        constraintIDFrom: int | None = None,
        constraintIDTo: int | None = None,
        constraintName: str | None = None,
        contingencyName: str | None = None,
        shadowPriceFrom: Decimal | None = None,
        shadowPriceTo: Decimal | None = None,
        maxShadowPriceFrom: Decimal | None = None,
        maxShadowPriceTo: Decimal | None = None,
        limitFrom: Decimal | None = None,
        limitTo: Decimal | None = None,
        valueFrom: Decimal | None = None,
        valueTo: Decimal | None = None,
        violatedMWFrom: Decimal | None = None,
        violatedMWTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """SCED Shadow Prices and Binding Transmission Constraints"""
        return _get(
            "np6-86-cd/shdw_prices_bnd_trns_const",
            fromStation=fromStation,
            toStation=toStation,
            fromStationkVFrom=fromStationkVFrom,
            fromStationkVTo=fromStationkVTo,
            toStationkVFrom=toStationkVFrom,
            toStationkVTo=toStationkVTo,
            CCTStatus=CCTStatus,
            SCEDTimestampFrom=SCEDTimestampFrom,
            SCEDTimestampTo=SCEDTimestampTo,
            repeatedHourFlag=repeatedHourFlag,
            constraintIDFrom=constraintIDFrom,
            constraintIDTo=constraintIDTo,
            constraintName=constraintName,
            contingencyName=contingencyName,
            shadowPriceFrom=shadowPriceFrom,
            shadowPriceTo=shadowPriceTo,
            maxShadowPriceFrom=maxShadowPriceFrom,
            maxShadowPriceTo=maxShadowPriceTo,
            limitFrom=limitFrom,
            limitTo=limitTo,
            valueFrom=valueFrom,
            valueTo=valueTo,
            violatedMWFrom=violatedMWFrom,
            violatedMWTo=violatedMWTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np6_905_cd:
    """Settlement Point Prices at Resource Nodes, Hubs and Load Zones  Settlement Point Price for each Settlement Point, produced from SCED LMPs every 15 minutes."""

    class SppNodeZoneHubParams(TypedDict, total=False):
        deliveryDateFrom: datetime.date
        deliveryDateTo: datetime.date
        deliveryHourFrom: int
        deliveryHourTo: int
        deliveryIntervalFrom: int
        deliveryIntervalTo: int
        settlementPoint: str
        settlementPointType: str
        settlementPointPriceFrom: Decimal
        settlementPointPriceTo: Decimal
        DSTFlag: bool
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def spp_node_zone_hub(
        *,
        deliveryDateFrom: datetime.date | None = None,
        deliveryDateTo: datetime.date | None = None,
        deliveryHourFrom: int | None = None,
        deliveryHourTo: int | None = None,
        deliveryIntervalFrom: int | None = None,
        deliveryIntervalTo: int | None = None,
        settlementPoint: str | None = None,
        settlementPointType: str | None = None,
        settlementPointPriceFrom: Decimal | None = None,
        settlementPointPriceTo: Decimal | None = None,
        DSTFlag: bool | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """Settlement Point Prices at Resource Nodes, Hubs and Load Zones"""
        return _get(
            "np6-905-cd/spp_node_zone_hub",
            deliveryDateFrom=deliveryDateFrom,
            deliveryDateTo=deliveryDateTo,
            deliveryHourFrom=deliveryHourFrom,
            deliveryHourTo=deliveryHourTo,
            deliveryIntervalFrom=deliveryIntervalFrom,
            deliveryIntervalTo=deliveryIntervalTo,
            settlementPoint=settlementPoint,
            settlementPointType=settlementPointType,
            settlementPointPriceFrom=settlementPointPriceFrom,
            settlementPointPriceTo=settlementPointPriceTo,
            DSTFlag=DSTFlag,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )


class np6_970_cd:
    """RTD Indicative LMPs by Resource Nodes, Load Zones and Hubs  This report is posted after every Look Ahead RTD run and includes indicative LMPs at Resource Nodes, Hub LMPs and Load Zone for each interval in the Look Ahead SCED-RTD Study Period."""

    class RtdLmpNodeZoneHubParams(TypedDict, total=False):
        RTDTimestampFrom: datetime.datetime
        RTDTimestampTo: datetime.datetime
        repeatHourFlag: bool
        intervalIdFrom: int
        intervalIdTo: int
        intervalEndingFrom: datetime.datetime
        intervalEndingTo: datetime.datetime
        intervalRepeatHourFlag: bool
        settlementPoint: str
        settlementPointType: str
        LMPFrom: Decimal
        LMPTo: Decimal
        page: int
        size: int
        sort: str
        dir: str

    @staticmethod
    def rtd_lmp_node_zone_hub(
        *,
        RTDTimestampFrom: datetime.datetime | None = None,
        RTDTimestampTo: datetime.datetime | None = None,
        repeatHourFlag: bool | None = None,
        intervalIdFrom: int | None = None,
        intervalIdTo: int | None = None,
        intervalEndingFrom: datetime.datetime | None = None,
        intervalEndingTo: datetime.datetime | None = None,
        intervalRepeatHourFlag: bool | None = None,
        settlementPoint: str | None = None,
        settlementPointType: str | None = None,
        LMPFrom: Decimal | None = None,
        LMPTo: Decimal | None = None,
        page: int | None = None,
        size: int | None = None,
        sort: str | None = None,
        dir: str | None = None,
    ) -> dict:
        """RTD Indicative LMPs by Resource Nodes, Load Zones and Hubs"""
        return _get(
            "np6-970-cd/rtd_lmp_node_zone_hub",
            RTDTimestampFrom=RTDTimestampFrom,
            RTDTimestampTo=RTDTimestampTo,
            repeatHourFlag=repeatHourFlag,
            intervalIdFrom=intervalIdFrom,
            intervalIdTo=intervalIdTo,
            intervalEndingFrom=intervalEndingFrom,
            intervalEndingTo=intervalEndingTo,
            intervalRepeatHourFlag=intervalRepeatHourFlag,
            settlementPoint=settlementPoint,
            settlementPointType=settlementPointType,
            LMPFrom=LMPFrom,
            LMPTo=LMPTo,
            page=page,
            size=size,
            sort=sort,
            dir=dir,
        )
