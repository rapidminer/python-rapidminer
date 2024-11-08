#
# This file is part of the RapidMiner Python package.
#
# Copyright (C) 2018-2024 RapidMiner GmbH
#
# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU Affero General Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with this program.
# If not, see https://www.gnu.org/licenses/.
#

import numpy as np
import pandas as pd
import os
import h5py
from pathlib import Path
from datetime import datetime
from .serdeutils import set_metadata_without_warning
from .utilities import ProjectException
from .utilities import TooManyBinomialValuesError
from .utilities import ValueConversionError
from .connections import Connections



def decode(x):
    if isinstance(x, str):
        return x
    return x.decode("utf-8")


class Project():
    """
    Class for using a project from RapidMiner Server that has been cloned locally. Use git for cloning the repository, then read and write calls can work on local resources. You need to use git commands to push changes that you make locally.
    """

    __NANOSECONDS_IN_A_DAY = 86400000000000
    _RM_HDF5_EXTENSION = ".rmhdf5table"
    _RM_RMP_EXTENSION = ".rmp"
    _METADATA_TYPES = {"NOMINAL": np.int8(1),
                       "INTEGER": np.int8(3),
                       "REAL": np.int8(4),
                       "TEXT": np.int8(5),
                       "BINOMINAL": np.int8(6),
                       "POLYNOMINAL": np.int8(7),
                       "FILE_PATH": np.int8(8),
                       "DATE_TIME": np.int8(9),
                       "DATE": np.int8(10),
                       "TIME": np.int8(11)}
    _LEGACY_TYPES = ["TEXT", "BINOMINAL", "FILE_PATH", "DATE"] # POLYNOMIAL handled separatly
    _METADATA_ROLES = ["BATCH", "CLUSTER", "ENCODING", "ID", "INTERPRETATION", "LABEL", "OUTLIER", "PREDICTION", "SOURCE", "WEIGHT"]

    __RM_MISSING_DATETIME_OR_TIME = 9223372036854775807 # constant value is coming from com.rapidminer.storage.hdf5.ExampleSetHdf5Writer.java#writeDateData/writeTimeData as of Long.MAX_VALUE/TimeColumn.MISSING_VALUE
    __PANDAS_MISSING_DATE = pd.to_numeric(pd.Series([datetime.utcfromtimestamp(0), None]), downcast="integer")[1]

    def __init__(self, path="."):
        """
        Initializes a reference to a locally cloned project. You need to clone a project from RapidMiner Server first (e.g. via git commands) to be able to use the methods of this instance.
        
        :param path: path to the local project repository root folder. It can be a relative path from the current working directory or an absolute path, . The default value points to the working directory.
        """
        if not os.path.exists(path):
            if path == "":
                msg_dir_part = "in the current directory"
            else:
                msg_dir_part = "at the specified path '%s'" % (os.path.dirname(path))
            raise ProjectException("Project '%s' does not exist %s. Please make sure you have a local copy of the project." % (os.path.basename(path), msg_dir_part))
        self.path = os.path.abspath(path)

    def read(self, path_or_buffer):
        """
        Reads a dataset from the local project repository into a pandas DataFrame. Note that only the new HDF5 format is supported, earlier RapidMiner Server data formats are not supported.
        
        :param path_or_buffer: this can either be a relative path inside the project (e.g. subfolder and file name), an absolute path, or a io.BytesIO stream. If a path is specified, the RapidMiner-specific HDF5 file extension can be omitted.
        """
        if isinstance(path_or_buffer, str):
            path_or_buffer = os.path.join(self.path, path_or_buffer)
            if not os.path.isfile(path_or_buffer):
                if (os.path.isfile(path_or_buffer + Project._RM_HDF5_EXTENSION)):
                    path_or_buffer = path_or_buffer + Project._RM_HDF5_EXTENSION
                else:
                    raise FileNotFoundError("File '%s' not found in the project." % (path_or_buffer))
        return Project.__read_data_safe(path_or_buffer)

    def write(self, df, path):
        """
        Writes a pandas DataFrame into the RapidMiner-specific HDF5 file format that the rest of the RapidMiner platform uses. Note that you need to explicitly commit and push your local changes to the remote project repository (e.g. via git commands) to make them available to the platform.
        
        :param path: relative path inside the project (e.g. subfolder and file name) specifying the target location or an absolute path. The RapidMiner-specific HDF5 file extension is automatically added to the filename, if it is missing.
        """
        path = os.path.join(self.path, path)
        if len(Path(path).suffix) == 0:
            path = path + Project._RM_HDF5_EXTENSION
        Project.__write_data_safe(df, path)

    def get_connections(self):
        """
        Returns the connection in that this project contains.
        """
        return Connections(self.path)
        
