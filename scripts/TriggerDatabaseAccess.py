#!/usr/bin/env python

__doc__    = """Library to download the trigger database."""
__date__   = "Thu 13 Mar 2025"
__author__ = "Gianluca Petrillo (petrillo@slac.stanford.edu)"

import sqlalchemy as sql
import numpy, pandas
import datetime, os, time

DefaultConnectionSettings = {
  'database': 'icarus_trigger_prd',
  'username': 'triggerdb_reader',
  'password': '******',
  'host': 'ifdbdaqrep01.fnal.gov',
  'port': 5455
}

# ------------------------------------------------------------------------------
# ---  Selectors
# ------------------------------------------------------------------------------
# 
# Selectors apply a WHERE clause to the query.
# 
class SelectorClass:
    """Utility class collecting information about which rows to select in a table.

    The `selector` parameter is directly used for the selection, and it should take a SQLAlchemy table
    as argument and return an object suitable for the `.where()` function of a query execution.
    """
    def __init__(self, tag, selector = None, description = ""):
        self.tag = tag
        self.description = description
        self.selector = selector
    def select(self, table): return self.selector(table)
    def hasSelector(self): return self.selector is not None
    def getSelector(self): return self.selector
    def __call__(self, table): return self.select(table)
    def __str__(self): return self.description
    def __hash__(self): return hash(self.tag)    
# SelectorClass

def registerSelector(key = None, *args, **kwargs):
    """Constructs, registers into `Selectors` and returns a SelectorClassObject."""
    selector = SelectorClass(*args, **kwargs)
    Selectors[selector.tag if key is None else key] = selector
    return selector
# registerSelector()

def selectSingleRun(run: int) -> str:
    selector = registerSelector(
      tag=f'Run{run:05d}',
      description=f"Run {run}",
      selector=(lambda table: table.c.run_number == run),
      )
    return selector.tag
# selectSingleRun()


def selectRunRange(firstRun: int, lastRun: int) -> str:
    selector = registerSelector(
      tag=f'Run{firstRun:05d}' if firstRun == lastRun else f'Runs{firstRun:05d}-{lastRun:05d}',
      description=f"Runs {firstRun}-{lastRun}",
      selector=(lambda table: sql.between(table.c.run_number, firstRun, lastRun)),
      )
    return selector.tag
# selectRunRange()


def selectTimeRange(start: int, stop: int) -> str:
    selector = registerSelector(
      tag=f'Time{start:010d}+{stop-start:07d}',
      description=f"from {time.ctime(start)} for {stop-start} s",
      selector=(lambda table: sql.between(table.c.beam_seconds, start, stop)),
      )
    return selector.tag
# selectTimeRange()


# ------------------------------------------------------------------------------
# Here are the currently implemented ones
#

global Selectors
Selectors = {}

registerSelector(
  tag='NoCalib',
  description="All periods and exclude calibration gates",
  selector=lambda table: sql.between(table.c.gate_type, 1, 4), # not calibration gate
  ) # 'NoCalib'


registerSelector(
  tag='LightTriggersNoCalib',
  description="All periods, only light-based trigger (no minimum bias), and exclude calibration gates",
  selector=lambda table: sql.and_(
    sql.between(table.c.gate_type, 1, 4), # not calibration gate
    table.c.trigger_type == 0,            # light-based trigger
    ),
  ) # 'LightTriggersNoCalib'


registerSelector(
  tag='OnBeamStreams',
  description="All periods, only on-beam gates (BNB and NuMI)",
  selector=lambda table: sql.or_(
    table.c.gate_type == 1, # BNB
    table.c.gate_type == 2, # NuMI
    ),
  ) # 'LightTriggersNoCalib'

OneMonthAgo = datetime.datetime.fromtimestamp(int(datetime.datetime.now().timestamp() - 3600*30*24)).replace(hour=0, minute=0, second=0, microsecond=0)
startTAIsecond = int(OneMonthAgo.timestamp()) + 37
registerSelector(
  key='Last30days',
  tag=f'{format(OneMonthAgo, "%Y%m%d")}+30days',
  description=f"one month back from {format(datetime.date.today(), '%c')}",
  selector=(lambda table: table.c.beam_seconds >= startTAIsecond),
  ) # '30days'

