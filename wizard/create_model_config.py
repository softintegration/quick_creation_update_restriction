# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class CreateModelConfig(models.TransientModel):
    _name = 'create.model.config'
    _description = 'Create model config'

    creation_config_id = fields.Many2one('quick.creation.config')
    model_ids = fields.Many2many('ir.model', string='Models')
    quick_create = fields.Boolean(string='Quick create', default=True)
    quick_write = fields.Boolean(string='Quick write', default=True)
    user_ids = fields.Many2many('res.users', string='Users',
                                help='User that can quickly create the model record without go to its menu')
    group_ids = fields.Many2many('res.groups', string='Groups',
                                 help='Users of this group can quickly create the model record without go to its menu')

    def apply(self):
        self._check_models()
        self._check_apply_scop()
        return self.creation_config_id.create_config(self.model_ids,self.user_ids,self.group_ids,self.quick_create,self.quick_write)

    def _check_models(self):
        if not self.model_ids:
            raise UserError(_("Models must be specified!"))

    def _check_apply_scop(self):
        if not self.user_ids and not self.group_ids:
            raise UserError(_("Users or Groups must be specified to apply the scop of config"))
