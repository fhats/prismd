import functools
import json
import logging
from optparse import OptionParser

import tornado.ioloop
import tornado.web
import yaml

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

    Talks to serial like so:
    START(4bits),rgb(24bits),i(4bits),n(8bits).
    if n=63, command addresses all lights.
    """

    @barfs_json
    def get(self):
        """Takes data and sets the lights correspondingly."""

        data = json.loads(self.get_argument("data"))

        logger.info(data)

        lights_data = data["lights"]

        for n, light in lights_data.iteritems():
            self.set_light(
                n,
                light["r"],
                light["g"],
                light["b"],
                light["i"])

        return self.application.settings['lights_state']

    def set_light(self, idx, r, g, b, i):
        """Use our serial connection to set the RGBI of the light at index idx"""
        self.application.settings["lights_state"]["idx"]



if __name__ == "__main__":
    config_file = open("prismd.yaml")
    config = yaml.load(config_file.read()) or {}

    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port", default=config.get("port", 8080), type=int, help="The port to listen on")
    parser.add_option("-x", "--grid-width", dest="grid_width", default=config.get("grid_width", 7), type=int, help="The grid width")
    parser.add_option("-y", "--grid-height", dest="grid_height", default=config.get("grid_height", 7), type=int, help="The grid height")

    (options, args) = parser.parse_args()

    # Make the settings object into something a bit nicer
    settings = dict((k,getattr(options, k)) for k in ('port', 'grid_width', 'grid_height'))
    # Initialize the state of the lights
    settings["lights_state"] = dict((n, {'r':0, 'g':0, 'b':0, 'i':0}) for n in xrange(settings['grid_width'] * settings['grid_height']))

    application = tornado.web.Application([
        (r"/", LightsHandler)
    ], **settings)
    application.listen(settings["port"])
    tornado.ioloop.IOLoop.instance().start()
