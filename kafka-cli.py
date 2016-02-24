#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import cmd
import json
import os
import re
import sys
import subprocess
import readline

parser = argparse.ArgumentParser(description='migrate kafka topic partition')
parser.add_argument('cmd', nargs='*', type=str, help='[execute|verify|status|elect|unbalanced]')
parser.add_argument('--topics', nargs='*', type=str, help='apply to these topics?')

args = parser.parse_args()

histfile = os.path.join(os.path.expanduser("~"), ".kafka_migrate_history")

try:
    readline.read_history_file(histfile)
except IOError:
    pass

import atexit
atexit.register(readline.write_history_file, histfile)


class KafkaUtils(object):

    def __init__(self):
        self.KAFKA_PATH = '/usr/local/kafka/bin'
        self.BROKER_LIST = [0, 1, 2]
        self.ZOOKEEPER = 'zk01:2190/kafka-cluster'
        self.METADATA = {}

    def broker_str(self):
        return ','.join(map(str, self.BROKER_LIST))

    def topic_to_move_fn(self):
        return 'gen-topic-to-move.json'

    def topic_reassignment_fn(self):
        return 'gen-reassignment.json'

    def topic_elect_fn(self):
        return 'gen-elect.json'

    def run_then_get_result(self, cmd):
        if 'kafka' in cmd:
            p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
            return p.stdout.read()
        else:
            raise RuntimeError('Invalid command!')

    def generate_topic_to_move_json(self, topics):
        with open(self.topic_to_move_fn(), 'w+') as f:
            d = {'topics': [{'topic': topic} for topic in topics], 'version': 1}
            f.write(json.dumps(d))

    def generate_reassignment_json(self, topics):
        self.generate_topic_to_move_json(topics)
        with open(self.topic_reassignment_fn(), 'w+') as f:
            result = self.run_then_get_result(
                '%s/kafka-reassign-partitions.sh --broker-list %s --zookeeper %s --topics-to-move-json-file %s --generate'
                % (self.KAFKA_PATH, self.broker_str(), self.ZOOKEEPER, self.topic_to_move_fn())
            )
            reassignment = result.split('\n')[-2]
            print result
            f.write(reassignment)

    def verify(self):
        result = self.run_then_get_result(
            '%s/kafka-reassign-partitions.sh --broker-list %s --zookeeper %s --reassignment-json-file %s --verify'
            % (self.KAFKA_PATH, self.broker_str(), self.ZOOKEEPER, self.topic_reassignment_fn())
        )
        print result

    def execute(self, topics):
        yes = raw_input('really want to do this? [y/n]')
        if yes == 'y':
            result = self.run_then_get_result(
                '%s/kafka-reassign-partitions.sh --broker-list %s --zookeeper %s --reassignment-json-file %s --execute'
                % (self.KAFKA_PATH, self.broker_str(), self.ZOOKEEPER, self.topic_reassignment_fn())
            )
            print result
        else:
            pass

    def elect(self, topics):
        self.metadata(topics, verbose=True)
        yes = raw_input('really want to do this? [y/n]')
        if yes != 'y':
            return
        with open(self.topic_elect_fn(), 'w+') as f:
            d = {'partitions': []}
            for t in topics:
                d['partitions'].extend([{'topic': t, 'partition': i} for i in range(0, self.METADATA[t]['partition_count'])])
            f.write(json.dumps(d))
        print json.dumps(d)
        print self.run_then_get_result(
            '%s/kafka-preferred-replica-election.sh --zookeeper %s --path-to-json-file %s'
            % (self.KAFKA_PATH, self.ZOOKEEPER, self.topic_elect_fn())
        )

    def metadata(self, topics=[], verbose=False):
        if not topics:
            raw = self.run_then_get_result('%s/kafka-topics.sh --zookeeper %s --describe' % (self.KAFKA_PATH, self.ZOOKEEPER))
        else:
            raw = ''
            for t in topics:
                raw += self.run_then_get_result('%s/kafka-topics.sh --zookeeper %s --describe --topic %s' % (self.KAFKA_PATH, self.ZOOKEEPER, t))
        if verbose:
            print raw
        splited = raw.split('\n')
        metadata = {}
        for line in splited:
            if not line:
                continue
            if line.startswith('Topic'):
                topic = line.split('\t')[0].split(':')[-1].strip()
                partition_count = int(line.split('\t')[1].split(':')[-1])
                metadata[topic] = {'partition_count': partition_count}
            else:
                leader = int(line.split('\t')[3].split(':')[-1])
                topic = line.split('\t')[1].split(':')[-1].strip()
                partition = int(line.split('\t')[2].split(':')[-1])
                if not metadata[topic].get(leader, None):
                    metadata[topic][leader] = [partition]
                else:
                    metadata[topic][leader].append(partition)

        for t in metadata:
            import math
            leader_count_should_be = math.ceil(metadata[t]['partition_count'] / len(self.BROKER_LIST))
            for broker in self.BROKER_LIST:
                if not metadata[t].get(broker, None) or len(metadata[t][broker]) != leader_count_should_be:
                    metadata[t]['is_balanced'] = False
                    continue
            metadata[t]['is_balanced'] = True
        self.METADATA.update(metadata)
        return metadata

    def is_balanced(self, partition_count, leaders):
        import math
        leader_count_should_be = math.ceil(partition_count / len(self.BROKER_LIST))
        for _, v in leaders.iteritems():
            if v != leader_count_should_be:
                return False
        return True

    def unbalanced(self):
        raw = self.run_then_get_result('%s/kafka-topics.sh --describe --zookeeper %s' % (self.KAFKA_PATH, self.ZOOKEEPER))
        splited = raw.split('\n')
        topic = None
        partition_count = None
        leaders = {}
        for line in splited:
            if not line:
                continue
            if line.startswith('Topic'):
                if topic is not None and not self.is_balanced(partition_count, leaders):
                    print '%s %s' % (topic, leaders)
                topic = line.split('\t')[0].split(':')[-1]
                partition_count = int(line.split('\t')[1].split(':')[-1])
                leaders = {}
            else:
                leader = line.split('\t')[3].split(':')[-1]
                if not leaders.get(int(leader)):
                    leaders[int(leader)] = 1
                else:
                    leaders[int(leader)] += 1

        if topic is None:
            pass
        elif not self.is_balanced(partition_count, leaders):
            print '%s %s' % (topic, leaders)


