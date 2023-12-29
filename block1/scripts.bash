
# для запуска обычного
docker-compose exec jobmanager ./bin/flink run -py /opt/pyflink/block1/checkpoint.py -d

# с hdfs
docker-compose exec jobmanager ./bin/flink run -py /opt/pyflink/block1/checkpoint_hdfs.py -d

python3 producer.py
python3 consumer.py