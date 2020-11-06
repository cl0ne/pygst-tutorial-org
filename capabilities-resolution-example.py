#!/usr/bin/env python

import os
import sys
import gi

gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gst, Gtk  # noqa: E402


class GTK_Main:
    def __init__(self):
        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("Resolutionchecker")
        window.set_default_size(300, -1)
        window.connect("destroy", Gtk.main_quit, "WM destroy")

        vbox = Gtk.VBox()
        window.add(vbox)
        self.entry = Gtk.Entry()
        vbox.pack_start(self.entry, False, True, 0)
        self.button = Gtk.Button(label="Check")
        self.button.connect("clicked", self.start_stop)
        vbox.add(self.button)
        self.resolution_label = Gtk.Label()
        vbox.add(self.resolution_label)
        window.show_all()

        self.player = Gst.Pipeline.new("player")
        make_element = Gst.ElementFactory.make
        source = make_element("filesrc", "file-source")
        decoder = make_element("decodebin", "decoder")
        decoder.connect("pad-added", self.decoder_callback)
        self.fakea = make_element("fakesink", "fakea")
        self.fakev = make_element("fakesink", "fakev")
        self.player.add(source)
        self.player.add(decoder)
        self.player.add(self.fakea)
        self.player.add(self.fakev)
        source.link(decoder)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

    def start_stop(self, w):
        filepath = self.entry.get_text().strip()
        if not os.path.isfile(filepath):
            return
        filepath = os.path.realpath(filepath)
        self.player.set_state(Gst.State.NULL)
        src = self.player.get_by_name("file-source")
        src.set_property("location", filepath)
        self.resolution_label.set_text("")
        self.player.set_state(Gst.State.PAUSED)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            error_source = message.src.name
            err, debug = message.parse_error()
            print("Error from '{}':".format(error_source), err.message)
            print("Debug info:", debug)
            self.player.set_state(Gst.State.NULL)
        elif t != Gst.MessageType.STATE_CHANGED:
            return
        if message.parse_state_changed()[1] != Gst.State.PAUSED:
            return
        decoder = self.player.get_by_name("decoder")
        for pad in decoder.srcpads:
            caps = pad.get_current_caps()
            structure_name = caps.to_string()
            if not structure_name.startswith("video"):
                continue
            width = caps.get_structure(0).get_int("width")[1]
            height = caps.get_structure(0).get_int("height")[1]
            if width >= 1e6:
                continue
            resolution_str = "Width: {}, Height: {}".format(width, height)
            self.resolution_label.set_text(resolution_str)
            self.player.set_state(Gst.State.NULL)
            break

    def decoder_callback(self, decoder, pad):
        structure_name = pad.get_current_caps().to_string()
        if structure_name.startswith("video"):
            fv_pad = self.fakev.get_static_pad("sink")
            pad.link(fv_pad)
        elif structure_name.startswith("audio"):
            fa_pad = self.fakea.get_static_pad("sink")
            pad.link(fa_pad)


if __name__ == "__main__":
    Gst.init(sys.argv)
    Gtk.init(sys.argv)
    GTK_Main()
    Gtk.main()
