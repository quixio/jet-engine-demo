import quixlab as ql

canvas = ql.Canvas(
    title="Jet Engine Test Rig Dashboard",
    lake_tree_open=["config-enriched-data"],
)


# ── Header ──────────────────────────────────────────────────────────────────
@canvas.cell(position=(60, 0), size=(1760, 100), code_height=160)
def header():
    return ql.ui.markdown(
        """
        # Jet Engine Test Rig Dashboard
        Interactive explorer for thrust-stand telemetry stored in QuixLake.
        """
    )


# ── Data load ──────────────────────────────────────────────────────────────
@canvas.dataset(position=(60, 130), size=(560, 320), code_height=160)
def all_data():
    return ql.sql("SELECT * FROM config-enriched-data")


# ── Campaign overview ──────────────────────────────────────────────────────
@canvas.cell(position=(60, 470), size=(1760, 60), code_height=120)
def campaign_overview_title():
    return ql.ui.markdown("## Campaign Overview")


@canvas.cell(
    position=(60, 550),
    size=(870, 460),
    code_height=200,
    viz={"type": "bar", "x": "campaign_id", "y": "test_runs"},
)
def runs_per_campaign(all_data):
    return (
        all_data.groupby("campaign_id")["test_id"]
        .nunique()
        .reset_index()
        .rename(columns={"test_id": "test_runs"})
        .sort_values("campaign_id")
    )


@canvas.cell(
    position=(950, 550),
    size=(870, 460),
    code_height=200,
    viz={"type": "bar", "x": "campaign_id", "y": "data_points"},
)
def points_per_campaign(all_data):
    return (
        all_data.groupby("campaign_id")
        .size()
        .reset_index(name="data_points")
        .sort_values("campaign_id")
    )


# ── Test selector ──────────────────────────────────────────────────────────
@canvas.cell(position=(60, 1040), size=(1760, 60), code_height=120)
def selector_title():
    return ql.ui.markdown("## Test Selector")


@canvas.cell(position=(60, 1120), size=(420, 180), code_height=160)
def campaign_dropdown(all_data):
    campaigns = sorted(all_data["campaign_id"].dropna().unique().tolist())
    return ql.ui.dropdown(campaigns, label="Campaign")


@canvas.cell(position=(500, 1120), size=(420, 180), code_height=200)
def test_dropdown(all_data, campaign_dropdown):
    campaign = campaign_dropdown.value
    if campaign:
        mask = all_data["campaign_id"] == campaign
        tests = sorted(all_data.loc[mask, "test_id"].dropna().unique().tolist())
    else:
        tests = []
    return ql.ui.dropdown(tests, label="Test")


@canvas.cell(position=(940, 1120), size=(880, 180), code_height=240)
def selected_df(all_data, campaign_dropdown, test_dropdown):
    campaign = campaign_dropdown.value
    test_id = test_dropdown.value
    if not campaign or not test_id:
        return None
    return (
        all_data[
            (all_data["campaign_id"] == campaign)
            & (all_data["test_id"] == test_id)
        ]
        .sort_values("timestamp")
        .reset_index(drop=True)
    )


# ── Waveform plots (single test) ───────────────────────────────────────────
@canvas.cell(position=(60, 1340), size=(1760, 60), code_height=120)
def waveform_title():
    return ql.ui.markdown("## Waveform Plots")


