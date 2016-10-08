# -*- coding: utf-8 -*-
import time
from openerp import api, _
from openerp import fields, models, api
import datetime
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.exceptions import UserError, ValidationError
import logging
logger = logging.getLogger(__name__)


class orans_direct_sale(models.Model):
    _name = "orans.direct.sale"
    _inherit = 'ir.needaction_mixin'
    _description = "Orans Direct Sale"


    @api.multi
    @api.onchange('partner_id')
    def order_project_partner_id(self):

        for o in self:
            o.update({
                'partner_name': self.env['res.partner'].name,
                'partner_phone': self.partner_id.phone,
            })
        return

    @api.depends('amount_total','delivery_cost', 'buliding_cost', 'installation_cost', 'measurement_cost', 'expedited_cost', 'custom_cost', 'activities_cost', 'activities_cost2', 'depreciation_cost', 'road_cost', 'pay_amount', 'amount')
    @api.multi
    def _amount_all(self):
        for order in self:
            val = 0
            deposit = 0
            for dep in order.deposit_line:
                deposit += dep.amount
            cost = order.delivery_cost + order.buliding_cost + order.installation_cost + order.measurement_cost + + order.expedited_cost + \
                   order.custom_cost + order.activities_cost - order.activities_cost2 + order.depreciation_cost + order.road_cost
            for line in order.order_line:
                val += line.price_subtotal

            order.update({
                'amount_total': val,
                'amount_cost': cost,
                'pay_amount': val + cost - deposit,
                'amount': val + cost - val * order.designers_rebate / 100,
            })

    @api.model
    def _get_default_shop(self):
        # user = self.env['res.users']
        shop_id = self.env.user.shop_id.id
        if not shop_id:
            raise UserError(_('There is no default shop for the current user!'))
        return shop_id


    @api.model
    def _get_default_company_id(self):
        company_id = self.env.user.company_id.id
        if not company_id:
            raise UserError(_('There is no default company for the current user!'))
        return company_id

    picking_id = fields.Many2many('stock.picking', 'superorder_pickings', 'superorder_pickids', 'picking_id',
                                   string=u'移库单')
    name = fields.Char(string=u'订单编号', copy=False, default='/')
    code = fields.Char(string=u'单号', copy=False)
    shop_id = fields.Many2one('sale.shop', string=u'渠道/门店', required=True, default=_get_default_shop)

    state = fields.Selection([
        ('0', u'草稿'),
        ('1', u'审核'),
        ('3', u'取消'),
        ('pause', u'暂停发货'),
        ('2', u'完成'),
        ], string=u'状态', readonly=True, track_visibility='onchange', select=True, copy=False, default='0')

    type = fields.Selection([
        ('0', u'直营'),
        ('1', u'商超'),
        ('2', u'工装'),
        ('3', u'家装'),
        ('4', u'分销'),
        ('5', u'网销'),
        ('6', u'内购'),
        ('7', u'内销'),
        ], string=u'类型', select=True, default='0')
    useage = fields.Selection([('0', u'公用'),('1', u'私用')], string=u'用途', select=True)
    partner_id = fields.Many2one('res.partner', string=u'客户', select=True)

    partner_name = fields.Char(string=u'顾客姓名', select=True)
    partner_phone = fields.Char(string=u'联系电话', select=True)

    city_id = fields.Many2one('orans.area.city', string=u'省', select=True)
    district_id = fields.Many2one('orans.area.district', u'市', select=True)
    town_id = fields.Many2one('orans.area.town', string=u'区', select=True)
    partner_address = fields.Char(string=u'送货地址', select=True)
    date_order = fields.Date(string=u'日期', required=True, select=True, default=datetime.date.today())
    manager_id = fields.Many2one('res.users', string=u'项目经理')
    sup_partner_id = fields.Many2one('res.partner', string=u'供应商')
    brand_id = fields.Char(string=u'品牌', copy=False)
    contract_id = fields.Char(string=u'合同编号', copy=False)
    delivery_order = fields.Date(string=u'送货日期', required=True, select=True, default=datetime.date.today())
    create_date = fields.Date(string=u'创建日期', select=True)
    create_uid = fields.Many2one('res.users', string=u'创建人', select=True)
    order_line = fields.One2many('orans.direct.line.sale', 'order_id', string='Direct Order Lines')
    deposit_line = fields.One2many('orans.deposit.line', 'deposit_id', string='Direct Order Lines')
    delivery_type = fields.Selection([('0', u'自提'),('1', u'送货')], string=u'送货方式', select=True, default='1')
    payment_term = fields.Many2one('account.payment.term', string=u'付款方式')
    delivery_cost = fields.Float(string=u'送货费', digits_compute= dp.get_precision('Account'))
    buliding_cost = fields.Float(string=u'搬楼费', digits_compute= dp.get_precision('Account'))
    installation_cost = fields.Float(string=u'安装费', digits_compute= dp.get_precision('Account'))
    measurement_cost = fields.Float(u'测量费', digits_compute= dp.get_precision('Account'))
    road_cost = fields.Float(string=u'过路费', digits_compute= dp.get_precision('Account'))
    custom_cost = fields.Float(string=u'定制费', digits_compute= dp.get_precision('Account'))
    expedited_cost = fields.Float(string=u'加急费', digits_compute= dp.get_precision('Account'))
    activities_cost = fields.Float(string=u'活动扣款', digits_compute= dp.get_precision('Account'))
    activities_cost2 = fields.Float(string=u'活动补贴', digits_compute= dp.get_precision('Account'))
    depreciation_cost = fields.Float(u'拆旧费', digits_compute= dp.get_precision('Account'))
    mold_cost = fields.Float(string=u'开模费', digits_compute= dp.get_precision('Account'))
    company_id = fields.Many2one('res.company', string='Company', default=_get_default_company_id)
    designers_rebate = fields.Float(string=u'设计师返点')
    market_rebate = fields.Float(string=u'商场扣点')
    company_rebate = fields.Float(string=u'家装公司返点')
    note = fields.Text(string='Terms and conditions')
    promotion = fields.Boolean(string=u'促销', copy=False)
    sale_man = fields.Many2one('res.users', string=u'销售员', copy=False)

    amount_cost = fields.Float(string=u'服务费合计', compute='_amount_all')
    amount_total = fields.Float(string=u'合计', compute='_amount_all')
    pay_amount = fields.Float(string=u'应付金额', compute='_amount_all')
    amount = fields.Float(string=u'实收', compute='_amount_all')

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', '单号必须唯一!'),
    ]
    _order = 'date_order desc'

    @api.model
    def get_promotion(self, vals, list, total):
        flag = False
        prom = self.env['shop.promotion'].load_shop_promotion(vals.get('shop_id'), vals.get('date_order'),
                                                                   vals.get('type'),list, total)
        if len(prom) > 1:
            src = ""
            for pr in prom:
                src += " 和 "
                src += pr['name']
            raise UserError(_(u'错误:'), _(u'此订单符合多个促销规格：%s' % (src,)))
        for pr in prom:
            if pr['mode'] == 'ZLCX' and pr['total'] >= total:
                vals.get('order_line').append([0, False,
                                               {'price_unit': 0, 'product_type': False, 'product_id': pr['product_id'],
                                                'colour': False, 'custom': False,
                                                'uom_qty': pr['qty'], 'product_uos': False, 'discount_price': 0.0,
                                                'product_att': False, 'description': False}])
                flag = True
            for line in vals.get('order_line'):
                if pr['mode'] == 'JGCX' and line[2].get('product_id') == pr['product_id']:
                    line[2].update({'discount_price': pr['price']})
                    flag = True
        if flag == True:
            vals.update({'promotion': True})
        return vals

    @api.model
    def create(self, vals):
        if self.env.context is None:
            self.env.context = {}
        list = []
        total = 0.0
        if vals.get('type', '0') == '0' and vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('direct.sale.type') or '/'
        if vals.get('type', '0') == '1' and vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('super.sale.type') or '/'
        if vals.get('type', '0') == '2' and vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('work.sale.type') or '/'
        if vals.get('type', '0') == '3' and vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('home.sale.type') or '/'
        if vals.get('type', '0') == '4' and vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('dist.sale.type') or '/'
        if vals.get('type', '0') == '5' and vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('web.sale.type') or '/'
        if vals.get('order_line'):
            for line in vals.get('order_line'):
                list.append(line[2].get('product_id'))
                total += line[2].get('uom_qty') * line[2].get('discount_price')
            vals = self.get_promotion(vals, list, total)
        partner_dy = self.env['res.partner']
        contact = 'contact'
        customer_partner = partner_dy.create({
            'name': vals.get('partner_name'),
            'phone': vals.get('partner_phone'),
            'type': contact,
        })
        return super(orans_direct_sale, self).create(vals)

    @api.one
    def copy(self, default=None):
        default = dict(default or {})
        default.update(state='0')
        return super(orans_direct_sale, self).copy(default)

    @api.multi
    def action_cancel(self):
        if self.env.context is None:
            self.env.context = {}
        self.write({'state': '3'})
        return True

    @api.multi
    def action_pause(self):
        self.write({'state': 'pause'})

    @api.multi
    def action_restart(self):
        self.write({'state': '1'})

    @api.model
    def get_discount_role(self):
        ir_model_data = self.env['ir.model.data']
        group_obj = self.env['res.groups']

        groups = ir_model_data.get_object_reference('orans_data', 'group_dy_general_manager')
        group_id = groups and groups[1] or False
        group = group_obj.browse(group_id)
        if self.env.uid in [user.id for user in group.users]:
            return 'gm'

        groups = ir_model_data.get_object_reference('base', 'group_sale_manager')
        group_id = groups and groups[1] or False
        group = group_obj.browse(group_id)
        if self.env.uid in [user.id for user in group.users]:
            return 'sd'

        groups = ir_model_data.get_object_reference('base', 'group_sale_salesman_all_leads')
        group_id = groups and groups[1] or False
        group = group_obj.browse(group_id)
        if self.env.uid in [user.id for user in group.users]:
            return 'sm'

        groups = ir_model_data.get_object_reference('base', 'group_sale_salesman')
        group_id = groups and groups[1] or False
        group = group_obj.browse(group_id)
        if self.env.uid in [user.id for user in group.users]:
            return 'sl'

    @api.multi
    def action_done(self):

        role = self.get_discount_role()

        for order in self.browse():
            if role == 'gm':
                continue
            elif role == 'sd':
                for line in order.order_line:
                    if line.discount_rate < line.product_id.sale_director_discount:
                        raise ValidationError(_(u'无权限, 折扣率为: %f' % (line.discount_rate,)))
                    else:
                        continue
                continue
            elif role == 'sm':
                for line in order.order_line:
                    if line.discount_rate < line.product_id.sale_manager_discount:
                        raise ValidationError(_(u'无权限, 折扣率为: %f' % (line.discount_rate,)))
                    else:
                        continue
                continue

            elif role == 'sl':
                for line in order.order_line:
                    if line.discount_rate < line.product_id.shop_discount:
                        raise ValidationError(_(u'无权限, 折扣率为: %f' % (line.discount_rate,)))
                    else:
                        continue
                continue

        assert len(self.ids) == 1, 'This option should only be used for a single id at a time.'

        picking_obj = self.env['stock.picking']
        stock_move = self.env['stock.move']
        ir_model_data = self.env['ir.model.data']

        dummy, location_dest_id = ir_model_data.get_object_reference('stock', 'stock_location_customers')
        for o in self:

            if not o.shop_id.warehouse_out_id.wh_output_stock_loc_id:
                raise ValidationError(_(u'出货仓库, 请为门店[%s]配置出货仓库' % (o.shop_id.name,)))

            picking_id = picking_obj.create({
                'name': self.env['ir.sequence'].next_by_code('stock.picking'),
                'origin': o.name,
                'date': o.date_order,
                'min_date': o.date_order,
                'date_done': o.date_order,
                'picking_type_id': o.shop_id.warehouse_out_id.out_type_id.id,
                'state': 'draft',
                'company_id': o.company_id.id,
                'note': o.note,
                'move_lines': [],
                'location_id': o.shop_id.warehouse_out_id.wh_output_stock_loc_id.id,
                'location_dest_id': location_dest_id,
            })

            logger.debug("Picking Created : %s" % (picking_id.id, ))

            for line in o.order_line:

                move_id = stock_move.create({
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.uom_qty,
                    'product_uos_qty': line.uom_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'product_uos': line.product_id.uom_id.id,
                    'date': o.date_order,
                    'date_expected': o.date_order,
                    'location_id': o.shop_id.warehouse_out_id.wh_output_stock_loc_id.id,
                    'location_dest_id': location_dest_id,
                    'picking_id': picking_id.id,
                    'type': 'internal',
                    'company_id': o.company_id.id,
                    'tracking_id': False,
                    'state': 'draft',
                })
                logger.debug("Stock Move Created : %s" % (move_id,))
            o.write({'state': '1'})

        return True


