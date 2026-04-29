import quixlab as ql

canvas = ql.Canvas(title="Realtime Dashboard", lake_tree_open=['ac_telemetry'])


@canvas.dataset(position=(2454, -1388), size=(560, 420), code_height=200)
def ac_telemetry():
    return ql.sql("""SELECT *
    FROM ac_telemetry
    LIMIT 100""")


@canvas.stream(position=(3177, -1039), size=(557, 482), code_height=235)
def stream_1():
    return ql.topic("f1-data", workspace="quixdev-aitest-dev", offset="earliest", limit=200)


@canvas.cell(position=(3797, -1039), size=(560, 420), code_height=200)
def cell_2(stream_1):
    df = stream_1.df
    return df.tail(20)


@canvas.notebook(position=(3083, -1398), size=(560, 420), code_height=200, viz={'outputCell': 0})
def notebook_3():
    # %%
    import pandas as pd
    df = pd.DataFrame({"x": [1,2,3], "y": [4,5,6]})
    df
    # %%
    import plotly.express as px
    px.bar(df, x="x", y="y")


if __name__ == "__main__":
    canvas.serve()


@canvas.dataset(position=(2207, -1456), size=(1046, 613), code_height=200)
def carcolours_v4():
    return ql.sql("""SELECT * 
    FROM carcolours_nowm2 
    ORDER BY start
    LIMIT 100""")


@canvas.cell(position=(3562, -2336), size=(1001, 730), code_height=200, viz={'type': 'line', 'x': 'start', 'y': 'count'})
def cell_3(carcolours_v4):
    # Reference upstream "carcolours_v4"
    return carcolours_v4.head(100) if hasattr(carcolours_v4, "head") else carcolours_v4


@canvas.stream(position=(4820, -1632), size=(820, 621), code_height=231)
def stream_2():
    return ql.topic("f1-data", workspace="quixdev-aitest-dev", offset="earliest", limit=200)


@canvas.cell(position=(5867, -2145), size=(799, 582), code_height=200, viz={'type': 'line', 'x': 'Timestamp', 'y': 'Speed'})
def cell_4(stream_2):
    # Reference upstream "stream_2"
    df = stream_2.df  # rolling buffer as DataFrame
    return df.tail(100)


@canvas.dataset(position=(943, 337), size=(864, 542), code_height=200)
def carcolours_nowm2():
    return ql.sql("""SELECT * FROM ac_telemetry WHERE environment = 'prague_office' AND test_rig = 'g29' AND experiment = 'VideoSyncLaps' AND driver = 'tomas' AND track = 'ks_nurburgring' AND carModel = 'bmw_1m' AND session_id = '2026-04-14T14:06:59.113Z' AND lap = 5""")


@canvas.cell(position=(2055, 340), size=(809, 634), code_height=200, viz={'type': 'table', 'x': 'packetId', 'y': 'gas'})
def cell_1():
    # Reference upstream "carcolours_nowm2"
    return carcolours_nowm2


@canvas.cell(position=(1867, 337), size=(420, 300), code_height=200)
def cell_5():
    # Reference upstream "carcolours_nowm2"
    return carcolours_nowm2.head(20) if hasattr(carcolours_nowm2, "head") else carcolours_nowm2
