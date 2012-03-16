from math import floor
import random
import time
from light_base import LightsBase

class RandomHandler(LightsBase):
    def get(self):
        times = int(self.get_argument("times", default=1))
        for i in xrange(times):
            self.write(str(i))
            for n in xrange(49):
                print i, n
                self.set_light(n, {'r': random.randint(0,15), 'g': random.randint(0,15), 'b': random.randint(0,15), 'i':255})

        return self.application.settings['lights_state']


class PrettyFader(LightsBase):
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


class Cycler(LightsBase):
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


class Sequence(LightsBase):
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


class RGBFade(LightsBase):
    def get(self):
        for d in (xrange(16), reversed(xrange(16))):
            for i in d:
                for n in xrange(49):
                    self.set_light(n, {'r': i, 'g': 0, 'b': 0, 'i': 255})
                time.sleep(0.05)


class StripyHorse(LightsBase):
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
    def get(self):
        for n in xrange(49):
            row = n // 7
            self.set_light(n, self.buckets[row])


class HorizontalStripyHorse(StripyHorse):
    def get(self):
        rev = dict((k,v) for k,v in zip(xrange(7), reversed(xrange(7))))
        for n in xrange(49):
            row = n % 7
            if n % 14 < 7:
                self.set_light(n, self.buckets[row])
            else:
                row = rev[row]
                self.set_light(n, self.buckets[row])

