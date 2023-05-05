"""
File is used to load data from csv files into database.
"""
import os

import numpy as np
import pandas as pd
import psycopg2.extras as extras
from django.db import connection

from datawiz_project.settings import BASE_DIR


def run():
    # app "products":
    df_categories = pd.read_csv(os.path.join(BASE_DIR, "scripts/csv_files/category.csv")).sort_values("parent_id")
    execute_addition(df_categories, "products_category")

    df_producer = pd.read_csv(os.path.join(BASE_DIR, "scripts/csv_files/producer.csv")).sort_values("id")
    execute_addition(df_producer, "products_producer")

    df_products = pd.read_csv(os.path.join(BASE_DIR, "scripts/csv_files/product_edit.csv")).sort_values("id")
    execute_addition(df_products, "products_product")

    # app "shops":
    df_shop_group = pd.read_csv(os.path.join(BASE_DIR, "scripts/csv_files/shop_group.csv")).sort_values("id")
    execute_addition(df_shop_group, "shops_shopgroup")

    df_shop = pd.read_csv(os.path.join(BASE_DIR, "scripts/csv_files/shop.csv")).sort_values("id")
    execute_addition(df_shop, "shops_shop")

    # app "receipts":
    df_terminal = pd.read_csv(os.path.join(BASE_DIR, "scripts/csv_files/terminal.csv")).sort_values("id")
    execute_addition(df_terminal, "receipts_terminal")

    df_supplier = pd.read_csv(os.path.join(BASE_DIR, "scripts/csv_files/supplier.csv")).sort_values("id")
    execute_addition(df_supplier, "receipts_supplier")

    execute_additions_gradually("receipts_receipt", os.path.join(BASE_DIR, "scripts/csv_files/receipt.csv"))

    execute_additions_gradually("receipts_cartitem", os.path.join(BASE_DIR, "scripts/csv_files/cartitem.csv"))


def execute_addition(df, table):
    df = df.astype(object).replace(np.nan, None)  # replace all nan with None
    tuples = [tuple(x) for x in df.to_numpy()]
    tuples_for_update = []  # variable only when inserting into 'products_category'

    # if we are inserting data from categories.csv, we should firstly add it without 'parent_id'
    # and only after inserting all data we should update column 'parent_id' with existing values
    if table == "products_category":
        tuples_for_update = []
        for tup in tuples:
            tuples_for_update.append((tup[0], tup[2]))
        df = df.assign(parent_id=None)
        tuples = [tuple(x) for x in df.to_numpy()]

    cols = '"' + '","'.join(list(df.columns)) + '"'

    # SQL query to execute
    query = f"INSERT INTO {table}({cols}) VALUES %s"

    try:
        with connection.cursor() as cursor:
            extras.execute_values(cursor, query, tuples)
    except Exception as error:
        print(f"Error: {error}")
        return 1

    # if this is 'products_category' table, we are updating 'parent_id' after inserting values
    if table == "products_category":
        update_query = """
            UPDATE products_category
            SET parent_id = data.parent_id
            FROM (VALUES %s) AS data (id, parent_id)
            WHERE products_category.id = data.id
        """
        with connection.cursor() as cursor:
            extras.execute_values(cursor, update_query, tuples_for_update)

    print(f"the dataframe is inserted into {table}")


def execute_additions_gradually(table, file_path, chunk_size=50000):
    """
    For gradual inserting records into database
    :param table:
    :param file_path:
    :param chunk_size:
    :return:
    """
    try:
        with connection.cursor() as cursor:
            # read from file only 50 000 records on each iteration
            for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                df = chunk.astype(object).replace(np.nan, None)  # replace all nan with None
                tuples = [tuple(x) for x in df.to_numpy()]

                cols = '"' + '","'.join(list(df.columns)) + '"'
                query = f"INSERT INTO {table}({cols}) VALUES %s"
                extras.execute_values(cursor, query, tuples)
    except Exception as error:
        print(f"Error: {error}")
        return 1
    print(f"dataframe is inserted into {table}")
