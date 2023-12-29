# Общая часть
docker-compose build
docker-compose up -d
docker-compose exec kafka kafka-topics.sh --bootstrap-server kafka:9092 --create --topic itmo2023 --partitions 1 --replication-factor 1
docker-compose exec kafka kafka-topics.sh --bootstrap-server kafka:9092 --create --topic itmo2023_result --partitions 1 --replication-factor 1
python3 producer.py

# Далее в зависимости от типа window

# tumbling 
docker-compose exec jobmanager ./bin/flink run -py /opt/pyflink/block2/tumbling.py -d
# session (в файле producer теперь сообщение шлется раз в randint(1, 4) секунды чтобы была возможность протестировать session с окном на 2 секунды)
docker-compose exec jobmanager ./bin/flink run -py /opt/pyflink/block2/session.py -d
# sliding
docker-compose exec jobmanager ./bin/flink run -py /opt/pyflink/block2/sliding.py -d

# И consumer

python3 consumer.py