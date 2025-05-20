# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'



    function = fields.Char(string='Position/Occupation')#label changed
    phone = fields.Char(string='Personal Phone')#label changed
    mobile = fields.Char(string='Mobile')#label changed
    work_phone = fields.Char(string='Work Phone')
    email = fields.Char(string='Personal Email') #label changed
    work_email = fields.Char(string='Work email')
    # additional info
    about = fields.Text(string='About')
    birthday = fields.Date(string='Birthday')
    home_anniversary = fields.Date(string='Home Anniversary')
    favorite_drink = fields.Char(string='Favorite Drink')
    favorite_restaurant = fields.Char(string='Favorite Restaurant')
    hobbies = fields.Text(string='Hobbies')
    # social media
    facebook_url = fields.Char(string='Facebook')
    google_plus_url = fields.Char(
        string='Google+')  # Note: Google+ is discontinued
    houzz_url = fields.Char(string='Houzz')
    instagram_url = fields.Char(string='Instagram')
    linkedin_url = fields.Char(string='LinkedIn')
    pinterest_url = fields.Char(string='Pinterest')
    twitter_url = fields.Char(string='Twitter')