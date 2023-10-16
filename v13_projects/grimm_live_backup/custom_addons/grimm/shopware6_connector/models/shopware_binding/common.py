# -*- coding: utf-8 -*-
# © 2013-2017 Guewen Baconnier,Camptocamp SA,Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action

class Shopware6Binding(models.AbstractModel):
    """ Abstract Model for the Bindings.

    All the models used as bindings between Shopware and Odoo
    (``shopware.res.partner``, ``shopware.product.product``, ...) should
    ``_inherit`` it.
    """
    _name = 'shopware6.binding'
    _inherit = 'external.binding'
    _description = 'Shopware6 Binding (abstract)'

    # openerp_id = odoo-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='shopware6.backend',
        string='Shopware6 Backend',
        required=True,
        ondelete='restrict',
    )
    # fields.Char because 0 is a valid Shopware ID
    shopware6_id = fields.Char(string='Shopware6 ID')
    created_at = fields.Datetime('Created At (on Shopware6)', readonly=True)
    updated_at = fields.Datetime('Updated At (on Shopware6)', readonly=True)

    queue_ids = fields.Many2many('queue.job', string='Queue Jobs', compute='_compute_queue')

    def _compute_queue(self):
        for binding in self:
            queue_jobs = self.env['queue.job'].sudo().search([('model_name', '=', binding._name),('rec_id', '=', str(binding.id))])
            job_ids = [(6, 0, queue_jobs.ids)]
            binding.queue_ids = job_ids

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_shopware6_link')
    def export_delete_record(self, backend, shopware6_id):
        """ Delete a record on Shopware """
        with backend.work_on(self._name) as work:
            deleter = work.component(usage='record.exporter.deleter')
            return deleter.run(shopware6_id)

    @job(default_channel='root.shopware6')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on Shopware """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_shopware6_link')
    @api.model
    def import_record(self, backend, shopware6_id, force=False):
        """ Import a Shopware6 record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(shopware6_id, force=force)

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self, fields=None, data_option=False):
        """ Export a record on Shopware """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            if data_option:
                return exporter.run(self, fields, data_option = data_option)
            else:
                return exporter.run(self, fields)