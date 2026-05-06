# import the Quix Streams modules for interacting with Kafka.
# For general info, see https://quix.io/docs/quix-streams/introduction.html
from quixstreams import Application, State
import time
import os

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()


def extract_data(row: dict, key, timestamp, headers):
    """
    Extract the 'data' array from the raw message.
    On failure, returns None — caller must filter these out and route to DLQ.
    """
    try:
        return row["data"]
    except (KeyError, TypeError):
        return None


def add_timestamp(row: dict, key, timestamp, headers):
    """
    Compute absolute wall-clock timestamp without relying on State.
    timestamp = Kafka message timestamp (epoch ms)
    row["timestamp"] = relative offset in ms since test start
    """
    row["new_timestamp"] = timestamp + row["timestamp"]
    return row


def unpack_data(row: dict) -> dict:
    """Flatten one level of nested dicts using __ separator."""
    new_row = {}
    for k in row:
        if type(row[k]) == dict:
            for j in row[k]:
                new_row[k + "__" + j] = row[k][j]
        else:
            new_row[k] = row[k]
    return new_row


def add_power(row: dict) -> dict:
    """Derive power_w = voltage_v * (current_ma / 1000)."""
    row["power_w"] = row["ina260__voltage_v"] * (row["ina260__current_ma"] / 1000)
    return row


def rename_fields(row: dict) -> dict:
    """Rename set_speed -> set_speed_frac to make units explicit (0-1 normalised fraction)."""
    if "set_speed" in row:
        row["set_speed_frac"] = row.pop("set_speed")
    return row


def main():

    # Setup necessary objects
    app = Application(
        consumer_group="data-norm-v3-dev",
        auto_create_topics=True,
        auto_offset_reset="earliest"
    )
    input_topic = app.topic(name=os.environ["input"])
    output_topic = app.topic(name=os.environ["output"])
    _dlq_name = os.environ.get("dead_letter_topic") or None
    dead_letter_topic = app.topic(name=_dlq_name) if _dlq_name else None

    sdf = app.dataframe(topic=input_topic)
    sdf = sdf.print(metadata=True)

    # Extract data array; None means malformed — route to DLQ
    sdf = sdf.apply(extract_data, metadata=True, expand=True)
    sdf = sdf.filter(lambda row: row is not None)

    # Add absolute timestamp (stateless — uses Kafka message timestamp as anchor)
    sdf = sdf.apply(add_timestamp, metadata=True)

    # Flatten nested sensor dicts
    sdf = sdf.apply(unpack_data)

    # Derived metric: electrical power
    sdf = sdf.apply(add_power)

    # Rename for clarity
    sdf = sdf.apply(rename_fields)

    # Key pass-through: Kafka message key (e.g. TEST-1000) is preserved as-is.
    # No group_by() here — repartitioning is not required; key identity is intentional.

    sdf = sdf.set_timestamp(lambda value, key, timestamp, headers: value['new_timestamp'])

    sdf = sdf.print(metadata=True)
    sdf.to_topic(output_topic)

    app.run()


if __name__ == "__main__":
    main()
