# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError
from openerp import SUPERUSER_ID
import logging
logger = logging.getLogger(__name__)


class product_revenue(models.Model):

    _name = "product.revenue"

    @api.depends('line_ids.qty', 'line_ids.price_subtotal', 'commission_price', 'performance_rate')
    def _amount_total(self):
        for order in self:
            member_total = 0
            amount_total = 0.0
            for line in order.line_ids:
                member_total += line.qty
                amount_total += line.price_subtotal
            logger.debug("member_total: %s, commission_price %s" % (order.member_total, order.commission_price))

            commission_total = member_total * order.commission_price * order.performance_rate

            order.update({
                'member_total': member_total,
                'amount_total': amount_total,
                'average_price': member_total and amount_total/member_total or 0,
                'commission_total': commission_total,
                'commission_average_price': member_total and amount_total/member_total or 0,
            })

    name = fields.Char(string='名称', required=True, default='New')

    product_id = fields.Many2one('product.product', '产品', required=True)

    commission_price = fields.Float(string='标准提成', default=350)
    performance_rate = fields.Float(string='业绩折算比', default=1.0)

    member_total = fields.Integer(string='收费人数合计', store=True, compute='_amount_total', track_visibility='always')

    amount_total = fields.Float(string='收费金额合计', store=True, compute='_amount_total', track_visibility='always')

    commission_total = fields.Float(string='提成金额合计', store=True, compute='_amount_total', track_visibility='always')

    average_price = fields.Float(string='收费金额小人均', store=True, compute='_amount_total', track_visibility='always')

    commission_average_price = fields.Float(string='提成金额人均', store=True, compute='_amount_total', track_visibility='always')

    line_ids = fields.One2many('product.revenue.line', 'order_id', 'Lines')

    _sql_constraints = [
        ('product_id_uniq', 'unique (product_id)', u"已存在相同产品的的收入表!"),
    ]

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        self.name = self.product_id.name

    @api.multi
    def make_amount_planned(self):

        print self.env.context

        plan_id = self.env['amount.planned'].search([('revenue_id.product_id', '=', self.product_id.id)])

        if plan_id:
            raise UserError(_(u'计划量已经创建!'))

        cost_item = self.env['cost.item']
        category_ids = self.env['cost.item.category'].search([('need_amount_plan', '=', True)])
        cost_items = cost_item.search([('category_id', 'in', [c.id for c in category_ids])])

        amount_plan_id = self.env['amount.planned'].sudo().create({
            'name': self.product_id.name,
            'revenue_id': self.id,
            'create_id': self.env.user.id,
        })

        for cost_item in cost_items:
            self.env['amount.planned.line'].create({
                'order_id': amount_plan_id.id,
                'cost_item_id': cost_item.id,
            })

        for role in self.env['tour.group.member.type'].search([]):
            logger.debug("ROLE: %s, BASE %s" % (role.name, role.allocation_base))
            self.env['amount.role.number.line'].create({
                'order_id': amount_plan_id.id,
                'role_type_id': role.id,
                'role_number': role.auto_allocation and self.member_total/role.allocation_base or self.member_total,
            })

        role_number_ids = self.env['amount.role.number.line'].search([('order_id', '=', amount_plan_id.id)])

        tour_number = 0
        for role in role_number_ids:
            if role.role_type_id in self.env['tour.group.number'].search([('name', '=', '团队人数')], limit=1).member_type_ids:
                tour_number += role.role_number

        amount_plan_id.write({
            'tour_number': tour_number,
        })

        tour_number_ids = self.env['tour.group.number'].search([])

        for number in tour_number_ids:
            total = 0
            for role in role_number_ids:
                if role.role_type_id in number.member_type_ids:
                    total += role.role_number
            self.env['amount.tour.number.line'].create({
                'order_id': amount_plan_id.id,
                'tour_group_number_id': number.id,
                'tour_number': total,
            })

        oplog = self.env['md.operation.log'].create({
            'category': u'产品计划量', 'state': 'ok',
            'name': u'产品: %s 的计划量已创建[ID: %s] !' % (self.product_id.name, amount_plan_id.id)
        })

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'md.operation.log',
            'res_id': oplog.id,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class product_revenue_line(models.Model):

    _name = "product.revenue.line"

    @api.depends('standard_price', 'qty')
    def _sub_total(self):
        for line in self:
            line.update({
                'price_subtotal': line.standard_price * line.qty,
            })

    @api.one
    @api.constrains('qty')
    def _check_qty(self):
        if self.qty < 0:
            raise ValidationError("Order quantity cannot be negative!")

    order_id = fields.Many2one('product.revenue', string='收入表', required=True, ondelete='cascade', index=True,
                               copy=False)

    sale_channel_id = fields.Many2one('md.sale.channel', string='销售渠道', required=True)
    standard_price = fields.Float(string='标准价', required=True, default=0)
    qty = fields.Integer(string='收费人数', required=True, default=0)

    price_subtotal = fields.Float(compute='_sub_total', string='Subtotal', readonly=True, store=True)