registerSelector(
  tag='TestSelection',
  description="A single run",
  selector=(lambda table: table.c.run_number == 12345),
  ) # 'TestSelection'


# ------------------------------------------------------------------------------
# ---  Library
# ------------------------------------------------------------------------------
#
# The common functions to use are `fetchAvailableColumns()` and
# `loadOrReadTriggerDatabase()`.
#
def prepareTriggerDatabaseConnectionEngine(
  connectionSettings: dict = None,
  verbose: bool = False,
) -> sql.Engine:
    """Prepares the SQL connection needed to fetch the database.

    :param connectionSettings: override the specified connection settings
      (see the global variable `DefaultConnectionSettings` in the source code).
      Most commonly overridden elements: `password`, `host`, `port`.

    :param verbose: enable additional messages on log

    :return the created SQL DB engine
    """

    DBconnSettings = DefaultConnectionSettings.copy()
    DBconnSettings.update(connectionSettings)
    
    # create the "engine" which will initiate the connections.
    DBconnectionURL = sql.URL.create('postgresql+psycopg', **DBconnSettings)
    DBengine = sql.create_engine(DBconnectionURL, echo=verbose)

    return DBengine
# prepareTriggerDatabaseConnectionEngine()


def prepareTriggerDatabaseTable(
  columns: list[str] or None,
  connectionSettings: dict or None = None,
  tableName: str = 'triggerdata',
  verbose: bool = False,
  createEngine: bool or None = None,
  metadata: sql.MetaData or None = None,
) -> ( sql.Table, sql.MetaData, sql.Engine ):
    """Prepares the SQL table object needed to fetch the database.

    If no column is specified, the table schema will be loaded from the database.
    For this reason, database connection information may be needed.

    If the `createEngine` argument is set to `True`, an database engine will be created and eventually returned.
    If the `createEngine` argument is set to `False`, an database engine will never be created, None will be returned,
    and if the engine would be needed, an exception is raised.
    The `createEngine` parameter can be `None`, in which case the engine is created only if needed
    (that is, if `columns` is specified).
    
    :param columns: name of the columns to fetch from the database (None for all).
      Columns with name ending in '@text' will be loaded as text.
    :type columns: list[str] or None

    :param connectionSettings: override the specified connection settings
      (see the internal variable `DefaultConnectionSettings` in the source code).
      Most commonly overridden elements: `password`, `host`, `port`.

    :param tableName: name of the database table.

    :param verbose: enable additional messages on log and on console

    :param createEngine: whether to create a database engine object (None: only if needed)

    :param metadata: SQL metadata object (optional; a new one will be created and returned if None)

    :return the SQL table object, the metadata object and the DB engine created to fetch it (may be None)
    
    """

    if createEngine is None:
        createEngine = not bool(columns)
    elif not createEngine:
        if not columns: raise RuntimeError("We need to create a database engine in order to get the table structure.")

    DBengine = prepareTriggerDatabaseConnectionEngine(connectionSettings, verbose=verbose) if createEngine else None

    # create a `MetaData` object (a glorified table dictionary) and register _the_ table into it
    DBmetadata = sql.MetaData() if metadata is None else metadata

    if columns:
        primaryKeys = { 'run_number', 'event_no' }
        table = sql.Table(
          tableName, DBmetadata,
          *[ sql.Column(
              colName.split('@')[0],
              sql.Text if colName.endswith('@text') else sql.Integer,
              primary_key=(colName.split('@')[0] in primaryKeys),
              nullable=False,
              )
            for colName in columns
            ],
          )
    else: # load everything, yeah
        table = sql.Table(tableName, DBmetadata, autoload_with=DBengine)

    return table, DBmetadata, DBengine
# prepareTriggerDatabaseTable()


