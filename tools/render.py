__author__ = 'one'

from jinja2.environment import Environment as JinjaEnvironment
from jinja2.loaders import FileSystemLoader


class JinjaRender(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(JinjaRender, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, template_dirs):
        self.template_dirs = template_dirs if template_dirs else []

        self.env = JinjaEnvironment(
            extensions=['jinja2.ext.i18n'],
            loader=FileSystemLoader(self.template_dirs)
        )

    def render(self, context, template, data, **params):
        self.env.globals.update({
            'model': lambda x: context.env[x],
            'root_model': lambda x: context.env[x].sudo(),
            'partial': lambda _template, _params=None: self.render(context, _template, _params),
        })

        if 'globals' in params:
            self.env.globals.update(params['globals'])

        if 'filters' in params:
            self.env.filters.update(params['filters'])

        if 'tests' in params:
            self.env.tests.update(params['tests'])

        if 'functions' in params:
            self.env.globals.update(params['functions'])

        tmpl = self.env.get_template(template)
        return tmpl.render(data)