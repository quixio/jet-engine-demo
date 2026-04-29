# /// script
# [tool.marimo.display]
# theme = "dark"
# ///

import marimo

__generated_with = "0.23.4"
app = marimo.App(width="full")


@app.cell
def _():
    import os
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    return go, make_subplots, mo, os, pd, px


@app.cell
def _(os):
    from quixlake import QuixLakeClient

    QUIXLAKE_URL = os.environ["quix_lake_api_url"]

    client = QuixLakeClient(
        base_url=QUIXLAKE_URL,
        token=os.environ["Quix__Sdk__Token"],
    )
    return (client,)


@app.cell
def _(client):
    # Load all data once for the dashboard
    all_data = client.query("SELECT * FROM config-enriched-data")

    # Get unique campaigns and tests
    campaigns = sorted(all_data["campaign_id"].dropna().unique().tolist())
    all_tests = sorted(all_data["test_id"].dropna().unique().tolist())
    return all_data, all_tests, campaigns


@app.cell
def _(mo):
    mo.md(r"""
    # Jet Engine Test Rig Dashboard
    Interactive explorer for thrust-stand telemetry stored in QuixLake.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Campaign Overview
    """)
    return


@app.cell
def _(all_data, mo, px):
    # Number of test runs per campaign
    _runs = (
        all_data.groupby("campaign_id")["test_id"]
        .nunique()
        .reset_index()
        .rename(columns={"test_id": "test_runs"})
    )

    # Total data points per campaign
    _points = (
        all_data.groupby("campaign_id")
        .size()
        .reset_index(name="data_points")
    )

    _campaign_summary = _runs.merge(_points, on="campaign_id")

    _fig_runs = px.bar(
        _campaign_summary,
        x="campaign_id",
        y="test_runs",
        title="Test Runs per Campaign",
        labels={"campaign_id": "Campaign", "test_runs": "# Test Runs"},
        template="plotly_dark",
    )

    _fig_points = px.bar(
        _campaign_summary,
        x="campaign_id",
        y="data_points",
        title="Total Data Points per Campaign",
        labels={"campaign_id": "Campaign", "data_points": "# Data Points"},
        template="plotly_dark",
    )

    mo.hstack(
        [mo.ui.plotly(_fig_runs), mo.ui.plotly(_fig_points)],
        justify="space-around",
        widths="equal",
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Test Selector
    """)
    return


@app.cell
def _(campaigns, mo):
    campaign_dropdown = mo.ui.dropdown(
        options={c: c for c in campaigns},
        label="Campaign",
    )
    campaign_dropdown
    return (campaign_dropdown,)


@app.cell
def _(all_data, campaign_dropdown, mo):
    # Filter tests for selected campaign
    if campaign_dropdown.value:
        _mask = all_data["campaign_id"] == campaign_dropdown.value
        tests_in_campaign = sorted(
            all_data.loc[_mask, "test_id"].dropna().unique().tolist()
        )
    else:
        tests_in_campaign = []

    test_dropdown = mo.ui.dropdown(
        options={t: t for t in tests_in_campaign},
        label="Test",
    )
    test_dropdown
    return (test_dropdown,)


@app.cell
def _(all_data, campaign_dropdown, test_dropdown):
    # Build the filtered DataFrame for the selected single test
    if campaign_dropdown.value and test_dropdown.value:
        selected_df = (
            all_data[
                (all_data["campaign_id"] == campaign_dropdown.value)
                & (all_data["test_id"] == test_dropdown.value)
            ]
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
    else:
        selected_df = None
    return (selected_df,)


@app.cell
def _(mo):
    mo.md(r"""
    ## Waveform Plots
    """)
    return


@app.cell
def _(go, make_subplots, mo, selected_df):
    mo.stop(selected_df is None or selected_df.empty, mo.md("*Select a campaign and test above to view waveforms.*"))

    _fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=("Voltage (V)", "Current (mA)", "Load Cell / Thrust"),
    )

    _fig.add_trace(
        go.Scatter(
            x=selected_df["timestamp"],
            y=selected_df["ina260__voltage_v"],
            mode="lines",
            name="Voltage",
            line=dict(color="#636EFA"),
        ),
        row=1,
        col=1,
    )

    _fig.add_trace(
        go.Scatter(
            x=selected_df["timestamp"],
            y=selected_df["ina260__current_ma"],
            mode="lines",
            name="Current",
            line=dict(color="#EF553B"),
        ),
        row=2,
        col=1,
    )

    _fig.add_trace(
        go.Scatter(
            x=selected_df["timestamp"],
            y=selected_df["load_cell__raw_value"],
            mode="lines",
            name="Load Cell",
            line=dict(color="#00CC96"),
        ),
        row=3,
        col=1,
    )

    _fig.update_layout(
        height=750,
        template="plotly_dark",
        title_text=f"Waveforms — {selected_df['test_id'].iloc[0]}",
        showlegend=True,
    )
    _fig.update_xaxes(title_text="Timestamp (ms)", row=3, col=1)
    _fig.update_yaxes(title_text="V", row=1, col=1)
    _fig.update_yaxes(title_text="mA", row=2, col=1)
    _fig.update_yaxes(title_text="Raw", row=3, col=1)

    mo.ui.plotly(_fig)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Summary Statistics
    """)
    return


