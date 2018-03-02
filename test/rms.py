

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


class RMS(Element):
    def __init__(self):
        super(RMS, self).__init__()

        self.channels = 6
        self.channels_mask = [1, 2, 3, 4]

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

    def on_data(self, data):
        pass

    def run(self):
        while not self.done:
            data = self.queue.get()
            data = np.fromstring(data, dtype='int16')

            rms_data = []
            rms_data_db = []
            for ch in self.channels_mask:
                mono = data[ch::self.channels]
                rms = np.sqrt(np.mean(np.square(mono.astype('int32'))))
                rms_data.append(rms)
                # rms = 20 * np.log10(rms)
                # rms_data_db.append(rms)
            
            print(rms_data)

            # x = np.fromstring(data, dtype='int16')

            super(RMS, self).put(data)


def main():
    import time
    import datetime

    src = Source(frames_size=1600)
    rms = RMS()

    # filename = '1.quiet.' + datetime.datetime.now().strftime("%Y%m%d.%H:%M:%S") + '.wav'
    # sink = FileSink(filename, channels=src.channels, rate=src.rate)

    src.pipeline(rms)

    # src.link(sink)

    src.pipeline_start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    src.pipeline_stop()


if __name__ == '__main__':
    main()
