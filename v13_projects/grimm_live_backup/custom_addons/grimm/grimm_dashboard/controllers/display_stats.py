from odoo import http, _
from odoo.http import request

import logging

_logger = logging.getLogger(__name__)


class DisplayStats(http.Controller):

    @http.route('/display_stats', type='json', auth='user')
    def display_stats(self, **kwargs):
        disp_stats = request.env['grimm.cost.data'].search([], order='id desc', limit=8)
        qtr_rec = [(elq.amount_total_ct, elq.amount_total_prev, elq.percentage, elq.team_id.id) for elq in disp_stats.filtered(lambda rec: rec.type == 'quarterly').sorted(key=lambda r: r.team_id.id)]
        mon_rec = [(elm.amount_total_ct, elm.amount_total_prev, elm.percentage, elm.team_id.id) for elm in disp_stats.filtered(lambda rec: rec.type == 'monthly').sorted(key=lambda r: r.team_id.id)]
        service, sales, shop, project, cls_service, cls_sales, cls_shop, cls_project = '', '', '', '', '', '', '', ''
        for rec in zip(qtr_rec, mon_rec):
            # (amount_total_ct, amount_total_prev, percentage, team_id)
            stat = '€ %s %s%s%% / € %s %s%s%%' % (rec[0][0], '+' if rec[0][0] > rec[0][1] else '-', rec[0][2], rec[1][0],
                                                '+' if rec[1][0] > rec[1][1] else '-', rec[1][2])
            # bootstrap_class = 'text-success' if rec.amount_total_ct_qtr > rec.amount_total_prev_qtr else 'text-danger'
            bootstrap_class = ''
            if rec[1][3] == 3:
                service, cls_service = stat, bootstrap_class
            if rec[1][3] == 1:
                sales, cls_sales = stat, bootstrap_class
            if rec[1][3] == 2:
                shop, cls_shop = stat, bootstrap_class
            if rec[1][3] == 8:
                project, cls_project = stat, bootstrap_class

        return {'service': service, 'sales': sales, 'shop': shop, 'project': project,
                'cls_service': cls_service, 'cls_sales': cls_sales, 'cls_shop': cls_shop, 'cls_project': cls_project}
