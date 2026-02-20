from enum import Enum
from pandas import DataFrame
from app.etl.data.base_data_types import IExtractor, FieldPathBase
from app.etl.data.remote.gee.google_earth_api_data_collector import (
    GoogleEarthAPIDataCollector,
)


class RemoteDataTypes(Enum):
    """Remote Types"""
    GEE = "gee"


class GEEDataExtractor(FieldPathBase, IExtractor):
    def __init__(self, path: str):
        FieldPathBase.__init__(self, path)
        self.path_parts = self.path.split("|")
        # path_parts[0] = project ID, path_parts[1] = dataset/satellite
        self.gee_api_collector = GoogleEarthAPIDataCollector(projectname=self.path_parts[0])

    def extract(self) -> DataFrame:
        return self.gee_api_collector.collect(
            satellite=self.path_parts[1],
            start_date=self.path_parts[2],
            end_date=self.path_parts[3],
            longitude=float(self.path_parts[4]),
            latitude=float(self.path_parts[5]),
            scale=float(self.path_parts[6]),
        )