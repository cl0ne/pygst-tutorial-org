#!/usr/bin/env python

import os
import sys
import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gst, GLib, Gtk  # noqa: E402
# Needed for set_window_handle() to work:
from gi.repository import GstVideo  # noqa: E402, F401


class GTK_Main:
    def __init__(self):
        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("Mpeg2-Player")
        window.set_default_size(500, 400)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox()
        window.add(vbox)
        hbox = Gtk.HBox()
        vbox.pack_start(hbox, False, False, 0)
        self.entry = Gtk.Entry()
        hbox.add(self.entry)
        self.button = Gtk.Button(label="Start")
        hbox.pack_start(self.button, False, False, 0)
        self.button.connect("clicked", self.start_stop)
        self.movie_window = Gtk.DrawingArea()
        vbox.add(self.movie_window)
        window.show_all()

        self.player = Gst.Pipeline.new("player")
        make_element = Gst.ElementFactory.make
        source = make_element("filesrc", "file-source")
        demuxer = make_element("mpegpsdemux", "demuxer")
        demuxer.connect("pad-added", self.demuxer_callback)

        self.queuea = make_element("queue", "queuea")
        audio_parser = make_element("mpegaudioparse", "audio-parser")
        audio_decoder = make_element("mpg123audiodec", "audio-decoder")
        audioconv = make_element("audioconvert", "converter")
        audiosink = make_element("autoaudiosink", "audio-output")

        self.queuev = make_element("queue", "queuev")
        video_parser = make_element("mpegvideoparse", "video-parser")
        video_decoder = make_element("mpeg2dec", "video-decoder")

        png_source = make_element("filesrc", "png-file")
        png_source.set_property("location", os.path.realpath("tvlogo.png"))
        png_parser = make_element("pngparse", "png-parser")
        png_decoder = make_element("pngdec", "png-decoder")
        imagefreeze = make_element("imagefreeze", "imagefreeze")
        videobox = make_element("videobox", "videobox")
        videobox.set_property("border-alpha", 0)
        videobox.set_property("alpha", 0.5)
        videobox.set_property("left", -20)
        videobox.set_property("top", -10)
        alphacolor = make_element("alphacolor", "alphacolor")

        mixer = make_element("videomixer", "mixer")
        video_convert = make_element("videoconvert", "video-convert")
        videosink = make_element("autovideosink", "video-output")

        for e in (
            source, demuxer,
            self.queuea, audio_parser, audio_decoder, audioconv, audiosink,
            self.queuev, video_parser, video_decoder,
            png_source, png_parser, png_decoder, imagefreeze,
            videobox, alphacolor,
            mixer, video_convert, videosink,
        ):
            self.player.add(e)

        source.link(demuxer)

        self.queuev.link(video_parser)
        video_parser.link(video_decoder)
        video_decoder.link(mixer)

        png_source.link(png_parser)
        png_parser.link(png_decoder)
        png_decoder.link(imagefreeze)
        imagefreeze.link(videobox)
        videobox.link(alphacolor)
        alphacolor.link(mixer)

        mixer.link(video_convert)
        video_convert.link(videosink)

        self.queuea.link(audio_parser)
        audio_parser.link(audio_decoder)
        audio_decoder.link(audioconv)
        audioconv.link(audiosink)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)

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

    def demuxer_callback(self, demuxer, pad):
        name_template = pad.get_property("template").name_template
        if name_template == "video_%02x":
            pad.link(self.queuev.get_static_pad("sink"))
        elif name_template == "audio_%02x":
            pad.link(self.queuea.get_static_pad("sink"))


if __name__ == "__main__":
    Gst.init(sys.argv)
    Gtk.init(sys.argv)
    GTK_Main()
    Gtk.main()
