import json
from optparse import OptionParser
import random
import time

import tornado.ioloop
import tornado.web
import zmq

import patterns.test

class PrismdController(tornado.web.RequestHandler):
    # def initialize(self):
    #     self.connect()

    def connect(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://%s:%s" % (self.application.settings["host"], self.application.settings["port"]))

    def change_lights(self, lights):
        self.connect()
        self.socket.send(json.dumps({"lights": lights}))

class BlanketHandler(PrismdController):
    def get(self):
        r,g,b = [int(self.get_argument(k, default=0)) for k in ('r','g','b')]

        lights = dict((n, {'r': r, 'g': g, 'b': b, 'i': 255}) for n in xrange(49))
        self.change_lights(lights)

class FlashHandler(PrismdController):
    def get(self):
        r,g,b = [int(self.get_argument(k, default=15)) for k in ('r','g','b')]
        slp = float(self.get_argument("sleep", default=0.5))
        times = int(self.get_argument("times", 5))

        on_lights = dict((n, {'r': r, 'g': g, 'b': b, 'i': 255}) for n in xrange(49))
        off_lights = dict((n, {'r': 0, 'g': 0, 'b': 0, 'i': 0}) for n in xrange(49))

        for i in xrange(times):
            self.change_lights(on_lights)
            time.sleep(slp)
            self.change_lights(off_lights)
            time.sleep(slp)


class RandomHandler(PrismdController):

    def do_random(self, times):
        for i in xrange(times):
            lights = dict((n, {
                'r': random.randint(0,15),
                'g': random.randint(0,15),
                'b': random.randint(0,15),
                'i': 255}) for n in xrange(49))
            self.change_lights(lights)

    def get(self):
        times = int(self.get_argument("times", 20))

        self.do_random(times)

class ColorFader(PrismdController):

    def do_color_fader(self, times):
        for t in xrange(times):
            for color in (
                {'r': 15, 'g': 0, 'b': 0, 'i': 255},
                {'r': 15, 'g': 7, 'b': 0, 'i': 255},
                {'r': 15, 'g': 15, 'b': 0, 'i': 255},
                {'r': 15, 'g': 0, 'b': 7, 'i': 255},
                {'r': 15, 'g': 0, 'b': 15, 'i': 255},
                {'r': 0, 'g': 15, 'b': 0, 'i': 255},
                {'r': 0, 'g': 15, 'b': 7, 'i': 255},
                {'r': 0, 'g': 15, 'b': 15, 'i': 255},
                {'r': 0, 'g': 0, 'b': 15, 'i': 255},
                {'r': 15, 'g': 15, 'b': 15, 'i': 255}):
                for r in (xrange(8), reversed(xrange(8))):
                    for i in r:
                        c = color
                        c['i'] = i * 32
                        lights = dict((n,c) for n in xrange(49))
                        self.change_lights(lights)

    def get(self):
        times = int(self.get_argument("times", 1))

        self.do_color_fader(times)


class SoloHandler(PrismdController):
    def do_solo(self):
        pass

    def get(self):
        pass

class MapHandler(PrismdController):
    crap_map = [
        48, 35, 34, 21, 20, 7,  6,
        47, 36, 33, 22, 19, 8,  5,
        46, 37, 32, 23, 18, 9,  4,
        45, 38, 31, 24, 17, 10, 3,
        44, 39, 30, 25, 16, 11, 2,
        43, 40, 29, 26, 15, 12, 1,
        42, 41, 28, 27, 14, 13, 0,
    ]

    def draw_from_map(self, mp):
        lights = {}
        for b, idx in zip(mp, self.crap_map):
            lights[idx] = {'r': b*15, 'g': 0, 'b': 0, 'i': 255}

        self.change_lights(lights)

    def x_y_to_n(self, x, y):
        n = x * y
        return self.crap_map[n]

class YelpHandler(MapHandler):

    yelp_y = [
        1, 0, 0, 0, 0, 0, 1,
        0, 1, 0, 0, 0, 1, 0,
        0, 0, 1, 0, 1, 0, 0,
        0, 0, 0, 1, 0, 0, 0,
        0, 0, 0, 1, 0, 0, 0,
        0, 0, 0, 1, 0, 0, 0,
        0, 0, 0, 1, 0, 0, 0,
    ]

    yelp_e = [
        1, 1, 1, 1, 1, 1, 1,
        1, 0, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0, 0,
        1, 1, 1, 1, 0, 0, 0,
        1, 0, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0, 0,
        1, 1, 1, 1, 1, 1, 1,
    ]

    yelp_l = [
        1, 0, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0, 0,
        1, 1, 1, 1, 1, 1, 1,
    ]

    yelp_p = [
        1, 1, 1, 1, 1, 0, 0,
        1, 0, 0, 0, 0, 1, 0,
        1, 0, 0, 0, 0, 1, 0,
        1, 1, 1, 1, 1, 0, 0,
        1, 0, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0, 0,
    ]

    yelp = [
        1, 0, 1, 0, 1, 1, 1,
        0, 1, 0, 0, 1, 1, 0,
        0, 1, 0, 0, 1, 1, 1,
        0, 0, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 1, 1, 1,
        1, 0, 0, 0, 1, 1, 1,
        1, 1, 1, 0, 1, 0, 0,
    ]

    def do_yelp(self):
        for letter in (self.yelp_y, self.yelp_e, self.yelp_l, self.yelp_p):
            self.draw_from_map(letter)
            time.sleep(1)
        self.draw_from_map(self.yelp)

    def get(self):
        self.do_yelp()

class ShowOffHandler(ColorFader, RandomHandler, YelpHandler):
    def get(self):
        times = int(self.get_argument("times", 1))
        for i in xrange(times):
            self.do_yelp()
            self.do_random(50)
            self.do_color_fader(1)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--prismd-host", dest="prismd_host", default="127.0.0.1", help="prismd host")
    parser.add_option("--prismd-port", dest="prismd_port", default="8080", help="prismd port")
    (options, args) = parser.parse_args()

    settings = {
        'host': options.prismd_host,
        'port': options.prismd_port,
    }

    application = tornado.web.Application([
        (r"/blanket", BlanketHandler),
        (r"/darwin", YelpHandler),
        (r"/flash", FlashHandler),
        (r"/random", RandomHandler),
        (r"/fader", ColorFader),
        (r"/showoff", ShowOffHandler)
    ], **settings)
    application.listen(9001)
    tornado.ioloop.IOLoop.instance().start()
