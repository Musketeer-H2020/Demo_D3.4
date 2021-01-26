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
            print('\n' + '#' * 80 + '\nERROR - The file musketeer.json is not available, please put it under the following path: "' + os.path.abspath(os.path.join("","../../")) + '"\n' + '#' * 80 + '\n')
            sys.exit()

    def stop_task(self, model: dict = None):
        try:
            with self.aggregator:
                self.aggregator.stop_task(model)
        except Exception as err:
            print(err)
            raise

    def create_master_and_taskname(self, display, logger, task_definition, user_name, user_password='Tester', task_name='Test', user_org='TREE', verbose=False):
        self.task_name = task_name
        self.Nworkers = task_definition['quorum']
        config = 'cloud'

        # Create context for the cloud communications
        ffl.Factory.register(config, fflapi.Context, fflapi.User, fflapi.Aggregator, fflapi.Participant)
        self.aggr_context = ffl.Factory.context(config, self.credentials_filename, user_name, user_password, encoder=serializer.Base64Serializer)

        try:
            user = ffl.Factory.user(self.aggr_context)
            with user:
                import json
                result = user.create_task(task_name, ffl.Topology.star, task_definition)
                task_definition = json.loads(user.task_info(task_name)['definition'])
        except Exception as err:
            display('Error: %s' %err, logger, verbose)
            import sys
            sys.exit()
 
        self.aggregator = ffl.Factory.aggregator(self.aggr_context, task_name=task_name)
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


    def create_worker_and_join_task(self, user_name, user_password, task_name, display, logger, user_org='TREE', verbose=False):
        config = 'cloud'

        # Create context for the cloud communications
        ffl.Factory.register(config, fflapi.Context, fflapi.User, fflapi.Aggregator, fflapi.Participant)
        context = ffl.Factory.context(config, self.credentials_filename, user_name, user_password, encoder=serializer.Base64Serializer)

        # Join task
        try:
            user = ffl.Factory.user(context)
            with user:
                user.join_task(task_name)
        except Exception as err:
            import sys
            display('Error: %s' %err, logger, verbose)
            sys.exit()

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
                #print(err)
                #print('Check here: error')
                #import code
                #code.interact(local=locals())
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

        display('Waiting for workers to join (%d of %d present)' %(len(workers), self.Nworkers), logger, verbose)

        ready = False
        while not ready:
            try:
                with self.aggregator:
                    resp = self.aggregator.receive(300)
                    participant = resp.notification['participant']
                display('Participant %s joined' %participant, logger, verbose)
            except Exception as err:
                raise err

            if len(workers) == self.Nworkers:
                ready = True

        return workers



    def print_lineage(self, user_name, user_password, task, display, logger, verbose=False):

        # print(user_name, user_password, task)
        aggr_context = ffl.Factory.context('cloud', self.credentials_filename, user_name, user_password)
        aggr_user = ffl.Factory.user(aggr_context)

        with aggr_user:

            result = aggr_user.model_lineage(task)
            # print(result)
            training_round = 0

            display(f"{'Round':5} {'Date':30} {'Origin':20} {'Id':10} {'Contribution':20} {'Reward':10}", logger, verbose)

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
