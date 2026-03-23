import os
print(os.environ)
from quixstreams import Application
from quixstreams.dataframe.joins.lookups.quix_configuration_service import QuixConfigurationService
from quixstreams.dataframe.joins.lookups.quix_configuration_service.lookup import JSONField

def as_json_field(jsonpath):
    return JSONField(type="TestConfig", jsonpath=jsonpath)

def get_fields():
    return {
        "test_id": as_json_field("test_id"),
        "environment_id": as_json_field("environment_id"),
        "campaign_id": as_json_field("campaign_id"),
        "device_id": as_json_field("devices[0].device_id"),  # Get first device's device_id
        "device_version": as_json_field("devices[0].device_version"),  # Get first device's device_version
        "operator": as_json_field("operator"),
        "throttle": as_json_field("sensors.throttle.value"),
        "hold_time": as_json_field("sensors.hold_time.value"),
        "battery_id": as_json_field("sensors.battery.id"),
        "motor_id": as_json_field("sensors.motor.id"),
        "shroud_id": as_json_field("sensors.shroud.id"),
        "fan_id": as_json_field("sensors.fan.id")
    }



def main():
    app = Application(
        consumer_group=os.environ["CONSUMER_GROUP"],
        auto_create_topics=True,
        auto_offset_reset="earliest"
    )
    data_topic = app.topic(name=os.environ["DATA_TOPIC"], key_deserializer="str")
    config_topic = app.topic(name=os.environ["CONFIG_TOPIC"])
    output_topic = app.topic(name=os.environ["OUTPUT_TOPIC"], key_serializer="str")

    app.dataframe(topic=data_topic).join_lookup(
        lookup=QuixConfigurationService(
            topic=config_topic,
            app_config=app.config,
            quix_sdk_token=os.environ["CONFIG_SDK_TOKEN"],
        ),
        fields=get_fields()
    ).to_topic(output_topic)

    app.run()


if __name__ == "__main__":
    main()