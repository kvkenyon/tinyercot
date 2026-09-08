"""Typed public dashboard payloads; source labels and sections are preserved."""

import re
from datetime import date, datetime
from decimal import Decimal
from html.parser import HTMLParser
from typing import Generic, Literal, TypeVar, get_args

import httpx
from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

T = TypeVar("T", bound=BaseModel)


class DashboardModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RealTimeConditions(DashboardModel):
    """Public display readings; lastUpdated has no source UTC offset."""

    lastUpdated: datetime
    currentFrequency: Decimal = Field(alias="Current Frequency")
    instantaneousTimeError: Decimal = Field(alias="Instantaneous Time Error")
    consecutiveBaalExceedances: int = Field(
        alias="Consecutive BAAL Clock-Minute Exceedances (min)"
    )
    actualSystemDemand: Decimal = Field(alias="Actual System Demand")
    averageNetLoad: Decimal = Field(alias="Average Net Load")
    totalSystemCapacity: Decimal = Field(
        alias="Total System Capacity (not including Ancillary Services)"
    )
    totalWindOutput: Decimal = Field(alias="Total Wind Output")
    totalPvgrOutput: Decimal = Field(alias="Total PVGR Output")
    currentSystemInertia: Decimal = Field(alias="Current System Inertia")
    dcE: Decimal = Field(alias="DC_E (East)")
    dcL: Decimal = Field(alias="DC_L (Laredo VFT)")
    dcN: Decimal = Field(alias="DC_N (North)")
    dcR: Decimal = Field(alias="DC_R (Railroad)")
    dcS: Decimal = Field(alias="DC_S (Eagle Pass)")


class RealTimeLmp(DashboardModel):
    settlementPoint: str = Field(alias="Settlement Point")
    LMP: Decimal = Field(alias="LMP")
    lmpChange: Decimal = Field(alias="5 Min Change to LMP")
    lmpWithAdder: Decimal = Field(alias="RTRDPA + LMP")
    lmpWithAdderChange: Decimal = Field(alias="5 Min Change to RTRDPA + LMP")


class RealTimeLmpSnapshot(DashboardModel):
    """Published price components and five-minute changes; timestamp has no offset."""

    lastUpdated: datetime
    RTRDPA: Decimal
    data: list[RealTimeLmp]


HubOrLoadZone = Literal[
    "HB_BUSAVG",
    "HB_HOUSTON",
    "HB_HUBAVG",
    "HB_NORTH",
    "HB_PAN",
    "HB_SOUTH",
    "HB_WEST",
    "LZ_AEN",
    "LZ_CPS",
    "LZ_HOUSTON",
    "LZ_LCRA",
    "LZ_NORTH",
    "LZ_RAYBN",
    "LZ_SOUTH",
    "LZ_WEST",
]


class RtdInterval(DashboardModel):
    intervalId: int
    minutesAhead: int
    LMP: Decimal


class RtdRun(DashboardModel):
    RTDTimestamp: datetime
    actualLMP: Decimal
    intervals: list[RtdInterval]


class RtdSnapshot(DashboardModel):
    """Public RTD display; indicative interval prices include reliability adders."""

    settlementPoint: HubOrLoadZone
    lastSCEDTimestamp: datetime
    includesReliabilityAdder: Literal[True] = True
    data: list[RtdRun]


DisplaySeries = TypeVar("DisplaySeries", bound=str)
AncillaryPriceSeries = Literal["NON-SPIN", "REG-DOWN", "REG-UP", "RRS", "ECRS"]
ForecastLoadSeries = Literal["NORTH", "SOUTH", "WEST", "HOUSTON", "TOTAL"]
WeatherLoadSeries = Literal[
    "COAST",
    "EAST",
    "FAR_WEST",
    "NORTH",
    "NORTH_C",
    "SOUTHERN",
    "SOUTH_C",
    "WEST",
    "TOTAL",
]


class MarketDisplayRow(DashboardModel, Generic[DisplaySeries]):
    """One source period; literal ending labels retain repeated-hour markers."""

    operatingDay: date
    periodEnding: str
    values: dict[DisplaySeries, Decimal]