#####################
# Private functions #
#####################

    __from_ts_nanos = np.vectorize(lambda x: datetime.utcfromtimestamp(x/1e9) if x != Project.__RM_MISSING_DATETIME_OR_TIME else None)
    __from_ts_seconds_and_nanos = np.vectorize(lambda x,y: datetime.utcfromtimestamp(x+y/1e9) if x != Project.__RM_MISSING_DATETIME_OR_TIME else None)
    __hyp5_string_dtype = h5py.string_dtype()
    __h5py_reference_dtype = h5py.special_dtype(ref=h5py.Reference)
    
    def __get_numerical(x, typestr):
        if typestr == 'Integer':
            # NaN values are not allowed in int64
            if not np.isnan(np.min(x[:])):
                return x.astype('int64')[:]
            else:
                return x
        elif typestr in ('Date-Time', 'Date'):
            return Project.__from_ts_seconds_and_nanos(x[:],0)
        elif typestr == "Time":
            return Project.__from_ts_nanos(x[:])
        else:
            return x

    def __get_data(f, x):
        r = f[x]
        mapping = r.attrs.get('dictionary')
        if "additional" in r.attrs and r.attrs.get("type") == "Date-Time":
            additional = r.attrs.get('additional')
            additional = f[additional]
            return Project.__from_ts_seconds_and_nanos(r[:], additional[:])
        if mapping is None:
            return Project.__get_numerical(r, decode(r.attrs.get('type')))
        if isinstance(mapping,h5py.Reference):
            mapping = f[mapping]
        mapping = mapping[1:]
        g = lambda x:x-1
        return pd.Categorical.from_codes(g(r[()]), [decode(s) if not isinstance(s, str) else s for s in mapping], ordered=False)

    def __get_type(df_kind_char, hdf_attrs):
        """
        Decides type based on the pandas DataFrame type, the explicit HDF5 type and whether there is a positive nominal type that indicates binominal.
        """
        if "legacy_type" in hdf_attrs:
            for k in Project._METADATA_TYPES.keys():
                if Project._METADATA_TYPES[k] == hdf_attrs.get("legacy_type"):
                    return k.lower()
        hdf_type = decode(hdf_attrs.get("type"))
        if hdf_type in ("Date-Time", "Date"):
            meta_type = "date_time"
        elif hdf_type == "Time":
            meta_type = "time"
        elif df_kind_char in ('i', 'u'):
            meta_type = 'integer'
        elif df_kind_char in ('f'):
            meta_type = 'real'
        elif df_kind_char in ('M'):
            meta_type = 'date_time'
        elif df_kind_char in ('b') or "positive_index" in hdf_attrs:
            meta_type = 'binominal'
        else:
            meta_type = 'polynominal'
        return meta_type

    def __get_role(hdf_column):
        if "role" in hdf_column.attrs:
            r = decode(hdf_column.attrs.get("role"))
            if r in Project._METADATA_ROLES:
                return r.lower()
            elif r in ["SCORE", "METADATA"]:
                return decode(hdf_column.attrs.get("legacy_role"))
            else:
                raise ProjectException("Role '" + r +  "' not recognized. (Column '" + decode(hdf_column.attrs.get('name')) + "'.)" )
        return None
    
    def __read_data_from_input(f):
        numberOfColumns = f.attrs.get('columns')
        keys = ["a" + str(i) for i in range(0, numberOfColumns)]
        names = [decode(f[x].attrs.get('name')) for x in keys]
        data = [Project.__get_data(f, x) for x in keys]
        df = pd.DataFrame.from_dict(dict(zip(names, data)))
        metadata = dict(zip(names,
            [((Project.__get_type(df.dtypes[decode(f[x].attrs.get('name'))].kind,
                                 f[x].attrs)),
             Project.__get_role(f[x])) for x in keys]))
        set_metadata_without_warning(df, metadata)
        return df

    def __read_data_safe(filename_or_buffer):
        try:
            return Project.__read_data(filename_or_buffer)
        except OSError:
            raise ProjectException("Cannot read file. Not a valid rmhdf5table file format.")


    def __read_data(filename_or_buffer):
        with h5py.File(filename_or_buffer, 'r') as f:
            return Project.__read_data_from_input(f)

    def __get_desired_type(frame, column, name):
        desired_type = None
        if hasattr(frame, "rm_metadata") and name in frame.rm_metadata and frame.rm_metadata[name][0]:
            desired_type = frame.rm_metadata[name][0].upper()
        else:
            if column.dtype.kind == 'O':
                desired_type = "NOMINAL"
            elif np.issubdtype(column.dtype, np.integer):
                desired_type = "INTEGER"
            elif column.dtype.kind == 'M':
                desired_type = "DATE_TIME"
            else:
                desired_type = "REAL"
        return desired_type

    def __create_dataset(f, column, desired_type, index):
        shortname = 'a'+str(index)
        if desired_type in ["NOMINAL", "BINOMINAL", "POLYNOMINAL", "TEXT", "FILE_PATH"]:
            cat = column.astype("category").cat
            dset = f.create_dataset(shortname, data = pd.to_numeric(cat.codes.apply(lambda x:x+1), downcast='integer'))
            mappingname = 'd'+str(index)
            mappingvals = cat.categories.values.astype(object)
            replacement = "NULL"
            while replacement in mappingvals:
                replacement = "\x00" + replacement
            mappingvals = np.concatenate([[replacement], mappingvals])
            if desired_type == "BINOMINAL" and len(mappingvals) > 3:
                raise TooManyBinomialValuesError("Column '%s' marked as binomial column in rm_metadata attribute, but has more there is more then two distinct values present.", )
            if len(mappingvals) <= 3:
                dset.attrs["dictionary"] = [str(v) for v in mappingvals]
                if desired_type == "BINOMINAL":
                    # positive index may change after read and write
                    dset.attrs['positive_index'] = np.int8(len(mappingvals) - 1)
            else:
                mset = f.create_dataset(mappingname, (len(mappingvals), ), dtype=Project.__hyp5_string_dtype)
                try:
                    mset[()] = mappingvals
                except TypeError:
                    # fixes error: TypeError: Can't implicitly convert non-string objects to strings (caused by some Python environments)
                    mset[()] = [str(v) for v in mappingvals]
                dset.attrs.create("dictionary", mset.ref, dtype=Project.__h5py_reference_dtype)
            dset.attrs['type'] = "Nominal"
        elif desired_type == "INTEGER":
            dset = f.create_dataset(shortname, data = column.astype("int64"))
            dset.attrs['type'] = "Integer"
        elif desired_type in ["DATE", "TIME", "DATE_TIME"]:
            if column.dtype.kind == "M":
                nanoseconds = pd.to_numeric(column.dt.tz_localize(None), downcast="integer")
            else:
                nanoseconds = pd.to_numeric(column, downcast="integer")
            if desired_type == "TIME":
                missing = nanoseconds==Project.__PANDAS_MISSING_DATE
                nanoseconds.loc[missing] = Project.__RM_MISSING_DATETIME_OR_TIME
                nanoseconds.loc[~missing] = nanoseconds.loc[~missing] % int(Project.__NANOSECONDS_IN_A_DAY)
                dset = f.create_dataset(shortname, data = nanoseconds)
                dset.attrs['type'] = "Time"
            else:
                seconds = nanoseconds.apply(lambda x: x // int(1e9) if x != Project.__PANDAS_MISSING_DATE else Project.__RM_MISSING_DATETIME_OR_TIME)
                dset = f.create_dataset(shortname, data = seconds )
                additionalname = shortname+"a"
                aset = f.create_dataset(additionalname, data = (nanoseconds % int(1e9)).astype("int32"))
                dset.attrs.create("additional", aset.ref, dtype=Project.__h5py_reference_dtype)
                dset.attrs['type'] = "Date-Time"
        else:
            dset = f.create_dataset(shortname, data = column.astype("float64"))
            dset.attrs['type'] = "Real"
        return dset

    def __to_column_role(role):
        if role.startswith("confidence"):
            return ("SCORE", role)
        elif role.upper() in Project._METADATA_ROLES:
            return (role.upper(), None)
        else:
            return ("METADATA", role)

    def __set_common_column_attributes(frame, dset, desired_type, name):
        dset.attrs['name'] = name
        if desired_type in Project._LEGACY_TYPES:
            dset.attrs['legacy_type'] = Project._METADATA_TYPES[desired_type]
        if hasattr(frame, "rm_metadata") and name in frame.rm_metadata:
            md = frame.rm_metadata[name]
            if len(md) > 1 and md[1]:
                role, legacy_role = Project.__to_column_role(md[1])
                dset.attrs['role'] = role
                if legacy_role is not None:
                    dset.attrs['legacy_role'] = legacy_role

    def __write_column(f, frame, column, name, index):
        desired_type = Project.__get_desired_type(frame, column, name)
        try:
            dset = Project.__create_dataset(f, column, desired_type, index)
        except ValueError as e:
            raise ValueConversionError("Cannot write output file with the desired format. Please review rm_metadata of the pandas DataFrame. Cause: " + str(e))
        Project.__set_common_column_attributes(frame, dset, desired_type, name)

    def __write_data_safe(data, filename):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("'data' attribute of write_data is not pandas DataFrame.")
        if not os.path.exists(os.path.dirname(filename)):
            raise ProjectException("Cannot write file. Parent directory '%s' does not exists." % (os.path.dirname(filename)))
        if hasattr(data, "rm_metadata"):
            md = data.rm_metadata
            for key in md.keys():
                if md[key][0] is not None and md[key][0].upper() not in Project._METADATA_TYPES.keys():
                    raise ProjectException("%s is not a valid type in rm_metadata." % (md[key][0]))
        Project.__write_data(data, filename)

    def __write_data(data, filename): #todo: error handling
        frame = data
        # without this call you get fixed length strings which can only be ascii
        with h5py.File(filename, 'w') as f:
            shape = frame.shape
            f.attrs['rows'] = np.int32(shape[0])
            f.attrs['columns'] = np.int32(shape[1])
            for i in range(0, len(frame.columns)):
                name = str(frame.columns[i])
                column = frame.iloc[:,i]
                Project.__write_column(f, frame, column, name, i)
