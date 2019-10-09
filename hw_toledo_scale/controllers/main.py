# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRLfs
#       Robin Keunen <robin@coopiteasy.be>
# 	    Vincent Van Rossem <vvrossem@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
import re
import random
import time

from odoo.addons.hw_scale.controllers import main as hw_scale
from odoo.tools.config import config

from ..secret_toledo_polynomial import p as toledo_polynomial_p
from .dialog06_protocol import Dialog06Protocol

_logger = logging.getLogger(__name__)

DRIVER_NAME = 'scale'
ACK = b'\x06'
NAK = b'\x15'
PRECISION = 3

try:
    import serial
except ImportError:
    _logger.error('Odoo module hw_toledo_scale depends on the pyserial python module')
    serial = None

protocol = Dialog06Protocol


class ToledoScaleDriver(hw_scale.Scale):
    def __init__(self):
        super().__init__()
        self.path_to_scale = config.get(
            'toledo_scale_path_to_scale', '/dev/ttyUSB0')
        self.price = 0
        self.priceKg = 0
        self.uom = 0
        self.error = u'00'

    def _parse_scale_answer(self, protocol, answer, regexp, parse):
        """
        Parse a scale's answer to a weighing request, returning a `(data, error)` pair
        """
        _logger.debug('[PARSE][SCALE] answer {} with the regexp {} and the parse {}'.format(answer, regexp, parse))
        data, error = None, None
        try:
            _logger.debug('[PARSE][SCALE] answer {} with regexp: {}'.format(answer, regexp))
            if not answer and protocol.emptyAnswerValid:
                return data
            if regexp and re.search(regexp, answer):
                _logger.debug('[PARSE][SCALE] answer {} with parse: {}'.format(answer, parse))
                data = parse(answer)
            else:
                match = re.search(regexp, answer)
                if match:
                    data_text = match.group(1)
                    try:
                        data = float(data_text)
                        _logger.debug('[PARSE][SCALE] <ACK> value: %s', data)
                    except ValueError:
                        _logger.exception("Cannot parse <ACK> [%r]", data_text)
                        error = 'Invalid <ACK>, please power-cycle the scale'
                else:
                    _logger.error("Cannot parse scale answer [%r]", answer)
                    error = 'Invalid scale answer, please power-cycle the scale'
        except Exception as e:
            _logger.exception("Cannot parse scale answer [%r]", answer)
            error = ("Could not <ACK> on scale %s with protocol %s: %s" % (
                self.path_to_scale, protocol.name, e))
        return data, error

    ##
    # checkout-dialog 06 methods
    ##
    def _get_kw_value(self, udw_generator, uw_checksum):
        ub_shifts = 0
        if not udw_generator:
            return 0
        udw_kw = uw_checksum << 16
        while not (udw_generator & 0x80000000):
            udw_generator <<= 1
        udw_kw ^= udw_generator
        while not (udw_kw & 0x80000000):
            udw_kw <<= 1
            ub_shifts += 1
            if ub_shifts == 16:
                break
        while (ub_shifts < 16):
            udw_kw ^= udw_generator
            while not (udw_kw & 0x80000000):
                udw_kw <<= 1
                ub_shifts += 1
                if ub_shifts == 16:
                    break
        udw_kw >>= 16
        return format(udw_kw, '04x')

    def _generate_random_hex_code(self):
        return ''.join([random.choice('0123456789ABCDEF') for x in range(4)])

    def _rotate_left(self, num, bits):
        """
        The encoding of the CS-values has to be made by rotating them to the left for n bits
        """
        debut = num[0:bits]
        fin = num[bits:16]
        return "".join(fin + debut)

    def _rotate_right(self, num, bits):
        """
        The encoding of the KW-values has to be made by rotating them to the right for n bits
        """
        debut = num[16 - bits:16]
        fin = num[0:16 - bits]
        return "".join(debut + fin)

    ##
    # records for communications from the POS to the scale
    ##
    def send_record_01(self, unit_price, device):
        """Transmitting of unit price (unit price format: 5/6 digits)"""
        record_01 = "{}{}{}{}{}{}".format(
            self.protocol.eot_stx,
            self.protocol.record_01,
            self.protocol.esc,
            unit_price,
            self.protocol.esc,
            self.protocol.etx).encode('utf-8')
        _logger.debug('------------[POS][Record 01] Transmitting of unit price {} : {}'.format(
            unit_price, record_01))
        device.write(record_01)

    def send_record_03(self, unit_price, tare_value, device):
        """Transmitting of unit_price and tare_value (unit price: 5/6 digits, tare value: 4 digits)"""
        record_03 = "{}{}{}{}{}{}{}".format(
            self.protocol.eot_stx,
            self.protocol.record_03,
            self.protocol.esc,
            unit_price,
            self.protocol.esc,
            tare_value,
            self.protocol.etx).encode('utf-8')
        _logger.debug('------------[POS][Record 03] Transmitting of unit price {} and tare value {} : {}'.format(
            unit_price, tare_value, record_03))
        device.write(record_03)

    def send_record_04(self, unit_price, text, device):
        """Transmitting of unit price and text (TLU) (unit price: 5/6 digits, text: 13 chars"""
        record_04 = "{}{}{}{}{}{}{}".format(
            self.protocol.eot_stx,
            self.protocol.record_04,
            self.protocol.esc,
            unit_price,
            self.protocol.esc,
            text,
            self.protocol.etx).encode('utf-8')
        _logger.debug('------------[POS][Record 04] Transmitting of unit price {} and text {} : {}'.format(
            unit_price, text, record_04))
        device.write(record_04)

    def send_record_05(self, unit_price, tare_value, text, device):
        """
        Transmitting of unit price, tare value and text (TLU)
        (unit price: 5/6 digits, tare value: 4 digits, text: 13 chars
        """
        record_05 = "{}{}{}{}{}{}{}{}{}".format(
            self.protocol.eot_stx,
            self.protocol.record_05,
            self.protocol.esc,
            unit_price,
            self.protocol.esc,
            tare_value,
            self.protocol.esc,
            text,
            self.protocol.etx).encode('utf-8')
        _logger.debug(
            '------------[POS][Record 05] Transmitting of unit price {}, tare value {}  and text {} : {}'.format(
                unit_price, tare_value, text, record_05))
        device.write(record_05)

    def send_record_08(self, device):
        """Status request after receiving <NAK> """
        record_08 = "{}{}{}".format(
            self.protocol.eot_stx,
            self.protocol.record_08,
            self.protocol.etx).encode('utf-8')
        _logger.debug('------------[POS][Record 08] Status request after receiving <NAK> : {}'.format(record_08))
        device.write(record_08)

    def send_record_10(self, cs, kw, device):
        """
        Transmitting of checksums.
        Checksums must be transmitted as uppercase hexadecimal ASCII-chars
        """
        record_10 = "{}{}{}{}{}{}".format(
            self.protocol.eot_stx,
            self.protocol.record_10,
            self.protocol.esc,
            cs,
            kw,
            self.protocol.etx).encode('utf-8')
        _logger.debug(
            '------------[POS][Record 10] Transmitting of checksums (cs : {}, kw : {}) : {}'.format(cs, kw, record_10))
        device.write(record_10)

    def send_eot_enq(self, device):
        """Request for weight"""
        eot_enq = "{}".format(self.protocol.eot_enq).encode('utf-8')
        _logger.debug('------------[POS][EOT ENQ] request for weight : {}'.format(eot_enq))
        device.write(eot_enq)

    def send_eot(self, device):
        """Resetting of scale interface (every response of the scale has to be answered by the POS with EOT)"""
        eot = "{}".format(self.protocol.eot).encode('utf-8')
        _logger.debug('------------[POS][EOT] Resetting of scale interface : {}'.format(eot))
        device.write(eot)

    ##
    # records for communications from the scale to the POS
    ##
    def _get_raw_response(self, connection):
        """ Read records from the scale to the POS """
        result = super()._get_raw_response(connection)
        _logger.debug('------------[SCALE][RAW] raw record : {}'.format(result))
        self.send_eot(connection)  # every response of the scale HAS to be answered by the POS with EOT
        return result

    def request_status_information(self, device):
        """
        Status request after receiving <NAK>
        The cause of the error can be explained by the POS sending record 08 and receiving record 09

        Send record 08
        Read and returns status information from Record 09
        """
        self.send_record_08(device)
        status_code = self.read_record_09(device)
        self.log_status(status_code)
        return status_code

    def read_record_09(self, device):
        scale_answer = self._get_raw_response(device)
        record_no, parse_error = self._parse_scale_answer(
            self.protocol, scale_answer,
            self.protocol.status_regexp,
            self.protocol.parse_record_no)

        if record_no == u'09':
            status_code, error = self._parse_scale_answer(
                self.protocol, scale_answer,
                self.protocol.error_regexp,
                self.protocol.parse_status)
            _logger.debug('------------[SCALE][Record 09] status code : {}'.format(status_code))
            return status_code

    def log_status(self, status):
        if status == u'00':
            _logger.debug('[SCALE][Record 09] status information: no error')
        elif status == u'01':
            _logger.debug('[SCALE][Record 09] status information: general error')
        elif status == u'02':
            _logger.debug('[SCALE][Record 09] status information: parity status or buffer overflow')
        elif status == u'10':
            _logger.debug('[SCALE][Record 09] status information: invalid record no.')
        elif status == u'11':
            _logger.debug('[SCALE][Record 09] status information: invalid unit price')
        elif status == u'12':
            _logger.debug('[SCALE][Record 09] status information: invalid tare value')
        elif status == u'13':
            _logger.debug('[SCALE][Record 09] status information: invalid text')
        elif status == u'20':
            _logger.debug('[SCALE][Record 09] status information: scale is still in motion')
        elif status == u'21':
            _logger.debug('[SCALE][Record 09] status information: scale was not in motion since last operation')
        elif status == u'22':
            _logger.debug('[SCALE][Record 09] status information: measurement is not yet finished')
        elif status == u'30':
            _logger.debug('[SCALE][Record 09] status information: weight is less than minimum weight')
        elif status == u'31':
            _logger.debug('[SCALE][Record 09] status information: scale is less than 0')
        elif status == u'32':
            _logger.debug('[SCALE][Record 09] status information: scale is overloaded')
        self.error = status

    def set_device(self):
        if not self.device:
            try:
                _logger.debug('[DEVICE] Probing %s with protocol %s', self.path_to_scale, protocol)
                self.device = serial.Serial(self.path_to_scale,
                                            baudrate=protocol.baudrate,
                                            bytesize=protocol.bytesize,
                                            stopbits=protocol.stopbits,
                                            parity=protocol.parity,
                                            timeout=1,  # longer timeouts for probing
                                            writeTimeout=1)  # longer timeouts for probing

                self.protocol = protocol
                connected, error = self.request_weighing_operation('001000')
                _logger.debug('[DEVICE] connected: {}'.format(connected))
                if connected:
                    _logger.info('Probing %s: answer looks ok for protocol %s', self.path_to_scale, protocol.name)
                    self.set_status(
                        'connected',
                        'Connected to %s with %s protocol' % (self.device, protocol.name)
                    )
                    self.device.timeout = protocol.timeout
                    self.device.writeTimeout = protocol.writeTimeout
                else:
                    _logger.info('Probing %s: no valid answer to protocol %s', self.path_to_scale, protocol.name)
                    self.set_status('disconnected', 'No supported USB scale found')
                    self.protocol = None
                    self.device = None

            except Exception as e:
                # _logger.exception('Failed probing for scales')
                self.set_status('error', 'Failed probing for scales: %s' % e)
                self.protocol = None
                self.device = None

    def calculate_checksums(self, scale_answer, device):
        """
        The scale sends a random number which has to be used by the POS for encoding the checksums.
        The random number is an 8-bit-number.
        The higher nibble (here called Z1) is used for encoding the CS-values.
        The lower nibble (Z2) is used for encoding the KW-values.
        Returns CS and KW as hexadecimal ASCII-chars
        """
        cs_hex_ascii_encoded, kw_hex_ascii_encoded = None, None

        if not device:
            _logger.debug('[CALCULATE CHECKSUMS] Device information not transmitted to initialization function')
        else:
            try:
                data, error = self._parse_scale_answer(
                    self.protocol, scale_answer,
                    self.protocol.checksums_regexp,
                    self.protocol.parse_checksums)
                d0, z = data
                _logger.debug('[CALCULATE CHECKSUMS] Record 11 returns d0 {} and Z {}'.format(d0, z))
                _logger.debug(
                    '[CALCULATE CHECKSUMS] Checksum and correction value generation with the number {}'.format(z))

                # choose a random checksum (cs)
                cs = self._generate_random_hex_code()
                cs_size = len(cs) * 4
                cs_bin = bin(int(cs, 16))[2:].zfill(cs_size)

                # apply first bit of z on checksum
                cs_bin_encoded = self._rotate_left(cs_bin, int(z[0], 16))
                cs_hex_ascii_encoded = "{:04X}".format(int(cs_bin_encoded, 2))

                # generate kw
                kw = self._get_kw_value(toledo_polynomial_p, int(cs, 16))
                kw_size = len(kw) * 4
                kw_bin = bin(int(kw, 16))[2:].zfill(kw_size)

                # apply second bit of z on kw
                kw_bin_encoded = self._rotate_right(kw_bin, int(z[1], 16))
                kw_hex_ascii_encoded = '{:04X}'.format(int(kw_bin_encoded, 2), 'X')

                _logger.debug('[CALCULATE CHECKSUMS] Checksum chosen before encoding: {}'.format(cs))
                _logger.debug('[CALCULATE CHECKSUMS] Checksum after encoding: {}'.format(cs_hex_ascii_encoded))
                _logger.debug(
                    '[CALCULATE CHECKSUMS] Correction value after encoding: {}'.format(kw_hex_ascii_encoded))
            except Exception as e:
                self.set_status(
                    'error',
                    "During generation of checksum and correction value with Exception {}".format(e))
                self.device = None
        return cs_hex_ascii_encoded, kw_hex_ascii_encoded

    def send_checksums(self, cs, kw, device):
        connected, error = False, None
        try:
            self.send_record_10(cs, kw, device)
            answer_checksum = self._get_raw_response(device)
            if answer_checksum == NAK:
                _logger.debug('[SEND CHECKSUM] Frame received is NAK frame')
                self.set_status(
                    'error',
                    'Could not connect on scale {} with protocol {}. Wrong or Nak response. Answer: {}'.format(
                        self.path_to_scale, self.protocol.name, answer_checksum))
                error = self.request_status_information(device)
            elif answer_checksum == ACK:
                _logger.debug(
                    '[SEND CHECKSUM] Frame received is ACK frame. POS transmits EOT ENQ')
                self.send_eot_enq(device)
                answer_status = self._get_raw_response(device)
                if answer_status == NAK:
                    error = self.request_status_information(device)
                else:
                    record_no, error = self._parse_scale_answer(
                        self.protocol, answer_status, self.protocol.status_regexp, self.protocol.parse_record_no)

                    if record_no == u'11':
                        _logger.debug(
                            '[SEND CHECKSUM] Record 11 received. Scale responds the validity of the checksums')
                        data, error = self._parse_scale_answer(
                            self.protocol,
                            answer_status,
                            self.protocol.checksums_regexp,
                            self.protocol.parse_checksums)
                        d0, z = data
                        _logger.debug('[SEND CHECKSUM] Record 11 returns D0 {} and Z {}'.format(d0, z))
                        if d0 == u'1':
                            _logger.debug('[SEND CHECKSUM] valid checksum: D0 = {}'.format(d0))
                            connected = True
                        elif d0 == u'0':
                            _logger.debug('[SEND CHECKSUM] invalid checksum: D0 = {}'.format(d0))
            else:
                # error during connection
                self.set_status(
                    'error',
                    'Could not connect on scale {} with protocol {}. Frame received : {}'.format(
                        self.path_to_scale, self.protocol.name, answer_checksum))
        except Exception as e:
            self.set_status(
                'error',
                'Could not weigh on scale {} with protocol {}: {}'.format(
                    self.path_to_scale, self.protocol.name, e))
        return connected, error

    def request_weighing_operation(self, price, tare=None, text=None):
        try:
            _logger.debug('[WEIGHING] POS transmits one of the Records 01, 03, 04 or 05')
            with self.scalelock:
                _logger.debug('[WEIGHING] With scalelock')
                if self.device:
                    _logger.debug('[WEIGHING] Has device')
                    # order of events
                    # POS transmits one of the Records 01, 03, 04 or 05
                    if tare and text:
                        self.send_record_05(price, tare, text, self.device)
                    elif text:
                        self.send_record_04(price, text, self.device)
                    elif tare:
                        self.send_record_03(price, tare, self.device)
                    else:
                        self.send_record_01(price, self.device)
                    scale_answer = self._get_raw_response(self.device)
                    return self._handle_weighing_answer(scale_answer)
        except Exception as e:
            _logger.debug('[WEIGHING] Could not weigh on scale {} with protocol {}: {}'.format(
                self.path_to_scale, self.protocol.name, e))
            self.set_status(
                'error',
                'Could not weigh on scale {} with protocol {}: {}'.format(
                    self.path_to_scale, self.protocol.name, e))
            self.device = None
            self.protocol = None

    def _handle_weighing_answer(self, answer):
        connected, error = False, None
        # if there is an error, the scale answers with NAK
        if answer == NAK:
            _logger.debug('[WEIGHING][SCALE] <NAK>')
            # the cause of the error can be explained by the POS sending record 08 and receiving record 09
            error = self.request_status_information(self.device)

        # if no errors, the scale answers with <ACK>
        elif answer == ACK:
            _logger.debug('[WEIGHING][SCALE] <ACK>')
            connected = True
            # the POS can request the weighing result from the scale by transmitting EOT ENQ
            self.send_eot_enq(self.device)
            weighing_result = self._get_raw_response(self.device)

            if weighing_result == NAK:
                _logger.debug('[WEIGHING][RESULT] <NAK> : An error occured.')
                error = self.request_status_information(self.device)
            else:
                record_no, error = self._parse_scale_answer(
                    self.protocol, weighing_result,
                    self.protocol.status_regexp,
                    self.protocol.parse_record_no)

                # if the result is known the scale answers with Record 02
                if record_no == u'02':
                    _logger.debug('[WEIGHING][Record 02] Weight data received.')
                    weight_data, error = self._parse_scale_answer(
                        self.protocol, weighing_result,
                        self.protocol.weigh_6_regexp,
                        self.protocol.parse_weighing_result)

                    # uom, weight, priceKg, price
                    self.uom, self.weight, self.priceKg, self.price = weight_data
                    _logger.debug('[WEIGHING][DATA] uom, weight, priceKg, price updated.')
                    _logger.debug('[WEIGHING][DATA] weight = {}'.format(self.weight))
                    _logger.debug('[WEIGHING][DATA] weight = {}'.format(self.get_weight()))
                else:
                    _logger.debug('[WEIGHING][RESULT] Weight data is not received after an ACK answer.')
                    _logger.debug('[WEIGHING][RESULT] Frame received is {} with status {}'
                                  .format(weighing_result, str(record_no)))
                    error = self.request_status_information(self.device)
        else:
            # at certain time, the scale will request from the POS the calculation and transmitting of checksums
            # this will happen in the course of a weighing operation
            # after receiving of one of the record 01, 03, 04 or 05
            # and happens if one of the following events occurs:
            # - the scale was just powered on
            # - there was an error detected before
            # - 50 weighing operations have taken place
            # - the version number was displayed by the scale (record 20)

            _logger.debug('[WEIGHING] The frame received is neither ACK nor NAK.')
            record_no, error = self._parse_scale_answer(
                self.protocol, answer,
                self.protocol.status_regexp,
                self.protocol.parse_record_no)
            if record_no == u'11':
                _logger.debug('[WEIGHING][Record 11] request of checksums.')
                cs, kw = self.calculate_checksums(answer, self.device)
                connected, error = self.send_checksums(cs, kw, self.device)
            else:
                _logger.debug('[WEIGHING] Record 11 is not received after a NAK answer.')
                _logger.debug('[WEIGHING] Frame received is {} with status {}'
                              .format(answer, str(record_no)))
        return connected, error

    def get_weight(self):
        self.lockedstart()
        return round(self.weight * (10 ** -PRECISION), PRECISION)

    def get_price_all(self):
        self.lockedstart()
        return round(self.price * (10 ** -PRECISION), PRECISION)

    def get_price_kg(self):
        self.lockedstart()
        return round(self.priceKg * (10 ** -PRECISION), PRECISION)

    def get_uom(self):
        self.lockedstart()
        if self.uom == 3:
            return 'kg'
        return self.uom

    def get_error(self):
        self.lockedstart()
        error = self.error
        self.error = u'00'
        return error

    def reset_values(self):
        self.uom = 0
        self.weight = 0
        self.priceKg = 0
        self.price = 0
        self.error = u'00'

    def get_status(self):
        self.lockedstart()
        return self.status

    def run(self):
        self.device = None

        while True:
            if not self.device:
                self.set_device()
                if not self.device:
                    # retry later to support "plug and play"
                    time.sleep(10)
