import logging
import os

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

import lizard_ui.views

from flooding_lib import excel_import_export
from flooding_lib import forms
from flooding_lib import permission_manager
from flooding_lib import scenario_sharing
from flooding_lib.sharedproject import models
from flooding_lib.util import viewutil
import flooding_lib.models

logger = logging.getLogger(__name__)


def excel_dir(project):
    return os.path.join(
        settings.BUILDOUT_DIR, 'var', 'excel', 'shared', project.name.lower())


def scenario_list(project, province):
    return (
        scenario for scenario in
        flooding_lib.models.Scenario.objects.filter(
            scenarioproject__project=project)
        if (province.in_province(scenario)))


class ParameterMixin(object):
    def dispatch(self, request, *args, **kwargs):
        for key, value in kwargs.items():
            logger.debug('setattr key={0} value={1}'.format(key, value))
            setattr(self, key, value)
        return super(ParameterMixin, self).dispatch(request, *args)


class View(
    lizard_ui.views.ViewContextMixin, ParameterMixin, TemplateView):
    pass


class Dashboard(View):
    template_name = 'sharedproject/dashboard.html'

    project_name = None
    province_id = None

    def dispatch(self, request, *args, **kwargs):
        self.form = forms.ExcelImportForm()

        self.permission_manager = permission_manager.get_permission_manager(
            request.user)
        if not self.permission_manager.check_project_permission(
            self.project,
            flooding_lib.models.UserPermission.PERMISSION_SCENARIO_APPROVE):
            raise PermissionDenied()

        return super(Dashboard, self).dispatch(request, *args, **kwargs)

    @property
    def project(self):
        if not hasattr(self, '_project'):
            if self.project_name == 'ror':
                setattr(
                    self, '_project',
                    flooding_lib.models.Project.objects.get(
                        pk=scenario_sharing.PROJECT_ROR))
        return self._project

    @property
    def province(self):
        if not self.province_id:
            return None

        logger.debug('1, self.province_id={0}'.format(self.province_id))
        if not hasattr(self, '_province'):
            self._province = models.Province.objects.get(
                pk=int(self.province_id))
        logger.debug('2')

        return getattr(self, '_province')

    def provinces(self):
        return models.Province.objects.all()

    def provinces_with_stats(self):
        return [
            (province, province.scenario_stats(self.project, self.scenarios()))
            for province in self.provinces()
            ]

    def scenarios(self):
        if not hasattr(self, '_scenarios'):
            scenarios = flooding_lib.models.Scenario.objects.filter(
                scenarioproject__project=self.project)

            return (scenario for scenario in scenarios
                    if (
                    not self.province or self.province.in_province(scenario))
)
        return self._scenarios


@permission_manager.receives_permission_manager
def excel(request, permission_manager, project_name, province_id):
    if project_name != 'ror':
        raise PermissionDenied()

    project = flooding_lib.models.Project.objects.get(
        pk=scenario_sharing.PROJECT_ROR)

    if not permission_manager.check_project_permission(
        project,
        flooding_lib.models.UserPermission.PERMISSION_SCENARIO_APPROVE):
        raise PermissionDenied()

    province = get_object_or_404(models.Province, pk=province_id)

    if request.method == 'GET':
        return get_excel(request, project, province)
    if request.method == 'POST':
        return post_excel(request, project, province)

    raise PermissionDenied()


def get_excel(request, project, province):
    directory = excel_dir(project)

    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = "{0}.xls".format(province.name)

    scenarios = scenario_list(project, province)

    excel_import_export.create_excel_file(
        project, scenarios, os.path.join(directory, filename),
        include_approval=True)

    return viewutil.serve_file(
        request=request,
        dirname=directory,
        filename=filename,
        nginx_dirname='/download_excel_shared')


def post_excel(request, project, province):
    form = forms.ExcelImportForm(request.POST, request.FILES)

    errors = []

    if form.is_valid():
        filename = request.FILES['excel_file'].name
        if not filename.startswith(province.name):
            errors += [
                'Filename begint niet met de naam van de provincie. '
                'Verkeerde file?']
        else:
            dest_path = os.path.join('/tmp', filename)
            with open(dest_path, 'wb') as dest:
                for chunk in request.FILES['excel_file'].chunks():
                    dest.write(chunk)

            allowed_scenario_ids = [scenario.id for scenario in
                                    scenario_list(project, province)]

            errors = (excel_import_export.
                      import_upload_excel_file_for_approval(
                    project, request.user.username,
                    dest_path, allowed_scenario_ids))

            if not errors:
                return HttpResponseRedirect(
                    reverse(
                        'sharedproject_dashboard'))
            else:
                return HttpResponse('\n'.join(errors))