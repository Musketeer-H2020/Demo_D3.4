# -*- coding: utf-8 -*-
'''
@author:  Marcos Fernandez Diaz
September 2020

Example of use: python aggregator.py --user <user> --password <password> --task_name <task_name>

Parameters:
    - user: String with the name of the user. If the user does not exist in the pycloudmessenger platform a new one will be created
    - password: String with the password
    - task_name: String with the name of the task. If the task already exists, an error will be displayed

'''

# Import general modules
import argparse
import logging
import json
import time
import numpy as np
import sys, os
import robust

# Add higher directory to python modules path.
sys.path.append("../../../../")
os.environ['KMP_WARNINGS'] = 'off' # Remove KMP_AFFINITY logs

# To be imported from MMLL (pip installed)
from RobustMMLL.nodes.MasterNode import MasterNode
from RobustMMLL.comms.comms_pycloudmessenger import Comms_master as Comms

# To be imported from demo_tools 
from demo_tools.task_manager_pycloudmessenger import Task_Manager
from demo_tools.data_connectors.Load_from_file import Load_From_File as DC                          # Data connector
from demo_tools.mylogging.logger_v1 import Logger
from demo_tools.evaluation_tools import display, plot_cm_seaborn


# Set up logger
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', type=str, required=True, help='User')
    parser.add_argument('--password', type=str, required=True, help='Password')
    parser.add_argument('--task_name', type=str, required=True, help='Name of the task')
    parser.add_argument('--credentials', type=str, required=True, help='Path to credentials file')
    parser.add_argument('--iterations', type=int, required=False, default=5, help='Number of iterations')
    parser.add_argument('--workers', type=int, required=False, default=2, help='Number of workers')
    parser.add_argument('--robustmethod', type=str, required=False, default='average', help='robustness scheme for aggregation')
    
    FLAGS, unparsed = parser.parse_known_args()
    user_name = FLAGS.user
    user_password = FLAGS.password
    task_name = FLAGS.task_name

    dataset_name = 'mnist'
    verbose = False
    comms_type = 'pycloudmessenger'
    pom = 1
    model_type = 'NN'
    Nworkers = FLAGS.workers


    # Create the directories for storing relevant outputs if they do not exist
    if not os.path.exists("../results/logs/"):
        os.makedirs("../results/logs/") # Create directory for the logs
    if not os.path.exists("../results/figures/"):
        os.makedirs("../results/figures/") # Create directory for the figures
    if not os.path.exists("../results/models/"):
        os.makedirs("../results/models/") # Create directory for the models


    # Setting up the logger    
    logger = Logger('../results/logs/pycloudmessenger_cloud_master_' + str(user_name) + '.log')


    # Load the model architecture as defined by Keras model.to_json()
    try:
        with open('./keras_model_MLP.json', 'r') as json_file:
            model_architecture = json_file.read()
    except:
        display('Error - The file keras_model_MLP.json defining the neural network architecture is not available, please put it under the following path: "' + os.path.abspath(os.path.join("","./")) + '"', logger, verbose)
        sys.exit()

    # Task definition
    task_definition = {"quorum": Nworkers, 
                       "POM": pom, 
                       "model_type": model_type, 
                       "Nmaxiter": FLAGS.iterations,
                       "learning_rate": 0.0003,
                       "model_architecture": model_architecture,
                       "optimizer": 'adam',
                       "loss": 'categorical_crossentropy',
                       "metric": 'accuracy',
                       "batch_size": 64,
                       "num_epochs": 2,
                       "model_averaging": 'True'
                      }


    display('===========================================', logger, verbose)
    display('Creating Master... ', logger, verbose)
    display('Please wait until Master is ready before launching the workers...', logger, verbose)
    # ==================================================
    # Note: this part creates the task and waits for the workers to join. This code is
    # intended to be used only at the demos, in Musketeer this part must be done in the client. 
    credentials_filename = os.path.abspath(os.path.expanduser(os.path.expandvars(FLAGS.credentials)))
    try:
        with open(credentials_filename, 'r') as f:
            credentials = json.load(f)
    except:
        display('Error - The credentials file is not available, please put it under the following path: "' + os.path.abspath(os.path.join("","../../")) + '"', logger, verbose)
        sys.exit()

    tm = Task_Manager(credentials_filename)
    # We need the aggregator to build comms object
    aggregator = tm.create_master_and_taskname(display, logger, task_definition, user_name=user_name, user_password=user_password, task_name=task_name)
    display('Waiting for the workers to join task name = %s' % tm.task_name, logger, verbose)
    tm.wait_for_workers_to_join(display, logger)
    # ==================================================
    
    #########################################
    display('Creating MasterNode under POM %d, communicating through pycloudmessenger' %pom, logger, verbose)
    # Creating Comms object, needed by MMLL
    comms = Comms(aggregator)

    # Creating the robust object
    method = FLAGS.robustmethod
    display('Creating robust object. Aggregation method: %s' %method, logger, verbose)
    try:
        robust = robust.Robust_Master(method=method)
    except Exception as err:
        display('Error when creating robust object', logger, verbose)
        raise

    # Creating Masternode
    mn = MasterNode(pom, comms, logger, verbose, robust=robust)
    display('-------------------- Loading dataset %s --------------------------' %dataset_name, logger, verbose)
    # Warning: this data connector is only designed for the demos. In Musketeer, appropriate data
    # connectors must be provided
    data_file = '../../../../input_data/' + dataset_name + '_hackathon_data.pkl'
    try:
        dc = DC(data_file)
    except:
        display('Error - The file ' + dataset_name + '_hackathon_data.pkl does not exist. Please download it from Box and put it under the following path: "' + os.path.abspath(os.path.join("","../../../../input_data/")) + '"', logger, verbose)
        sys.exit()

  
    #---------------  Creating a ML model (Master side) ---------------------  
    ########################################
    # Parameters depending on the model_type
    ########################################
    model_parameters = {}
    model_parameters['learning_rate'] = float(task_definition['learning_rate'])
    model_parameters['Nmaxiter'] = int(task_definition['Nmaxiter'])
    model_parameters['model_architecture'] = task_definition['model_architecture']
    model_parameters['optimizer'] = task_definition['optimizer']
    model_parameters['loss'] = task_definition['loss']
    model_parameters['metric'] = task_definition['metric']
    model_parameters['batch_size'] = int(task_definition['batch_size'])
    model_parameters['num_epochs'] = int(task_definition['num_epochs'])
    model_parameters['model_averaging'] = task_definition['model_averaging']
    mn.create_model_Master(model_type, model_parameters=model_parameters)
    display('MMLL model %s is ready for training!' % model_type, logger, verbose)

    # We start the training procedure.
    display('Training the model %s' % model_type, logger, verbose)
    t_ini = time.time()
    [Xval, yval] = dc.get_data_val()
    mn.fit(Xval=Xval, yval=yval)
    t_end = time.time()
    display('Training is complete: Training time = %s seconds' % str(t_end - t_ini)[0:6], logger, verbose)
    display('----------------------------------------------------------------------', logger, verbose)

    display('Retrieving the trained model from MasterNode', logger, verbose)
    model = mn.get_model()
    
    # Warning: this save_model utility is only for demo purposes
    output_filename_model = '../results/models/POM' + str(pom) + '_' + model_type + '_master_' + dataset_name + '_model.pkl'
    mn.save_model(output_filename_model)
    
    display('-------------  Obtaining predictions----------------------------------\n', logger, verbose)
    [Xtst, ytst] = dc.get_data_tst()
    preds_tst = model.predict(Xtst)
    y = np.argmax(ytst, axis=-1) # Convert to labels
    classes = np.arange(ytst.shape[1]) # 0 to 9

    display('-------------  Evaluating --------------------------------------------\n', logger, verbose)
    # Warning, these evaluation methods are not part of the MMLL library, they are only intended
    # to be used for the demos. Use them at your own risk.
    plot_cm_seaborn(preds_tst, y, classes, 'NN confusion matrix in test set master', model_type, dataset_name, logger, verbose, normalize=True)

    display('Terminating all worker nodes.', logger, True)
    mn.terminate_Workers()
    tm.stop_task()
    tm.print_lineage(user_name, user_password, task_name, display, logger, verbose)


    display('----------------------------------------------------------------------', logger, verbose)
    display('------------------------- END MMLL Procedure -------------------------', logger, verbose)
    display('----------------------------------------------------------------------\n', logger, verbose)
