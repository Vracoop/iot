# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRLfs
#       Robin Keunen <robin@coopiteasy.be>
# 	    Vincent Van Rossem <vvrossem@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import http
from odoo.addons.hw_proxy.controllers import main as hw_proxy

from .main import ToledoScaleDriver


_logger = logging.getLogger(__name__)

DRIVER_NAME = 'scale'

try:
    import serial
except ImportError:
    _logger.error('Odoo module hw_toledo_scale depends on the pyserial python module')
    serial = None

scale_thread = None
if serial:
    scale_thread = ToledoScaleDriver()
    hw_proxy.drivers[DRIVER_NAME] = scale_thread


class ToledoScaleProxy(hw_proxy.Proxy):
    @http.route('/hw_proxy/scale_read/', type='json', auth='none', cors='*')
    def scale_read(self):

        if scale_thread:
            scale_thread.request_weighing_operation('001000')
            try:
                res = {'weight': scale_thread.get_weight(),
                    'unit': 'kg',
                    'info': scale_thread.get_error()}
            except AttributeError:
                return False
            return res
        return None

    @http.route('/hw_proxy/scale_price', type='json', auth='none', cors='*')
    def scale_read_data_price(self, price):
        if scale_thread:
            scale_thread.request_weighing_operation(price)
            # retour des résultats
            try:
                res = {'weight': scale_thread.get_weight(),
                       'price': scale_thread.get_price_all(),
                       'uom': scale_thread.get_uom(),
                       'priceKg': scale_thread.get_price_kg(),
                       'error': scale_thread.get_error()}
            except AttributeError:
                return False
            return res
        return None

    @http.route('/hw_proxy/scale_price_tare', type='json', auth='none', cors='*')
    def scale_read_data_price_tare(self, price, tare):
        if scale_thread:
            scale_thread.request_weighing_operation(price, tare)
            # retour des résultats
            try:
                res = {'weight': scale_thread.get_weight(),
                       'price': scale_thread.get_price_all(),
                       'uom': scale_thread.get_uom(),
                       'priceKg': scale_thread.get_price_kg(),
                       'error': scale_thread.get_error()}
            except AttributeError:
                return False
            return res
        return None

    @http.route('/hw_proxy/scale_price_text', type='json', auth='none', cors='*')
    def scale_read_data_price_text(self, price, text):
        if scale_thread:
            scale_thread.request_weighing_operation(price, text)
            # retour des résultats
            try:
                res = {'weight': scale_thread.get_weight(),
                       'price': scale_thread.get_price_all(),
                       'uom': scale_thread.get_uom(),
                       'priceKg': scale_thread.get_price_kg(),
                       'error': scale_thread.get_error()}
            except AttributeError:
                return False
            return res
        return None

    @http.route('/hw_proxy/scale_price_tare_text', type='json', auth='none', cors='*')
    def scale_read_data_price_tare_text(self, price, tare, text):
        if scale_thread:
            scale_thread.request_weighing_operation(price, tare, text)
            # retour des résultats
            try:
                res = {'weight': scale_thread.get_weight(),
                       'price': scale_thread.get_price_all(),
                       'uom': scale_thread.get_uom(),
                       'priceKg': scale_thread.get_price_kg(),
                       'error': scale_thread.get_error()}
            except AttributeError:
                return False
            return res
        return None

    @http.route('/hw_proxy/reset_weight', type='json', auth='none', cors='*')
    def scale_reset_weight(self):
        if scale_thread:
            try:
                scale_thread.reset_values(),
            except AttributeError:
                pass
        return {'status': 'weight reset'}
