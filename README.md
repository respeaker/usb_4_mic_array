# ReSpeaker USB 4 Mic Array

>Coming soon

![](http://respeaker.io/assets/images/usb_4_mic_array.png)

The ReSpeaker USB 4 Mic Array is the successor of the ReSpeaker USB 6+1 Mic Array. It has better built-in audio processing algorithms than the 6+1 Mic Array, so it has better audio recording quality, although it only has 4 microphones.

## Features
+ 4 microphones
+ 12 RGB LEDs
+ USB
+ built-in AEC, VAD, DOA, Beamforming and NS
+ 16000 sample rate

## Usage
[Audacity](https://www.audacityteam.org/) is recommended to test audio recording.

## Install DFU and LED control driver for Windows
On Linux and macOS, the USB 4 Mic Array will just work. On Windows, audio recording and playback will also work without installing a driver. But in order to upgrade the device's firmware or to control LEDs an DSP parameters on Windows, the libusb-win32 driver is required. We use [a handy tool - Zadig]() to install the libusb-win32 driver for both `SEEED DFU` and `SEEED Control` (the USB 4 Mic Array has 4 devices on Windows Device Manager).

![](http://respeaker.io/assets/images/usb_4mic_array_driver.png)

>Make sure that libusb-win32 is selected, not WinUSB or libusbK

## Device Firmware Update
The Microphone Array supports USB DFU. We have [a python script - dfu.py](https://github.com/respeaker/mic_array_dfu/blob/master/dfu.py) to do that.

```
pip install pyusb
python dfu.py --download new_firmware.bin
```

| firmware             | channels | note                                                                                                                                                                    |
|----------------------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| default_firmware.bin | 1              | processed audio for ASR                                                                                                                                                 |
| i6_firmware.bin      | 6              |  channel 0: processed audio for ASR  channel 1: mic 1 raw data channel 2: mic 2 raw data channel 3: mic 3 raw data channel 4: mic 4 raw data channel 5: merged playback |

## How to control the RGB LED ring
The USB 4 Mic Array has on-board 12 RGB LEDs and has a variety of light effects. Go to the [respeaker/pixel_ring](https://github.com/respeaker/pixel_ring) to learn how to use it. The LED control protocol is at [respeaker/pixel_ring wiki](https://github.com/respeaker/pixel_ring/wiki/ReSpeaker-USB-4-Mic-Array-LED-Control-Protocol).


## Tuning
There are some parameters of built-in algorithms to configure. For example, we can turn off Automatic Gain Control (AGC):

```
python tuning.py AGCONOFF 0
```

To get the full list parameters, run:

```
python tuning.py -p
```

