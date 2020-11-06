#!/usr/bin/env python

import sys
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gst, Gtk  # noqa: E402
# Needed for set_window_handle() to work:
from gi.repository import GstVideo  # noqa: E402, F401


class GTK_Main:
    def __init__(self):
        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("Webcam-Viewer")
        window.set_default_size(500, 400)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        self.movie_window = Gtk.DrawingArea()
        vbox.add(self.movie_window)
        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, False, 0)
        hbox.set_border_width(10)
        hbox.pack_start(Gtk.Label(), False, False, 0)
        self.button = Gtk.Button(label="Start")
        self.button.connect("clicked", self.start_stop)
        hbox.pack_start(self.button, False, False, 0)
        self.button2 = Gtk.Button(label="Quit")
        self.button2.connect("clicked", Gtk.main_quit)
        hbox.pack_start(self.button2, False, False, 0)
        hbox.add(Gtk.Label())
        window.show_all()

        # Set up the gstreamer pipeline
        pipeline_description = "v4l2src ! videoconvert ! autovideosink"
        self.player = Gst.parse_launch(pipeline_description)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)

    def start_stop(self, w):
        if self.button.get_label() == "Start":
            self.button.set_label("Stop")
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
        print("done")
        self.player.set_state(Gst.State.NULL)
        self.button.set_label("Start")

    def on_sync_message(self, bus, message):
        message_name = message.get_structure().get_name()
        if message_name != "prepare-window-handle":
            return
        imagesink = message.src
        imagesink.set_property("force-aspect-ratio", True)
        window_id = self.movie_window.get_property("window").get_xid()
        imagesink.set_window_handle(window_id)


if __name__ == "__main__":
    Gst.init(sys.argv)
    Gtk.init(sys.argv)
    GTK_Main()
    Gtk.main()
