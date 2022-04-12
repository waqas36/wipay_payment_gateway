# coding: utf-8

import json
import logging

import dateutil.parser
import pytz
from werkzeug import urls

from odoo import api, fields, models, _
# from odoo.addons.payment.models.payment_acquirer import ValidationError

# from odoo.tools.float_utils import float_compare
# from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.wipay_payment.controllers.controllers import WipayController
# from odoo.addons.payment_gateway.wipay_payment.controllers.controllers import WipayController
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Acquirerwipay(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[
        ('wipay', 'wipay')
    ], ondelete={'wipay': 'set default'})
    wipay_developer_id = fields.Char(string="Developer ID")
    wipay_merchant_id = fields.Char(string="Merchant ID")


    # def _get_feature_support(self):
    #     """Get advanced feature support by provider.
    # 
    #     Each provider should add its technical in the corresponding
    #     key for the following features:
    #         * fees: support payment fees computations
    #         * authorize: support authorizing payment (separates
    #                      authorization and capture)
    #         * tokenize: support saving payment data in a payment.tokenize
    #                     object
    #     """
    #     res = super(Acquirerwipay, self)._get_feature_support()
    #     res['fees'].append('wipay')
    #     return res

    @api.model
    def _get_wipay_urls(self, environment):

        """ wipay URLS """
        if environment == 'prod':
            return {
                'wipay_form_url': 'https://tt.wipayfinancial.com/plugins/payments/request',

            }
        else:
            return {
                'wipay_form_url': 'https://tt.wipayfinancial.com/plugins/payments/request',

            }

    # def wipay_compute_fees(self, amount, currency_id, country_id):
    #     """ Compute wipay fees.
    #
    #         :param float amount: the amount to pay
    #         :param integer country_id: an ID of a res.country, or None. This is
    #                                    the customer's country, to be compared to
    #                                    the acquirer company country.
    #         :return float fees: computed fees
    #     """
    #     if not self.fees_active:
    #         return 0.0
    #     country = self.env['res.country'].browse(country_id)
    #     if country and self.company_id.country_id.id == country.id:
    #         percentage = self.fees_dom_var
    #         fixed = self.fees_dom_fixed
    #     else:
    #         percentage = self.fees_int_var
    #         fixed = self.fees_int_fixed
    #     fees = (percentage / 100.0 * amount + fixed) / (1 - percentage / 100.0)
    #     return fees

    def wipay_form_generate_values(self, values):
        base_url = self.get_base_url()
        # currency = self.env["sale.order"].sudo().search([("name", "=", values['reference'])])
        # country_code =
        wipay_tx_values = dict(values)
        wipay_tx_values.update({
            'total': "{:.2f}".format(values['amount']),
            'phone': values['partner_phone'],
            'email': values['partner_email'],
            'environment': "live" if self.state == 'enabled' else "sandbox",
            'currency': values["currency"].symbol,
            'country_code': "TT",
            'fee_structure': 'customer_pay',
            'method': 'credit_card',
            'origin': "origin_" + values['reference'],
            'name': values['partner_name'],
            'order_id': values['reference'],
            'response_url': urls.url_join(base_url, WipayController._return_url),
            'account_number': self.wipay_merchant_id if self.state == 'enabled' else "1234567890",

        })
        return wipay_tx_values

    def wipay_get_form_action_url(self):
        self.ensure_one()
        environment = 'prod' if self.state == 'enabled' else 'test'
        return self._get_wipay_urls(environment)['wipay_form_url']


