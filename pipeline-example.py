#!/usr/bin/env python

import sys
import os
import gi

gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gst, Gtk  # noqa: E402


class GTK_Main(object):
    def __init__(self):
        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("MP3-Player")
        window.set_default_size(400, -1)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        self.entry = Gtk.Entry()
        vbox.pack_start(self.entry, False, True, 0)
        self.button = Gtk.Button(label="Start")
        self.button.connect("clicked", self.start_stop)
        vbox.add(self.button)
        window.show_all()

        self.player = Gst.Pipeline.new("player")
        source = Gst.ElementFactory.make("filesrc", "file-source")
        parse = Gst.ElementFactory.make("mpegaudioparse", "mp3-parse")
        decoder = Gst.ElementFactory.make("mpg123audiodec", "mp3-decoder")
        conv = Gst.ElementFactory.make("audioconvert", "converter")
        sink = Gst.ElementFactory.make("autoaudiosink", "audio-out")

        for e in (source, parse, decoder, conv, sink):
            self.player.add(e)

        source.link(parse)
        parse.link(decoder)
        decoder.link(conv)
        conv.link(sink)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

    def start_stop(self, w):
        if self.button.get_label() == "Start":
            filepath = self.entry.get_text().strip()
            if not os.path.isfile(filepath):
                return
            filepath = os.path.realpath(filepath)
            self.button.set_label("Stop")
            src = self.player.get_by_name("file-source")
            src.set_property("location", filepath)
            self.player.set_state(Gst.State.PLAYING)
        else:
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")

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
        self.button.set_label("Start")


if __name__ == "__main__":
    Gst.init(sys.argv)
    Gtk.init(sys.argv)
    GTK_Main()
    Gtk.main()
