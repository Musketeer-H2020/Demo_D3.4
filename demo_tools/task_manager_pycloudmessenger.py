# -*- coding: utf-8 -*-
'''
Task managing utilities
@author:  Angel Navia Vázquez
'''
__author__ = "Angel Navia Vázquez, UC3M."

import random, string
import time
import sys, os
import json

try:
    import pycloudmessenger.ffl.abstractions as ffl
    import pycloudmessenger.ffl.fflapi as fflapi
    import pycloudmessenger.serializer as serializer
except:
    print("pycloudmessenger is not installed, use:")
    print("pip install https://github.com/IBM/pycloudmessenger/archive/v0.3.0.tar.gz")
    sys.exit()


class Task_Manager:
    """
    """


class Task_Manager:
    """
    """

    def __init__(self, credentials_filename):
        """
        """
        try:
            with open(credentials_filename, 'r') as f:
                credentials = json.load(f)

            self.credentials_filename = credentials_filename
        except:
            print(
                '\n' + '#' * 80 + '\nERROR - The file musketeer.json is not available, please put it under the following path: "' + os.path.abspath(
                    os.path.join("", "../../")) + '"\n' + '#' * 80 + '\n')
            sys.exit()

    def create_master_random_taskname(self, pom, Nworkers, user_name=None, user_password='Tester', user_org='Musketeer',
                                      task_name='Test', random_taskname=True):
        self.pom = pom
        self.Nworkers = Nworkers
        config = 'cloud'
        if random_taskname:
            rword = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
            version = '_' + rword
        else:
            version = '_v2'
        task_name += version
        self.task_name = task_name
        user_password += version

        if user_name is None:
            user_name = 'ma' + version

        fflapi.create_user(user_name, user_password, user_org, self.credentials_filename)
        ffl.Factory.register(config, fflapi.Context, fflapi.User, fflapi.Aggregator, fflapi.Participant)
        context_master = ffl.Factory.context(config, self.credentials_filename, user_name, user_password,
                                             encoder=serializer.Base64Serializer)

        # Create task
        task_definition = {"task_name": task_name,
                           "owner": user_name,
                           "quorum": self.Nworkers,
                           "POM": self.pom,
                           "model_type": "None",
                           }

        ffl_user_master = ffl.Factory.user(context_master)
        with ffl_user_master:
            try:
                result = ffl_user_master.create_task(task_name, ffl.Topology.star, task_definition)
            except Exception as err:
                print(str(err).split(':')[1])

        '''
        with ffl_user_master:
            try:
                ffl_user_master.create_user(user_name, user_password, user_org)
            except Exception as err:
                print(str(err).split(':')[1])

        context_master = ffl.Factory.context(config, self.credentials_filename, user_name, user_password, encoder = serializer.Base64Serializer)
        ffl_user_master = ffl.Factory.user(context_master)
        '''

        # We write to disk the name of the task, to be read by the workers. In the real system, 
        # the task_name must be communicated by other means.
        with open('current_taskname.txt', 'w') as f:
            f.write(task_name)

        self.aggregator = ffl.Factory.aggregator(context_master, task_name=task_name)
        # return context_master, task_name
        return self.aggregator

    def create_master_and_taskname(self, display, logger, task_definition, user_name=None, user_password='Tester',
                                   task_name='Test', user_org='TREE', verbose=False):
        self.task_name = task_name
        self.Nworkers = task_definition['quorum']
        config = 'cloud'

        # Create context for the cloud communications
        try:
            fflapi.create_user(user_name, user_password, user_org, self.credentials_filename)
        except Exception as err:
            display('The user %s is already registered in pycloudmessenger platform.' % user_name, logger, verbose)
        ffl.Factory.register(config, fflapi.Context, fflapi.User, fflapi.Aggregator, fflapi.Participant)
        context_master = ffl.Factory.context(config, self.credentials_filename, user_name, user_password,
                                             encoder=serializer.Base64Serializer)

        # Create task
        ffl_user_master = ffl.Factory.user(context_master)
        with ffl_user_master:
            try:
                result = ffl_user_master.create_task(task_name, ffl.Topology.star, task_definition)
            except Exception as err:
                display('Error - %' % str(err).split(':')[1], logger, verbose)

        self.aggregator = ffl.Factory.aggregator(context_master, task_name=task_name)
        return self.aggregator

    def get_current_task_name(self):
        task_available = False
        while not task_available:
            try:
                with open('current_taskname.txt', 'r') as f:
                    self.task_name = f.read()
                task_available = True
            except:
                print('No available task yet...')
                time.sleep(1)
                pass
        return self.task_name

    def create_worker_join_task(self, id, user_password='Tester', user_org='Musketeer'):
        created = False
        while not created:
            try:

                self.task_name = self.get_current_task_name()
                print(self.task_name)
                config = 'cloud'

                version = self.task_name.split('_')[1]
                worker_name = 'worker_' + str(id) + '_' + version
                user_password += version

                ffl.Factory.register(config, fflapi.Context, fflapi.User, fflapi.Aggregator, fflapi.Participant)
                fflapi.create_user(worker_name, user_password, user_org, self.credentials_filename)

                # context_w = ffl.Factory.context(config, self.credentials_filename)
                context_w = ffl.Factory.context(config, self.credentials_filename, worker_name, user_password,
                                                encoder=serializer.Base64Serializer)

                '''
                ffl_user_worker = ffl.Factory.user(context_w)
                with ffl_user_worker:
                    try:
                        ffl_user_worker.create_user(worker_name, user_password, user_org)
                    except Exception as err:
                        print(str(err).split(':')[1])
                '''
                # context_w = ffl.Factory.context('cloud', self.credentials_filename, worker_name, user_password, encoder = serializer.Base64Serializer)
                # user_worker0 = ffl.Factory.user(context_w)

                user_worker = ffl.Factory.user(context_w)
                with user_worker:
                    try:

                        result = user_worker.join_task(self.task_name)
                        print('Worker %s has joined task %s' % (worker_name, self.task_name))
                        created = True
                    except Exception as err:
                        print(str(err).split(':')[1])
            except:
                print('waiting for Master...')
                time.sleep(1)
                pass

        participant = ffl.Factory.participant(context_w, task_name=self.task_name)

        return participant

    def create_worker_and_join_task(self, user_name, user_password, task_name, display, logger, user_org='TREE',
                                    verbose=False):
        config = 'cloud'
        created = False
        while not created:
            try:
                # Create context for the cloud communications
                ffl.Factory.register(config, fflapi.Context, fflapi.User, fflapi.Aggregator, fflapi.Participant)
                try:
                    fflapi.create_user(user_name, user_password, user_org, self.credentials_filename)
                except Exception as err:
                    display('The user %s is already registered in pycloudmessenger platform.' % user_name, logger,
                            verbose)
                context = ffl.Factory.context(config, self.credentials_filename, user_name, user_password,
                                              encoder=serializer.Base64Serializer, dispatch_threshold=0)

                # Join task
                user = ffl.Factory.user(context)
                with user:
                    try:
                        result = user.join_task(task_name)
                        display('Worker %s has joined task %s' % (user_name, task_name), logger, verbose)
                        created = True
                    except Exception as err:
                        display('Error - %' % str(err).split(':')[1], logger, verbose)
            except Exception as err:
                print(err)
                display('Waiting for Master...', logger, verbose)
                time.sleep(5)
                pass

        # Create the comms object        
        participant = ffl.Factory.participant(context, task_name=task_name)
        return participant

    def wait_for_workers(self):

        stop = False
        workers = self.aggregator.get_participants()

        while not stop:
            try:
                with self.aggregator:
                    resp = self.aggregator.receive(1)
                participant = resp.notification['participant']
                workers.append(participant)
                print('Task %s: participant %s has joined' % (self.task_name, participant))
            except Exception as err:
                print("Task %s: joined %d participants out of %d" % (self.task_name, len(workers), self.Nworkers))
                # print(err)
                # print('Check here: error')
                # import code
                # code.interact(local=locals())
                pass

            if len(workers) == self.Nworkers:
                stop = True

        workers = self.aggregator.get_participants()
        return list(workers.keys())

    def wait_for_workers_to_join(self, display, logger, verbose=False):
        """
        Wait for workers to join until quorum is met.
        """
        with self.aggregator:
            workers = self.aggregator.get_participants()

        if workers:
            if len(workers) == self.Nworkers:
                display('Participants have already joined', logger, verbose)
                return workers

        display('Waiting for workers to join (%d of %d present)' % (len(workers), self.Nworkers), logger, verbose)

        ready = False
        while not ready:
            try:
                with self.aggregator:
                    resp = self.aggregator.receive(300)
                    participant = resp.notification['participant']
                display('Participant %s joined' % participant, logger, verbose)
            except Exception as err:
                raise err

            if len(workers) == self.Nworkers:
                ready = True

        return workers

    def print_lineage(self, user_name, user_password, task, display, logger, verbose=False):

        aggr_context = ffl.Factory.context('cloud', self.credentials_filename, user_name, user_password)
        aggr_user = ffl.Factory.user(aggr_context)

        with aggr_user:

            result = aggr_user.model_lineage(task)
            training_round = 0

            display(f"{'Round':5} {'Date':30} {'Origin':20} {'Id':10} {'Contribution':20} {'Reward':10}", logger,
                    verbose)

            for line in result:
                if 'genre' in line:
                    if line['genre'] == 'INTERIM':
                        training_round += 1
                        display(f"{training_round:^5d} {line['added']:30} {'AGGREGATOR':20} " +
                                f"{str(line['external_id'][-7:]):10}", logger, verbose)
                    elif line['genre'] == 'COMPLETE':
                        display(f"Done  {line['added']:30} {'AGGREGATOR':20} " +
                                f"{str(line['external_id'][-7:]):10}", logger, verbose)
                    else:
                        display(f"{training_round:^5d} {line['added']:30} {line['participant']:20} " +
                                f"{str(line['external_id'][-7:]):10} " +
                                f"{str(line['contribution']):20} {str(line['reward']):10}", logger, verbose)
                else:
                    training_round += 1
                    display(f"{training_round:^5d} {line['added']:30} {line['metadata']:20} " +
                            f"{str(''):10} " +
                            f"{str(line['contribution']):20} {str(line['reward']):10}", logger, verbose)
