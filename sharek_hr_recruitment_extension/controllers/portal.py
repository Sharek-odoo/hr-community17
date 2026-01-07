from odoo import http
from odoo.http import request
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment

class WebsiteHrRecruitmentExtended(WebsiteHrRecruitment):

    def _prepare_application_values(self, job, **post):
        """Extend default values with custom fields."""
        values = super()._prepare_application_values(job, **post)

        values.update({
            'years_of_experience': post.get('years_of_experience'),
            'notice_period': post.get('notice_period'),
            'salary_expected': post.get('salary_expected'),
            'gender': post.get('gender'),
            'certificate_two': post.get('certificate_two'),
            'source_id': int(post.get('source_id')) if post.get('source_id') else False,
            'city_residence': int(post.get('city_residence')) if post.get('city_residence') else False,
        })
        return values

    @http.route('/jobs/apply/<model("hr.job"):job>', type='http', auth="public", website=True, sitemap=True)
    def jobs_apply(self, job, **kwargs):
        error = {}
        default = {}
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')

        utm_sources = request.env['utm.source'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])

        return request.render("website_hr_recruitment.apply", {
            'job': job,
            'error': error,
            'default': default,
            'utm_sources': utm_sources,
            'states': states,
        })
