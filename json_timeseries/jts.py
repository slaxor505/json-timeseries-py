import json
import uuid
from datetime import datetime
from typing import Union, List

from dateutil import parser

TimeSeriesDataType = ('NUMBER', 'TEXT', 'TIME', 'COORDINATES')



class TsRecord:
    """
    Record of TimeSeries object
    """
    def __init__(self, timestamp: datetime, value: Union[float, str, int], quality: int = None,
                 annotation: str = None):
        self.timestamp = timestamp
        self.value = value
        self.quality = quality
        self.annotation = annotation


def __datetimeconverter(m):
    if isinstance(m, datetime):
        return m.isoformat()


class TimeSeries:
    """
    TimeSeries object

    :param data_type: Type of time series. E.g.: 'NUMBER', 'TEXT', 'TIME', 'COORDINATES'
    :type data_type: str, optional
    :param records: List of records
    :type records: list, optional
    :param name: Time series name
    :type name: str
    :param identifier: Time series ID. Autogenerated as UUID4 if not specified
    :type identifier: str, optional
    """

    def __init__(self, name: str, units: str = None, identifier: str = str(uuid.uuid4()),
                 data_type: str = 'NUMBER',
                 records: Union[List[TsRecord], TsRecord] = None):
        self.identifier = identifier
        self.name = name
        self.units = units
        self.data_type = data_type

        if records is None:
            self.records = []
        elif isinstance(records, TsRecord):
            self.records = [records]
        elif isinstance(records, list) and all(isinstance(x, TsRecord) for x in records):
            self.records = records
        else:
            raise TypeError("'records' value must be TsRecord or List[TsRecord]")

    # def __eq__(self, other):
    #     return self.__dict__ is other.__dict__

    def insert(self, records: Union[TsRecord, List[TsRecord]]):

        if isinstance(records, list):
            self.records.extend(records)
        # single instance
        else:
            self.records.append(records)

    # def sort(self):
    #     pass
    #
    # def clone(self):
    #     # ITimeSeries<Type>;
    #     pass

    def __len__(self):
        return self.records.__len__()

    def toJSON(self) -> str:
        """
        Outputs JSON string
        """
        return json.dumps(self, default=__datetimeconverter)

# TODO METHODS to implement
#
#   def get_timestamps:
#
#   public sort (): TimeSeries<Type> {
#
#   public clone (): TimeSeries<Type> {
#
#   private recordToJSON (record: ITimeSeriesRecord<Type>): ITimeSeriesRecordJson<Type> {
#
#   private valueToJSON (value: Type | undefined): Type | undefined | string | null {
#
#   private cloneRecords (records: ITimeSeriesRecord<Type>[]): ITimeSeriesRecord<Type>[] {


