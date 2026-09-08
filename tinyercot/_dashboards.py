"""Typed public dashboard payloads; source labels and sections are preserved."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, TypeVar

import httpx
from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

T = TypeVar("T", bound=BaseModel)


class DashboardModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


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
    copHslWindDayAhead: Decimal
    stwpfDayAhead: Decimal
    wgrppDayAhead: Decimal
    copHslSolar: Decimal
    stppf: Decimal
    pvgrpp: Decimal
    copHslSolarDayAhead: Decimal
    stppfDayAhead: Decimal
    pvgrppDayAhead: Decimal
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
    dayAheadForecast: Decimal
    currentDayHsl: Decimal | None = None
    dayAheadHsl: Decimal
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
