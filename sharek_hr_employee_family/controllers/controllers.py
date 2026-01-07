# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
# from odoo import http


# class LmHrFamily(http.Controller):
#     @http.route('/lm_hr_family/lm_hr_family/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lm_hr_family/lm_hr_family/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('lm_hr_family.listing', {
#             'root': '/lm_hr_family/lm_hr_family',
#             'objects': http.request.env['lm_hr_family.lm_hr_family'].search([]),
#         })

#     @http.route('/lm_hr_family/lm_hr_family/objects/<model("lm_hr_family.lm_hr_family"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lm_hr_family.object', {
#             'object': obj
#         })
