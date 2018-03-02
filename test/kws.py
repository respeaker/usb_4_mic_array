# -*- coding: utf-8 -*-

"""
Keyword spotting using pocketsphinx
"""

import os
import threading

try:
    import Queue as queue
except ImportError:
    import queue

from voice_engine.element import Element
from pocketsphinx.pocketsphinx import Decoder

class KWS(Element):
    def __init__(self):
        super(KWS, self).__init__()

        self.queue = queue.Queue()
        self.on_detected = None
        self.done = False

    def put(self, data):
        self.queue.put(data)

    def start(self):
        self.done = False
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.done = True

    def set_callback(self, callback):
        self.on_detected = callback

    def run(self):
        pocketsphinx_data = os.path.join(os.path.dirname(__file__), 'pocketsphinx-data')
        hmm = os.path.join(pocketsphinx_data, 'hmm')
        dic = os.path.join(pocketsphinx_data, 'dictionary.txt')
        kws_list = os.path.join(pocketsphinx_data, 'keywords.txt')

        config = Decoder.default_config()
        config.set_string('-hmm', hmm)
        config.set_string('-dict', dic)
        config.set_string('-kws', kws_list)
        # config.set_int('-samprate', SAMPLE_RATE) # uncomment if rate is not 16000. use config.set_float() on ubuntu
        config.set_int('-nfft', 512)
        config.set_float('-vad_threshold', 2.7)
        config.set_string('-logfn', os.devnull)

        decoder = Decoder(config)

        decoder.start_utt()

        while not self.done:
            data = self.queue.get()
            decoder.process_raw(data, False, False)
            hypothesis = decoder.hyp()
            if hypothesis:
                keyword = hypothesis.hypstr
                if callable(self.on_detected):
                    self.on_detected(keyword)

                decoder.end_utt()
                decoder.start_utt()

            super(KWS, self).put(data)


def main():
    import time
    from .source import Source

    src = Source()
    kws = KWS()

    src.link(kws)

    def on_detected(keyword):
        print('found {}'.format(keyword))

    kws.set_callback(on_detected)

    kws.start()
    src.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    kws.stop()
    src.stop()


if __name__ == '__main__':
    main()
