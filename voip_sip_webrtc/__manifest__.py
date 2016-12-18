# -*- coding: utf-8 -*-
{
    'name': "Voip Communication",
    'version': "1.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary': "Make video calls with other users",
    'license':'LGPL-3',
    'data': [
        'views/voip_sip_webrtc_templates.xml',
        'views/res_users_views.xml',
        'views/voip_call_views.xml',
        'views/voip_ringtone_views.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'depends': ['web','crm','bus'],
    'qweb': ['static/src/xml/*.xml'],
    'images':[
        'static/description/1.jpg',
        'static/description/2.jpg',
    ],
    'installable': True,
}