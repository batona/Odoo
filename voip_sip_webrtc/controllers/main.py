# -*- coding: utf-8 -*-
import requests
import json
import datetime
import logging
_logger = logging.getLogger(__name__)
import werkzeug.utils
import werkzeug.wrappers
import urllib2
import werkzeug
import base64

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import ustr
import openerp.http as http
from openerp.http import request

class VoipController(http.Controller):         
   
    @http.route('/voip/ringtone/<ringtone>/<filename>', type="http", auth="user")
    def voip_ringtone(self, ringtone, filename):
        """Return the ringtone file to be used by javascript"""
        
        voip_ringtone = request.env['voip.ringtone'].browse( int(ringtone) )

        headers = []
        ringtone_base64 = base64.b64decode(voip_ringtone.media)
        headers.append(('Content-Length', len(ringtone_base64)))
        response = request.make_response(ringtone_base64, headers)

        return response

    @http.route('/voip/accept/<call>', type="http", auth="user")
    def voip_accept(self, call):
        """Mark the call as accepted, and open the VOIP window"""
        
        voip_call = request.env['voip.call'].browse( int(call) )
        voip_call.start_time = datetime.datetime.now()
        
        #Assign yourself as the to partner
        voip_call.partner_id = request.env.user.partner_id.id
        
        #Mark your yourself as joined
        self_client = request.env['voip.call.client'].sudo().search([('partner_id','=', request.env.user.partner_id.id), ('vc_id','=', voip_call.id)])
        self_client.state = 'joined'

        #Send the notiofication to everyone including yourself thath you have joined the room
        for voip_client in voip_call.client_ids:
            notification = {'call_id': voip_call.id, 'client_name': request.env.user.partner_id.name}
            request.env['bus.bus'].sendone((request._cr.dbname, 'voip.join', voip_client.partner_id.id), notification)

        return werkzeug.utils.redirect("/voip/window?call=" + str(call) )

    @http.route('/voip/reject/<call>', type="json", auth="user")
    def voip_reject(self, call):
        """Mark the call as rejected"""
        
        voip_call = request.env['voip.call'].browse( int(call) )
        voip_call.status = "rejected"
        return True

    @http.route('/voip/missed/<call>', type="json", auth="user")
    def voip_missed(self, call):
        """Mark the call as missed"""
        
        voip_call = request.env['voip.call'].browse( int(call) )
        voip_call.status = "missed"
        return True
            
    @http.route('/voip/window', type="http", auth="user")
    def voip_window(self, **kwargs):
        """Window for video calls which can be dragged around"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value
        
        voip_call = request.env['voip.call'].browse( int(values['call']) )

        request.uid = request.session.uid
        context = request.env['ir.http'].webclient_rendering_context()

        context['voip_call'] = voip_call
        
        return http.request.render('voip_sip_webrtc.voip_window', qcontext=context)

    @http.route('/voip/call/connect', type="http", auth="user")
    def voip_call_connect(self, **kwargs):
        """The user has accepted camera / audio access, notify everyone else in the call room"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        voip_call = request.env['voip.call'].browse( int(values['call_id']) )

        
        #Send the notiofication to everyone including yourself
        for voip_client in voip_call.client_ids:
            notification = {'call_id': voip_call.id, 'client_name': request.env.user.partner_id.name}
            request.env['bus.bus'].sendone((request._cr.dbname, 'voip.join', voip_client.partner_id.id), notification)

        return "Hi"

    @http.route('/voip/call/sdp', type="http", auth="user")
    def voip_call_sdp(self, **kwargs):
        """Store the description and send it to everyone else"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        voip_call = request.env['voip.call'].browse( int(values['call_id']) )
        
        _logger.error("voip SDP")
        sdp_json = values['sdp']
        
        for voip_client in voip_call.client_ids:
            if voip_client.partner_id.id == request.env.user.partner_id.id:
                _logger.error("self sdp")
                voip_client.sdp = sdp_json
            else:
                _logger.error("other sdp")
                notification = {'call_id': voip_call.id, 'sdp': sdp_json }
                request.env['bus.bus'].sendone((request._cr.dbname, 'voip.sdp', voip_client.partner_id.id), notification)
        
        return "Hello"

    @http.route('/voip/call/ice', type="http", auth="user")
    def voip_call_ice(self, **kwargs):
        """send it to everyone else"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        voip_call = request.env['voip.call'].browse( int(values['call_id']) )
        
        _logger.error("voip ICE")
        ice_json = values['ice']
        
        for voip_client in voip_call.client_ids:
            if voip_client.partner_id.id == request.env.user.partner_id.id:
                _logger.error("self ice")
                voip_client.sdp = ice_json
            else:
                _logger.error("other ice")
                notification = {'call_id': voip_call.id, 'ice': ice_json }
                request.env['bus.bus'].sendone((request._cr.dbname, 'voip.ice', voip_client.partner_id.id), notification)
        
        return "Hello"
        
    @http.route('/voip/call/end', type="http", auth="user")
    def voip_call_end(self, **kwargs):
        """Call ends when person clicks the the end call button"""

        values = {}
        for field_name, field_value in kwargs.items():
            values[field_name] = field_value

        call = request.env['voip.call'].browse( int(values['call_id']) )
        call.status = 'over'
        call.end_time = datetime.datetime.now()
        diff_time = datetime.datetime.strptime(call.end_time, DEFAULT_SERVER_DATETIME_FORMAT) - datetime.datetime.strptime(call.start_date, DEFAULT_SERVER_DATETIME_FORMAT)
        call.duration = str(diff_time.seconds) + " Seconds"
        return True