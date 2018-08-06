#!/usr/bin/env python
"""
DFU tool for ReSpeaker USB Mic Array

Requirements:
    pip install pyusb click

Usage:
    python dfu.py --download new_firmware.bin
    python dfu.py --revertfactory
"""

import sys
import time
import usb.core
import usb.util
import click


class DFU(object):
    TIMEOUT = 120000

    DFU_DETACH = 0
    DFU_DNLOAD = 1
    DFU_UPLOAD = 2
    DFU_GETSTATUS = 3
    DFU_CLRSTATUS = 4
    DFU_GETSTATE = 5
    DFU_ABORT = 6

    DFU_STATUS_DICT = {
        0x00: 'No error condition is present.',
        0x01: 'File is not targeted for use by this device.',
        0x02: 'File is for this device but fails some vendor-specific '
            'verification test.',
        0x03: 'Device is unable to write memory.',
        0x04: 'Memory erase function failed.',
        0x05: 'Memory erase check failed.',
        0x06: 'Program memory function failed.',
        0x07: 'Programmed memory failed verification.',
        0x08: 'Cannot program memory due to received address that is our of '
            'range.',
        0x09: 'Received DFU_DNLOAD with wLength = 0, but device does not think it'
            'has all of the data yet.',
        0x0a: "Device's firmware is corrupt. It cannot return to run-time "
            "(non-DFU) operations.",
        0x0b: 'iString indicates a vendor-specific error.',
        0x0c: 'Device detected unexpected USB reset signaling.',
        0x0d: 'Device detected unexpected power on reset.',
        0x0e: 'Something went wrong, but the device does not know what is was.',
        0x0f: 'Device stalled a unexpected request.',
    }

    @staticmethod
    def find():
        """
        find all USB devices with a DFU interface
        """
        devices = []
        for device in usb.core.find(find_all=True, idVendor=0x2886, idProduct=0x0018):
            configuration = device.get_active_configuration()

            for interface in configuration:
                if interface.bInterfaceClass == 0xFE and interface.bInterfaceSubClass == 0x01:
                    devices.append((device,  interface.bInterfaceNumber, configuration.bNumInterfaces))
                    break

        return devices

    def __init__(self):
        devices = self.find()
        if not devices:
            raise ValueError('No DFU device found')

        # TODO: support multiple devices
        if len(devices) > 1:
            raise ValueError('Multiple DFU devices found')

        self.device, self.interface, self.num_interfaces = devices[0]

        # if self.device.is_kernel_driver_active(self.interface):
        #     self.device.detach_kernel_driver(self.interface)

        usb.util.claim_interface(self.device, self.interface)

    def __enter__(self):
        # TODO: suppose the device has more than 1 interface at Run-Time
        if self.num_interfaces > 1:
            print('entering dfu mode')
            self._detach()
            self.close()

            # wait for re-enumerating device
            timeout = 20
            while timeout:
                timeout -= 1
                time.sleep(1)
                devices = self.find()

                if len(devices) and devices[0][2] == 1:
                    print('found dfu device')
                    break
            else:
                raise ValueError('No re-enumerated DFU device found')

            self.device, self.interface, _ = devices[0]

            # # Windows doesn't implement this
            # if self.device.is_kernel_driver_active(self.interface):
            #     self.device.detach_kernel_driver(self.interface)

            usb.util.claim_interface(self.device, self.interface)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def download(self, firmware):
        """
        Args:
            firmware (file object): the file to download.
        """
        block_size = 64
        block_number = 0
        print('downloading')
        while True:
            data = firmware.read(block_size)
            self._download(block_number, data)
            status = self._get_status()[0]
            if status:
                raise IOError(self.DFU_STATUS_DICT[status])

            block_number += 1
            sys.stdout.write('{} bytes\r'.format(block_number * block_size))
            sys.stdout.flush()

            if not data:
                break

        print('\ndone')

    def upload(self, firmware):
        pass

    def _detach(self):
        return self._out_request(self.DFU_DETACH)

    def _download(self, block_number, data):
        return self._out_request(self.DFU_DNLOAD, value=block_number, data=data)


    def _get_status(self):
        data = self._in_request(self.DFU_GETSTATUS, 6)

        status = data[0]
        timeout = data[1] + data[2] << 8 + data[3] << 16
        state = data[4]
        status_description = data[5]         # index of status description in string table

        return status, timeout, state, status_description

    def _clear_status(self):
        return self._out_request(self.DFU_CLRSTATUS)

    def _get_state(self):
        return self._in_request(self.DFU_GETSTATE, 1)[0]

    def _abort(self):
        return self._out_request(self.DFU_ABORT)

    def _out_request(self, request, value=0, data=None):
        return self.device.ctrl_transfer(
            usb.util.CTRL_OUT | usb.util.CTRL_TYPE_CLASS | usb.util.CTRL_RECIPIENT_INTERFACE,
            request, value, self.interface, data, self.TIMEOUT)

    def _in_request(self, request, length):
        return self.device.ctrl_transfer(
            usb.util.CTRL_IN | usb.util.CTRL_TYPE_CLASS | usb.util.CTRL_RECIPIENT_INTERFACE,
            request, 0x0, self.interface, length, self.TIMEOUT)

    def close(self):
        """
        close the interface
        """
        usb.util.dispose_resources(self.device)


class XMOS_DFU(DFU):
    XMOS_DFU_RESETDEVICE = 0xf0
    XMOS_DFU_REVERTFACTORY = 0xf1
    XMOS_DFU_RESETINTODFU = 0xf2
    XMOS_DFU_RESETFROMDFU = 0xf3
    XMOS_DFU_SAVESTATE = 0xf5
    XMOS_DFU_RESTORESTATE = 0xf6

    def __init__(self):
        super(XMOS_DFU, self).__init__()

    def _detach(self):
        return self._out_request(self.XMOS_DFU_RESETINTODFU)

    def leave(self):
        return self._out_request(self.XMOS_DFU_RESETFROMDFU)

    def revertfactory(self):
        return self._out_request(self.XMOS_DFU_REVERTFACTORY)

    def __exit__(self, exc_type, exc_value, traceback):
        self.leave()   



@click.command()
@click.option('--download', '-d', nargs=1, type=click.File('rb'), help='the firmware to download')
@click.option('--revertfactory', is_flag=True, help="factory reset")
def main(download, revertfactory):
    dev = XMOS_DFU()

    with dev:
        if download:
            dev.download(download)
        elif revertfactory:
            dev.revertfactory()

    dev.close()

if __name__ == '__main__':
    main()


