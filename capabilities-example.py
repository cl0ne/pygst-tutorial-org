#!/usr/bin/env python

import sys
import gi

gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gst, Gtk  # noqa: E402


class GTK_Main:
    def __init__(self):
        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("Videotestsrc-Player")
        window.set_default_size(300, -1)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        self.button = Gtk.Button(label="Start")
        self.button.connect("clicked", self.start_stop)
        vbox.add(self.button)
        window.show_all()

        self.player = Gst.Pipeline.new("player")

        source = Gst.ElementFactory.make("videotestsrc", "video-source")
        self.player.add(source)

        filter = Gst.ElementFactory.make("capsfilter", "filter")
        self.player.add(filter)
        caps = Gst.Caps.from_string("video/x-raw, width=320, height=230")
        filter.set_property("caps", caps)
        source.link(filter)

        sink = Gst.ElementFactory.make("xvimagesink", "video-output")
        self.player.add(sink)
        filter.link(sink)

    def start_stop(self, w):
        if self.button.get_label() == "Start":
            self.button.set_label("Stop")
            self.player.set_state(Gst.State.PLAYING)
        else:
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")


if __name__ == "__main__":
    Gst.init(sys.argv)
    Gtk.init(sys.argv)
    GTK_Main()
    Gtk.main()
