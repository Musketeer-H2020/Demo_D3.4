from flask import Flask, make_response, request, jsonify
import logging

app = Flask(__name__)
my_messages = {}
app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True

@app.route('/clear/', methods=['POST'])
def clear():
    """
    Clears the message queue.
    """  
    my_messages = {}
    
    return make_response("", 200)
 
 
@app.route('/send/', methods=['POST'])
def send():
    """
    Adds the sent message to the queue.
    """  
    sender = request.args["sender"]
    receiver = request.args["receiver"]
    message = request.args["message"]
    
    if receiver not in my_messages.keys():
        my_messages[receiver] = {}
        
    if sender not in my_messages[receiver].keys():
        my_messages[receiver][sender] = []
        
    my_messages[receiver][sender] += [message]
    
    return make_response("", 200)

    
@app.route('/receive/', methods=['GET'])
def receive():
    """
    Retrieves and removes the oldest message for the particular receiver from the queue and returns it with 200.
    If queue is empty, status code is 204.
    """  
    sender = request.args["sender"]
    receiver = request.args["receiver"]
    
    message = None
    if receiver in my_messages.keys():
        if sender in my_messages[receiver].keys():
            if len(my_messages[receiver][sender]) > 0:
                message = my_messages[receiver][sender][0]
                my_messages[receiver][sender] = my_messages[receiver][sender][1:]
    
    if message is None:
        #return make_response("", 204)
        return  make_response("", 204)
    else:
        return make_response(jsonify({"message": message}), 200)

        
if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=True)