class MarketDisplay(DashboardModel, Generic[DisplaySeries]):
    """Published table, without inferred time zone or repeated-hour flags."""

    operatingDay: date
    lastUpdated: datetime
    periodType: Literal["Hour Ending", "Interval Ending"]
    data: list[MarketDisplayRow[DisplaySeries]]


class _DisplayTable(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.operating_day: date | None = None
        self.values: dict[str, str | datetime] = {}
        self.cells: list[str] = []
        self.rows: list[list[str]] = []
        self.tag: str | None = None
        self.text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "input" and dict(attrs).get("id") == "currentDate":
            self.operating_day = datetime.strptime(  # noqa: DTZ007
                dict(attrs).get("value") or "", "%m/%d/%Y"
            ).date()
        if tag == "tr":
            self.cells = []
        if tag == "br" and self.tag:
            self.text += " "
        classes = (dict(attrs).get("class") or "").split()
        if (
            tag in ("td", "th")
            or (tag == "div" and "schedTime" in classes)
            or (tag == "option" and "selected" in dict(attrs))
        ):
            self.tag, self.text = tag, ""

    def handle_data(self, data: str) -> None:
        if self.tag:
            self.text += data

    def handle_endtag(self, tag: str) -> None:
        if tag == self.tag:
            text = " ".join(self.text.split())
            if tag in ("td", "th"):
                self.cells.append(text)
            elif tag == "option":
                self.values["settlementPoint"] = text
            else:
                label, timestamp = text.split(": ", 1)
                key = {
                    "Last Updated": "lastUpdated",
                    "Last Date and Time": "lastUpdated",
                    "Last SCED Date and Time": "lastSCEDTimestamp",
                }[label]
                # The public display supplies no UTC offset, including at DST folds.
                self.values[key] = datetime.strptime(  # noqa: DTZ007
                    timestamp,
                    "%b %d, %Y %H:%M:%S"
                    if timestamp.count(":") == 2
                    else "%b %d, %Y %H:%M",
                )
            self.tag = None
        if tag == "tr" and self.cells:
            self.rows.append(self.cells)
            self.cells = []


class FuelMixValues(DashboardModel):
    coal_and_lignite: Decimal = Field(alias="Coal and Lignite")
    hydro: Decimal = Field(alias="Hydro")
    nuclear: Decimal = Field(alias="Nuclear")
    other: Decimal = Field(alias="Other")
    power_storage: Decimal = Field(alias="Power Storage")
    solar: Decimal = Field(alias="Solar")
    wind: Decimal = Field(alias="Wind")
    natural_gas: Decimal = Field(alias="Natural Gas")


class GridCondition(DashboardModel):
    condition_note: str
    eea_level: int
    energy_level_value: int
    state: str
    title: str
    prc_value: str
    index: int
    datetime: int


class PrcRow(DashboardModel):
    timestamp: str
    epoch: int
    interval: str
    dstFlag: str
    prc: int


class EsrRow(DashboardModel):
    tagCLastTime: str
    dstFlag: str
    totalCharging: Decimal
    totalDischarging: Decimal
    netOutput: Decimal
    timestamp: datetime
    epoch: int


class EsrDay(DashboardModel):
    dayDate: str
    data: tuple[EsrRow, ...]


class OutageAmounts(DashboardModel):
    unplanned: int
    planned: int
    total: int


class GenerationOutageRow(DashboardModel):
    deliveryTime: str
    dstFlag: str
    combined: OutageAmounts = Field(alias="Combined")
    dispatchable: OutageAmounts = Field(alias="Dispatchable")
    renewable: OutageAmounts = Field(alias="Renewable")


class OutageDays(DashboardModel):
    previous: tuple[str, ...]
    current: tuple[str, ...]


class DcTieRow(DashboardModel):
    currentFrequency: Decimal
    currentSystemInertia: int
    dcE: int
    dcN: int
    dcL: int
    dcR: int
    timestamp: str
    epoch: int
    interval: str
    dstFlag: str


class DashboardPrices(DashboardModel):
    hbBusAvg: Decimal
    hbHubAvg: Decimal
    hbHouston: Decimal
    hbNorth: Decimal
    hbPan: Decimal
    hbSouth: Decimal
    hbWest: Decimal
    lzAen: Decimal
    lzCps: Decimal
    lzHouston: Decimal
    lzLcra: Decimal
    lzNorth: Decimal
    lzRaybn: Decimal
    lzSouth: Decimal
    lzWest: Decimal
    dstFlag: str
    timestamp: str
    interval: int


class RealTimeDashboardPrice(DashboardPrices):
    intervalEnding: str


class DayAheadDashboardPrice(DashboardPrices):
    hourEnding: int


class SupplyObservation(DashboardModel):
    capacity: int
    demand: int
    dstFlag: int
    interval: int
    hourEnding: int
    timestamp: str
    epoch: int


class SupplyActualRow(SupplyObservation):
    forecast: Literal[0]


class SupplyForecastRow(SupplyObservation):
    forecast: Literal[1]
    available: int


class SupplyOutlookRow(DashboardModel):
    deliveryDate: str
    dstFlag: str
    hourEnding: int
    deliveryDateHrBegin: str
    deliveryDateHrEnd: str
    availCapGen: int
    forecastedDemand: int
    timestamp: str
    epoch: int


class FuelGeneration(DashboardModel):
    gen: Decimal


class FuelMixSnapshot(DashboardModel):
    lastUpdated: datetime
    monthlyCapacity: FuelMixValues
    data: dict[date, dict[datetime, dict[str, FuelGeneration]]]


class GridConditionsSnapshot(DashboardModel):
    lastUpdated: datetime
    current_condition: GridCondition
    data: list[PrcRow]


class EsrSnapshot(DashboardModel):
    lastUpdated: datetime
    previousDay: EsrDay
    currentDay: EsrDay


class GenerationOutagesSnapshot(DashboardModel):
    lastUpdated: datetime
    currentOutages: int
    days: OutageDays
    types: list[str]
    current: dict[str, GenerationOutageRow]
    previous: dict[str, GenerationOutageRow]


class DcTieSnapshot(DashboardModel):
    lastUpdated: datetime
    data: list[DcTieRow]


class SystemPricesSnapshot(DashboardModel):
    lastUpdated: datetime
    rtSppData: list[RealTimeDashboardPrice]
    damSppData: list[DayAheadDashboardPrice]


class SupplyDemandSnapshot(DashboardModel):
    lastUpdated: datetime
    data: list[SupplyActualRow | SupplyForecastRow]
    forecast: list[SupplyOutlookRow]


class WindSolarRow(DashboardModel):
    hourEnding: int
    dstFlag: str
    actualWind: Decimal | None
    actualSolar: Decimal | None = None
    copHslWind: Decimal
    stwpf: Decimal
    wgrpp: Decimal
    copHslWindDayAhead: Decimal | None
    stwpfDayAhead: Decimal | None
    wgrppDayAhead: Decimal | None
    copHslSolar: Decimal
    stppf: Decimal
    pvgrpp: Decimal
    copHslSolarDayAhead: Decimal | None
    stppfDayAhead: Decimal | None
    pvgrppDayAhead: Decimal | None
    timestamp: datetime
    epoch: int


class WindSolarDay(DashboardModel):
    date: datetime
    data: dict[str, WindSolarRow]


class WindSolarSnapshot(DashboardModel):
    lastUpdated: datetime
    currentDay: WindSolarDay
    nextDay: WindSolarDay


class DemandRow(DashboardModel):
    hourEnding: int
    dstFlag: str
    currentLoadForecast: Decimal
    dayAheadForecast: Decimal | None = None
    currentDayHsl: Decimal | None = None
    dayAheadHsl: Decimal | None = None
    systemLoad: Decimal | None = None
    timestamp: datetime
    epoch: int


class DemandDay(DashboardModel):
    dayDate: datetime
    data: list[DemandRow]


class DemandSnapshot(DashboardModel):
    lastUpdated: datetime
    previousDay: DemandDay
    currentDay: DemandDay
    nextDay: DemandDay


class FrequencyRow(DashboardModel):
    timestamp: datetime
    interval: int
    dstFlag: str
    currentFrequency: Decimal


class AncillaryRow(DashboardModel):
    timestamp: datetime
    interval: int
    dstFlag: str
    deployedRegUp: int
    undeployedRegUp: int
    deployedRegDown: int
    undeployedRegDown: int
    rrs: int
    nsrs: int
    ecrs: int


class AncillarySnapshot(DashboardModel):
    lastUpdated: datetime
    data: list[FrequencyRow]
    ascapmon: list[AncillaryRow]
    lastDeployedRegUp: int
    lastUndeployedRegDown: int
    lastRrs: int
    lastNsrs: int
    lastDeployedRegDown: int
    lastUndeployedRegUp: int
    lastEcrs: int


class ScedCapacityRow(DashboardModel):
    timestamp: datetime
    epoch: int
    dstFlag: str
    increaseGenResESRs: Decimal
    decreaseGenResESRs: Decimal


class ScedCapacityDay(DashboardModel):
    timestamp: datetime
    data: list[ScedCapacityRow]


class ScedCapacitySnapshot(DashboardModel):
    lastUpdated: datetime
    current: ScedCapacityDay
    previous: ScedCapacityDay


class _CapacityGroup(DashboardModel):
    @model_validator(mode="before")
    @classmethod
    def _key_value_table(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        if not value or value[0] != ["key", "value"]:
            raise ValueError("Expected a capacity table with key/value headers")
        fields: dict[str, object] = {}
        for row in value[1:]:
            if not isinstance(row, (list, tuple)) or len(row) != 2:
                raise ValueError("Expected a capacity key/value pair")
            key, amount = row
            if not isinstance(key, str) or key in fields:
                raise ValueError("Capacity keys must be distinct strings")
            fields[key] = amount
        return fields


class ResponsiveReserveCapability(_CapacityGroup):
    rrcCapPfrGenEsr: Decimal
    rrcCapLrWoClr: Decimal
    rrcCapLr: Decimal
    rrcCapFfr: Decimal
    rrcCapFfrEsr: Decimal


class ResponsiveReserveAwards(_CapacityGroup):
    rrAwdGen: Decimal
    rrAwdNonClr: Decimal
    rrAwdClr: Decimal
    rrAwdFfr: Decimal


class ContingencyReserveCapability(_CapacityGroup):
    ecrsCapGen: Decimal
    ecrsCapNclr: Decimal
    ecrsCapClr: Decimal
    ecrsCapQs: Decimal
    ecrsCapEsr: Decimal
    ecrsCapDeployedGenLr: Decimal


class ContingencyReserveAwards(_CapacityGroup):
    ecrsAwdGen: Decimal
    ecrsAwdNonClr: Decimal
    ecrsAwdClr: Decimal
    ecrsAwdQs: Decimal
    ecrsAwdEsr: Decimal


class NonSpinReserveCapability(_CapacityGroup):
    nsrCapOnGenWoEo: Decimal
    nsrCapOffResWOs: Decimal
    nsrCapUndeployedLr: Decimal
    nsrCapOffGen: Decimal
    nsrCapEsr: Decimal


class NonSpinReserveAwards(_CapacityGroup):
    nsrAwdGenWEo: Decimal
    nsrAwdGenWOs: Decimal
    nsrAwdLr: Decimal
    nsrAwdOffGen: Decimal
    nsrAwdQs: Decimal
    nsrAwdAs: Decimal


class RegulationCapacity(_CapacityGroup):
    regUpCap: Decimal
    regDownCap: Decimal
    regUpUndeployed: Decimal
    regDownUndeployed: Decimal
    regUpDeployed: Decimal
    regDownDeployed: Decimal


class RegulationAwards(_CapacityGroup):
    regUpAwd: Decimal
    regDownAwd: Decimal


class SystemAvailableCapacity(_CapacityGroup):
    capClrDecreaseBp: Decimal
    capClrIncreaseBp: Decimal
    capWEoIncreaseBp: Decimal
    capWEoDecreaseBp: Decimal
    capWoEoIncreaseBp: Decimal
    capWoEoDecreaseBp: Decimal
    esrCapWEoIncreaseBp: Decimal
    esrCapWEoDecreaseBp: Decimal
    esrCapWoEoIncreaseBp: Decimal
    esrCapWoEoDecreaseBp: Decimal
    capIncreaseGenBp: Decimal
    capDecreaseGenBp: Decimal
    sumCapResRegUpRrs: Decimal
    sumCapResRegUpRrsEcrs: Decimal
    sumCapResRegUpRrsEcrsNsr: Decimal


class PhysicalResponsiveCapability(_CapacityGroup):
    prc: Decimal


class OperatingReserveDemandCurveCapacity(_CapacityGroup):
    rtReserveOnline: Decimal
    rtReserveOnOffline: Decimal


class EmergencyOutageCapacity(_CapacityGroup):
    telemHslEmr: Decimal
    telemHslOut: Decimal
    telemHslOutl: Decimal


class AncillaryCapacityData(DashboardModel):
    responsiveReserveCapabilityGroup: ResponsiveReserveCapability
    responsiveReserveAwardsGroup: ResponsiveReserveAwards
    ercotContingencyReserveCapabilityGroup: ContingencyReserveCapability
    ercotContingencyReserveAwardsGroup: ContingencyReserveAwards
    nonSpinReserveCapabilityGroup: NonSpinReserveCapability
    nonSpinReserveAwardsGroup: NonSpinReserveAwards
    regulationCapacityGroup: RegulationCapacity
    regulationAwardsGroup: RegulationAwards
    systemAvailableCapacityGroup: SystemAvailableCapacity
    ercotWidePhysicalResponsiveCapabilityGroup: PhysicalResponsiveCapability
    realTimeOperatingReserveDemandCurveCapacityGroup: (
        OperatingReserveDemandCurveCapacity
    )
    emrOutAndOutLCapacityGroup: EmergencyOutageCapacity


class AncillaryCapacitySnapshot(DashboardModel):
    lastUpdated: datetime
    epoch: int
    interval: str
    dstFlag: str
    data: AncillaryCapacityData


class CityWeather(DashboardModel):
    name: str
    y: int
    x: int
    low: int
    high: int
    low15yr: int
    high15yr: int
    icon: str


class WeatherForecast(DashboardModel):
    lastUpdated: datetime
    data: dict[str, CityWeather]


class WeatherForecasts(RootModel[list[WeatherForecast]]):
    pass


class Dashboards:
    def __init__(self, client: httpx.Client) -> None:
        self._http = client

    def _get(self, path: str, model: type[T]) -> T:
        response = self._http.get(
            f"https://www.ercot.com/api/1/services/read/dashboards/{path}.json"
        )
        response.raise_for_status()
        return model.model_validate(response.json(parse_float=Decimal))

    def fuel_mix(self) -> FuelMixSnapshot:
        return self._get("fuel-mix", FuelMixSnapshot)

    def grid_conditions(self) -> GridConditionsSnapshot:
        return self._get("daily-prc", GridConditionsSnapshot)

    def _html(self, name: str) -> _DisplayTable:
        response = self._http.get(f"https://www.ercot.com/content/cdr/html/{name}.html")
        response.raise_for_status()
        parser = _DisplayTable()
        parser.feed(response.text)
        parser.close()
        return parser

    def real_time_conditions(self) -> RealTimeConditions:
        """Read the public system-conditions table, including time error and BAAL."""
        parser = self._html("real_time_system_conditions")
        for cells in parser.rows:
            if len(cells) == 1:  # Section heading.
                continue
            if len(cells) != 2 or cells[0] in parser.values:
                raise ValueError("Expected distinct system-condition label/value rows")
            parser.values[cells[0]] = cells[1]
        return RealTimeConditions.model_validate(parser.values)

    def real_time_lmps(self, *, hubs_and_zones: bool = False) -> RealTimeLmpSnapshot:
        """Latest published LMPs, separate reliability adder and five-minute changes."""
        parser = self._html("hb_lz" if hubs_and_zones else "current_np6788")
        if len(parser.rows) < 2:
            raise ValueError("No real-time LMP table in the public display")
        adder, headers, *rows = parser.rows
        if (
            len(adder) != 2
            or adder[0] != "Price Adders"
            or not adder[1].startswith("RTRDPA: $")
        ):
            raise ValueError("Unrecognized real-time price-adder heading")
        expected = {field.alias for field in RealTimeLmp.model_fields.values()}
        if len(headers) != len(expected) or set(headers) != expected:
            raise ValueError("Unrecognized real-time LMP columns")
        return RealTimeLmpSnapshot.model_validate(
            {
                **parser.values,
                "RTRDPA": Decimal(adder[1].removeprefix("RTRDPA: $")),
                "data": [
                    RealTimeLmp.model_validate(dict(zip(headers, row, strict=True)))
                    for row in rows
                ],
            }
        )

    def indicative_prices(
        self, settlement_point: HubOrLoadZone = "HB_BUSAVG"
    ) -> RtdSnapshot:
        """Recent RTD runs and published horizons, including reliability adders."""
        if settlement_point not in get_args(HubOrLoadZone):
            raise ValueError("Expected a published hub or load zone")
        suffix = "" if settlement_point == "HB_BUSAVG" else f"_{settlement_point}"
        parser = self._html(f"rtd_ind_lmp_lz_hb{suffix}")
        if parser.values.get("settlementPoint") != settlement_point:
            raise ValueError(
                "The RTD display does not match the requested settlement point"
            )
        if (
            not parser.rows
            or len(parser.rows[0]) < 3
            or parser.rows[0][:2] != ["RTD Date and Time", "Actual LMP"]
        ):
            raise ValueError("No recognized RTD price table in the public display")
        horizons = []
        for header in parser.rows[0][2:]:
            match = re.fullmatch(r"RTD Int (\d+) \(Time\+(\d+)\)", header)
            if match is None:
                raise ValueError(f"Unrecognized RTD horizon: {header}")
            horizons.append((int(match[1]), int(match[2])))
        runs = []
        for row in parser.rows[1:]:
            runs.append(
                RtdRun(
                    # The source supplies neither an offset nor a repeated-hour flag.
                    RTDTimestamp=datetime.strptime(row[0], "%m/%d/%Y %H:%M:%S"),  # noqa: DTZ007
                    actualLMP=Decimal(row[1]),
                    intervals=[
                        RtdInterval(
                            intervalId=index, minutesAhead=minutes, LMP=Decimal(price)
                        )
                        for (index, minutes), price in zip(
                            horizons, row[2:], strict=True
                        )
                    ],
                )
            )
        return RtdSnapshot.model_validate({**parser.values, "data": runs})

    def _market_display(
        self,
        name: str,
        operating_day: date | None,
        model: type[MarketDisplay[DisplaySeries]],
        series: tuple[str, ...],
        period: Literal["Hour Ending", "Interval Ending"],
    ) -> MarketDisplay[DisplaySeries]:
        prefix = f"{operating_day:%Y%m%d}_" if operating_day is not None else ""
        parser = self._html(prefix + name)
        if operating_day is not None and parser.operating_day != operating_day:
            raise ValueError("The display does not match the requested operating day")
        if not parser.rows:
            raise ValueError("No published market table in the public display")
        headers, *rows = parser.rows
        if (
            headers[:2] != ["Oper Day", period]
            or len(headers[2:]) != len(series)
            or set(headers[2:]) != set(series)
        ):
            raise ValueError("Unrecognized market display columns")
        data = []
        for cells in rows:
            values = dict(zip(headers, cells, strict=True))
            day = datetime.strptime(values.pop("Oper Day"), "%m/%d/%Y").date()  # noqa: DTZ007
            if day != parser.operating_day:
                raise ValueError("Row operating day differs from the display heading")
            data.append(
                {
                    "operatingDay": day,
                    "periodEnding": values.pop(period),
                    "values": values,
                }
            )
        return model.model_validate(
            {
                "operatingDay": parser.operating_day,
                "lastUpdated": parser.values.get("lastUpdated"),
                "periodType": period,
                "data": data,
            }
        )

    def day_ahead_prices(
        self, operating_day: date | None = None
    ) -> MarketDisplay[HubOrLoadZone]:
        """Hourly hub/load-zone settlement prices from the anonymous DAM display."""
        return self._market_display(
            "dam_spp",
            operating_day,
            MarketDisplay[HubOrLoadZone],
            get_args(HubOrLoadZone),
            "Hour Ending",
        )

    def real_time_prices(
        self, operating_day: date | None = None
    ) -> MarketDisplay[HubOrLoadZone]:
        """Settlement interval prices, including reliability deployment price adders."""
        return self._market_display(
            "real_time_spp",
            operating_day,
            MarketDisplay[HubOrLoadZone],
            get_args(HubOrLoadZone),
            "Interval Ending",
        )

    def day_ahead_ancillary_prices(
        self, operating_day: date | None = None
    ) -> MarketDisplay[AncillaryPriceSeries]:
        """Hourly DAM clearing prices for the five published ancillary services."""
        return self._market_display(
            "dam_mcpc",
            operating_day,
            MarketDisplay[AncillaryPriceSeries],
            get_args(AncillaryPriceSeries),
            "Hour Ending",
        )

    def actual_forecast_zone_load(
        self, operating_day: date | None = None
    ) -> MarketDisplay[ForecastLoadSeries]:
        """Hourly actual load by forecast zone and the separately published total."""
        return self._market_display(
            "actual_loads_of_forecast_zones",
            operating_day,
            MarketDisplay[ForecastLoadSeries],
            get_args(ForecastLoadSeries),
            "Hour Ending",
        )

    def actual_weather_zone_load(
        self, operating_day: date | None = None
    ) -> MarketDisplay[WeatherLoadSeries]:
        """Hourly actual load by weather zone and the separately published total."""
        return self._market_display(
            "actual_loads_of_weather_zones",
            operating_day,
            MarketDisplay[WeatherLoadSeries],
            get_args(WeatherLoadSeries),
            "Hour Ending",
        )

    def energy_storage(self) -> EsrSnapshot:
        return self._get("energy-storage-resources", EsrSnapshot)

    def generation_outages(self) -> GenerationOutagesSnapshot:
        return self._get("generation-outages", GenerationOutagesSnapshot)

    def dc_tie_flows(self) -> DcTieSnapshot:
        return self._get("dc-tie-flows", DcTieSnapshot)

    def system_prices(self) -> SystemPricesSnapshot:
        return self._get("system-wide-prices", SystemPricesSnapshot)

    def supply_demand(self) -> SupplyDemandSnapshot:
        return self._get("supply-demand", SupplyDemandSnapshot)

    def combined_wind_solar(self) -> WindSolarSnapshot:
        return self._get("combine-wind-solar", WindSolarSnapshot)

    def system_demand(self) -> DemandSnapshot:
        return self._get("system-wide-demand", DemandSnapshot)

    def ancillary_services(self) -> AncillarySnapshot:
        return self._get("ancillary-services", AncillarySnapshot)

    def sced_capacity(self) -> ScedCapacitySnapshot:
        """Current and previous day capacity to increase/decrease SCED base points, MW."""
        return self._get("capacity-available-sced", ScedCapacitySnapshot)

    def ancillary_capacity(self) -> AncillaryCapacitySnapshot:
        """Current reserve capability, awards and available capacity by source group, MW."""
        return self._get(
            "ancillary-service-capacity-monitor", AncillaryCapacitySnapshot
        )

    def weather_forecast(self) -> list[WeatherForecast]:
        return self._get("weather-forecast", WeatherForecasts).root

    def price_map(self, *, legend: bool = False) -> bytes:
        """Return ERCOT's current real-time locational price map as PNG bytes."""
        name = "rtmLmpLegend" if legend else "rtmLmp"
        response = self._http.get(
            f"https://www.ercot.com/content/cdr/contours/{name}.png"
        )
        response.raise_for_status()
        return response.content
