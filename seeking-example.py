#!/usr/bin/env python

import os
import sys
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gst, GLib, Gtk  # noqa: E402


NS_IN_SECOND = 1_000_000_000
PREROLL_FINISHED = (Gst.State.READY, Gst.State.PAUSED, Gst.State.PLAYING)


class GTK_Main:
    def __init__(self):
        self.position_refresh_id = None
        self._duration_str = ""

        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("Vorbis-Player")
        window.set_default_size(500, -1)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        self.entry = Gtk.Entry()
        vbox.pack_start(self.entry, False, False, 0)
        hbox = Gtk.HBox()
        vbox.add(hbox)
        buttonbox = Gtk.HButtonBox()
        hbox.pack_start(buttonbox, False, False, 0)
        rewind_button = Gtk.Button(label="Rewind")
        rewind_button.connect("clicked", self.rewind_callback)
        buttonbox.add(rewind_button)
        self.button = Gtk.Button(label="Start")
        self.button.connect("clicked", self.start_stop)
        buttonbox.add(self.button)
        forward_button = Gtk.Button(label="Forward")
        forward_button.connect("clicked", self.forward_callback)
        buttonbox.add(forward_button)
        self.time_label = Gtk.Label()
        self.time_label.set_text("00:00 / 00:00")
        hbox.add(self.time_label)
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
        self.time_label.set_text("00:00 / 00:00")
        if self.button.get_label() == "Start":
            filepath = self.entry.get_text().strip()
            if not os.path.isfile(filepath):
                return
            filepath = os.path.realpath(filepath)
            self.button.set_label("Stop")
            filesrc = self.player.get_by_name("file-source")
            filesrc.set_property("location", filepath)
            self.player.set_state(Gst.State.PLAYING)
        else:
            GLib.source_remove(self.position_refresh_id)
            self.position_refresh_id = None
            self.player.set_state(Gst.State.NULL)
            self.button.set_label("Start")

    def position_refresh(self):
        _, current_pos = self.player.query_position(Gst.Format.TIME)
        pos_str = self.format_ns(current_pos)
        self.time_label.set_text(pos_str + " / " + self._duration_str)
        return GLib.SOURCE_CONTINUE

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.STATE_CHANGED:
            state_transition = message.parse_state_changed()
            if state_transition != PREROLL_FINISHED:
                return
            _, duration = self.player.query_duration(Gst.Format.TIME)
            self._duration_str = self.format_ns(duration)
            self.time_label.set_text("00:00 / " + self._duration_str)
            position_refresh_id = GLib.timeout_add(500, self.position_refresh)
            self.position_refresh_id = position_refresh_id
            return
        elif t == Gst.MessageType.ERROR:
            error_source = message.src.name
            err, debug = message.parse_error()
            print("Error from '{}':".format(error_source), err.message)
            print("Debug info:", debug)
        elif t != Gst.MessageType.EOS:
            return
        GLib.source_remove(self.position_refresh_id)
        self.position_refresh_id = None
        self.player.set_state(Gst.State.NULL)
        self.button.set_label("Start")
        self.time_label.set_text("00:00 / 00:00")

    def demuxer_callback(self, demuxer, pad):
        dec_pad = self.audio_decoder.get_static_pad("sink")
        pad.link(dec_pad)

    def rewind_callback(self, w):
        _, current_pos = self.player.query_position(Gst.Format.TIME)
        new_pos = max(0, current_pos - 10 * NS_IN_SECOND)
        print("Backward:", current_pos, "ns -> ", new_pos, " ns")
        self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, new_pos)

    def forward_callback(self, w):
        _, current_pos = self.player.query_position(Gst.Format.TIME)
        new_pos = current_pos + 10 * NS_IN_SECOND
        print("Forward:", current_pos, "ns -> ", new_pos, " ns")
        self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, new_pos)

    def format_ns(self, t):
        # This method was submitted by Sam Mason.
        # It's much shorter than the original one.
        s, ns = divmod(t, NS_IN_SECOND)
        m, s = divmod(s, 60)

        if m < 60:
            return "%02i:%02i" % (m, s)
        else:
            h, m = divmod(m, 60)
            return "%i:%02i:%02i" % (h, m, s)


if __name__ == "__main__":
    Gst.init(sys.argv)
    Gtk.init(sys.argv)
    GTK_Main()
    Gtk.main()