class KafkaMigrationCmd(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)

    def preloop(self):
        self.util = KafkaUtils()
        self.refresh_prompt()
        self.DELIMITER = re.compile('[ ,]+')
        print 'Make sure KAFKA_PATH, BROKER_LIST and ZOOKEEPER config is right!!!'
        self.do_getzk('')
        self.do_getbrokers('')
        self.do_getpath('')

    def refresh_prompt(self):
        prompt = '<%s|%s> ' % (self.util.ZOOKEEPER, self.util.BROKER_LIST)
        self.prompt = prompt

    def do_setpath(self, line):
        '''set kafka scripts path'''
        self.util.KAFKA_PATH = line
        if not os.path.isfile('%s/kafka-topics.sh' % self.util.KAFKA_PATH):
            print 'WARN: maybe kafka bin path is wrong!'
        print 'KAFKA_PATH set to: %s' % self.util.KAFKA_PATH

    def do_getpath(self, line):
        '''get kafka scripts path'''
        if not os.path.isfile('%s/kafka-topics.sh' % self.util.KAFKA_PATH):
            print 'WARN: maybe kafka bin path is wrong!'
        print 'KAFKA_PATH set to: %s' % self.util.KAFKA_PATH

    def do_refresh(self, line):
        '''refresh metadata of topics, useful when you need topic name autocomplete'''
        verbose = line == 'verbose'
        self.util.metadata(verbose=verbose)

    def complete_refresh(self, text, line, start_index, end_index):
        params = ['verbose']
        return [p for p in params if p.startswith(text)]

    def do_getzk(self, line):
        '''show current zookeeper address'''
        print 'ZOOKEEPER set to: %s' % self.util.ZOOKEEPER

    def do_setzk(self, line):
        '''set zookeeper address'''
        self.util.ZOOKEEPER = line.strip()
        self.refresh_prompt()
        print 'ZOOKEEPER address set to: %s' % self.util.ZOOKEEPER

    def do_getbrokers(self, line):
        '''show broker ids'''
        print 'BROKER_LIST set to: %s' % self.util.BROKER_LIST

    def do_setbrokers(self, line):
        '''set broker ids'''
        brokers = map(int, self.DELIMITER.split(line))
        self.util.BROKER_LIST = brokers
        self.refresh_prompt()
        print 'BROKER_LIST set to: %s' % self.util.BROKER_LIST

    def do_status(self, line):
        '''show status of topics, if no topic specified, show all'''
        topics = self.DELIMITER.split(line)
        self.util.metadata(topics, verbose=True)

    def complete_status(self, text, line, start_index, end_index):
        return [topic for topic in self.util.METADATA if topic.startswith(text)]

    def do_execute(self, line):
        '''do migration for specific topics'''
        topics = self.DELIMITER.split(line)
        if not topics:
            print 'Topics must be specified'
            return
        self.util.generate_reassignment_json(topics)
        self.util.verify()
        self.util.execute(topics)

    def complete_execute(self, text, line, start_index, end_index):
        return [topic for topic in self.util.METADATA if topic.startswith(text)]

    def do_verify(self, line):
        '''check migration status'''
        self.util.verify()

    def do_elect(self, line):
        '''force leader election for specific topics'''
        topics = self.DELIMITER.split(line)
        if not topics:
            print 'Topics must be specified'
            return
        self.util.elect(topics)

    def complete_elect(self, text, line, start_index, end_index):
        return [topic for topic in self.util.METADATA if topic.startswith(text)]

    def do_unbalanced(self, line):
        '''show all unbalanced topics'''
        self.util.unbalanced()

    def do_exit(self, line):
        sys.exit(0)


if __name__ == '__main__':
    if not args.cmd:
        cmd = KafkaMigrationCmd()
        cmd.cmdloop()
    else:
        util = KafkaUtils()
        if args.cmd == 'verify':
            util.verify()
        elif args.cmd == 'execute':
            if not args.topics:
                print 'Need topics specified'
                sys.exit(1)
            util.generate_reassignment_json(args.topics)
            util.verify()
            util.execute(args.topics)
        elif args.cmd == 'elect':
            if not args.topics:
                print 'Need topics specified'
                sys.exit(1)
            util.elect(args.topics)
        elif args.cmd == 'status':
            util.metadata(args.topics, verbose=True)
        elif args.cmd == 'unbalanced':
            util.unbalanced()
