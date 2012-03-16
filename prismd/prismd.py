import functools
import json
import logging
from math import floor
from optparse import OptionParser
import random
import time

import serial
import tornado.ioloop
import tornado.web
import yaml
import zmq

from light_base import LightsBase
import patterns.test
import srsly

logger = logging.getLogger("prismd")
logger.setLevel(logging.DEBUG)

def barfs_json(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        ret = f(self, *args, **kwargs)
        self.write(ret)
    return wrapper

class LightsHandler(LightsBase):
    """The main handler for requests to change the lights.

    Accepts a post argument called "data" with JSON of the form:
    {
        "lights": {
            "0": {
                "r": 0-15,
                "g": 0-15,
                "b": 0-15,
                "i": 0-255,
            },
            "1": {
                "r": 0-15,
                "g": 0-15,
                "b": 0-15,
                "i": 0-255,
            }
            # ... -> n lights
        }
    }
    """

    @barfs_json
    def post(self):
        """Takes data and sets the lights correspondingly."""

        data = json.loads(self.get_argument("data"))

        logger.info(data)

        lights_data = data["lights"]

        for n, light in lights_data.iteritems():
            self.set_light(int(n), light)

        return self.application.settings['lights_state']


def process_message(msg, srl):
    """Processes a message received from a client.

    Returns a dict."""
    try:
        data = json.loads(msg)
    except Exception, e:
        return {
            "status": "error",
            "message": str(e)
        }

    lights_data = data["lights"]

    for n, light in lights_data.iteritems():
        print "Set light %s with %r" % (n, light)
        set_light(srl, int(n), light)

    return {"status": "ok"}

def set_light(srl, idx, light):
        """Use our serial connection to set the RGBI of the light at index idx"""

        packed_cmd = srsly.pack_light_data(idx, light)
        srsly.write_light_cmd(srl, packed_cmd)

if __name__ == "__main__":
    config_file = open("prismd.yaml")
    config = yaml.load(config_file.read()) or {}

    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port", default=config.get("port", 8080), type=int, help="The port to listen on")
    parser.add_option("-x", "--grid-width", dest="grid_width", default=config.get("grid_width", 7), type=int, help="The grid width")
    parser.add_option("-y", "--grid-height", dest="grid_height", default=config.get("grid_height", 7), type=int, help="The grid height")
    parser.add_option("-b", "--baud-rate", dest="baud_rate", default=config.get("baud_rate", 115200), type=int, help="Baud rate")
    parser.add_option("-s", "--serial-port", dest="serial_port", default=config.get("serial_port", 0), type=str, help="Serial port to open")
    parser.add_option("--testing", dest="testing", action="store_true", help="Whether or not to start the Tornado web server")

    (options, args) = parser.parse_args()

    # Make the settings object into something a bit nicer
    settings = dict((k,getattr(options, k)) for k in parser.defaults.keys())
    # Initialize the state of the lights
    settings["lights_state"] = dict((n, {'r':0, 'g':0, 'b':0, 'i':0}) for n in xrange(settings['grid_width'] * settings['grid_height']))

    # open our serial connection
    srl = serial.Serial(settings['serial_port'], settings["baud_rate"])
    settings["serial_connection"] = srl

    if options.testing:
        application = tornado.web.Application([
            (r"/", LightsHandler),
            (r"/test/random_pattern", patterns.test.RandomHandler),
            (r"/test/pretty_fader", patterns.test.PrettyFader),
            (r"/test/cycler", patterns.test.Cycler),
            (r"/test/sequence", patterns.test.Sequence),
            (r"/test/stripe", patterns.test.StripyHorse),
            (r"/test/hstripe", patterns.test.HorizontalStripyHorse),
            (r"/test/rgbfade", patterns.test.RGBFade),
        ], **settings)
        application.listen(settings["port"])
        tornado.ioloop.IOLoop.instance().start()

    else:
        # ZMQ
        # TCP, SRVR, REQUEST?REPLY
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://127.0.0.1:%d" % settings["port"])

        while True:
            msg = socket.recv()
            print "Got message %s" % msg
            output = process_message(msg, srl)
            print "Sending %s" % output
            socket.send(json.dumps(output))
