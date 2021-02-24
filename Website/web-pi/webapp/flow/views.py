from flask import render_template,request,Blueprint
from flask_login import login_required
from webapp import login_manager
import paho.mqtt.client as mqtt
import json
import ssl


flow = Blueprint('flow',__name__)

BROKER_ADDRESS="test.mosquitto.org"
N=8884

client = mqtt.Client()
client.tls_set(ca_certs="mosquitto.org.crt",certfile="client.crt",keyfile="client.key",tls_version=ssl.PROTOCOL_TLSv1_2)
print("Transmission:")
print(client.connect(BROKER_ADDRESS,port=N))
client.subscribe("IC.embedded/TBChip/#")
data = {'temperature':0.0, 'warnings': "..."}


    #return render_template('flow.html', data=data)



# TODO: require authentification from login_manager
@flow.route('/flow')
# @login_required
def flow_page():
    '''
    This is the data flow.
    '''
    def on_message(client, userdata, message):
        global data
        datacpy = message.payload
        data = json.loads(datacpy)

        print(data)
    # If start pushed
    client.on_message = on_message
    client.loop_start()

    # If stop pushed
    # client.end_loop()

    return render_template('flow.html', data=data)
"""
@flow.route('/receiver')
def receiver():"""

"""
    text = request.args.get('jsdata')
    global data
    return render_template('suggestions.html', data=data)
"""