@canvas.cell(position=(60, 1420), size=(1760, 820), code_height=320)
def waveforms(selected_df):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    if selected_df is None or selected_df.empty:
        return ql.ui.markdown(
            "*Select a campaign and test above to view waveforms.*"
        )

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=("Voltage (V)", "Current (mA)", "Load Cell / Thrust"),
    )

    fig.add_trace(
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
    fig.add_trace(
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
    fig.add_trace(
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

    fig.update_layout(
        height=750,
        title_text=f"Waveforms — {selected_df['test_id'].iloc[0]}",
        showlegend=True,
    )
    fig.update_xaxes(title_text="Timestamp (ms)", row=3, col=1)
    fig.update_yaxes(title_text="V", row=1, col=1)
    fig.update_yaxes(title_text="mA", row=2, col=1)
    fig.update_yaxes(title_text="Raw", row=3, col=1)

    return fig


# ── Summary statistics ─────────────────────────────────────────────────────
@canvas.cell(position=(60, 2280), size=(1760, 60), code_height=120)
def stats_title():
    return ql.ui.markdown("## Summary Statistics")


@canvas.cell(
    position=(60, 2360),
    size=(880, 460),
    code_height=240,
    viz={"type": "table"},
)
def stats_table(selected_df):
    import pandas as pd

    if selected_df is None or selected_df.empty:
        return ql.ui.markdown("*Select a test to see summary statistics.*")

    metrics = [
        ("ina260__voltage_v", "Voltage (V)"),
        ("ina260__current_ma", "Current (mA)"),
        ("load_cell__raw_value", "Load Cell (raw)"),
        ("set_speed", "Set Speed"),
    ]
    rows = []
    for col, label in metrics:
        if col in selected_df.columns:
            s = selected_df[col].dropna()
            rows.append({
                "Metric": label,
                "Min": round(s.min(), 2) if len(s) else None,
                "Max": round(s.max(), 2) if len(s) else None,
                "Mean": round(s.mean(), 2) if len(s) else None,
                "Std": round(s.std(), 2) if len(s) else None,
                "Count": int(s.count()),
            })
    return pd.DataFrame(rows)


# ── Test comparison (two tests overlaid) ───────────────────────────────────
@canvas.cell(position=(60, 2860), size=(1760, 60), code_height=120)
def compare_title():
    return ql.ui.markdown(
        """
        ## Test Comparison
        QuixLab doesn't ship a multiselect — pick two tests below to overlay.
        """
    )


@canvas.cell(position=(60, 2960), size=(420, 180), code_height=200)
def compare_a(all_data):
    tests = sorted(all_data["test_id"].dropna().unique().tolist())
    return ql.ui.dropdown(tests, label="Test A")


@canvas.cell(position=(500, 2960), size=(420, 180), code_height=200)
def compare_b(all_data):
    tests = sorted(all_data["test_id"].dropna().unique().tolist())
    return ql.ui.dropdown(tests, label="Test B")


@canvas.cell(position=(60, 3160), size=(1760, 820), code_height=320)
def compare_plot(all_data, compare_a, compare_b):
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    a, b = compare_a.value, compare_b.value
    selected = [t for t in (a, b) if t]
    selected = list(dict.fromkeys(selected))  # de-dupe while preserving order
    if len(selected) < 2:
        return ql.ui.markdown(
            "*Pick two different tests above to overlay their waveforms.*"
        )

    colors = px.colors.qualitative.Plotly
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=("Voltage (V)", "Current (mA)", "Load Cell / Thrust"),
    )

    for i, tid in enumerate(selected):
        tdf = (
            all_data[all_data["test_id"] == tid]
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
        c = colors[i % len(colors)]
        fig.add_trace(
            go.Scatter(
                x=tdf["timestamp"], y=tdf["ina260__voltage_v"],
                mode="lines", name=f"{tid} V",
                line=dict(color=c), legendgroup=tid,
            ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=tdf["timestamp"], y=tdf["ina260__current_ma"],
                mode="lines", name=f"{tid} mA",
                line=dict(color=c), legendgroup=tid, showlegend=False,
            ),
            row=2, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=tdf["timestamp"], y=tdf["load_cell__raw_value"],
                mode="lines", name=f"{tid} Load",
                line=dict(color=c), legendgroup=tid, showlegend=False,
            ),
            row=3, col=1,
        )

    fig.update_layout(height=750, title_text="Test Comparison", showlegend=True)
    fig.update_xaxes(title_text="Timestamp (ms)", row=3, col=1)
    fig.update_yaxes(title_text="V", row=1, col=1)
    fig.update_yaxes(title_text="mA", row=2, col=1)
    fig.update_yaxes(title_text="Raw", row=3, col=1)
    return fig


if __name__ == "__main__":
    canvas.serve()
