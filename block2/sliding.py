from pyflink.common import SimpleStringSchema
from pyflink.common.typeinfo import Types, RowTypeInfo
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment, TimeCharacteristic, CheckpointingMode
from pyflink.datastream.connectors import DeliveryGuarantee
from pyflink.datastream.connectors.kafka import KafkaSource, \
    KafkaOffsetsInitializer, KafkaSink, KafkaRecordSerializationSchema
from pyflink.datastream.formats.json import JsonRowDeserializationSchema
from pyflink.datastream.checkpoint_storage import CheckpointStorage
from pyflink.datastream.window import SlidingProcessingTimeWindows, SlidingEventTimeWindows
from pyflink.common import Time
from pyflink.datastream.functions import MapFunction

def sliding_windows_temperature():
    env = StreamExecutionEnvironment.get_execution_environment()
    # Set the parallelism to be one to make sure that all data including fired timer and normal data
    # are processed by the same worker and the collected result would be in order which is good for
    # assertion.
    env.set_parallelism(1)
    env.set_stream_time_characteristic(TimeCharacteristic.EventTime)

    env.enable_checkpointing(1000)
    env.get_checkpoint_config().set_checkpointing_mode(CheckpointingMode.EXACTLY_ONCE)
    env.get_checkpoint_config().set_checkpoint_storage(CheckpointStorage('file:///opt/pyflink/tmp/checkpoints/logs'))

    type_info: RowTypeInfo = Types.ROW_NAMED(['device_id', 'temperature', 'execution_time'],
                                             [Types.INT(), Types.DOUBLE(), Types.INT()])

    json_row_schema = JsonRowDeserializationSchema.builder().type_info(type_info).build()

    source = KafkaSource.builder() \
        .set_bootstrap_servers('kafka:9092') \
        .set_topics('itmo2023') \
        .set_group_id('pyflink-e2e-source') \
        .set_starting_offsets(KafkaOffsetsInitializer.earliest()) \
        .set_value_only_deserializer(json_row_schema) \
        .build()

    sink = KafkaSink.builder() \
        .set_bootstrap_servers('kafka:9092') \
        .set_record_serializer(KafkaRecordSerializationSchema.builder()
                               .set_topic('itmo2023result')
                               .set_value_serialization_schema(SimpleStringSchema())
                               .build()
                               ) \
        .set_delivery_guarantee(DeliveryGuarantee.AT_LEAST_ONCE) \
        .build()
    ds = env.from_source(source, WatermarkStrategy.no_watermarks(), "Kafka Source")
    ds.window_all(SlidingProcessingTimeWindows.of(Time.seconds(8), Time.seconds(7))) \
        .reduce(
            lambda t1, t2: t1 if t1.temperature > t2.temperature else t2
        ) \
        .map(TemperatureFunction(), Types.STRING()) \
        .sink_to(sink)
    env.execute_async("Devices preprocessing")

class TemperatureFunction(MapFunction):

    def map(self, value):
        device_id, temperature, execution_time = value
        return str({"device_id": device_id, "temperature": temperature - 273, "execution_time": execution_time})


if __name__ == '__main__':
    sliding_windows_temperature()
