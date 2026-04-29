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


@canvas.notebook(position=(1687, 185), size=(959, 702), code_height=200, viz={'cells': {'0': {'type': 'table', 'x': 'timestamp', 'y': 'ina260__voltage_v'}, '1': {'type': 'line', 'x': 'timestamp', 'y': 'ina260__voltage_v'}}, 'outputCell': 1, 'outputCells': [1, 2], 'type': 'line', 'x': 'timestamp', 'y': ['timestamp_diff']})
def cell_2(config_enriched_data):
    # %%
    config_enriched_data["timestamp_diff"] = config_enriched_data["timestamp"].diff()
    # %%
    config_enriched_data


if __name__ == "__main__":
    canvas.serve()
