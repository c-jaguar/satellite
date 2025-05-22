from datetime import datetime
from functools import cache

import numpy as np
import pandas as pd
from case.basic import get_satellites_from_txt, timing
from skyfield.api import EarthSatellite, Time, load
from skyfield.positionlib import ICRF
from skyfield.toposlib import Topos


def get_decimal_degrees_from_dms(latitude_dms: tuple[int, int, int], longitude_dms: tuple[int, int, int])\
        -> tuple[float, float]:
    return (latitude_dms[0] + latitude_dms[1] / 60 + latitude_dms[2] / 3600,
            longitude_dms[0] + longitude_dms[1] / 60 + longitude_dms[2] / 3600)

def get_terminal(latitude: float, longitude: float) -> Topos:
    return Topos(latitude, longitude)


def get_time_range(start: str | datetime, end: str | datetime, time_stamps_count: int)\
        -> np.array:
    if isinstance(start, str):
        start = datetime.strptime(start, "%d.%m.%Y %H:%M:%S")
    if isinstance(end, str):
        end = datetime.strptime(end, "%d.%m.%Y %H:%M:%S")

    time_scale = load.timescale()
    return time_scale.linspace(time_scale.tt(*start.timetuple()[:6]), time_scale.tt(*end.timetuple()[:6]),
                                     time_stamps_count)

def angles_to_vector(alt: np.float32, az: np.float32) -> np.array:
    az_rad = np.deg2rad(az)
    alt_rad = np.deg2rad(alt)
    x = np.cos(alt_rad) * np.sin(az_rad)
    y = np.cos(alt_rad) * np.cos(az_rad)
    z = np.sin(alt_rad)
    return np.array([x, y, z])


class SatelliteTestUpward:
    def __init__(self, start_time: str, end_time: str, file_name: str, latitude_dms: tuple[int, int, int],
                 longitude_dms: tuple[int, int, int], visibility_angle: float,
                 time_stamps_count: int = 20) -> None:
        self._time_range = get_time_range(start_time, end_time, time_stamps_count)
        self._satellites = get_satellites_from_txt(file_name)
        self._terminal = get_terminal(*get_decimal_degrees_from_dms(latitude_dms, longitude_dms))
        self._visibility_angle = visibility_angle
        self._altitude_deg = 90. - visibility_angle

    def apply_at_time(self, satellite: EarthSatellite, time_: Time) -> ICRF:
        difference_vector = satellite - self._terminal
        return difference_vector.at(time_)

    @cache
    @timing
    def _satellite_difference_at_time(self) -> pd.DataFrame:
        data = [
            [x.tt_strftime("%d.%m.%Y %H:%M:%S"), self._satellites, x]
            for x in self._time_range
        ]
        df_0 = pd.DataFrame(data=data, columns=["time", "satellite", "tt_time"])
        df_0 = df_0.explode("satellite")
        df_0["difference_at_time"] = df_0.apply(lambda x: self.apply_at_time(x["satellite"], x["tt_time"]), axis=1)
        df_0["altaz"] = df_0["difference_at_time"].apply(lambda x: [y.degrees for y in x.altaz()[:-1]])
        return df_0

    @timing
    def _visible_at_time_range(self) -> pd.DataFrame:
        df_0 = self._satellite_difference_at_time()
        df_0["altitude"] = df_0["altaz"].apply(lambda x: x[0])
        df_1 = df_0[df_0["altitude"] >= self._altitude_deg]
        return df_1.copy()

    def visible_at_time_range_name(self) -> None:
        dataframe = self._visible_at_time_range()
        sat_unique = dataframe["satellite"].unique()
        print("count = ", len(sat_unique))
        print("visible_names = ", [sat.name for sat in sat_unique])

    def visible_at_time_range_closest(self) -> None:
        df_0 = self._visible_at_time_range()
        df_0["distance"] = df_0["difference_at_time"].apply(lambda x: x.distance().km)
        result = df_0[df_0["distance"] == df_0["distance"].min()].copy()
        result["name"] = result["satellite"].apply(lambda x: x.name)
        result["azimuth"] = result["altaz"].apply(lambda x: x[1])
        result = result.drop(columns=["difference_at_time", "tt_time", "satellite", "altaz"])
        print(result.to_string())

class SatelliteTestBeam(SatelliteTestUpward):
    def __init__(self, altitude_deg: np.float32, azimuth_deg: np.float32, **kwargs) -> None:  # noqa: ANN003
        super().__init__(**kwargs)
        self._altitude_deg = altitude_deg
        self._azimuth_deg = azimuth_deg
        self._beam_vector = angles_to_vector(self._altitude_deg, self._azimuth_deg)

    @timing
    def _visible_at_time_range(self) -> pd.DataFrame:
        df_0 = self._satellite_difference_at_time()
        df_0["angle"] = df_0["altaz"].apply(
            lambda x: np.rad2deg(np.arccos(np.dot(self._beam_vector, angles_to_vector(x[0], x[1])))))
        half_angle = self._visibility_angle / 2.
        df_1 = df_0[df_0["angle"] <= half_angle]
        return df_1.copy()

    def visible_at_time_range_closest(self) -> None:
        print("Not implemented")
