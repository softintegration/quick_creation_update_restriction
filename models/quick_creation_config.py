# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
import ast


class QuickCreationConfig(models.Model):
    _name = "quick.creation.config"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Quick creation config'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean('Active', default=True)
    quick_create = fields.Boolean(string='Quick create', default=True)
    quick_write = fields.Boolean(string='Quick write', default=True)
    quick_creation_model_ids = fields.One2many('quick.creation.config.line', 'creation_config_id')
    quick_creation_model_ids_count = fields.Integer(compute='_compute_quick_creation_model_ids_count')

    @api.depends('quick_creation_model_ids')
    def _compute_quick_creation_model_ids_count(self):
        self.quick_creation_model_ids_count = len(self._get_all_quick_creation_model_ids())

    def action_view_config_lines(self):
        return self._get_action_view_quick_creation_lines(self._get_all_quick_creation_model_ids())

    def _get_all_quick_creation_model_ids(self):
        return self.quick_creation_model_ids+self._get_archived_quick_creation_model_ids()

    def _get_archived_quick_creation_model_ids(self):
        domain = [('creation_config_id', '=', self.id), ('active', '=', False)]
        return self.env['quick.creation.config.line'].search(domain)

    def _get_action_view_quick_creation_lines(self, config_lines):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "quick_creation_update_restriction.quick_creation_config_line_action")
        if len(config_lines) > 1:
            action['domain'] = [('id', 'in', config_lines.ids)]
        elif config_lines:
            form_view = [(self.env.ref('quick_creation_update_restriction.quick_creation_config_line_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = config_lines.id
        # Prepare the context.
        if action.get('context', False):
            new_context = ast.literal_eval(action['context'])
            new_context.update(dict(self._context, default_creation_config_id=self.id))
        else:
            new_context = dict(self._context, default_creation_config_id=self.id)
        action['context'] = new_context
        return action

    def create_config(self, models, users, groups,quick_create,quick_write):
        config_lines = []
        for model in models:
            config_lines.append((0, 0, {
                'model_id': model.id,
                'active': self.active,
                'quick_create':quick_create,
                'quick_write':quick_write,
                'user_ids': users and [(6, 0, users.ids)] or False,
                'group_ids': groups and [(6, 0, users.ids)] or False,
            }))
        self.write({'quick_creation_model_ids': config_lines})

    @api.model
    @tools.ormcache('uid', 'model_name')
    def _user_can_quick_create_model(self, uid, model_name):
        quick_config_detail = self.env['quick.creation.config.line']._get_quick_create_config_by_model(model_name)
        # we have to get all the users directly linked to model quick creation or by their group
        users = quick_config_detail.user_ids + quick_config_detail.group_ids.mapped("users")
        return uid in users.ids

    @api.model
    @tools.ormcache('uid', 'model_name')
    def _user_can_quick_write_model(self, uid, model_name):
        quick_config_detail = self.env['quick.creation.config.line']._get_quick_write_config_by_model(model_name)
        # we have to get all the users directly linked to model quick creation or by their group
        users = quick_config_detail.user_ids + quick_config_detail.group_ids.mapped("users")
        return uid in users.ids

    # the details must be notified so that they can notify the cache by turn
    def write(self, vals):
        writes_to_propagate = {}
        if 'active' in vals:
            writes_to_propagate.update({'active': vals['active']})
        if 'quick_create' in vals:
            writes_to_propagate.update({'quick_create': vals['quick_create']})
        if 'quick_write' in vals:
            writes_to_propagate.update({'quick_write': vals['quick_write']})
        if writes_to_propagate:
            self._get_all_quick_creation_model_ids().write(writes_to_propagate)
        return super(QuickCreationConfig, self).write(vals)

    def unlink(self):
        self._get_all_quick_creation_model_ids().unlink()
        return super(QuickCreationConfig, self).unlink()


class QuickCreationConfigLine(models.Model):
    _name = 'quick.creation.config.line'
    _rec_name = 'model_id'

    creation_config_id = fields.Many2one('quick.creation.config', ondelete='cascade')
    active = fields.Boolean('Active', default=True)
    user_ids = fields.Many2many('res.users', 'quick_creation_user_rel', 'quick_creation_line_id', 'user_id',
                                string='Users',
                                help='User that can quickly create the model record without go to its menu')
    group_ids = fields.Many2many('res.groups', 'quick_creation_group_rel', 'quick_creation_line_id', 'group_id',
                                 string='Groups',
                                 help='Users of this group can quickly create the model record without go to its menu')
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    model_name = fields.Char(string='Model', compute='_compute_model_name')
    quick_create = fields.Boolean(string='Quick create',default=True)
    quick_write = fields.Boolean(string='Quick write',default=True)

    @api.depends('model_id')
    def _compute_model_name(self):
        self.model_name = self.model_id and self.model_id.model or False

    @api.model
    def _get_quick_create_config_by_model(self, model_name):
        domain = [('model', '=', model_name)]
        model = self.env['ir.model'].search(domain)
        return self.search([('model_id', '=', model.id),('quick_create','=',True)])

    @api.model
    def _get_quick_write_config_by_model(self, model_name):
        domain = [('model', '=', model_name)]
        model = self.env['ir.model'].search(domain)
        return self.search([('model_id', '=', model.id),('quick_write','=',True)])

    # we have to deal with cache in the case of update or delete
    @api.model
    def create(self, vals):
        res = super(QuickCreationConfigLine, self).create(vals)
        self.creation_config_id._user_can_quick_create_model.clear_cache(self)
        return res

    def write(self, vals):
        res = super(QuickCreationConfigLine, self).write(vals)
        self.creation_config_id._user_can_quick_create_model.clear_cache(self)
        return res

    def unlink(self):
        res = super(QuickCreationConfigLine, self).unlink()
        self.creation_config_id._user_can_quick_create_model.clear_cache(self)
        return res