def triggerDatabaseFileBaseName(
  triggerDataTable: sql.Table,
  selector: SelectorClass or str or None,
  date: datetime.date or str or None = None,
) -> str:
    """Returns the base name to be used for a database with the specified characteristics.

    The `df` dataframe is saved into a pickle data file.
    The name of the data file includes:
      * a stem 'TriggerDatabase';
      * a date tag, in <year><month><day> format;
      * the column content registered in the SQL table, hashed;
      * the row `selection` tag.

    :param triggerDataTable: SQLAlchemy table the dataframe came from, used to encode the column information into the file name.
    :param selector: the selector used for the WHERE clause of the database query, or a string representing it
    :param date: the date the database was extracted on, either as `datetime.date` object or as a string (default is today)

    :return the name of the output file that was created
    """
    import hashlib
    columnContentTag = hashlib.md5(','.join(map(str, triggerDataTable.c.values())).encode('utf-8'), usedforsecurity=False).hexdigest()[:8].upper()
    if date is None: date = datetime.date.today()
    if isinstance(date, datetime.date): date = format(date, "%Y%m%d")
    try: selector = selector.tag
    except AttributeError: pass
    return f"TriggerDatabase{('-' + selector) if selector else ''}-{columnContentTag}-{date}"
# triggerDatabaseFileBaseName()


def downloadTriggerDatabaseData(
  triggerDataTable: sql.Table,
  DBengine: sql.Engine,
  selector: SelectorClass or None = None,
) -> pandas.DataFrame:
    """Downloads the data of the specified table using the specified DB engine.
    
    :param triggerDataTable: the SQL table object describing the table to download
    :param DBengine: the SQL DB engine to create connection to the database
    :param selector: class specifying the WHERE clause of the database query

    :return a Pandas dataframe with all the downloaded information
    """
    # data loading
    DBselector = sql.select(triggerDataTable)
    if selector.hasSelector():
        DBselector = DBselector.where(selector(triggerDataTable))
    
    with DBengine.connect() as DBconn:
        df = pandas.read_sql_query(DBselector, DBconn)
    
    return df
# downloadTriggerDatabaseData()


def triggerDatabaseTablePostprocessing(df: pandas.DataFrame) -> None:
    """Performs post-processing of the `df` table.

    Postprocessing performed:
     * timestamps are merged into 64-bit integers (e.g. `wr_seconds` becomes `wr_timestamp`)
     * data is sorted by run and event number
     * convenience column added: 'triggerFromBeamGate' [ns], if the ingredients are available (`wr` and `beam` timestamps)

    **The dataframe in argument is modified in place.**

    The function applied to an already post-processed dataframe is currently a no-op.

    :param df: the dataframe to be post-processed
    """

    # timestamp merge
    for colName in df.columns:
        if not colName.endswith('_seconds'): continue
        baseName = colName[:-len('_seconds')]
        if baseName + '_nanoseconds' not in df.columns: continue
        df[baseName + '_timestamp'] = df[baseName + "_seconds"] * 1_000_000_000 + df[baseName + "_nanoseconds"]
        del df[baseName + "_seconds"], df[baseName + "_nanoseconds"]
    # for columns

    # hex conversion (blanket: if it's an object type, interpret it as hex)
    for colName in df.columns:
        if type(df[colName].dtype) is not numpy.dtypes.ObjectDType: continue
        df[colName] = df[colName].apply(int, base=16)

    # sort; by trigger timestamp would also be ok, but we are not guaranteed there is any
    sortKeys = [ colName for colName in ( 'run_number', 'event_no' ) if colName in df.columns ]
    if not sortKeys and ('wr_timestamp' in df.columns): sortKeys = [ 'wr_timestamp' ]
    if sortKeys: df.sort_values(sortKeys, inplace=True, ignore_index=True)

    # convenience columns
    if 'beam_timestamp' in df.columns and 'wr_timestamp' in df.columns and 'triggerFromBeamGate' not in df.columns:
        df['triggerFromBeamGate'] = df.wr_timestamp - df.beam_timestamp
        
    # deliberately not returning df to make it clear that it is post-processed in place
    # (that also means that `df` should not be a transient object)
# triggerDatabaseTablePostprocessing()


