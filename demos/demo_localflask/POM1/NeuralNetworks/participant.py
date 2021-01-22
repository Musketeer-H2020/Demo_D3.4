# -*- coding: utf-8 -*-
'''
@author:  Marcos Fernandez Diaz
May 2020

Example of use: python participant.py --id 0

Parameters:
    - id: Integer representing the partition of data to be used by the worker. Each worker should use a different partition, possible values are 0 to 4.

'''

# Import general modules
import argparse
import numpy as np
import logging
import sys, os

# Add higher directory to python modules path.
sys.path.append("../../../../")

# To be imported from MMLL (pip installed)
from RobustMMLL.comms.comms_local_Flask import Comms
from RobustMMLL.nodes.WorkerNode import WorkerNode

# To be imported from demo_tools
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
    parser.add_argument('--id', type=str, default=None, help='The addresses of the workers')
    FLAGS, unparsed = parser.parse_known_args()

    if FLAGS.id is None or FLAGS.id not in ['0', '1', '2', '3', '4']:
        print("\n ********************************\n STOP: Please provide a valid id value\n *********************************\n")
        print('Usage: python pom1_Kmeans_worker_local_flask.py --id <id>')
        print('Valid id values: 0, 1, 2, 3, 4\n')
        sys.exit()

    worker_address = FLAGS.id
    dataset_name = 'mnist'
    verbose = False
    comms_type = 'local_flask'
    pom = 1
    model_type = 'NN'


    # Create the directories for storing relevant outputs if they do not exist
    if not os.path.exists("../results/logs/"):
        os.makedirs("../results/logs/") # Create directory for the logs
    if not os.path.exists("../results/figures/"):
        os.makedirs("../results/figures/") # Create directory for the figures
    if not os.path.exists("../results/models/"):
        os.makedirs("../results/models/") # Create directory for the models


    # Setting up the logger
    logger = Logger('../results/logs/Local_flask_worker_' + str(worker_address) + '.log')

    
    display('===========================================', logger, verbose)
    display('Creating Worker...', logger, verbose)
    # ==================================================
    # Note: this part creates the worker (participant) and it joins the task. This code is
    # intended to be used only at the demos, in Musketeer this part must be done in the client. 
    # ==================================================


    # Creating the comms object
    display('Creating WorkerNode under POM %d, communicating through local flask' %pom, logger, verbose)
    comms = Comms(my_id=worker_address)


    # Creating Workernode
    wn = WorkerNode(pom, comms, logger, verbose)
    display('-------------------- Loading dataset %s --------------------------' % dataset_name, logger, verbose)

    # Warning: this data connector is only designed for the demos. In Musketeer, appropriate data
    # connectors must be provided
    data_file = '../../../../input_data/' + dataset_name + '_demonstrator_data.pkl'
    try:
        dc = DC(data_file)
    except:
        display('Error - The file ' + dataset_name + '_demonstrator_data.pkl does not exist. Please download it from Box and put it under the following path: "' + os.path.abspath(os.path.join("","../../../../input_data/")) + '"', logger, verbose)
        sys.exit()

    [Xtr, ytr, _, _, Xtst, ytst] = dc.get_all_data_Worker(int(worker_address))
    wn.set_training_data(dataset_name, Xtr, ytr)
    display('WorkerNode loaded %d patterns for training' % wn.NPtr, logger, verbose)


    #---------------  Creating a ML model (Worker side) ---------------------  
    wn.create_model_worker(model_type)
    display('MMLL model %s is ready for training!' %model_type, logger, verbose)
    display('Worker_' + model_type + ' %s is running...' %worker_address, logger, verbose)
    wn.run()
    display('Worker_' + model_type + ' %s: EXIT' %worker_address, logger, verbose)

    # Retrieving and saving the trained model
    display('Retrieving the trained model from WorkerNode', logger, verbose)
    model = wn.get_model()
    
    # Warning: this save_model utility is only for demo purposes
    output_filename_model = '../results/models/POM' + str(pom) + '_' + model_type + '_worker_' + dataset_name + '_model.pkl'
    wn.save_model(output_filename_model)

    display('-------------  Obtaining predictions------------------------------------\n', logger, verbose)
    preds_tst = model.predict(Xtst)
    y = np.argmax(ytst, axis=-1) # Convert to labels
    classes = np.arange(ytst.shape[1]) # 0 to 9

    display('-------------  Evaluating --------------------------------------------\n', logger, verbose)
    # Warning, these evaluation methods are not part of the MMLL library, they are only intended
    # to be used for the demos. Use them at your own risk.
    plot_cm_seaborn(preds_tst, y, classes, 'NN confusion matrix in test set worker', model_type, dataset_name, logger, verbose, normalize=True)
