# -*- coding: utf-8 -*-

{
    'name': 'Quick creation/update restriction',
    'version': '1.0.1',
    'author':'Soft-integration',
    'category': 'Security/Access rights',
    'summary': 'Add restriction to quick creation of records',
    'description': "",
    'depends': [
        'portal'
    ],
    'data': [
        'security/quick_creation_restriction_security.xml',
        'security/ir.model.access.csv',
        'wizard/create_model_config_views.xml',
        'views/quick_creation_config_views.xml',
        'views/quick_creation_restriction_action.xml',
        'views/quick_creation_restriction_menuitem.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