def loadTriggerDatabase(
  columns: list[str] or None,
  connectionSettings: dict = None,
  selector: SelectorClass = None,
  tableName: str = 'triggerdata',
  verbose: bool = False
) -> pandas.DataFrame:
    """Loads the trigger table from the database.

    It just joins `prepareTriggerDatabaseTable()` and `fetchTriggerDatabaseTable()`.

    Postprocessing is also performed:
     * timestamps are merged into 64-bit integers (e.g. `wr_seconds` becomes `wr_timestamp`)
     * data is sorted by run and event number

    :param columns: name of the columns to fetch from the database (None for all).
      Columns with name ending in '@text' will be loaded as text.
    :type columns: list[str] or None

    :param connectionSettings: override the specified connection settings
      (see the internal variable `DefaultConnectionSettings` in the source code).
      Most commonly overridden elements: `password`, `host`, `port`.

    :param tableName: name of the database table.

    :param verbose: enable additional messages on log and on console

    :return a Pandas dataframe with all the information loaded, one per event, sorted by run:event
    
    """

    triggerDataTable, DBmetadata, DBengine = prepareTriggerDatabaseTable(
      columns=columns, connectionSettings=connectionSettings, tableName=tableName,
      verbose=verbose, createEngine=True,
      )

    df = downloadTriggerDatabaseData(triggerDataTable, DBengine, selector=selector)
    
    triggerDatabaseTablePostprocessing(df)

    return df
# loadTriggerDatabase()


def saveTriggerDatabase(
  df: pandas.DataFrame,
  triggerDataTable: sql.Table,
  selector: SelectorClass or str or None,
  format_: str = '.gz',
  date: datetime.date or str or None = None,
) -> str:
    """Serializes the specified trigger database dataframe into a pickled file.

    The `df` dataframe is saved into a pickle data file.
    The name of the data file includes:
      * a stem 'TriggerDatabase';
      * a date tag, in <year><month><day> format;
      * the column content registered in the SQL table, hashed;
      * the row `selection` tag.

    :param df: dataframe with the database content to serialize.
    :param triggerDataTable: SQLAlchemy table the dataframe came from, used to encode the column information into the file name.
    :param selector: the selector used for the WHERE clause of the database query, or a string representing it
    :param format: the output file compression format (among the ones supported by `pandas.DataFrame.to_pickle`)
    :param date: the date the database was extracted on, either as `datetime.date` object or as a string (default is today)

    :return the name of the output file that was created
    """

    if format_ and (format_[0] != '.'): format_ = '.' + format_
    localDatabaseFile = triggerDatabaseFileBaseName(triggerDataTable, selector=selector, date=date) + '.pickle' + format_
    df.to_pickle(localDatabaseFile)
    return localDatabaseFile
# saveTriggerDatabase()


