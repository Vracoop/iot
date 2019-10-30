# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRLfs
#       Robin Keunen <robin@coopiteasy.be>
# 	    Vincent Van Rossem <vvrossem@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from collections import namedtuple

_logger = logging.getLogger(__name__)

try:
    import serial
except ImportError:
    _logger.error('Odoo module hw_dialog06_scale depends on the pyserial python module')
    serial = None


def _parse_record_no(data):
    """ Parse a record, returning number value"""
    data = data.decode('utf-8')
    stx = data.index(u'\x02')  # STX (Start of Text) ASCII control character
    record_no = data[stx + 1: stx + 3]
    _logger.debug('[PARSE][RECORD] record no. : {}'.format(record_no))
    return record_no


def _parse_checksums_request(data):
    """
    Parse record 11, returning d0 value (and z value only if d0 == 2)
    If checksums are invalid, d0 = 0 else d0 = 1
    If d0 = 2, use random number z

    """
    d0, z = None, None

    record_no = _parse_record_no(data)
    data = data.decode('utf-8')
    if record_no == u'11':
        esc = data.index(u'\x1b')
        d0 = data[esc + 1]
        if d0 == u'2':
            z = data[data.index(d0) + 1:data.index(d0) + 3]
    _logger.debug('[PARSE][CHECKSUMS] d0 : {} and z : {}'.format(d0, z))
    return d0, z


def _parse_weighing_result(data):
    """ Parse Record 02, returning unit of measure (uom), weight, unit price and total price values """
    record_no, uom, scale_weight, unit_price, total_price = None, None, None, None, None

    record_no = _parse_record_no(data)
    data = data.decode('utf-8')
    if record_no == u'02':
        esc_indices = [i for i, x in enumerate(data) if x == u'\x1b']
        uom = data[esc_indices[0] + 1]
        scale_weight = data[esc_indices[1] + 1: esc_indices[1] + 6]
        unit_price = data[esc_indices[2] + 1: esc_indices[2] + 7]
        total_price = data[esc_indices[3] + 1: esc_indices[3] + 7]

    _logger.debug('[PARSE][WEIGHING] uom : {}, weight : {}, price_kg : {} and price : {}'.format(
        uom, scale_weight, unit_price, total_price))
    return int(uom), int(scale_weight), int(unit_price), int(total_price)


def _parse_status_information(data):
    """ Parse record 09, returning the status code value """
    status_code = None

    record_no = _parse_record_no(data)
    data = data.decode('utf-8')
    if record_no == u'09':
        esc = data.index(u'\x1b')
        status_code = data[esc + 1:esc + 3]
    _logger.debug('[PARSE][STATUS] status code : {}'.format(status_code))
    return status_code


ScaleProtocol = namedtuple(
    'ScaleProtocol',
    "name baudrate bytesize stopbits parity timeout writeTimeout weightRegexp statusRegexp "
    "statusParse commandTerminator commandDelay weightDelay newWeightDelay "
    "weightCommand zeroCommand tareCommand clearCommand emptyAnswerValid autoResetWeight "
    "ack_regexp status_regexp checksums_regexp weigh_6_regexp error_regexp "
    "parse_record_no parse_checksums parse_weighing_result parse_status "
    "record_01 record_03 record_04 record_05 record_08 record_10 "
    "eot_stx etx esc eot_enq eot")

Dialog06Protocol = ScaleProtocol(
    name='Dialog06',
    baudrate=9600,
    bytesize=serial.SEVENBITS,
    stopbits=serial.STOPBITS_ONE,
    parity=serial.PARITY_ODD,
    timeout=0.03,

    writeTimeout=0.5,
    weightRegexp=None,

    commandTerminator=u"",
    commandDelay=0.2,
    weightDelay=0.5,
    newWeightDelay=5,

    weightCommand=None,
    zeroCommand=None,
    tareCommand=None,
    clearCommand=None,  # No clear command -> Tare again

    eot_stx=u'\x04\x02',  # EOT and Start of Text ASCII control characters
    etx=u'\x03',  # End of Text ASCII control character
    esc=u'\x1b',  # Escape ASCII control character
    eot_enq=u'\x04\x05',  # EOT and Enquiry ASCII control characters
    eot=u'\x04',  # End of Transmission ASCII control character

    ack_regexp=b'',
    status_regexp=b'^\\x02([0-9]*)',
    checksums_regexp=b'^\\x0211\\x1b([0-9a-fA-F]+)',
    weigh_6_regexp=b'^\\x0202\\x1b([0-9a-fA-F]+)\\x1b([0-9a-fA-F]+)\\x1b([0-9a-fA-F]+)\\x1b([0-9a-fA-F]+)',
    error_regexp=b'^\\x0209\\x1b([0-9a-fA-F]+)',
    statusRegexp=None,

    statusParse=None,
    parse_record_no=_parse_record_no,
    parse_checksums=_parse_checksums_request,
    parse_weighing_result=_parse_weighing_result,
    parse_status=_parse_status_information,

    record_01=u'01',
    record_03=u'03',
    record_04=u'04',
    record_05=u'05',
    record_08=u'08',
    record_10=u'10',

    emptyAnswerValid=None,
    autoResetWeight=None,
)
