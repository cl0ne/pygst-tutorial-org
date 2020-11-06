#!/usr/bin/env python

import os
import sys
import gi

gi.require_version("Gst", "1.0")

from gi.repository import Gst, GLib  # noqa: E402


class CLI_Main:
    def __init__(self, argv):
        self.player = Gst.ElementFactory.make("playbin", "player")
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        self.loop = GLib.MainLoop()
        self.playlist = iter(argv[1:])

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            error_source = message.src.name
            err, debug = message.parse_error()
            print("Error from '{}':".format(error_source), err.message)
            print("Debug info:", debug)
        elif t != Gst.MessageType.EOS:
            return
        self.player.set_state(Gst.State.NULL)
        if not self._play_next():
            self.loop.quit()

    def _play_next(self):
        for filepath in self.playlist:
            if not os.path.isfile(filepath):
                print("is not a file:", filepath)
                continue
            filepath = os.path.realpath(filepath)
            self.player.set_property("uri", Gst.filename_to_uri(filepath))
            self.player.set_state(Gst.State.PLAYING)
            print("now playing:", filepath)
            return True
        return False

    def start(self):
        if self._play_next():
            self.loop.run()


if __name__ == "__main__":
    args = Gst.init(sys.argv)
    CLI_Main(args).start()
