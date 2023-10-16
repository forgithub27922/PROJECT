# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
import logging
_logger = logging.getLogger(__name__)

class EbayPolicy(models.Model):
    _inherit = 'ebay.policy'

    backend_id = fields.Many2one('ebay.backend', required=True, copy=False)

    @api.model
    def sync_policies(self, backend_id=False):
        response = self.env['product.template'].ebay_execute('GetUserPreferences',
                                                             {'ShowSellerProfilePreferences': True}, backend_id=backend_id)
        if 'SellerProfilePreferences' not in response.dict() or \
                not response.dict()['SellerProfilePreferences']['SupportedSellerProfiles']:
            raise UserError(_('No Business Policies'))
        policies = response.dict()['SellerProfilePreferences']['SupportedSellerProfiles']['SupportedSellerProfile']
        if not isinstance(policies, list):
            policies = [policies]
        # Delete the policies not existing anymore on eBay
        policy_ids = [p['ProfileID'] for p in policies]
        self.search([('policy_id', 'not in', policy_ids),('backend_id', '=', backend_id.id)]).unlink()
        for policy in policies:
            record = self.search([('policy_id', '=', policy['ProfileID']),('backend_id', '=', backend_id.id)])
            if not record:
                record = self.create({
                    'policy_id': policy['ProfileID'],
                    'backend_id': backend_id.id,
                })
            record.write({
                'name': policy['ProfileName'],
                'policy_type': policy['ProfileType'],
                'short_summary': policy['ShortSummary'] if 'ShortSummary' in policy else ' ',
            })

class EbayMapping(models.Model):
    _name = 'ebay.mapping'
    _description = "Ebay Mapping"

    ebay_backend_id = fields.Many2one('ebay.backend', required=True, copy=False)
    mapping_type = fields.Selection([('category', 'Category'),('property', 'Property')], string='Mapping Type', default='category')
    shop_categ_id = fields.Many2one('product.category', copy=False)
    ebay_categ_id = fields.Many2one('ebay.category', copy=False)
    property_id = fields.Many2one('property.set', copy=False)
    ebay_store_categ_id = fields.Many2one('ebay.category', copy=False)

    _sql_constraints = [('unique_mapping', 'unique (ebay_backend_id,mapping_type,shop_categ_id)',
                         'You can not create mapping for same category or attribute')]


