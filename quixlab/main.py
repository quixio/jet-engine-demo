import quixlab as ql

canvas = ql.Canvas(title="My Notebook", lake_tree_open=['config_enriched_data', 'config_enriched_data/campaign_id=CAMP-2024-001', 'config_enriched_data/campaign_id=CAMP-2024-001/environment_id=Lab-A-01'])


@canvas.dataset(position=(817, 313), size=(701, 538), code_height=147)
def config_enriched_data(experiment):
    return ql.sql(f"""SELECT *
    FROM config_enriched_data
    WHERE campaign_id = '{experiment[1]}'
      AND environment_id = '{experiment[2]}'
      AND test_id = '{experiment[3]}'
    ORDER BY timestamp""")


@canvas.cell(position=(-255, 362), size=(724, 466), code_height=0)
def experiment():
    campaigns = ql.sql(r"""
    SELECT DISTINCT(campaign_id)
    FROM config_enriched_data
    """)

    campaign_id = ql.ui.dropdown(campaigns["campaign_id"].to_list(), label="Campaign")
    campaign_id

    environments = ql.sql(f"""
    SELECT DISTINCT(environment_id)
    FROM config_enriched_data
    WHERE campaign_id = '{campaign_id}'
    """)
    environment_id = ql.ui.dropdown(environments["environment_id"].to_list(), label="Test")


    tests = ql.sql(f"""
    SELECT DISTINCT(test_id)
    FROM config_enriched_data
    WHERE campaign_id = '{campaign_id}' AND environment_id = '{environment_id}'
    """)
    test_id = ql.ui.dropdown(tests["test_id"].to_list(), label="Test")

    heading = ql.ui.markdown(r"""
    # Experiment picker
    Select experiment available in LakeHouse storage
    """)

    [heading, campaign_id, environment_id, test_id]


@canvas.notebook(position=(1837, 185), size=(959, 702), code_height=200, viz={'cells': {'0': {'type': 'table', 'x': 'timestamp', 'y': 'ina260__voltage_v'}, '1': {'type': 'line', 'x': 'timestamp', 'y': 'ina260__voltage_v'}}, 'outputCells': [1, 2], 'type': 'line', 'x': 'timestamp', 'y': ['timestamp_diff']})
def cell_2(config_enriched_data):
    # %%
    config_enriched_data["timestamp_diff"] = config_enriched_data["timestamp"].diff()
    # %%
    config_enriched_data


@canvas.cell(position=(2981, 21), size=(977, 577), code_height=200, viz={'storagePath': '', 'storageType': 'folder'})
def blob_folder():
    ql.StorageFolder("")


@canvas.cell(position=(2995, 760), size=(350, 450), code_height=200, viz={'storagePath': 'demo-jetenginedemo-prod', 'storageType': 'folder'})
def demo_jetenginedemo_prod():
    ql.StorageFolder("demo-jetenginedemo-prod")


@canvas.cell(position=(4018, 21), size=(890, 657), code_height=200)
def cell_1(blob_folder):
    import pandas as pd

    csv_file = blob_folder.create_file("data_1.csv")
    csv_file.write(blob_folder.files["data_1.txt"].read())


@canvas.cell(position=(3735, 879), size=(980, 632), code_height=417)
def cell_3(blob_folder):
    from nptdms import TdmsFile


    with blob_folder.files["Current_D0.tdms"].open() as f:
          tdms_file = TdmsFile.read(f)

    df = tdms_file.as_dataframe() 
    df


if __name__ == "__main__":
    canvas.serve()
