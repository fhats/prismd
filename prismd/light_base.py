import tornado.web

import srsly

class LightsBase(tornado.web.RequestHandler):
    def set_light(self, idx, light):
        """Use our serial connection to set the RGBI of the light at index idx"""

        # Don't set a light that doesn't need its thing set
        if self.application.settings["lights_state"][idx] == light:
           return

        # synchronize our internal representation of the lights
        self.application.settings["lights_state"][idx] = light

        packed_cmd = srsly.pack_light_data(idx, light)
        srsly.write_light_cmd(self.application.settings['serial_connection'], packed_cmd)

