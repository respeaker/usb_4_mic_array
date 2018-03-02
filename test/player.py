"""

"""

import threading
import types
import wave
import pyaudio


CHUNK_SIZE = 1024


class Player:
    def __init__(self, pyaudio_instance=None):
        self.pyaudio_instance = pyaudio_instance if pyaudio_instance else pyaudio.PyAudio()
        self.stop_event = threading.Event()

        self.device_index = None
        for i in range(self.pyaudio_instance.get_device_count()):
            dev = self.pyaudio_instance.get_device_info_by_index(i)
            name = dev['name'].encode('utf-8')
            print('{}:{} with {} input channels'.format(i, name, dev['maxOutputChannels']))
            if name.find('ReSpeaker 4 Mic Array') >= 0 and dev['maxOutputChannels'] >= 1:
                self.device_index = i
                break

        if self.device_index is None:
            raise ValueError('Can not find {}'.format('ReSpeaker 4 Mic Array'))

    def _play(self, data, rate=16000, channels=1, width=2):
        stream = self.pyaudio_instance.open(
            format=self.pyaudio_instance.get_format_from_width(width),
            channels=channels,
            rate=rate,
            output=True,
            output_device_index=self.device_index,
            frames_per_buffer=CHUNK_SIZE,
        )

        if isinstance(data, types.GeneratorType):
            for d in data:
                if self.stop_event.is_set():
                    break

                stream.write(d)
        else:
            stream.write(data)

        stream.close()

    def play(self, wav=None, data=None, rate=16000, channels=1, width=2, block=True):
        """
        play wav file or raw audio (string or generator)
        Args:
            wav: wav file path
            data: raw audio data, str or iterator
            rate: sample rate, only for raw audio
            channels: channel number, only for raw data
            width: raw audio data width, 16 bit is 2, only for raw data
            block: if true, block until audio is played.
            spectrum: if true, use a spectrum analyzer thread to analyze data
        """
        if wav:
            f = wave.open(wav, 'rb')
            rate = f.getframerate()
            channels = f.getnchannels()
            width = f.getsampwidth()

            def gen(w):
                d = w.readframes(CHUNK_SIZE)
                while d:
                    yield d
                    d = w.readframes(CHUNK_SIZE)
                w.close()

            data = gen(f)

        self.stop_event.clear()
        if block:
            self._play(data, rate, channels, width)
        else:
            thread = threading.Thread(target=self._play, args=(data, rate, channels, width))
            thread.start()

    def stop(self):
        self.stop_event.set()

    def close(self):
        pass


def main():
    import sys

    if len(sys.argv) < 2:
        print('Usage: python {} music.wav'.format(sys.argv[0]))
        sys.exit(1)

    player = Player()
    player.play(sys.argv[1])


if __name__ == '__main__':
    main()
