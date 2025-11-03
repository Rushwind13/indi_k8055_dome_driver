"""
A Python module created to interact with pyk8055
Copyright 2016 Observatory Developer

Free software. Do what you want with it.
"""

from ctypes import *

import pyk8055


class device:
    def __init__(self, port=0, mock=False):
        self.mock = mock
        if not self.mock:
            self.dome = pyk8055.device()

    def disconnect(self):
        print("Disconnecting the device...")
        if not self.mock:
            self.dome.lib.CloseDevice()
        print("done.")

    def analog_in(self, channel):
        print("Checking analogue channel %d..." % channel)
        status = 0
        if not self.mock:
            status = self.dome.lib.ReadAnalogChannel(channel)
        print("done.")
        return status

    def analog_all_in(self):
        data1, data2 = c_int(), c_int()
        print("Checking all analogue channels...")
        if not self.mock:
            self.dome.lib.ReadAllAnalog(byref(data1), byref(data2))
        print("done.")
        return data1.value, data2.value

    def analog_clear(self, channel):
        print("Clearing analogue channel %d..." % channel)
        if not self.mock:
            self.dome.lib.ClearAnalogChannel(channel)
        print("done.")

    def analog_all_clear(self):
        print("Clearing both analogue channels...")
        if not self.mock:
            self.dome.lib.ClearAllAnalog()
        print("done.")

    def analog_out(self, channel, value):
        print("Changing the value of analogue channel %d to %d..." % (channel, value))
        if 0 <= value <= 255:
            if not self.mock:
                self.dome.lib.OutputAnalogChannel(channel, value)
            print("done.")
        else:
            print()
            print("Value must be between (inclusive) 0 and 255")

    def analog_all_out(self, data1, data2):
        print("Changing the value of both analogue channels...")
        if 0 <= data1 <= 255 and 0 <= data2 <= 255:
            if not self.mock:
                self.dome.lib.OutputAllAnalog(data1, data2)
            print("done.")
        else:
            print()
            print("Value must be between (inclusive) 0 and 255")

    def digital_write(self, data):
        print("Writing %d to digital channels..." % data)
        if not self.mock:
            self.dome.lib.WriteAllDigital(data)
        print("done.")

    def digital_off(self, channel):
        print("Turning digital channel %d OFF..." % channel)
        if not self.mock:
            self.dome.lib.ClearDigitalChannel(channel)
        print("done.")

    def digital_all_off(self):
        print("Turning all digital channels OFF...")
        if not self.mock:
            self.dome.lib.ClearAllDigital()
        print("done.")

    def digital_on(self, channel):
        print("Turning digital channel %d ON..." % channel)
        if not self.mock:
            self.dome.lib.SetDigitalChannel(channel)
        print("done.")

    def digital_all_on(self):
        print("Turning all digital channels ON...")
        if not self.mock:
            self.dome.lib.SetAllDigital()
        print("done.")

    def digital_in(self, channel):
        print("Checking digital channel %d..." % channel)
        status = 0
        if not self.mock:
            status = self.dome.lib.ReadDigitalChannel(channel)
        print("done.")
        return status

    def digital_all_in(self):
        print("Checking all digital channels...")
        status = 0
        if not self.mock:
            status = self.dome.lib.ReadAllDigital()
        print("done.")
        return status

    def counter_reset(self, channel):
        print("Resetting Counter value...")
        if not self.mock:
            self.dome.lib.ResetCounter(channel)
        print("done.")

    def counter_read(self, channel):
        print("Checking Counter value from counter %d..." % channel)
        status = 0
        if not self.mock:
            status = self.dome.lib.ReadCounter(channel)
        print("done.")
        return status

    def counter_set_debounce(self, channel, time):
        if 0 <= time <= 5000:
            print("Setting Counter %d's debounce time to %dms..." % (channel, time))
            if not self.mock:
                self.dome.lib.SetCounterDebounceTime(channel, time)
            print("done.")
        else:
            print("Time must be between 0 and 5000ms (inclusive).")
