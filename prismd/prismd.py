import functools
import json
import logging
from optparse import OptionParser

import serial
import tornado.ioloop
import tornado.web
import yaml

import srsly

logger = logging.getLogger("prismd")

def barfs_json(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        ret = f(self, *args, **kwargs)
        self.write(ret)
    return wrapper

class LightsHandler(tornado.web.RequestHandler):
    """The main handler for requests to change the lights.

    Accepts a post argument called "data" with JSON of the form:
    {
        "lights": {
            "0": {
                "r": 0,
                "g": 255,
                "b": 122,
                "i": 255,
            },
            "1": {
                "r": 255,
                "g": 250,
                "b": 100,
                "i": 201,
            }
            # ... -> n lights
        }
    }
    """

    @barfs_json
    def get(self):
        """Takes data and sets the lights correspondingly."""

        data = json.loads(self.get_argument("data"))

        logger.info(data)

        lights_data = data["lights"]

        for n, light in lights_data.iteritems():
            n = int(n)
            self.set_light(n, light)

        return self.application.settings['lights_state']

    def set_light(self, idx, light):
        """Use our serial connection to set the RGBI of the light at index idx"""

        # synchronize our internal representation of the lights
        self.application.settings["lights_state"][idx] = light

        packed_cmd = srsly.pack_light_data(idx, light)
        srsly.write_light_cmd(self.application.settings['serial_connection'], packed_cmd)


if __name__ == "__main__":
    config_file = open("prismd.yaml")
    config = yaml.load(config_file.read()) or {}

    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port", default=config.get("port", 8080), type=int, help="The port to listen on")
    parser.add_option("-x", "--grid-width", dest="grid_width", default=config.get("grid_width", 7), type=int, help="The grid width")
    parser.add_option("-y", "--grid-height", dest="grid_height", default=config.get("grid_height", 7), type=int, help="The grid height")
    parser.add_option("-b", "--baud-rate", dest="baud_rate", default=config.get("baud_rate", 151200), type=int, help="Baud rate")
    parser.add_option("-s", "--serial-port", dest="serial_port", default=config.get("serial_port", 0), type=str, help="Serial port to open")

    (options, args) = parser.parse_args()

    # Make the settings object into something a bit nicer
    settings = dict((k,getattr(options, k)) for k in parser.defaults.keys())
    # Initialize the state of the lights
    settings["lights_state"] = dict((str(n), {'r':0, 'g':0, 'b':0, 'i':0}) for n in xrange(settings['grid_width'] * settings['grid_height']))

    # open our serial connection
    srl = serial.Serial(settings['serial_port'], settings["baud_rate"])
    settings["serial_connection"] = srl

    application = tornado.web.Application([
        (r"/", LightsHandler)
    ], **settings)
    application.listen(settings["port"])
    tornado.ioloop.IOLoop.instance().start()
