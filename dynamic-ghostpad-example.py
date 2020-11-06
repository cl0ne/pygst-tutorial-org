#!/usr/bin/env python

import os
import sys
import gi

gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gst, Gtk  # noqa: E402


class GTK_Main(object):
    def __init__(self):
        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("Vorbis-Player")
        window.set_default_size(500, -1)
        window.connect("destroy", Gtk.main_quit, "WM destroy")

        vbox = Gtk.VBox()
        window.add(vbox)
        self.entry = Gtk.Entry()
        vbox.pack_start(self.entry, False, False, 0)
        self.button = Gtk.Button(label="Start")
        vbox.add(self.button)
        self.button.connect("clicked", self.start_stop)
        window.show_all()

        self.player = Gst.Pipeline.new("player")
        make_element = Gst.ElementFactory.make
        source = make_element("filesrc", "file-source")
        demuxer = make_element("oggdemux", "demuxer")
        demuxer.connect("pad-added", self.demuxer_callback)
        self.audio_decoder = make_element("vorbisdec", "vorbis-decoder")
        audioconv = make_element("audioconvert", "converter")
        audiosink = make_element("autoaudiosink", "audio-output")

        for e in (source, demuxer, self.audio_decoder, audioconv, audiosink):
            self.player.add(e)

        source.link(demuxer)
        self.audio_decoder.link(audioconv)
        audioconv.link(audiosink)

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

    def demuxer_callback(self, demuxer, pad):
        adec_pad = self.audio_decoder.get_static_pad("sink")
        pad.link(adec_pad)


if __name__ == "__main__":
    Gst.init(sys.argv)
    Gtk.init(sys.argv)
    GTK_Main()
    Gtk.main()
