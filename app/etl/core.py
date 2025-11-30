# -*- coding: utf-8 -*-
from typing import Any, Tuple
import pandas as pd
from app.compiler.ast_nodes import *
from app.etl.data.data_factories import LoaderDataFactory, ExtractorDataFactory
from app.etl.data.base_data_types import IExtractor, ILoader
from app.etl.helpers import (
    apply_filtering, apply_groupby, apply_groupby_with_order,
    check_if_column_names_is_in_group_by,
    convert_select_column_indices_to_name,
    generate_aggregation_row, get_unique, group_by_columns_names,
    apply_order_by_without_groupby
)

transformed_data = None

def extract(data_source_type: str, data_source_path: str) -> pd.DataFrame:
    data_extractor: IExtractor = ExtractorDataFactory.create(data_source_type, data_source_path)
    data: pd.DataFrame = data_extractor.extract()
    return data

def transform_select(data: pd.DataFrame, criteria: dict) -> pd.DataFrame:
    global transformed_data

    if data is None:
        raise ValueError("Input DataFrame is None")

    are_select_columns_aggregation = False
    if criteria["COLUMNS"] != "__all__":
        are_select_columns_aggregation = all(isinstance(item, tuple) for item in criteria["COLUMNS"])

    # WHERE
    if criteria["FILTER"]:
        data = apply_filtering(data, criteria["FILTER"])

    # ORDER without GROUP
    if (not criteria["GROUP"]) and criteria["ORDER"] and not are_select_columns_aggregation:
        order_by_node: OrderByNode = criteria["ORDER"]
        data = apply_order_by_without_groupby(data, order_by_node)

    # GROUP BY
    if criteria["GROUP"]:
        groupby_cols = get_unique(group_by_columns_names(data, criteria["GROUP"]))
        select_cols = convert_select_column_indices_to_name(data, criteria["COLUMNS"])

        if not check_if_column_names_is_in_group_by(select_cols, groupby_cols):
            raise Exception("There is a column not included in GROUP BY")

        if criteria["ORDER"]:
            order_by_node: OrderByNode = criteria["ORDER"]
            data = apply_groupby_with_order(data, select_cols, groupby_cols, order_by_node)
        else:
            data = apply_groupby(data, select_cols, groupby_cols)

    else:
        # SELECT specific columns (no GROUP BY)
        if criteria["COLUMNS"] != "__all__":
            columns = criteria["COLUMNS"]

            def is_column_number(x):
                return isinstance(x, str) and x.startswith("[") and x.endswith("]")

            # Handle aggregation functions like SUM(x)
            if are_select_columns_aggregation:
                aggregate_columns = []
                for col in columns:
                    # col is tuple like (func, column)
                    func = col[0]
                    col_ref = col[1]
                    if isinstance(col_ref, str) and is_column_number(col_ref):
                        # numeric index reference
                        idx = int(col_ref[1:-1])
                        if idx < 0 or idx >= len(data.columns):
                            raise IndexError(f"Column index {idx} out of range")
                        aggregate_columns.append((func, data.columns[idx]))
                    else:
                        aggregate_columns.append((func, col_ref))
                data = generate_aggregation_row(data, aggregate_columns)
            else:
                # disallow mixing aggregation without GROUP
                if any(isinstance(col, tuple) for col in columns):
                    raise Exception("Aggregation functions used without GROUP BY")

                # convert indices to names safely
                column_names = []
                for col in columns:
                    if isinstance(col, str) and is_column_number(col):
                        idx = int(col[1:-1])
                        if idx < 0 or idx >= len(data.columns):
                            raise IndexError(f"Column index {idx} out of range")
                        column_names.append(data.columns[idx])
                    else:
                        column_names.append(col)
                data = data[column_names]

    # DISTINCT
    if criteria["DISTINCT"]:
        data = data.drop_duplicates()

    # LIMIT / TAIL
    if criteria["LIMIT_OR_TAIL"] is not None:
        operator, number = criteria["LIMIT_OR_TAIL"]
        if not isinstance(number, int) or number < 0:
            raise ValueError("LIMIT/TAIL requires a non-negative integer")
        if number == 0:
            data = pd.DataFrame(columns=data.columns)
        elif operator == "limit":
            data = data.head(number)
        else:
            data = data.tail(number)

    transformed_data = data
    return data

def join(df1: pd.DataFrame, df2: pd.DataFrame, left_col: str, right_col: str, how: str = "inner") -> pd.DataFrame:
    global transformed_data

    valid_join_types = ["inner", "left", "right", "outer"]
    if how not in valid_join_types:
        raise ValueError(f"Invalid join type '{how}'. Must be one of {valid_join_types}")

    # handle empties
    if df1 is None or df2 is None:
        raise ValueError("Input DataFrames must not be None")

    if df1.empty and df2.empty:
        transformed_data = pd.DataFrame()
        return transformed_data

    if df1.empty:
        if how in ["inner", "left"]:
            transformed_data = pd.DataFrame()
            return transformed_data
        else:
            transformed_data = df2.copy()
            return transformed_data

    if df2.empty:
        if how in ["inner", "right"]:
            transformed_data = pd.DataFrame()
            return transformed_data
        else:
            transformed_data = df1.copy()
            return transformed_data

    if left_col not in df1.columns:
        raise KeyError(f"Column '{left_col}' not found in left DataFrame. Available: {list(df1.columns)}")
    if right_col not in df2.columns:
        raise KeyError(f"Column '{right_col}' not found in right DataFrame. Available: {list(df2.columns)}")

    try:
        result = df1.merge(df2, left_on=left_col, right_on=right_col, how=how, suffixes=("_left", "_right"))
    except Exception as e:
        raise Exception(f"Error during join: {str(e)} (left_col={left_col}, right_col={right_col}, how={how})")

    transformed_data = result
    return result

def load(data: pd.DataFrame, source_type: str, data_destination: str) -> None:
    try:
        data_loader: ILoader = LoaderDataFactory.create(source_type, data_destination)
        data_loader.load(data)
    except Exception as e:
        raise Exception(f"Error loading data to '{source_type}:{data_destination}': {str(e)}")

# Utilities
def get_transformed_data() -> pd.DataFrame:
    global transformed_data
    return transformed_data

def clear_transformed_data() -> None:
    global transformed_data
    transformed_data = None

def preview_data(data: pd.DataFrame, rows: int = 5) -> pd.DataFrame:
    return data.head(rows)

def get_data_info(data: pd.DataFrame) -> dict:
    return {
        "shape": data.shape,
        "columns": list(data.columns),
        "dtypes": {col: str(dtype) for col, dtype in data.dtypes.items()},
        "memory_usage": data.memory_usage(deep=True).sum(),
        "null_counts": data.isnull().sum().to_dict(),
    }
