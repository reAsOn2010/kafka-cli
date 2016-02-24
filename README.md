## kafka-cli

Interactive command line tool for kafka ops.

tested with kafka version:

* 0.8.2.2

### usage

three import config:

* KAFKA_PATH --- kafka binary path
* ZOOKEEPER --- zookeeper host port and path
* BROEKR_LIST --- broker id list for topic migration

config get/set:

* setpath
* setbrokers
* setzk
* getpath
* getbrokers
* getzk

supported commands:

* refresh --- get current topics metadata, used for topic name autocomplete
* status --- show topic(s) metadata
* execute --- do migration on specific topic(s)
* verify --- verify migration progress
* elect --- force leader election on specific topic(s)
* unbalanced --- show topics which are not balanced
* help --- show help message
* exit

some examples:

```
<zk01:2190/kafka-cluster|[0, 1, 2]> status timeline.log
Topic:timeline.log	PartitionCount:6	ReplicationFactor:2	Configs:
	Topic: timeline.log	Partition: 0	Leader: 1	Replicas: 1,2	Isr: 2,1
	Topic: timeline.log	Partition: 1	Leader: 2	Replicas: 2,0	Isr: 0,2
	Topic: timeline.log	Partition: 2	Leader: 0	Replicas: 0,1	Isr: 1,0
	Topic: timeline.log	Partition: 3	Leader: 1	Replicas: 1,0	Isr: 0,1
	Topic: timeline.log	Partition: 4	Leader: 2	Replicas: 2,1	Isr: 1,2
	Topic: timeline.log	Partition: 5	Leader: 0	Replicas: 0,2	Isr: 2,0
```

```
<zk01:2190/kafka-cluster|[0, 1, 2]> elect timeline.log
Topic:timeline.log	PartitionCount:6	ReplicationFactor:2	Configs:
	Topic: timeline.log	Partition: 0	Leader: 1	Replicas: 1,2	Isr: 2,1
	Topic: timeline.log	Partition: 1	Leader: 2	Replicas: 2,0	Isr: 0,2
	Topic: timeline.log	Partition: 2	Leader: 0	Replicas: 0,1	Isr: 1,0
	Topic: timeline.log	Partition: 3	Leader: 1	Replicas: 1,0	Isr: 0,1
	Topic: timeline.log	Partition: 4	Leader: 2	Replicas: 2,1	Isr: 1,2
	Topic: timeline.log	Partition: 5	Leader: 0	Replicas: 0,2	Isr: 2,0

really want to do this? [y/n]
```

```
<zk01:2190/kafka-cluster|[0, 1, 2]> execute timeline.log sys.log
Current partition replica assignment

{"version":1,"partitions":[{"topic":"timeline.log","partition":1,"replicas":[2,0]},{"topic":"sys.log","partition":0,"replicas":[0,1]},{"topic":"timeline.log","partition":5,"replicas":[0,2]},{"topic":"timeline.log","partition":4,"replicas":[2,1]},{"topic":"sys.log","partition":3,"replicas":[0,2]},{"topic":"timeline.log","partition":0,"replicas":[1,2]},{"topic":"sys.log","partition":2,"replicas":[2,0]},{"topic":"sys.log","partition":4,"replicas":[1,0]},{"topic":"timeline.log","partition":3,"replicas":[1,0]},{"topic":"sys.log","partition":1,"replicas":[1,2]},{"topic":"sys.log","partition":5,"replicas":[2,1]},{"topic":"timeline.log","partition":2,"replicas":[0,1]}]}
Proposed partition reassignment configuration

{"version":1,"partitions":[{"topic":"timeline.log","partition":1,"replicas":[1,2]},{"topic":"sys.log","partition":0,"replicas":[1,0]},{"topic":"timeline.log","partition":5,"replicas":[2,1]},{"topic":"timeline.log","partition":4,"replicas":[1,0]},{"topic":"sys.log","partition":3,"replicas":[1,2]},{"topic":"timeline.log","partition":0,"replicas":[0,1]},{"topic":"sys.log","partition":4,"replicas":[2,0]},{"topic":"sys.log","partition":2,"replicas":[0,2]},{"topic":"timeline.log","partition":3,"replicas":[0,2]},{"topic":"sys.log","partition":5,"replicas":[0,1]},{"topic":"sys.log","partition":1,"replicas":[2,1]},{"topic":"timeline.log","partition":2,"replicas":[2,0]}]}

Status of partition reassignment:
ERROR: Assigned replicas (0,2) don't match the list of replicas for reassignment (1,2) for partition [sys.log,3]
ERROR: Assigned replicas (1,0) don't match the list of replicas for reassignment (0,2) for partition [timeline.log,3]
ERROR: Assigned replicas (0,1) don't match the list of replicas for reassignment (2,0) for partition [timeline.log,2]
ERROR: Assigned replicas (2,0) don't match the list of replicas for reassignment (0,2) for partition [sys.log,2]
ERROR: Assigned replicas (2,0) don't match the list of replicas for reassignment (1,2) for partition [timeline.log,1]
ERROR: Assigned replicas (1,2) don't match the list of replicas for reassignment (2,1) for partition [sys.log,1]
ERROR: Assigned replicas (0,2) don't match the list of replicas for reassignment (2,1) for partition [timeline.log,5]
ERROR: Assigned replicas (2,1) don't match the list of replicas for reassignment (1,0) for partition [timeline.log,4]
ERROR: Assigned replicas (1,0) don't match the list of replicas for reassignment (2,0) for partition [sys.log,4]
ERROR: Assigned replicas (1,2) don't match the list of replicas for reassignment (0,1) for partition [timeline.log,0]
ERROR: Assigned replicas (2,1) don't match the list of replicas for reassignment (0,1) for partition [sys.log,5]
ERROR: Assigned replicas (0,1) don't match the list of replicas for reassignment (1,0) for partition [sys.log,0]
Reassignment of partition [sys.log,3] failed
Reassignment of partition [timeline.log,3] failed
Reassignment of partition [timeline.log,2] failed
Reassignment of partition [sys.log,2] failed
Reassignment of partition [timeline.log,1] failed
Reassignment of partition [sys.log,1] failed
Reassignment of partition [timeline.log,5] failed
Reassignment of partition [timeline.log,4] failed
Reassignment of partition [sys.log,4] failed
Reassignment of partition [timeline.log,0] failed
Reassignment of partition [sys.log,5] failed
Reassignment of partition [sys.log,0] failed

really want to do this? [y/n]
```