class JtsDocument:
    """
    JTS document object

    :raise [TypeError]: [Value of 'series' must be types of TimeSeries or List[TimeSeries]]
    """

    """
    TODO Methods to implement

    // Output as stringified JSON
    jtsDocument.toString()

    // Clone document (also clones series)
    jtsDocument.clone()

    // Create a new jtsDocument from JSON
    const jtsDocument = JtsDocument.from('{"docType": "jts", ...}')

    Properties

    // Get JTS specification version number
    jtsDocument.version // 1

    // Get 
    jtsDocument.series // [timeseries1, timeseries2]
    """

    def __init__(self, series: Union[List[TimeSeries], TimeSeries] = None, version: str = "1.0"):
        # enforce accepted types
        if series is not None:
            if (not isinstance(series, list) and not isinstance(series, TimeSeries)) \
                    or (isinstance(series, list) and not all(isinstance(x, TimeSeries) for x in series)):
                raise TypeError("Value of 'series' must be types of TimeSeries or List[TimeSeries]")

        self.version = version

        if isinstance(series, list):
            self.series = series
        elif isinstance(series, TimeSeries):
            self.series = [series]
        else:
            self.series = []

    # def __eq__(self, other):
    #     return self.__dict__ is other.__dict__

    def addSeries(self, series: Union[List[TimeSeries], TimeSeries]):
        """
        Add single or multiple TimeSeries
        """
        if isinstance(series, list):
            self.series.extend(series)
        # single instance
        else:
            self.series.append(series)

    def __len__(self):
        return self.series.__len__()

    def toJSON(self) -> str:
        """
        Output as formatted JSON
        """
        return json.dumps(self.__build())

    def __build(self):
        doc = dict(docType='jts',
                   version=self.version)

        data = self.__get_data()
        if not data:
            raise Exception("Cannot build without jts 'data'")
        header = self.__get_header(data)
        if header:
            doc['header'] = header
        doc['data'] = data

        return doc

    def __get_header(self, data):
        return dict(startTime=data[0]['ts'],
                    endTime=data[-1]['ts'],
                    recordCount=len(data),
                    columns=self.__getHeaderColumns()
                    ) if data else None

    def __getHeaderColumns(self):
        column_map = {}
        for idx, s in enumerate(self.series):
            column_map[idx] = dict(
                id=s.identifier,
                name=s.name,
                dataType=s.data_type,
            )
            if s.units:
                column_map[idx]["units"] = s.units

        return column_map

    # build "data" section of the document
    def __get_data(self):
        record_map = {}
        for idx, s in enumerate(self.series):
            for r in s.records:
                if (r.value is None) and (r.annotation is None) and (r.quality is None):
                    continue
                key = r.timestamp.strftime('%s')  # epoch as key for the entry

                if not record_map.get(key):
                    record_map[key] = {"ts": r.timestamp.isoformat(), "f": {}}

                record_map[key]["f"][idx] = self.__getDataColumnFromRecord(r, s.data_type)  # dict of entry values

        # record_map_sorted = dict(sorted(record_map.items()))
        record_map_sorted = [x[1] for x in sorted(record_map.items())]  # use tuple here?

        return record_map_sorted

    def __getDataColumnFromRecord(self, r, data_type):

        column = {}
        v = r.value
        if v:
            if data_type == 'NUMBER':
                column["v"] = float(v)
            elif data_type == 'TEXT':
                column["v"] = str(v)

        # TODO other types below
        # case 'TIME': return { $time: (v as Date).toISOString?.() || 'invalid date' }
        # case 'COORDINATES': return { $coords: ((v as Array<number>).length === 2 ? v : []) }

        if r.quality:
            column["q"] = r.quality

        if r.annotation:
            column["a"] = r.annotation

        return column

    @staticmethod
    def fromJSON(json_str):
        json_obj = json.loads(json_str)

        jts_doc = JtsDocument(version=json_obj.get('version'))

        # build series from header columns
        for idx, c in json_obj['header']["columns"].items():
            jts_doc.addSeries(TimeSeries(
                identifier=c.get("id"),
                name=c.get("name"),
                data_type=c.get("dataType"),
                units=c.get("units"))
            )

        # add records to corresponding series
        for e in json_obj['data']:

            ts = parser.parse(e["ts"])
            f = e["f"]

            for i, r in f.items():
                jts_doc.series[int(i)].insert(
                    TsRecord(
                        timestamp=ts,
                        value=r.get('v'),
                        quality=r.get('q'),
                        annotation=r.get('a'))
                )
                # else:
                #     raise Exception("Data columns do not match Header columns")

        return jts_doc

    def getSeries(self, identifier: str) -> TimeSeries:
        """
        Get series by id
        :param identifier: 
        :type identifier: 
        :return: 
        :rtype: 
        """


        return next((x for x in self.series if x.identifier == identifier), None)

# TODO check if I need extra methods then publish and rewrite OPB API using the library
# TODO all type hints of public API
# TODO DOCS - read.me from eagle rewrite and any necessary docs