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
            0: {
                "r": 0,
                "g": 255,
                "b": 122,
                "i": 255,
            },
            1: {
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
            self.set_light(n, light)

        return self.application.settings['lights_state']

    def set_light(self, idx, light):
        """Use our serial connection to set the RGBI of the light at index idx"""

        # Don't set a light that doesn't need its
        if self.application.settings["lights_state"][idx] == light:
           return

        # synchronize our internal representation of the lights
        self.application.settings["lights_state"][idx] = light

        packed_cmd = srsly.pack_light_data(idx, light)
        srsly.write_light_cmd(self.application.settings['serial_connection'], packed_cmd)
        #if bytes_written != 4:
        #    logging.warn("I read %d bytes and expected 4." % bytes_written)


class RandomHandler(LightsHandler):
    def get(self):
        times = int(self.get_argument("times", default=1))
        for i in xrange(times):
            self.write(str(i))
            for n in xrange(49):
                print i, n
                self.set_light(n, {'r': random.randint(0,15), 'g': random.randint(0,15), 'b': random.randint(0,15), 'i':255})
        self.write("hi")

        return self.application.settings['lights_state']


class PrettyFader(LightsHandler):
    def get(self):
        times = int(self.get_argument("times", default=1))
        for t in xrange(times):
            for d in (xrange(32), reversed(xrange(32))):
                for i in d:
                    for n in xrange(49):
                        #print "%d %d %d" % (t,i,n)
                        self.set_light(
                            n,
                            {
                                'r': (n % 16),
                                'g': ((n + 6) % 16),
                                'b': ((n + 12) % 16),
                                'i': i * 8
                            })


class Cycler(LightsHandler):
    def get(self):
        for i in xrange(4096):
            for n in xrange(49):
                c = (i + floor(n * (4096/49))) % 4096
                rgb = self.rgbsplit(c)
                self.set_light(
                    n,
                    {
                        'r': rgb[0],
                        'g': rgb[1],
                        'b': rgb[2],
                        'i': 255
                    })
                print "Set line %d to %d %d %d %d" % (n, rgb[0], rgb[1], rgb[2], 255)
        return self.application.settings['lights_state']

    def rgbsplit(self, rgb):
        rgb = int(rgb)
        return (
            (rgb & 0xF00) >> 8,
            (rgb & 0xF0) >> 4,
            (rgb & 0xF))


class Sequence(LightsHandler):
    def get(self):
        for n in xrange(49):
            d = n % 3
            rgb = {
                'r': 15 if d == 0 else 0,
                'g': 15 if d == 1 else 0,
                'b': 15 if d == 2 else 0,
                'i': 255
            }
            self.set_light(n, rgb)
            time.sleep(0.5)
        for n in xrange(49):
            self.set_light(n, {'r': 0, 'g': 0, 'b': 0, 'i': 0})
            time.sleep(0.5)


class RGBFade(LightsHandler):
    def get(self):
        for d in (xrange(16), reversed(xrange(16))):
            for i in d:
                for n in xrange(49):
                    self.set_light(n, {'r': i, 'g': 0, 'b': 0, 'i': 255})
                time.sleep(0.05)


class StripyHorse(LightsHandler):
    def get(self):
        buckets = {
            0: {
                'r': 15,
                'g': 0,
                'b': 0,
                'i': 255
            },
            1: {
                'r': 15,
                'g': 15,
                'b': 0,
                'i': 255
            },
            2: {
                'r': 15,
                'g': 0,
                'b': 15,
                'i': 255
            },
            3: {
                'r': 0,
                'g': 15,
                'b': 0,
                'i': 255
            },
            4: {
                'r': 0,
                'g': 15,
                'b': 15,
                'i': 255
            },
            5: {
                'r': 0,
                'g': 0,
                'b': 15,
                'i': 255
            },
            6: {
                'r': 15,
                'g': 15,
                'b': 15,
                'i': 255
            }

        }
        for n in xrange(49):
            row = n // 7
            self.set_light(n, buckets[row])


if __name__ == "__main__":
    config_file = open("prismd.yaml")
    config = yaml.load(config_file.read()) or {}

    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port", default=config.get("port", 8080), type=int, help="The port to listen on")
    parser.add_option("-x", "--grid-width", dest="grid_width", default=config.get("grid_width", 7), type=int, help="The grid width")
    parser.add_option("-y", "--grid-height", dest="grid_height", default=config.get("grid_height", 7), type=int, help="The grid height")
    parser.add_option("-b", "--baud-rate", dest="baud_rate", default=config.get("baud_rate", 115200), type=int, help="Baud rate")
    parser.add_option("-s", "--serial-port", dest="serial_port", default=config.get("serial_port", 0), type=str, help="Serial port to open")

    (options, args) = parser.parse_args()

    # Make the settings object into something a bit nicer
    settings = dict((k,getattr(options, k)) for k in parser.defaults.keys())
    # Initialize the state of the lights
    settings["lights_state"] = dict((n, {'r':0, 'g':0, 'b':0, 'i':0}) for n in xrange(settings['grid_width'] * settings['grid_height']))

    # open our serial connection
    srl = serial.Serial(settings['serial_port'], settings["baud_rate"])
    settings["serial_connection"] = srl

    application = tornado.web.Application([
        (r"/", LightsHandler),
        (r"/random_pattern", RandomHandler),
        (r"/pretty_fader", PrettyFader),
        (r"/cycler", Cycler),
        (r"/sequence", Sequence),
        (r"/stripe", StripyHorse),
        (r"/rgbfade", RGBFade),
    ], **settings)
    application.listen(settings["port"])
    tornado.ioloop.IOLoop.instance().start()
