# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRLfs
# 	    Robin Keunen <robin@coopiteasy.be>
#       Vincent Van Rossem <vvrossem@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Mettler-Toledo Weighing Scale (Checkout-Dialog 06 Protocol) Hardware Driver',
    'version': '12.0.0.1.0',
    "author": "Coop IT Easy SCRLfs,"
              "Odoo Community Association (OCA)",
    'license': "AGPL-3",
    'website': "https://github.com/OCA/iot/",
    'category': 'Hardware Drivers',
    'summary': 'Hardware Driver for Mettler-Toledo Scales using the Checkout-Dialog 06 Protocol',
    'description': """
Mettler-Toledo Weighing Scale Hardware Driver
=============================================

This module allows the Point-Of-Sale (POS) to connect to a Mettler-Toledo scale using the Checkout-Dialog 06 Protocol 
and is designed to be installed on the POSBox[less] (the gateway between the POS and the hardware) only.

To configure the hardware, add the following entry in the configuration file of the Odoo server of the POSBox[less]:
* toledo_scale_path_to_scale (default = /dev/ttyUSB0)

To configure a static path (e.g. /dev/toledo), please refer to: 
https://unix.stackexchange.com/questions/66901/how-to-bind-usb-device-under-a-static-name

On the main Odoo server: 
* install the Point-Of-Sale Application
* activate the Electronic Scale in IotBox / Hardware Proxy (Point Of Sale > Configuration > Point of Sale) 

This module has been tested with a Mettler-Toledo Ariva-S configured with the Checkout-Dialog 06 protocol
* Ariva-S User's Guide: https://www.mt.com/dam/RET_DOCS/Ariv.pdf
* Checkout-Dialog06 protocol: https://www.manualslib.com/manual/861274/Mettler-Toledo-Viva.html?page=42#manual

""",
    'depends': ['hw_scale'],
    'external_dependencies': {'python': ['serial']},
    'installable': False,
}
