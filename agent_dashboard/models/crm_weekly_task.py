from odoo import models, fields

class CRMWeeklyTask(models.Model):
    _name = 'crm.weekly.task'
    _description = 'Weekly Task'

    name = fields.Char(string="Task Description", required=True)
    day = fields.Selection([
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ], string="Day of the Week", required=True)
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    completed = fields.Boolean(string="Completed", default=False)