def loadOrReadTriggerDatabase(
  columns: list[str] or None,
  connectionSettings: dict = None,
  selector: SelectorClass = None,
  tableName: str = 'triggerdata',
  databaseDir: str or os.PathLike = ".",
  verbose: bool = False,
  forceToday: bool = False,
  forceReprocessing: bool = False,
  saveFormat: str or None = '.gz',
):
    """Returns the trigger database with the specified columns and selection.

    :param columns: name of the columns to fetch from the database (None for all).
      Columns with name ending in '@text' will be loaded as text.
    
    :param connectionSettings: override the specified connection settings
      (see the internal variable `DefaultConnectionSettings` in the source code).
      Most commonly overridden elements: `password`, `host`, `port`.

    :param selector: class specifying the WHERE clause of the database query
    
    :param tableName: name of the database table.

    :param databaseDir: directory where to look for and where to save local database copies
    
    :param verbose: enable additional messages on log and on console

    :param forceToday: require that the local database is tagged as coming from today, otherwise download it anew

    :param forceReprocessing: rerun post-processing even if the content was loaded
      from an already post-processed local copy. Useful, together with `saveFormat`,
      to update the local database after a (backward-compatible) change in reprocessing.
    
    :param saveFormat: the compression format to use when writing the pickled Pandas dataframe into a file.
      Specifying it empty still forces writing a (uncompressed) file, while `None` will not save any local copy.

    :return tha Pandas dataframe with the database information
    """    
    doReprocessing = forceReprocessing
    
    # first we prepare the table; we may or may not need to access the database
    # (will not, if a `columns` list is specified)
    triggerDataTable, DBmetadata, DBengine = prepareTriggerDatabaseTable(
      columns=columns, connectionSettings=connectionSettings, tableName=tableName,
      verbose=verbose,
      )

    # try to get the data from a file
    customOutputFile = saveFormat and not saveFormat.startswith('.')
    if customOutputFile:
        availableFiles = []
        if os.path.exists(saveFormat): availableFiles.append(saveFormat)
    else:
        from pathlib import Path
        databaseDir = Path(databaseDir)
        DBfilePattern = triggerDatabaseFileBaseName(triggerDataTable, selector, date=None if forceToday else '*')
        availableFiles = list(databaseDir.glob(DBfilePattern + '.pickle*'))
    # if
    if availableFiles:
        # there is a database file we are interested into:
        # pick the "newest", meaning the one with the higher date tag
        availableFiles.sort(key=str)
        databaseFilePath = availableFiles[-1]
        print(f"Reading database from file '{databaseFilePath}'...")
        df = pandas.read_pickle(databaseFilePath)
    # if file was found
    else: 
        # nope, we need to load it from the DB server
        if not DBengine:
            DBengine = prepareTriggerDatabaseConnectionEngine(connectionSettings, verbose=verbose)
        
        print(f"Downloading data from database server...")
        df = downloadTriggerDatabaseData(triggerDataTable, DBengine, selector=selector)

        doReprocessing = True
    # if ... else

    if doReprocessing:
        print(f"Post-processing {len(df)} entries...")
        triggerDatabaseTablePostprocessing(df)
        if saveFormat is not None:
            if df.empty:
                print(f"Database not saved because empty.")
            else:
                if customOutputFile:
                    outputFile = saveFormat
                    df.to_pickle(outputFile)
                else:
                    outputFile = saveTriggerDatabase(df, triggerDataTable, selector=selector, format_=saveFormat, date=None)
                print(f"Database saved into '{outputFile}'.")
            # if data
        # if saving
    # if reprocessing
    
    return df
# loadOrReadTriggerDatabase()


def fetchAvailableColumns(
  connectionSettings: dict or None = None,
  tableName: str = 'triggerdata',
  verbose: bool = False,
  metadata: sql.MetaData or None = None,
  returnDBobjects = False,
) -> list[sql.Column] or ( list, sql.Table, sql.MetaData, sql.Engine ):
    """Fetches the table schema and reports the list of columns in it.

    The columns in the list are of type `sql.Column`, which converts into `str` with the name of the column
    but also records the type of the data and other information about the column.

    In order to discover the table schema a connection to the database is required.
    If `returnDBobjects` is `True`, the intermediate database objects used are also returned for future use,
    including the table object, the metadata object and the connection engine.
    
    :param connectionSettings: override the specified connection settings
      (see the internal variable `DefaultConnectionSettings` in the source code).
      Most commonly overridden elements: `password`, `host`, `port`.

    :param tableName: name of the database table.

    :param verbose: enable additional messages on log and on console

    :param metadata: SQL metadata object (optional; a new one will be created and returned if None)

    :param returnDBobjects: if true, additional intermediate objects are returned to be used later
    
    :return a list of column objects, and if `returnDBobjects` is true,
      also the SQL table object, the metadata object and the DB engine created to fetch it (may be None)
    
    """
    triggerDataTable, DBmetadata, DBengine = prepareTriggerDatabaseTable(
      columns=None, connectionSettings=connectionSettings, tableName=tableName,
      verbose=verbose,
      metadata=metadata,
      )
    columns = list(triggerDataTable.columns)
    if returnDBobjects: return columns, triggerDataTable, DBmetadata, DBengine
    else: return columns
# fetchAvailableColumns()


