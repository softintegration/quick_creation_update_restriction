# -*- coding: utf-8 -*-


from lxml import etree
from odoo import models
from odoo.addons.base.models.ir_ui_view import transfer_field_to_modifiers
import logging

_logger = logging.getLogger(__name__)


class IrUiView(models.Model):
    _inherit = "ir.ui.view"

    def _postprocess_tag_field(self, node, name_manager, node_info):
        if node.get('name'):
            attrs = {'id': node.get('id'), 'select': node.get('select')}
            field = name_manager.model._fields.get(node.get('name'))
            if field:
                # apply groups (no tested)
                if field.groups and not self.user_has_groups(groups=field.groups):
                    node.getparent().remove(node)
                    # no point processing view-level ``groups`` anymore, return
                    return
                views = {}
                for child in node:
                    if child.tag in ('form', 'tree', 'graph', 'kanban', 'calendar'):
                        node.remove(child)
                        sub_name_manager = self.with_context(
                            base_model_name=name_manager.model._name,
                        )._postprocess_view(
                            child, field.comodel_name, editable=node_info['editable'],
                        )
                        xarch = etree.tostring(child, encoding="unicode").replace('\t', '')
                        views[child.tag] = {
                            'arch': xarch,
                            'fields': dict(sub_name_manager.available_fields),
                        }
                attrs['views'] = views
                if field.type in ('many2one', 'many2many'):
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

            name_manager.has_field(node.get('name'), attrs)

            field_info = name_manager.field_info.get(node.get('name'))
            if field_info:
                transfer_field_to_modifiers(field_info, node_info['modifiers'])
