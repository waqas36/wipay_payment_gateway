# -*- coding: utf-8 -*-
import logging
import pprint
import hashlib

import requests
import werkzeug
from werkzeug import urls

from odoo import http
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class WipayController(http.Controller):
    _return_url = '/payment/wipay/dpn'

    @http.route('/payment/wipay/dpn', type='http', auth="public", methods=['POST', 'GET'], csrf=False)
    def wipay_dpn(self, **post):
        """ Paypal DPN """
        _logger.info('Beginning Paypal DPN form_feedback with post data %s', pprint.pformat(post))  # debug
        try:
            print("Confirmation Done.")
            res = self.wipay_validate_data(**post)
        except ValidationError:
            _logger.exception('Unable to validate the Paypal payment')
        return werkzeug.utils.redirect('/payment/process')

    def wipay_validate_data(self, **post):
        res = False
        # post['cmd'] = '_notify-validate'
        reference = post.get('order_id')
        tx = None
        if reference:
            tx = request.env['payment.transaction'].sudo().search([('reference', '=', reference)])
        if not tx:
            # we have seemingly received a notification for a payment that did not come from
            # odoo, acknowledge it otherwise paypal will keep trying
            _logger.warning('received notification for unknown payment reference')
            return False

        wipay_acquirer = request.env['payment.acquirer'].search([('provider', '=', 'wipay')])
        dev_id = wipay_acquirer.wipay_developer_id if wipay_acquirer.state == 'enabled' else "123"
        order_name = post.get("order_id").split("-")[0]
        total = request.env["sale.order"].sudo().search([("name", "=", order_name)]).amount_total
        total = "{:.2f}".format(total)
        key = post.get('transaction_id') + total + dev_id
        result = hashlib.md5(key.encode())
        hash = result.hexdigest()
        resp = []
        if hash == post.get('hash'):
            resp.append("success")
        else:
            resp.append("failed")
        # post.get('status')
        if 'success' in resp:
            _logger.info('WiPay: validated data')
            res = request.env['payment.transaction'].sudo().form_feedback(post, 'wipay')
            if not res and tx:
                tx._set_transaction_error('Validation error occured. Please contact your administrator.')
        elif 'failed' in resp:
            _logger.warning('WiPay: answered INVALID/FAIL on data verification')
            if tx:
                tx._set_transaction_error('Invalid response from WiPay. Please contact your administrator.')
        else:
            _logger.warning('WiPay: unrecognized paypal answer, received %s instead of VERIFIED/SUCCESS or INVALID/FAIL (validation: %s)' % (resp, 'PDT' if pdt_request else 'IPN/DPN'))
            if tx:
                tx._set_transaction_error('Unrecognized error from WiPay. Please contact your administrator.')
        return res

