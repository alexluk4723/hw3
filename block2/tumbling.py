from pyflink.common import SimpleStringSchema
from pyflink.common.typeinfo import Types, RowTypeInfo
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.datastream import StreamExecutionEnvironment, TimeCharacteristic
from pyflink.datastream.connectors import DeliveryGuarantee
from pyflink.datastream.connectors.kafka import KafkaSource, \
    KafkaOffsetsInitializer, KafkaSink, KafkaRecordSerializationSchema
from pyflink.datastream.formats.json import JsonRowDeserializationSchema

from pyflink.datastream.window import TumblingEventTimeWindows
from pyflink.common import Time

def tumbling_windows_temperature():
    env = StreamExecutionEnvironment.get_execution_environment()
    # Set the parallelism to be one to make sure that all data including fired timer and normal data
    # are processed by the same worker and the collected result would be in order which is good for
    # assertion.
    env.set_parallelism(1)
    env.set_stream_time_characteristic(TimeCharacteristic.EventTime)
    

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
                               .set_topic('itmo2023_result')
                               .set_value_serialization_schema(SimpleStringSchema())
                               .build()
                               ) \
        .set_delivery_guarantee(DeliveryGuarantee.AT_LEAST_ONCE) \
        .build()
    ds = env.from_source(source, WatermarkStrategy.no_watermarks(), "Kafka Source")
    ds.window_all(TumblingEventTimeWindows.of(Time.seconds(2))) \
        .reduce(
            lambda t1, t2: t1 if t1[1] > t2[1] else t2,
            output_type=Types.TUPLE([Types.INT(), Types.DOUBLE(), Types.INT()]),
        ) \
        .sink_to(sink)
    env.execute_async("Devices preprocessing")

if __name__ == '__main__':
    tumbling_windows_temperature()
