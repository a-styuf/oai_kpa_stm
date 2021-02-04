# -*- coding: utf-8 -*-

import time
import threading
# pip install https://github.com/CrinitusFeles/OaiModbus/releases/download/v.1.1/OAI_ModBus-0.1.1.tar.gz
import oai_modbus
import json


class OaiKpaSTM:
    def __init__(self, *args, **kwargs):
        # разбор именованных параметров
        self.serial_number = kwargs.get('serial_num', '20713699424D')
        self.debug = kwargs.get('debug', False)
        # создание объекта для общения по МодБас
        self.client = oai_modbus.OAI_Modbus(serial_num=[self.serial_number])
        self.client.debug_print_flag = True
        # параметры связи
        self.state = 0
        # описание связи через запись/чтение регистров
        """
            mode: master - 0, slave - 1
            direction: 2Line - 0, 2Line_rx_only - 1, 1Line - 2
            data_size: 8 bit - 0, 16 bit - 1
            polarity: low - 0, high - 1
            phase: one_edge - 0, two_edge - 1
            slave: not_used_et
            baud: 0 - 21 MB / s, 1 - 10, 5 MB / s, 2 - 5, 25 MB / s, 3 - 2, 625 MB / s, 4 - 1, 3125 MB / s, 5 - 656, 25 kB / s, 6 - 328, 125 kB / s, 7 - 164, 062 kB / s.
            firs_bit: 0 - MSB_first, 1 - LSB_first 
            ti_mode: 0 - disable, 1 – enable
        """
        self.register_addr = {
            "scaler": 1246,
            "mode": 1247,
            "direction": 1248,
            "polarity": 1249,
            "phase": 1250,
            "slave": 1251,
            "baud": 1252,
            "first_bit": 1253,
            "ti_mode": 1254
        }
        # параметры работы модуля
        self.iteration = 0
        self.adc_param = {"adc_num": 2, "channel_num": 16}
        self.channel_row_adc_data = [[0 for i in range(self.adc_param["channel_num"])]
                                     for j in range(self.adc_param["adc_num"])]
        self.channel_adc_voltage = [[0 for i in range(self.adc_param["channel_num"])]
                                    for j in range(self.adc_param["adc_num"])]
        self.adc_cal_a = [[1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3],
                          [1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 2.207E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3, 1.224E-3]]
        self.adc_cal_b = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                          [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
        self.stm_max_min_bound = {"min": [[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                                          1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
                                          [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                                          1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]],
                                  "max": [[2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
                                          2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
                                          [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
                                           2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]]
                                  }
        self.channel_state = [[0 for i in range(self.adc_param["channel_num"])]
                              for j in range(self.adc_param["adc_num"])]  # (0 - open, 1 - short, 2 - undefined)
        #
        self.read_write_thread = threading.Thread(target=self.__stm_update, args=(), daemon=True)
        self.read_write_thread.start()
        self.adc_data_lock = threading.Lock()

    def connect(self, serial_num=None):
        """
        connection to the HW-module
        connection parameter can be updated
        :param serial_num: serial_number
        :return: nothing
        """
        if serial_num:
            self.serial_number = serial_num
            self.client.serial_numbers.append(self.serial_number)
        pass
        if self.client.connect() == 1:
            self.state = 1
        else:
            self.state = -1
        return self.state

    def disconnect(self):
        try:
            if self.client.disconnect() == 0:
                self.state = 0
            else:
                self.state = -1
        except AttributeError:
            self.state = -1
            pass
        return self.state

    def __stm_update(self):
        adc_num = 0
        while 1:
            if self.client.connection_status:
                #
                self.client.start_continuously_queue_reading(ai=[[2074, 2078]], ao=[], write=[])
                #
                self.client.write_regs(offset=1246, data_list=[1, 0, 0, 1,
                                                               0, 1, 0, 5,
                                                               0, 0])
                self.client.write_regs(offset=1318, data_list=[1, 0, 0, 1, 2])
                #
                self.iteration += 1
                ch_num = self.iteration % self.adc_param["channel_num"]
                adc_num_old = adc_num
                adc_num = (self.iteration//self.adc_param["channel_num"]) % self.adc_param["adc_num"]
                # set cs
                # set control register
                control_register = ((0x02 << 10) | ((ch_num & 0x0F) << 6) | (0x03 << 4) | (0x01 << 2) | (0x01 << 0)) << 4
                self.client.write_regs(offset=1276, data_list=[control_register, 0x00])

                if adc_num == 0:
                    self.client.write_regs(offset=1266, data_list=[1, 0, 1, 1, 0, 1, 1])
                else:
                    self.client.write_regs(offset=1266, data_list=[1, 0, 1, 1, 0, 1, 2])
                # release cs
                # stm_mod.client.write_regs(offset=1060, data_list=[0x1C00, 0x0000, 0x0000, 0x0000])
                # stm_mod.client.write_regs(offset=1064, data_list=[0x1C00, 0x0000, 0x0000, 0x0000])
                #
                time.sleep(0.1)

                channel_num = (self.client.ai_register_map[2074] >> 12) & 0x0F
                channel_data = (self.client.ai_register_map[2074] & 0xFFF)

                # print("%04X" % self.client.ai_register_map[2074])
                # print(adc_num, ch_num, adc_num_old, channel_num)

                if channel_num != ch_num:
                    # raise ValueError("Error with adc channel")
                    # print("error", channel_num, ch_num)
                    pass
                self.channel_row_adc_data[adc_num][channel_num] = channel_data & 0xFFF
                self.__refresh_channel_values(adc_num, channel_num)
        pass

    def get_channel_values(self, adc, ch_num):
        """
        return state of single adc_channel
        :param adc: adc number (0 or 1)
        :param ch_num: adc channel number (from 0 to 15)
        :return: value pair of voltage and state (0 - open, 1 - short, 2 - undefined)
        """
        with self.adc_data_lock:
            try:
                return self.channel_adc_voltage[adc][ch_num], self.channel_state[adc][ch_num]
            except IndexError:
                raise IndexError("Incorrect adc (0, 1) or channel number(0-15")

    def get_channels_values(self):
        """
        return state of all adc_channels
        :return: list of value pairs of voltage and state (0 - open, 1 - short, 2 - undefined)
        """
        with self.adc_data_lock:
            try:
                val_list = [self.channel_adc_voltage[adc][ch_num] for adc in range(self.adc_param["adc_num"])
                            for ch_num in range(self.adc_param["channel_num"])]
                state_list = [self.channel_state[adc][ch_num] for adc in range(self.adc_param["adc_num"])
                              for ch_num in range(self.adc_param["channel_num"])]
                return val_list, state_list
            except IndexError:
                raise IndexError("Incorrect adc (0, 1) or channel number(0-15")

    def __refresh_channel_values(self, adc, ch_num):
        with self.adc_data_lock:
            a = self.adc_cal_a[adc][ch_num]
            b = self.adc_cal_b[adc][ch_num]
            self.channel_adc_voltage[adc][ch_num] = a * self.channel_row_adc_data[adc][ch_num] + b
            self.channel_state[adc][ch_num] = self.__get_state_from_bound(self.channel_adc_voltage[adc][ch_num],
                                                                          self.stm_max_min_bound["min"][adc][ch_num],
                                                                          self.stm_max_min_bound["max"][adc][ch_num])

    def data_process(self):
        """
        calculate all data from adc_value
        :return: nothing
        """
        for adc in range(self.adc_param["adc_num"]):
            for ch_num in range(self.adc_param["channel_num"]):
                a = self.adc_cal_a[adc][ch_num]
                b = self.adc_cal_b[adc][ch_num]
                self.channel_adc_voltage[adc][ch_num] = a*self.channel_row_adc_data[adc][ch_num] + b
                self.channel_state[adc][ch_num] = self.__get_state_from_bound(self.channel_adc_voltage[adc][ch_num],
                                                                 self.stm_max_min_bound["min"][adc][ch_num],
                                                                 self.stm_max_min_bound["max"][adc][ch_num])

    @staticmethod
    def __get_state_from_bound(val, bound_1, bound_2):
        """
        value checks on correspondence to bounds intervals
        :param val:  value on test
        :param bound_1: minimal bound
        :param bound_2: maximum bound
        :return: state: 1 - val <= bound_1, 0 - val >= bound_2, 2 - other
        """
        if val >= bound_2:
            return 0
        elif val <= bound_1:
            return 1
        else:
            return 2

    def __repr__(self):
        return_str = "oai_kpa_stm module: ser_num %s\n" % self.serial_number
        for adc in range(self.adc_param["adc_num"]):
            return_str += "\t <adc %02d> " % adc
            for ch_num in range(self.adc_param["channel_num"]):
                return_str += "\t %02d: %04.3f" % (ch_num, self.channel_adc_voltage[adc][ch_num])
            return_str += "\n"
        return return_str


if __name__ == '__main__':
    itteration_num = 0
    stm_mod = OaiKpaSTM(serial_num="2082369E424D", debug=False)
    print("Connect")
    stm_mod.connect()
    #
    while 1:
        print(stm_mod)
        time.sleep(1)

