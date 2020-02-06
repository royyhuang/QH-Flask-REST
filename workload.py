from flask_restful import Resource
import pandas as pd
import mysql.connector as sql
import credentials


class Workload(Resource):

    @staticmethod
    def get():
        # connect to the database
        conn = sql.connect(host=credentials.HOST,
                           user=credentials.USER,
                           passwd=credentials.PASSWD,
                           database='quantum',
                           port=3306)
        # sql statements needed
        pods_query = "select POD from pods"
        clients_query = "select `INITIAL_POD`, output.`GroupID`," \
                        " `PCG_ALL_TIME_HOURS`," \
                        " `PCGPDC_TIME_HOURS`," \
                        " `PCGPAC_TIME_HOURS`," \
                        " `PCGFLLUP_TIME_HOURS`," \
                        " `PCGNEWALERT_TIME_HOURS`," \
                        " `PCGREF_TIME_HOURS`," \
                        " `PCGTERM_TIME_HOURS`," \
                        " `PCGEMPGRP_TIME_HOURS`" \
                        " from `pods_clients_map` map" \
                        " inner join `model_output_data` output" \
                        " on map.`GroupID` = output.`GroupID`" \
                        " where map.`INITIAL_POD` = {};"
        # query all the POD id
        pods_df: pd.DataFrame = pd.read_sql(pods_query, conn)

        # calculate the current overall workload for each POD
        workload_df: pd.DataFrame = pd.DataFrame()
        for row in pods_df.itertuples():
            # query the workload (in hours) for all the clients belonging to
            # a POD
            clients_df = pd.read_sql(clients_query.format(row.POD), conn)
            clients_workload_s: pd.Series = clients_df.sum(axis=0)
            clients_workload_s["INITIAL_POD"] = row.POD
            clients_workload_s.drop("GroupID", inplace=True)
            workload_df = workload_df.append(clients_workload_s,
                                             ignore_index=True)
        conn.close()

        # parse the pd.Dataframe into deserializable type
        workload_df.set_index("INITIAL_POD", inplace=True)
        return workload_df.to_dict(orient="index")