def printAvailableColumns(connectionSettings = {}):
    columns = fetchAvailableColumns(connectionSettings=connectionSettings)
    print(f"Found {len(columns)} columns:")
    for iColumn, column in enumerate(columns):
        attributes = []
        if column.primary_key: attributes.append('[PRIMARY KEY]')
        if column.nullable: attributes.append('[NULLABLE]')
        print(f"[{iColumn:0{len(str(len(columns)-1))}d}] '{column}' ({column.type})", " ".join(attributes))
    # for columns
# printAvailableColumns()


# ------------------------------------------------------------------------------
# --- Main program (also works as test)
#
if __name__ == "__main__":

    DefaultColumns = (
      'run_number', 'event_no',
      'wr_seconds', 'wr_nanoseconds',
      'beam_seconds', 'beam_nanoseconds',
      'enable_seconds', 'enable_nanoseconds',
      'gate_type', 'trigger_type', 'trigger_source',
      'gate_id', 'gate_id_bnb', 'gate_id_numi', 'gate_id_bnboff', 'gate_id_numioff',
      )
    DefaultSelector = 'TestSelection'

    import argparse
    import sys
    
    parser = argparse.ArgumentParser(add_help=True, description="""
This script requires a direct connection to the database, and possibly a tunnel to Fermilab machines.
For example: `icarusgpvm03 tunnel '5455=>ifdbdaqrep01.fnal.gov:5455'`

The starting column set, if not overridden, is:
""" + ", ".join(DefaultColumns) + """.
""")
    
    parser.add_argument('--quiet', '-q', action='count', default=0,
      help="suppresses messages from the database access and from this program")
    parser.add_argument('--force', action='store_true',
      help="forces database retrieval again when existing is older than one day")
    parser.add_argument('--output',
      help="override output file name [default: ... it's complicate]")
    
    ConnectionGroup = parser.add_argument_group('Connection', "Database connection options")
    ConnectionGroup.add_argument('--hostname', '--host', default='localhost',
      help="database host [%(default)s]")
    ConnectionGroup.add_argument('--port', '-P', type=int,
      help="port number for connection to database")
    ConnectionGroup.add_argument('--password', help="database connection password")
    
    SelectionGroup = parser.add_argument_group('Query', "Event selection options")
    SelectionGroup.add_argument('--selector', '-S', 
      help="which selector to run [%(default)s]")
    SelectionGroup.add_argument('--fromrun', type=int,
      help="select all the events from this run on")
    SelectionGroup.add_argument('--torun', type=int,
      help="select all the events to this run (included)")
    SelectionGroup.add_argument('--runs', type=int,
      help="select events for this many runs")
    SelectionGroup.add_argument('--run', type=int,
      help="select events for this specific run")
    SelectionGroup.add_argument('--from', type=int, dest="from_",
      help="select all the events from this time [s] on")
    SelectionGroup.add_argument('--to', type=int,
      help="select all the events to this time [s] (included)")
    SelectionGroup.add_argument('--for', type=int, dest="for_",
      help="select all the events for this time interval [s]")
    
    ColumnGroup = parser.add_argument_group('Columns', "Column selection options")
    ColumnGroup.add_argument('--columns', default=[], action='append',
      help="which columns to download [see main help]")
    ColumnGroup.add_argument('--addcolumns', action='append', default=[],
      help="add these columns to the column list to be fetched (after remove)")
    ColumnGroup.add_argument('--removecolumns', action='append', default=[],
      help="remove these columns to the column list to be fetched (before add)")
    
    ModeGroup = parser.add_argument_group('Mode', "Operation mode options")
    ModeGroup.add_argument('--printcolumns', '-C', action='store_true',
      help="print the name of the available columns and exit")
    ModeGroup.add_argument('--printselectors', action='store_true',
      help="print the name of the available selectors and exit")
    
    args = parser.parse_args()
    
    Verbosity = 3 - args.quiet
    
    #
    # process connection settings
    #
    ConnectionSettings = {}
    host = args.hostname
    port = args.port
    if host:
        try:
            host, port = host.rsplit(':', 1)
        except ValueError: pass
        else:
            port = int(port)
    #
    
    if host: ConnectionSettings['host'] = host
    if port is not None: ConnectionSettings['port'] = port
    
    if args.password is not None:
        ConnectionSettings['password'] = args.password
    
    infoModeExit = None
    
    if args.printcolumns:
        printAvailableColumns(connectionSettings=ConnectionSettings)
        infoModeExit = 0
    
    if args.printselectors:
        print("Available selectors:", ", ".join(Selectors.keys()))
        infoModeExit = 0
    
    if infoModeExit is not None: sys.exit(infoModeExit)
    
    #
    # process selector
    #
    def computeRange(start=None, stop=None, count=None):
        if sum(( start is None, stop is None, count is None )) != 1: return None, None
        if start is None: start = stop - (count - 1)
        if stop is None: stop = start + (count - 1)
        return start, stop
    # computeRange()
    
    if args.fromrun is not None or args.torun is not None or args.runs is not None:
        if args.run is not None or args.from_ is not None or args.to is not None or args.selector is not None:
            raise RuntimeError("Either a run range, a single run, a time range or a selector must be specified.")
        fromRun, toRun = computeRange(args.fromrun, args.torun, args.runs)
        if fromRun is None:
            raise RuntimeError("When selecting a run range, exactly two between --fromrun, --torun and --runs must be specified.")
        if fromRun > toRun:
            raise RuntimeError(f"Selection resulted in an empty run range ({fromRun} -- {toRun})")
        selectorKey = selectRunRange(fromRun, toRun)
        selector = Selectors[selectorKey]
    elif args.from_ is not None or args.to is not None or args.for_ is not None:
        if args.run is not None or args.selector is not None:
            raise RuntimeError("Either a run range, a single run, a time range or a selector must be specified.")
        now = int(time.time())
        fromTime = args.from_
        if fromTime is not None and fromTime < 0: fromTime += now
        toTime = args.to
        if toTime is not None and toTime < 0: toTime += now
        if toTime is None and (args.for_ is None or fromTime is None): toTime = now
        fromTime, toTime = computeRange(fromTime, toTime, args.for_)
        if fromTime >= toTime:
            raise RuntimeError(f"Selection resulted in an empty time interval ({fromTime} -- {toTime})")
        selectorKey = selectTimeRange(fromTime, toTime)
        selector = Selectors[selectorKey]
    elif args.run is not None:
        if args.selector is not None:
            raise RuntimeError("Either a run range, a single run, a time range or a selector must be specified.")
        selectorKey = selectRunRange(args.run, args.run)
        selector = Selectors[selectorKey]
    else:
        selectorKey = DefaultSelector if args.selector is None else args.selector
        try:
            selector = Selectors[selectorKey]
        except KeyError:
            print(f"Unknown selector '{selectorKey}'."
                "\nAvailable selectors: " + ", ".join(Selectors.keys()),
                file=sys.stderr,
                )
            sys.exit(1)
        # try
    # if ... else
    
    #
    # process column list
    #
    columns = list(args.columns if args.columns else DefaultColumns)
    
    def expandSpecs(specs, sep=','):
        return [ item for spec in specs for item in map(str.strip, spec.split(sep)) ]
    
    for colName in expandSpecs(args.removecolumns):
        try:
            while True: columns.remove(colName) # remove all instances
        except ValueError: pass
    # for col
    
    for colName in expandSpecs(args.addcolumns):
        if colName not in columns: columns.append(colName)
    
    #
    # process output name
    #
    saveFormat = '.gz' if args.output is None else args.output
    
    #
    # do the thing
    #
    startTime = time.time()
    try:
        df = loadOrReadTriggerDatabase(
          columns=columns,
          connectionSettings=ConnectionSettings,
          selector=selector,
          verbose=(Verbosity >= 3),
          forceToday=args.force,
          saveFormat=saveFormat,
          )
    except sql.exc.OperationalError as e:
        print(
          """An "operational" error occurred while connecting to the database:\n""",
          str(e),
          file=sys.stderr,
          )
        sys.exit(2)
    #
    
    if Verbosity >= 1:
        print(f"It took {time.time() - startTime:.1f}\" to load {len(df)} entries and {len(df.columns)} columns.")

    # display(df)
  
# if main