class EbayCategory(models.Model):
    _inherit = 'ebay.category'

    backend_id = fields.Many2one('ebay.backend', required=True, copy=False)

    def name_get(self):
        result = []
        for cat in self:
            if self._context.get("only_name",False):
                result.append((cat.id, cat.name))
            else:
                result.append((cat.id, cat.full_name))
        return result

    @api.depends('category_parent_id', 'name')
    def _compute_full_name(self):
        name = self.name if self.name else ''
        parent_id = self.category_parent_id
        category_type = self.category_type
        while parent_id != '0':
            parent = self.search([
                ('category_id', '=', parent_id),
                ('category_type', '=', category_type),
            ], limit=1)
            parent_name = parent.name if parent.name else ''
            name = parent_name + " > " + name
            parent_id = parent.category_parent_id if parent.category_parent_id else '0'
        self.full_name = name

    @api.model
    def _cron_sync(self, auto_commit=False, backend_id=False):
        try:
            self.sync_categories(backend_id=backend_id)
        except UserError as e:
            if auto_commit:
                self.env.cr.rollback()
                self.env.user.message_post(
                    body=_("eBay error: Impossible to synchronize the categories. \n'%s'") % e.args[0])
                self.env.cr.commit()
            else:
                raise e
        except RedirectWarning as e:
            if not auto_commit:
                raise e
            # not configured, ignore
            return

    @api.model
    def sync_store_categories(self, backend_id=False):
        try:
            response = self.env['product.template'].ebay_execute('GetStore', backend_id=backend_id)
        except UserError as e:
            # If the user is not using a store we don't fetch the store categories
            if '13003' in e.name:
                return
            raise e
        categories = response.dict()['Store']['CustomCategories']['CustomCategory']
        if not isinstance(categories, list):
            categories = [categories]
        new_categories = []
        self._create_store_categories(categories, '0', new_categories, backend_id=backend_id)
        # Delete the store categories not existing anymore on eBay
        self.search([
            ('category_id', 'not in', new_categories),
            ('category_type', '=', 'store'),
            ('backend_id', '=', backend_id.id),
        ]).unlink()

    @api.model
    def sync_categories(self, backend_id=False):
        self.sync_store_categories(backend_id=backend_id)

        domain = backend_id.get_values()["ebay_domain"]
        prod = self.env['product.template']
        # First call to 'GetCategories' to only get the categories' version
        categories = prod.ebay_execute('GetCategories',backend_id=backend_id)
        ebay_version = categories.dict()['Version']
        version = backend_id.get_values()['ebay_sandbox_category_version' if domain == 'sand' else 'ebay_prod_category_version']
        if version != ebay_version:
            # If the version returned by eBay is different than the one in Odoo
            # Another call to 'GetCategories' with all the information (ReturnAll) is done

            _logger.info("Passed backend is ===========>>> %s"%backend_id)
            if domain == 'sand':
                backend_id.ebay_sandbox_category_version = ebay_version
            else:
                backend_id.ebay_prod_category_version = ebay_version
            if domain == 'sand':
                levellimit = 2
                call_data = {
                    'DetailLevel': 'ReturnAll',
                    'LevelLimit': levellimit,
                }
            else:
                levellimit = 4
                call_data = {
                    'DetailLevel': 'ReturnAll',
                    #'CategoryParent': 11874,
                }
            response = prod.ebay_execute('GetCategories', call_data, backend_id=backend_id)
            categories = response.dict()['CategoryArray']['Category']
            # Delete the eBay categories not existing anymore on eBay
            category_ids = [c['CategoryID'] for c in categories]
            self.search([
                ('category_id', 'not in', category_ids),
                ('category_type', '=', 'ebay'),
                ('backend_id', '=', backend_id.id),
            ]).unlink()
            self.create_categories(categories, backend_id=backend_id)

    @api.model
    def create_categories(self, categories, backend_id=False):
        for category in categories:
            cat = self.search([
                ('category_id', '=', category['CategoryID']),
                ('category_type', '=', 'ebay'),
                ('backend_id', '=', backend_id.id),
            ])
            if not cat:
                cat = self.create({
                    'category_id': category['CategoryID'],
                    'category_type': 'ebay',
                    'backend_id': backend_id.id,
                })
            cat.write({
                'name': category['CategoryName'],
                'category_parent_id': category['CategoryParentID'] if category['CategoryID'] != category[
                    'CategoryParentID'] else '0',
                'leaf_category': category.get('LeafCategory'),
            })
            if category['CategoryLevel'] == '1':
                call_data = {
                    'CategoryID': category['CategoryID'],
                    'ViewAllNodes': True,
                    'DetailLevel': 'ReturnAll',
                    'AllFeaturesForCategory': True,
                }
                response = self.env['product.template'].ebay_execute('GetCategoryFeatures', call_data, backend_id=backend_id)
                if 'ConditionValues' in response.dict()['Category']:
                    conditions = response.dict()['Category']['ConditionValues']['Condition']
                    if not isinstance(conditions, list):
                        conditions = [conditions]
                    for condition in conditions:
                        if not self.env['ebay.item.condition'].search([('code', '=', condition['ID'])]):
                            self.env['ebay.item.condition'].create({
                                'code': condition['ID'],
                                'name': condition['DisplayName'],
                            })

    @api.model
    def _create_store_categories(self, categories, parent_id, new_categories, backend_id=False):
        for category in categories:
            cat = self.search([
                ('category_id', '=', category['CategoryID']),
                ('category_type', '=', 'store'),
                ('backend_id', '=', backend_id.id),
            ])
            if not cat:
                cat = self.create({
                    'category_id': category['CategoryID'],
                    'category_type': 'store',
                    'backend_id': backend_id.id,
                })
            cat.write({
                'name': category['Name'],
                'category_parent_id': parent_id,
            })
            new_categories.append(category['CategoryID'])
            if 'ChildCategory' in category:
                childs = category['ChildCategory']
                if not isinstance(childs, list):
                    childs = [childs]
                cat._create_store_categories(childs, cat.category_id, new_categories, backend_id=backend_id)
            else:
                cat.leaf_category = True