

import threading
import sys
if sys.version_info[0] < 3:
    import Queue as queue
else:
    import queue

import numpy as np
import audioop
import pyaudio

from voice_engine.element import Element
from voice_engine.file_sink import FileSink
from kws import KWS
from player import Player


class Source(Element):
    def __init__(self, rate=16000, frames_size=None):

        super(Source, self).__init__()

        self.rate = rate
        self.frames_size = frames_size if frames_size else rate / 100
        self.channels = 6

        self.pyaudio_instance = pyaudio.PyAudio()

        device_index = None
        for i in range(self.pyaudio_instance.get_device_count()):
            dev = self.pyaudio_instance.get_device_info_by_index(i)
            name = dev['name'].encode('utf-8')
            print('{}:{} with {} input channels'.format(i, name, dev['maxInputChannels']))
            if name.find('ReSpeaker 4 Mic Array') >= 0 and dev['maxInputChannels'] == self.channels:
                device_index = i
                break

        if device_index is None:
            raise ValueError('Can not find an input device with {} channel(s)'.format(self.channels))

        self.stream = self.pyaudio_instance.open(
            start=False,
            format=pyaudio.paInt16,
            input_device_index=device_index,
            channels=self.channels,
            rate=int(self.rate),
            frames_per_buffer=int(self.frames_size),
            stream_callback=self._callback,
            input=True
        )

    def _callback(self, in_data, frame_count, time_info, status):
        super(Source, self).put(in_data)

        return None, pyaudio.paContinue

    def start(self):
        self.stream.start_stream()

    def stop(self):
        self.stream.stop_stream()


class Route(Element):
    def __init__(self):
        super(Route, self).__init__()

        self.channels = 6
        self.detect_mask = 0

        self.kws_list = []
        for ch in range(self.channels):
            def callback_gen(channel):
                def on_detected(keyword):
                    self.detect_mask |= 1 << channel
                    print('channel {} detected'.format(channel))

                return on_detected

            kws = KWS()
            self.kws_list.append(kws)
            kws.on_detected = callback_gen(ch)
            kws.start()

        self.queue = queue.Queue()
        self.done = True

    def put(self, data):
        self.queue.put(data)

    def start(self):
        self.done = False
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.done = True

        for ch in range(self.channels):
            self.kws_list[ch].stop()

    def on_data(self, data):
        pass

    def run(self):
        while not self.done:
            data = self.queue.get()
            data = np.fromstring(data, dtype='int16')

            rms_data = []
            rms_data_db = []
            for ch in range(self.channels):
                mono = data[ch::self.channels]
                self.kws_list[ch].put(mono.tostring())


def main():
    import time
    import datetime

    src = Source(frames_size=1600)
    route = Route()

    player = Player(pyaudio_instance=src.pyaudio_instance)

    # filename = '1.quiet.' + datetime.datetime.now().strftime("%Y%m%d.%H:%M:%S") + '.wav'
    # sink = FileSink(filename, channels=src.channels, rate=src.rate)

    src.pipeline(route)

    # src.link(sink)

    src.pipeline_start()

    time.sleep(1)
    player.play('respeaker.wav')
    time.sleep(1)
    player.play('respeaker.wav')

    for _ in range(10):
        time.sleep(1)
        if route.detect_mask == 0b111111:
            print('all channels detected')
            break

    src.pipeline_stop()

    if route.detect_mask != 0b111111:
        print('Not all channels detected')


if __name__ == '__main__':
    main()