class WipayPayment(models.Model):
    _inherit = 'payment.transaction'

    # wipay_txn_type = fields.Char('Transaction type')
    wipay_hash = fields.Char('Hash')

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _wipay_form_get_tx_from_data(self, data):
        reference = data.get('order_id')
        if not reference:
            error_msg = _('wipay: received data with missing reference (%s) or txn_id (%s)') % (reference, txn_id)
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        # find tx -> @TDENOTE use txn_id ?
        txs = self.env['payment.transaction'].search([('reference', '=', reference)])
        if not txs or len(txs) > 1:
            error_msg = 'wipay: received data for reference %s' % (reference)
            if not txs:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        return txs[0]

    def _wipay_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        # _logger.info('Received a notification from wipay with IPN version %s', data.get('notify_version'))
        # if data.get('test_ipn'):
        #     _logger.warning(
        #         'Received a notification from wipay using sandbox'
        #     ),
        #
        # # TODO: txn_id: shoudl be false at draft, set afterwards, and verified with txn details
        # if self.acquirer_reference and data.get('txn_id') != self.acquirer_reference:
        #     invalid_parameters.append(('txn_id', data.get('txn_id'), self.acquirer_reference))
        # # check what is buyed
        # if float_compare(float(data.get('mc_gross', '0.0')), (self.amount + self.fees), 2) != 0:
        #     invalid_parameters.append(('mc_gross', data.get('mc_gross'), '%.2f' % (self.amount + self.fees)))  # mc_gross is amount + fees
        # if data.get('mc_currency') != self.currency_id.name:
        #     invalid_parameters.append(('mc_currency', data.get('mc_currency'), self.currency_id.name))
        # if 'handling_amount' in data and float_compare(float(data.get('handling_amount')), self.fees, 2) != 0:
        #     invalid_parameters.append(('handling_amount', data.get('handling_amount'), self.fees))
        # # check buyer
        # if self.payment_token_id and data.get('payer_id') != self.payment_token_id.acquirer_ref:
        #     invalid_parameters.append(('payer_id', data.get('payer_id'), self.payment_token_id.acquirer_ref))
        # # check seller
        # if data.get('receiver_id') and self.acquirer_id.wipay_seller_account and data['receiver_id'] != self.acquirer_id.wipay_seller_account:
        #     invalid_parameters.append(('receiver_id', data.get('receiver_id'), self.acquirer_id.wipay_seller_account))
        # if not data.get('receiver_id') or not self.acquirer_id.wipay_seller_account:
        #     # Check receiver_email only if receiver_id was not checked.
        #     # In wipay, this is possible to configure as receiver_email a different email than the business email (the login email)
        #     # In Odoo, there is only one field for the wipay email: the business email. This isn't possible to set a receiver_email
        #     # different than the business email. Therefore, if you want such a configuration in your wipay, you are then obliged to fill
        #     # the Merchant ID in the wipay payment acquirer in Odoo, so the check is performed on this variable instead of the receiver_email.
        #     # At least one of the two checks must be done, to avoid fraudsters.
        #     if data.get('receiver_email') and data.get('receiver_email') != self.acquirer_id.wipay_email_account:
        #         invalid_parameters.append(('receiver_email', data.get('receiver_email'), self.acquirer_id.wipay_email_account))
        #     if data.get('business') and data.get('business') != self.acquirer_id.wipay_email_account:
        #         invalid_parameters.append(('business', data.get('business'), self.acquirer_id.wipay_email_account))

        return invalid_parameters

    def _wipay_form_validate(self, data):
        status = data.get('status')
        former_tx_state = self.state
        res = {
            'acquirer_reference': data.get('transaction_id'),
            'wipay_hash': data.get('hash'),
            # 'wipay_txn_type': data.get('payment_type'),
        }
        # if not self.acquirer_id.wipay_pdt_token and not self.acquirer_id.wipay_seller_account and status in ['Completed', 'Processed', 'Pending']:
        #     template = self.env.ref('payment_wipay.mail_template_wipay_invite_user_to_configure', False)
        #     if template:
        #         render_template = template._render({
        #             'acquirer': self.acquirer_id,
        #         }, engine='ir.qweb')
        #         mail_body = self.env['mail.render.mixin']._replace_local_links(render_template)
        #         mail_values = {
        #             'body_html': mail_body,
        #             'subject': _('Add your wipay account to Odoo'),
        #             'email_to': self.acquirer_id.wipay_email_account,
        #             'email_from': self.acquirer_id.create_uid.email_formatted,
        #             'author_id': self.acquirer_id.create_uid.partner_id.id,
        #         }
        #         self.env['mail.mail'].sudo().create(mail_values).send()

        if status in ['success']:
            try:
                # dateutil and pytz don't recognize abbreviations PDT/PST
                tzinfos = {
                    'PST': -8 * 3600,
                    'PDT': -7 * 3600,
                }
                date = dateutil.parser.parse(data.get('date'), tzinfos=tzinfos).astimezone(pytz.utc).replace(tzinfo=None)
            except:
                date = fields.Datetime.now()
            res.update(date=date)
            self._set_transaction_done()
            if self.state == 'done' and self.state != former_tx_state:
                _logger.info('Validated wipay payment for tx %s: set as done' % (self.reference))
                return self.write(res)
            return True
        elif status in ['Pending', 'Expired']:
            res.update(state_message=data.get('pending_reason', ''))
            self._set_transaction_pending()
            if self.state == 'pending' and self.state != former_tx_state:
                _logger.info('Received notification for wipay payment %s: set as pending' % (self.reference))
                return self.write(res)
            return True
        else:
            error = 'Received unrecognized status for wipay payment %s: %s, set as error' % (self.reference, status)
            res.update(state_message=error)
            self._set_transaction_cancel()
            if self.state == 'cancel' and self.state != former_tx_state:
                _logger.info(error)
                return self.write(res)
            return True
