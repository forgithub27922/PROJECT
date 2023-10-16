from odoo import http
from odoo.addons.website.controllers.main import Website


class WebsiteHome(Website):

    @http.route('/', type='http', auth="public", website=True)
    def index(self, **kw):
        # super(WebsiteHome, self).index(**kw)
        if not http.request.session.uid:
            return http.request.redirect('/web/login')
        return http.request.redirect('/web')


class WebsiteHrRecruitment(http.Controller):
 
    @http.route('''/jobs/apply/<model("hr.job", "[('website_id', 'in', (False, current_website_id))]"):job>''', type='http', auth="public", website=True)
    def jobs_apply(self, job, **kwargs):
        country_data = http.request.env['res.country'].sudo().search([])
        country_list = [(country.id, country.name) for country in country_data]

        state_list = []
        city_list = []
        if http.request.env.company.country_id:
            state_data = http.request.env['res.country.state'].sudo().search([('country_id', '=', http.request.env.company.country_id.id)])
            state_list = [(state.id, state.name) for state in state_data]
            if state_data:
                city_data = http.request.env['res.city'].sudo().search([('state_id', 'in', state_data.ids)])
                city_list = [(city.id, city.name) for city in city_data]

        job_data = http.request.env['hr.job'].sudo().search([])
        job_list = [(job.id, job.name) for job in job_data]

        values = {
            'countries': country_list,
            'states': state_list,
            'jobs': job_list,
            'cities': city_list,
            'job': job,
        }
        return http.request.render("website_hr_recruitment.apply", values)

 
class WebsiteForm(http.Controller):

    @http.route('/website_form_recruitment', type='json', auth="public", methods=['POST'], website=True)
    def website_form(self, **kwargs):
        applicant_obj = http.request.env['hr.applicant'].sudo()
        training_obj = http.request.env['hr.training'].sudo()
        experience_obj = http.request.env['hr.experience'].sudo()
        education_obj = http.request.env['hr.education'].sudo()

        applicant_dict = {
            'first_name_arabic': kwargs.get('first_name_arabic') or False,
            'middle_name_arabic': kwargs.get('middle_name_arabic') or False,
            'last_name_arabic': kwargs.get('last_name_arabic') or False,
            'fourth_name_arabic': kwargs.get('fourth_name_arabic') or False,
            'partner_name': kwargs.get('first_name') or False,
            'middle_name': kwargs.get('middle_name') or False,
            'last_name': kwargs.get('last_name') or False,
            'fourth_name': kwargs.get('fourth_name') or False,
            'address': kwargs.get('address') or False,
            'city_id': kwargs.get('city_id') and int(kwargs.get('city_id')) or False,
            'partner_phone': kwargs.get('partner_phone') or False,
            'email_from': kwargs.get('email_from') or False,
            'religion': kwargs.get('religion') or False,
            'gender': kwargs.get('gender') or False,
            'date_of_birth': kwargs.get('date_of_birth') or False,
            'place_of_birth': kwargs.get('place_of_birth') and int(kwargs.get('place_of_birth')) or False,
            'nationality_id': kwargs.get('nationality') and int(kwargs.get('nationality')) or False,
            'marital_status': kwargs.get('marital_status') or False,
            'military_status': kwargs.get('military_status') or False,
            'national_id': kwargs.get('national_id') or False,
            'passport_id': kwargs.get('passport_id') or False,
            'general_service_status': kwargs.get('general_service_status') or False,
            'spouse_name': kwargs.get('partner_full_name') or False,
            'spouse_national_id': kwargs.get('partner_national_id') or False,
            'spouse_academic_qualification': kwargs.get('partner_qualification') or False,
            'spouse_date_of_birth': kwargs.get('partner_birthdate') or False,
            'spouse_place_of_birth': kwargs.get('partner_place_of_birth') and int(kwargs.get('partner_place_of_birth')) or False,
            'spouse_employment': kwargs.get('partner_employment') or False,
            'spouse_employment_location': kwargs.get('partner_employment_location') or False,
            'spouse_with_children': kwargs.get('with_children') or False,
            'cv': kwargs.get('upload_cv') or False,
            'fname': kwargs.get('fname', kwargs.get('english_name')) or 'CV',
            'job_id': kwargs.get('job_id') and int(kwargs.get('job_id')) or False,
            'department_id': kwargs.get('department_id') and int(kwargs.get('department_id')) or False,
        }

        applicant = applicant_obj.create(applicant_dict)

        #Education Qualification
        for education in kwargs.get('education_data'):
            if not all(values == False for values in education.values()):
                edu_vals = {
                    'applicant_id': applicant.id,
                    'institute': education.get('institute') or False,
                    'name': education.get('name') or False,
                    'start_date': education.get('start_date') or False,
                    'end_date': education.get('end_date') or False,
                    'final_grade' : education.get('final_grade')
                }
                education_obj.create(edu_vals)


        #Training
        for training in kwargs.get('training_data'):
            if not all(values == False for values in training.values()):
                tra_vals = {
                    'applicant_id': applicant.id,
                    'institute_name': training.get('institute_name') or False,
                    'name': training.get('name') or False,
                    'start_date': training.get('start_date') or False,
                    'end_date': training.get('end_date') or False,
                }
                training_obj.create(tra_vals)

        #Experience
        for experience in kwargs.get('experience_data'):
            if not all(values == False for values in experience.values()):
                vals = {
                    'applicant_id': applicant.id,
                    'job_id': experience.get('job_id') and int(experience.get('job_id')) or False,
                    'name': experience.get('employer_name') or False,
                    'start_date': experience.get('experience_start_date') or False,
                    'end_date': experience.get('experience_end_date') or False,
                }
                experience_obj.create(vals)
        return True


class Details(http.Controller):

    @http.route('/add_details', type='json', auth='public', website=True)
    def add_details(self, detail_type=None):
        View = http.request.env['ir.ui.view'].sudo()
        if detail_type == 'tra':
            return View.render_template('sky_website_hr_recruitment_custom.training_details')
        if detail_type == 'exp':
            job_data = http.request.env['hr.job'].sudo().search([])
            job_list = [(job.id, job.name) for job in job_data]
            return View.render_template('sky_website_hr_recruitment_custom.experience_details', {'jobs': job_list})
        if detail_type == 'edu':
            return View.render_template('sky_website_hr_recruitment_custom.education_details')