class orans_direct_line_sale(models.Model):

    _name = "orans.direct.line.sale"
    _description = "Orans Direct Line Sale"

    @api.multi
    @api.depends('discount_price', 'uom_qty')
    def _amount_line(self):
        for line in self:
            if line.discount_price:
                line.update({
                    'price_subtotal': line.discount_price * line.uom_qty
                })
            else:
                line.update({
                    'price_subtotal': line.price_unit * line.uom_qty,
                })

    @api.multi
    @api.depends('discount_price', 'price_unit')
    def _discount_rate(self):
        for line in self:
            if line.discount_price and line.price_unit > 0.0:
                line.update({
                    'discount_rate': line.discount_price / line.price_unit,
                })
            else:
                line.update({
                    'discount_rate': 1.0,
                })

    order_id = fields.Many2one('orans.direct.sale', string='Order Reference', required=True, ondelete='cascade', select=True)
    sequence = fields.Integer(string='Sequence', help="Gives the sequence order when displaying a list of sales order lines.")
    product_id = fields.Many2one('product.product', string=u'商品名称', domain=[('sale_ok', '=', True)], change_default=True)
    product_type = fields.Char(string=u'型号')
    product_size = fields.Char(string=u'规格')
    product_att = fields.Char(string=u'属性')
    colour = fields.Char(string=u'颜色')
    price_unit = fields.Float(string=u'市场价', digits_compute= dp.get_precision('Product Price'))
    discount_price = fields.Float(string=u'折后价', digits_compute= dp.get_precision('Product Price'))
    uom_qty = fields.Float(string=u'数量', digits_compute= dp.get_precision('Product UoS'), required=True, default='1.0')
    product_uos = fields.Many2one('product.uom', string=u'单位')
    price_subtotal = fields.Float(string=u'小计', digits_compute= dp.get_precision('Account'), compute='_amount_line')
    # price_subtotal = fields.Function(_amount_line, string=u'小计', digits_compute= dp.get_precision('Account'))
    discount_rate = fields.Float(string=u'折扣率', compute='_discount_rate')
    # discount_rate = fields.Function(_discount_rate, string=u'折扣率')
    description = fields.Text(string=u'备注')
    custom = fields.Boolean(string=u'定制')

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        self.update({
            'price_unit': self.product_id.list_price,
            'discount_price': self.product_id.list_price,
            'product_type': self.product_id.product_type,
            'product_size': self.product_id.product_size,
            'product_att': self.product_id.product_att,
            'colour': self.product_id.colour,
        })


class orans_deposit_line(models.Model):
    _name = "orans.deposit.line"
    _description = "Orans Deposit Line"

    deposit_id = fields.Many2one('orans.direct.sale', string='Order Reference', required=True, ondelete='cascade', select=True)
    sequence = fields.Integer(string='Sequence', help="Gives the sequence order when displaying a list of sales order lines.")
    amount = fields.Float(string=u'金额', digits_compute= dp.get_precision('Account'))
    date_order = fields.Date(string=u'日期', select=True)
    description = fields.Char(string=u'备注')


