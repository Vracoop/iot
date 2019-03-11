# -*- coding: utf-8 -*-
# Copyright 2019 Coop IT Easy SCRLfs
# 	    Robin Keunen <robin@coopiteasy.be>
#       Vincent Van Rossem <vvrossem@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Mettler-Toledo Weighing Scale (Checkout-Dialog 06 Protocol) Hardware Driver',
    'category': 'Point of Sale',
    'sequence': 6,
    'summary': 'Hardware Driver for Mettler-Toledo Scales using the Checkout-Dialog 06 Protocol',
    'description': """
Mettler-Toledo Weighing Scale Hardware Driver
=============================================

This module allows the point of sale to connect to a Mettler Toledo scale using the Checkout-Dialog 06 Protocol

""",
    'depends': ['hw_scale'],
    'external_dependencies': {'python': ['serial']},
    'installable': False,
}
