# -*- coding: utf-8 -*-
# from odoo import http

 
# class LmHrContract(http.Controller):
#     @http.route('/lm_hr_contract/lm_hr_contract/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lm_hr_contract/lm_hr_contract/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lm_hr_contract.listing', {
#             'root': '/lm_hr_contract/lm_hr_contract',
#             'objects': http.request.env['lm_hr_contract.lm_hr_contract'].search([]),
#         })

#     @http.route('/lm_hr_contract/lm_hr_contract/objects/<model("lm_hr_contract.lm_hr_contract"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lm_hr_contract.object', {
#             'object': obj
#         })