@app.cell
def _(mo, pd, selected_df):
    mo.stop(selected_df is None or selected_df.empty, mo.md("*Select a test to see summary statistics.*"))

    _metrics = ["ina260__voltage_v", "ina260__current_ma", "load_cell__raw_value", "set_speed"]
    _labels = ["Voltage (V)", "Current (mA)", "Load Cell (raw)", "Set Speed"]

    _rows = []
    for _col, _label in zip(_metrics, _labels):
        if _col in selected_df.columns:
            _s = selected_df[_col].dropna()
            _rows.append(
                {
                    "Metric": _label,
                    "Min": round(_s.min(), 2),
                    "Max": round(_s.max(), 2),
                    "Mean": round(_s.mean(), 2),
                    "Std": round(_s.std(), 2),
                    "Count": int(_s.count()),
                }
            )

    _stats_df = pd.DataFrame(_rows)
    mo.ui.table(_stats_df, selection=None)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Test Comparison
    """)
    return


@app.cell
def _(all_tests, mo):
    compare_selector = mo.ui.multiselect(
        options={t: t for t in all_tests},
        label="Select tests to compare",
    )
    compare_selector
    return (compare_selector,)


@app.cell
def _(all_data, compare_selector, go, make_subplots, mo, px):
    mo.stop(
        not compare_selector.value or len(compare_selector.value) < 2,
        mo.md("*Select 2 or more tests above to overlay their waveforms.*"),
    )

    _colors = px.colors.qualitative.Plotly
    _tests = compare_selector.value

    _fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=("Voltage (V)", "Current (mA)", "Load Cell / Thrust"),
    )

    for _i, _tid in enumerate(_tests):
        _tdf = (
            all_data[all_data["test_id"] == _tid]
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
        _c = _colors[_i % len(_colors)]

        _fig.add_trace(
            go.Scatter(
                x=_tdf["timestamp"],
                y=_tdf["ina260__voltage_v"],
                mode="lines",
                name=f"{_tid} V",
                line=dict(color=_c),
                legendgroup=_tid,
            ),
            row=1,
            col=1,
        )
        _fig.add_trace(
            go.Scatter(
                x=_tdf["timestamp"],
                y=_tdf["ina260__current_ma"],
                mode="lines",
                name=f"{_tid} mA",
                line=dict(color=_c),
                legendgroup=_tid,
                showlegend=False,
            ),
            row=2,
            col=1,
        )
        _fig.add_trace(
            go.Scatter(
                x=_tdf["timestamp"],
                y=_tdf["load_cell__raw_value"],
                mode="lines",
                name=f"{_tid} Load",
                line=dict(color=_c),
                legendgroup=_tid,
                showlegend=False,
            ),
            row=3,
            col=1,
        )

    _fig.update_layout(
        height=750,
        template="plotly_dark",
        title_text="Test Comparison",
        showlegend=True,
    )
    _fig.update_xaxes(title_text="Timestamp (ms)", row=3, col=1)
    _fig.update_yaxes(title_text="V", row=1, col=1)
    _fig.update_yaxes(title_text="mA", row=2, col=1)
    _fig.update_yaxes(title_text="Raw", row=3, col=1)

    mo.ui.plotly(_fig)
    return


if __name__ == "__main__":
    app.run()
