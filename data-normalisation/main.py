# import the Quix Streams modules for interacting with Kafka.
# For general info, see https://quix.io/docs/quix-streams/introduction.html
from quixstreams import Application, State
import time
import os

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

# add timestamp
def add_timestamp(row: dict, key, timestamp, headers, state: State):
    time_0 = state.get("time_0", default=None)
    if not time_0:
        state.set("time_0", timestamp)
        time_0 = state.get("time_0", default=None)
    row["new_timestamp"] = time_0 + row["timestamp"]
    return row

# unpack data
def unpack_data(row: dict):
    new_row = {}
    for k in row:
        if type(row[k]) == dict:
            for j in row[k]:
                new_row[k+"__"+j] = row[k][j]
        else:
            new_row[k] = row[k]

    return new_row


def main():

    # Setup necessary objects
    app = Application(
        consumer_group="data-norm-v3-dev",
        auto_create_topics=True,
        auto_offset_reset="earliest"
    )
    input_topic = app.topic(name=os.environ["input"])
    output_topic = app.topic(name=os.environ["output"])
    sdf = app.dataframe(topic=input_topic)

    # Do StreamingDataFrame operations/transformations here
    sdf = sdf.print(metadata=True)
    sdf = sdf.apply(lambda row: row["data"], expand=True)
    
    # Add timestamp
    sdf = sdf.apply(add_timestamp, metadata=True, stateful=True)

    # Unpack data further
    sdf = sdf.apply(lambda row: unpack_data(row))

    sdf = sdf.set_timestamp(lambda value, key, timestamp, headers: value['new_timestamp'])

    # Finish off by writing to the final result to the output topic
    sdf = sdf.print(metadata=True)
    sdf.to_topic(output_topic)

    # With our pipeline defined, now run the Application
    app.run()


# It is recommended to execute Applications under a conditional main
if __name__ == "__main__":
    main()