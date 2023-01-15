# -*- coding: utf-8 -*-


from lxml import etree
from odoo import models,SUPERUSER_ID
from odoo.addons.base.models.ir_ui_view import transfer_field_to_modifiers
import logging

_logger = logging.getLogger(__name__)


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    def _postprocess_tag_field(self, node, name_manager, node_info):
        super(IrUiView,self)._postprocess_tag_field(node,name_manager,node_info)
        # The super-administrators (technical admin user and human admin user) are not concerned by this constrains
        if self.env.user.id in (SUPERUSER_ID, self.env.ref('base.user_admin').id):
            return
        if node.get('name'):
            field = name_manager.model._fields.get(node.get('name'))
            if field and field.type in ('many2one', 'many2many'):
                comodel = self.env[field.comodel_name].sudo(False)
                can_create = comodel.check_access_rights('create', raise_exception=False)
                can_write = comodel.check_access_rights('write', raise_exception=False)
                # another layer of security must be added here
                can_create = can_create and self.env['quick.creation.config']._user_can_quick_create_model(
                    self.env.uid, comodel._name)
                can_write = can_write and self.env['quick.creation.config']._user_can_quick_write_model(
                    self.env.uid, comodel._name)
                node.set('can_create', 'true' if can_create else 'false')
                node.set('can_write', 'true' if can_write else 'false')