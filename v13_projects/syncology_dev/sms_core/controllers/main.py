from odoo import http
from odoo.http import request
import json
import base64
from odoo.addons.website_sale.controllers.main import WebsiteSale


# class AppointmentController(http.Controller):

#     @http.route('/sms_core/appointments', auth='user', type='json')
#     def appointment_banner(self):
#         return {
#             'html': """
#                     <div>
#                         <link>
#                         <center><h1><font color="red">Subscribe the channel.......!</font></h1></center>
#                         <center>
#                         <p><font color="blue"><a href="https://www.youtube.com/channel/UCVKlUZP7HAhdQgs-9iTJklQ/videos">
#                             Get Notified Regarding All The Odoo Updates!</a></p>
#                             </font></div></center> """
#                                 }
# 
# 
# class WebsiteSaleInherit(WebsiteSale):
# 
#     @http.route([
#         '''/shop''',
#         '''/shop/page/<int:page>''',
#         '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>''',
#         '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>/page/<int:page>'''
#     ], type='http', auth="public", website=True)
#     def shop(self, page=0, category=None, search='', ppg=False, **post):
#         res = super(WebsiteSaleInherit, self).shop(page=0, category=None, search='', ppg=False, **post)
#         print("Inherited Odoo Mates ....", res)
#         return res


class Admission(http.Controller):

    @http.route('/admission_webform', type="http", auth="public", website=True)
    def admission_webform(self, **kw):
        nationality = request.env['res.country'].sudo().search([])
        city = request.env['res.city'].sudo().search([])
        city_lst = [(ct.id, ct.name) for ct in city]
        school_data = request.env['schools.list'].sudo().search([])

        school_list = [(school.id, school.name) for school in school_data]
        school_class_data = ""
        if school_list:
            for school in school_list:
                school_class_data = request.env['school.class'].sudo().search([('school_id', '=', school[0])])
                break
        school_class_list = [(cl.id, cl.name) for cl in school_class_data]
        return http.request.render('sms_core.create_admission', {'full_name': '',
                                                                 'nationality': nationality,
                                                                 'father_nationality': nationality,
                                                                 'mother_nationality': nationality,
                                                                 'guardian_nationality': nationality,
                                                                 'application_for_id': school_list,
                                                                 'class_grade': school_class_list,
                                                                 'city': city,
                                                                 'city_lst': city_lst
                                                                 })

    @http.route(['/filter/model'], type='json', auth='public', methods=['POST'], website=True)
    def get_filter_grade(self, **kwargs):
        model_list = []
        if kwargs.get('application_for_id'):
            for grade in request.env['school.class'].sudo().search(
                    [('school_id', '=', int(kwargs.get('application_for_id')))]):
                model_list.append({
                    'grade_id': grade.id,
                    'grade_name': grade.name,
                })
        return model_list

    @http.route(['/filter/grade'], type='json', auth='public', methods=['POST'], website=True)
    def get_filter_child_grade(self, **kwargs):
        child_grade_list = []
        if kwargs.get('application_for_id'):
            for grade in request.env['school.class'].sudo().search(
                    [('school_id', '=', int(kwargs.get('application_for_id')))]):
                child_grade_list.append({
                    'grade_id': grade.id,
                    'grade_name': grade.name,
                })
        return child_grade_list

    @http.route('/create/webadmission', type="http", auth="public", website=True)
    def create_webadmission(self, **kw):
        childs = []
        reg_res = ''
        print("This is the student admission form ", kw)

        if kw.get('student_image'):
            image = kw.get('student_image').read()
            kw['student_image'] = base64.b64encode(image)
        else:
            print("student image not found")

        childs = kw['child_list']
        kw.pop("child_list")
        create_record = request.env['student.admission.form'].sudo().create(kw)
        if childs != "False":
            childs = json.loads(childs)
            childs.pop(0)
            for f in childs:
                kw.update(f)
                kw['student_image'] = ''
                print("This is the dictionary update ", f)
                create_record = request.env['student.admission.form'].sudo().create(kw)
        if "std_name" in create_record:
            reg_res = str(create_record['std_name']) + '  National ID : ' + str(
                create_record['national_id']) + '  Application Status : ' + str(create_record['status'])
            return request.render("sms_core.student_already_exists", {'student': reg_res})
        else:
            return request.render("sms_core.student_thanks", {})

    # @http.route('/patient_webform', website=True, auth='user')
    # def patient_webform(self):
    #     return request.render("sms_core.patient_webform", {})
    #
    # # Check and insert values from the form on the model <model>
    # @http.route(['/create_web_patient'], type='http', auth="public", website=True)
    # def patient_contact_create(self, **kwargs):
    #     print("ccccccccccccc")
    #     request.env['hospital.patient'].sudo().create(kwargs)
    #     return request.render("sms_core.patient_thanks", {})

    # Sample Controller Created
    @http.route('/hospital/patient/', website=True, auth='user')
    def hospital_patient(self, **kw):
        # return "Thanks for watching"
        patients = request.env['hospital.patient'].sudo().search([])
        return request.render("sms_core.patients_page", {
            'patients': patients
        })

    # Sample Controller Created
    @http.route('/update_patient', type='json', auth='user')
    def update_patient(self, **rec):
        if request.jsonrequest:
            if rec['id']:
                print("rec...", rec)
                patient = request.env['hospital.patient'].sudo().search([('id', '=', rec['id'])])
                if patient:
                    patient.sudo().write(rec)
                args = {'success': True, 'message': 'Patient Updated'}
        return args

    @http.route('/create_patient', type='json', auth='user')
    def create_patient(self, **rec):
        if request.jsonrequest:
            print("rec", rec)
            if rec['name']:
                vals = {
                    'patient_name': rec['name'],
                    'email_id': rec['email_id']
                }
                new_patient = request.env['hospital.patient'].sudo().create(vals)
                print("New Patient Is", new_patient)
                args = {'success': True, 'message': 'Success', 'id': new_patient.id}
        return args

    @http.route('/get_patients', type='json', auth='user')
    def get_patients(self):
        print("Yes here entered")
        patients_rec = request.env['hospital.patient'].search([])
        patients = []
        for rec in patients_rec:
            vals = {
                'id': rec.id,
                'name': rec.patient_name,
                'sequence': rec.name_seq,
            }
            patients.append(vals)
        print("Patient List--->", patients)
        data = {'status': 200, 'response': patients, 'message': 'Done All Patients Returned'}
        return data
