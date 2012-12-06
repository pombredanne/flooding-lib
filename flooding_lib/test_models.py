"""Tests for flooding_lib/models.py."""

from __future__ import unicode_literals

import factory
import mock

from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from flooding_lib import models
from flooding_lib import permission_manager
from flooding_lib.tools.approvaltool.models import ApprovalObjectType
from flooding_lib.tools.approvaltool.models import ApprovalRule
from flooding_lib.tools.approvaltool.models import ApprovalObjectState
from flooding_lib.tools.importtool import models as importmodels

from flooding_lib.tools.importtool.test_models import InputFieldF

MULTIPOLYGON = 'MULTIPOLYGON(((0 0,4 0,4 4,0 4,0 0),(1 1,2 1,2 2,1 2,1 1)))'
POINT = 'POINT(0 0)'


class FakeObject(object):
    """Object with some attributes"""
    def __init__(self, **kwargs):
        for attribute, value in kwargs.iteritems():
            setattr(self, attribute, value)


class UnicodeTester(object):
    """Mixin for testing __unicode__."""
    def assert_has_unicode(self, ob):
        """Assert that ob's __unicode__ returns a non-empty unicode
        string."""
        uni = ob.__unicode__()
        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))

## Model factories


class ContentTypeF(factory.Factory):
    FACTORY_FOR = ContentType


class AttachmentF(factory.Factory):
    FACTORY_FOR = models.Attachment

    content_type = ContentTypeF.create()
    object_id = 1


class SobekVersionF(factory.Factory):
    FACTORY_FOR = models.SobekVersion


class SobekModelF(factory.Factory):
    FACTORY_FOR = models.SobekModel

    sobekversion = SobekVersionF.create()
    sobekmodeltype = 1
    model_case = 0
    model_srid = 28992


class CutoffLocationF(factory.Factory):
    FACTORY_FOR = models.CutoffLocation

    name = "some cutoff location"
    bottomlevel = 0.0
    width = 1.0
    type = 1  # sluis (_('lock'))
    geom = POINT


class DikeF(factory.Factory):
    FACTORY_FOR = models.Dike


class ExtraInfoFieldF(factory.Factory):
    FACTORY_FOR = models.ExtraInfoField

    name = 'dummy'
    use_in_scenario_overview = True
    header = models.ExtraInfoField.HEADER_SCENARIO
    position = 0


class ScenarioF(factory.Factory):
    FACTORY_FOR = models.Scenario

    owner = User.objects.get_or_create(username='remco')[0]
    tsim = 0.0


class ExtraScenarioInfoF(factory.Factory):
    FACTORY_FOR = models.ExtraScenarioInfo

    extrainfofield = ExtraInfoFieldF(name='forextrascenarioinfo')
    scenario = ScenarioF.build()
    value = None


class ScenarioProjectF(factory.Factory):
    FACTORY_FOR = models.ScenarioProject

    scenario = factory.LazyAttribute(lambda obj: ScenarioF.create())
    project = factory.LazyAttribute(lambda obj: ProjectF.create())
    is_main_project = True


class ProjectF(factory.Factory):
    FACTORY_FOR = models.Project

    owner = User.objects.get_or_create(username='remco')[0]
    friendlyname = "friendly name of ProjectF"


class UserPermissionF(factory.Factory):
    """Factory for UserPermission."""
    FACTORY_FOR = models.UserPermission

    user = User.objects.get_or_create(username='remco')[0]
    permission = models.UserPermission.PERMISSION_SCENARIO_VIEW


class ProjectGroupPermissionF(factory.Factory):
    """Factory for ProjectGroupPermission."""
    FACTORY_FOR = models.ProjectGroupPermission

    group = Group.objects.get_or_create(name="some group")[0]
    project = ProjectF.build()

    permission = models.UserPermission.PERMISSION_SCENARIO_VIEW


class ExternalWaterF(factory.Factory):
    FACTORY_FOR = models.ExternalWater

    name = 'dewoeligebaren'
    type = models.ExternalWater.TYPE_SEA

    deftsim = 0.0


class RegionF(factory.Factory):
    FACTORY_FOR = models.Region

    name = 'Utrecht'
    longname = 'Uuuuuuutrecht'
    geom = MULTIPOLYGON


class RegionSetF(factory.Factory):
    FACTORY_FOR = models.RegionSet

    name = "testregionset"


class DikeF(factory.Factory):
    FACTORY_FOR = models.Dike

    name = "Een dijk"


class BreachF(factory.Factory):
    FACTORY_FOR = models.Breach

    name = 'testname'

    externalwater = factory.LazyAttribute(lambda obj: ExternalWaterF.create())
    region = factory.LazyAttribute(lambda obj: RegionF.create())
    dike = factory.LazyAttribute(lambda obj: DikeF.create())
    defaulttide = factory.LazyAttribute(lambda obj: WaterlevelSetF.create())

    levelnormfrequency = 1
    groundlevel = 1
    defrucritical = 0
    internalnode = 'POINT(0 0)'
    externalnode = 'POINT(0 0)'

    geom = 'POINT(0 0)'


class BreachSobekModelF(factory.Factory):
    """Factory for BreachSobekModel."""
    FACTORY_FOR = models.BreachSobekModel

    sobekid = "some sobek id"


class CutoffLocationSetF(factory.Factory):
    """Factory for CutoffLocationSet."""
    FACTORY_FOR = models.CutoffLocationSet

    name = "some cutofflocationset"


class WaterlevelSetF(factory.Factory):
    FACTORY_FOR = models.WaterlevelSet

    type = models.WaterlevelSet.WATERLEVELSETTYPE_UNDEFINED


class ScenarioBreachF(factory.Factory):
    FACTORY_FOR = models.ScenarioBreach

    scenario = factory.LazyAttribute(lambda obj: ScenarioF.create())
    breach = factory.LazyAttribute(lambda obj: BreachF.create())
    waterlevelset = factory.LazyAttribute(lambda obj: WaterlevelSetF.create())

    widthbrinit = 1
    methstartbreach = 1
    tstartbreach = 1
    hstartbreach = 1
    brdischcoef = 1
    brf1 = 1
    brf2 = 1
    bottomlevelbreach = 1
    ucritical = 1
    pitdepth = 1
    tmaxdepth = 1
    extwmaxlevel = 1


class ScenarioCutoffLocationF(factory.Factory):
    """Factory for ScenarioCutoffLocation."""
    FACTORY_FOR = models.ScenarioCutoffLocation

    scenario = factory.LazyAttribute(lambda obj: ScenarioF.create())
    cutofflocation = factory.LazyAttribute(
        lambda obj: CutoffLocationF.create())


class ProgramF(factory.Factory):
    """Factory for Program."""
    FACTORY_FOR = models.Program

    name = "some program"


class ResultTypeF(factory.Factory):
    """Factory for ResultType."""
    FACTORY_FOR = models.ResultType

    name = "result type name"


class CutoffLocationSobekModelSettingF(factory.Factory):
    """Factory for CutoffLocationSobekModelSetting."""
    FACTORY_FOR = models.CutoffLocationSobekModelSetting

    cutofflocation = factory.LazyAttribute(
        lambda obj: CutoffLocationF.create())
    sobekmodel = factory.LazyAttribute(
        lambda obj: SobekModelF.create())

    sobekid = "some sobekid"


class TaskTypeF(factory.Factory):
    """Factory for TaskType."""
    FACTORY_FOR = models.TaskType

    id = 150
    name = "PNG creation"


class TaskF(factory.Factory):
    """Factory for Task."""
    FACTORY_FOR = models.Task

    scenario = factory.LazyAttribute(lambda obj: ScenarioF.create())
    remarks = ''
    tasktype = factory.LazyAttribute(lambda obj: TaskTypeF.create())

    creatorlog = "test"


class WaterlevelF(factory.Factory):
    FACTORY_FOR = models.Waterlevel

    time = 0
    value = 0


class MapF(factory.Factory):
    FACTORY_FOR = models.Map

    name = "testmap"


class TaskExecutorF(factory.Factory):
    FACTORY_FOR = models.TaskExecutor

    name = "testtaskexecutor"


class ResultTypePresentationTypeF(factory.Factory):
    FACTORY_FOR = models.ResultType_PresentationType

    remarks = "testremarks"


class StrategyF(factory.Factory):
    FACTORY_FOR = models.Strategy

    name = "teststrategy"


class MeasureF(factory.Factory):
    FACTORY_FOR = models.Measure

    name = "testmeasure"


class EmbankmentUnitF(factory.Factory):
    FACTORY_FOR = models.EmbankmentUnit

    unit_id = "test"

## Test cases


class TestHelperFunctions(TestCase):
    def testColorToHex_CorrectInput(self):
        self.assertEquals(
            "#00FF00",
            models.convert_color_to_hex((0, 255, 0)))

    def testAttachmentPath_CorrectInput(self):
        instance = FakeObject(
            content_type=u'test_content_type',
            object_id=1234)

        self.assertEquals(
            'attachments/test_content_type/1234/filename.zip',
            models.get_attachment_path(instance, 'filename.zip'))


class TestAttachment(UnicodeTester, TestCase):
    def testFilename(self):
        path = 'some/path/with/several.periods.txt'
        filename = 'several.periods.txt'

        attachment = AttachmentF()
        attachment.file = FakeObject(name=path)

        self.assertEquals(
            attachment.filename, filename)

    def test_has_unicode(self):
        """Check that with __unicode__ returns is in fact unicode."""
        self.assert_has_unicode(AttachmentF(name=u"some name"))


class TestSobekVersion(UnicodeTester, TestCase):
    def test_has_unicode(self):
        """Check that with __unicode__ returns is in fact unicode."""
        self.assert_has_unicode(SobekVersionF(name=u"some name"))


class TestSobekModel(UnicodeTester, TestCase):
    """Tests for SobekModel."""
    def test_has_unicode(self):
        """Check that with __unicode__ returns is in fact unicode."""
        self.assert_has_unicode(SobekModelF())

    def test_get_summary_str(self):
        """Check that it returns something and is Unicode"""
        sobekmodel = SobekModelF()
        summary = sobekmodel.get_summary_str()
        self.assertEquals(type(summary), unicode)
        self.assertTrue(summary)


class TestCutoffLocation(UnicodeTester, TestCase):
    """Tests for CutoffLocation."""
    def test_has_unicode(self):
        """Check that with __unicode__ returns is in fact unicode."""
        self.assert_has_unicode(CutoffLocationF())

    def test_isinternal(self):
        """Returns if CutoffLocation is an internal cutoff location

        True if it is exclusively connected to region's,
        False if it is exclusively connected to external waters
        None else
        """
        cutofflocation = CutoffLocationF()
        # Should be None because we didn't connect it at all
        self.assertEquals(cutofflocation.isinternal(), None)

    def test_isinternal_connected_to_region(self):
        cutofflocation = CutoffLocationF.create()
        cutofflocation.region_set.add(RegionF.create())

        self.assertEquals(cutofflocation.isinternal(), True)

    def test_isinternal_connected_to_externalwater(self):
        cutofflocation = CutoffLocationF.create()
        cutofflocation.externalwater_set.add(ExternalWaterF.create())

        self.assertEquals(cutofflocation.isinternal(), False)

    def test_isinternal_connected_to_both(self):
        cutofflocation = CutoffLocationF.create()
        cutofflocation.region_set.add(RegionF.create())
        cutofflocation.externalwater_set.add(ExternalWaterF.create())

        self.assertEquals(cutofflocation.isinternal(), None)

    def test_getdeftclose_seconds(self):
        cutofflocation = CutoffLocationF.build(deftclose=1)
        self.assertEquals(cutofflocation.get_deftclose_seconds(), 86400)


class TestExternalWater(TestCase):
    def test_has_unicode(self):
        externalwater = ExternalWaterF.build()
        self.assertEquals(type(externalwater.__unicode__()), unicode)


class TestDike(TestCase):
    def test_has_unicode(self):
        dike = DikeF.build()
        self.assertEquals(type(dike.__unicode__()), unicode)


class TestWaterlevelSet(TestCase):
    def test_has_unicode(self):
        waterlevelset = WaterlevelSetF.build()
        self.assertEquals(type(waterlevelset.__unicode__()), unicode)


class TestWaterlevel(TestCase):
    def test_has_unicode(self):
        waterlevel = WaterlevelF.build(
            waterlevelset=WaterlevelSetF.create())

        self.assertEquals(type(waterlevel.__unicode__()), unicode)


class TestRegion(TestCase):
    def test_unicode_with_long_name(self):
        region = RegionF.build(longname="whee")

        uni = region.__unicode__()

        self.assertEquals(uni, "whee")
        self.assertTrue(isinstance(uni, unicode))

    def test_unicode_without_long_name(self):
        region = RegionF.build(
            longname=None, name="whe")

        uni = region.__unicode__()

        self.assertEquals(uni, "whe")
        self.assertTrue(isinstance(uni, unicode))


class TestRegionSet(TestCase):
    def test_has_unicode(self):
        regionset = RegionSetF.build()
        uni = regionset.__unicode__()
        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))

    def test_get_all_regions_empty(self):
        regionset = RegionSetF.create()

        self.assertEquals(len(regionset.get_all_regions()), 0)

    def test_get_all_regions_returns_own_regions(self):
        region = RegionF.create()
        regionset = RegionSetF.create()
        regionset.regions.add(region)

        all_regions = regionset.get_all_regions(filter_active=None)
        self.assertEquals(len(all_regions), 1)
        self.assertTrue(region in all_regions)

    def test_get_all_regions_returns_descendants_regions(self):
        region = RegionF.create()
        regionsetparent = RegionSetF.create()
        regionsetchild = RegionSetF.create(parent=regionsetparent)
        regionsetchild.regions.add(region)

        all_regions = regionsetparent.get_all_regions(filter_active=None)
        self.assertEquals(len(all_regions), 1)
        self.assertTrue(region in all_regions)

    def test_get_all_regions_returns_descendants_regions2(self):
        region = RegionF.create()
        regionsetparent = RegionSetF.create()
        regionsetchild = RegionSetF.create(parent=regionsetparent)
        regionsetgrandchild = RegionSetF.create(parent=regionsetchild)
        regionsetgrandchild.regions.add(region)

        all_regions = regionsetparent.get_all_regions(filter_active=None)
        self.assertEquals(len(all_regions), 1)
        self.assertTrue(region in all_regions)

    def test_get_all_regions_returns_region_only_once(self):
        region = RegionF.create()

        regionsetparent = RegionSetF.create()
        regionsetparent.regions.add(region)
        regionsetchild1 = RegionSetF.create(parent=regionsetparent)
        regionsetchild1.regions.add(region)
        regionsetchild2 = RegionSetF.create(parent=regionsetparent)
        regionsetchild2.regions.add(region)

        all_regions = regionsetparent.get_all_regions(filter_active=None)
        self.assertTrue(len(all_regions), 1)

    def test_get_all_regions_filter_active_works(self):
        regionset = RegionSetF.create()
        regionset.regions.add(RegionF.create(active=True))
        regionset.regions.add(RegionF.create(active=False))

        regions = regionset.get_all_regions(filter_active=False)
        self.assertEquals(len(regions), 1)
        self.assertFalse(regions[0].active)

    def test_get_all_regions_sorting_works(self):
        regionset = RegionSetF.create()
        regionset.regions.add(RegionF.create(name='B'))
        regionset.regions.add(RegionF.create(name='A'))
        regionset.regions.add(RegionF.create(name='C'))

        regions = regionset.get_all_regions(filter_active=None)
        self.assertEquals(len(regions), 3)
        self.assertEquals(regions[0].name, 'A')
        self.assertEquals(regions[1].name, 'B')
        self.assertEquals(regions[2].name, 'C')


class TestBreach(TestCase):
    """Tests for Breach model."""
    def test_has_unicode(self):
        """Does the __unicode__ method return unicode."""
        breach = BreachF.build()
        uni = breach.__unicode__()
        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestBreachSobekModel(TestCase):
    """Tests for BreachSobekModel."""
    def test_has_unicode(self):
        """Test whether it returns unicode."""
        sobekmodel = SobekModelF.create()
        breach = BreachF.create()

        bsm = BreachSobekModelF.create(
            sobekmodel=sobekmodel, breach=breach)

        uni = bsm.__unicode__()
        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestMap(TestCase):
    """Tests for Map."""
    def test_has_unicode(self):
        """Test whether it returns unicode."""
        amap = MapF.build()
        uni = amap.__unicode__()
        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestCutoffLocationSet(TestCase):
    """Tests for CutoffLocationSet."""
    def test_has_unicode(self):
        """Test whether it returns unicode."""
        cls = CutoffLocationSetF.build()
        uni = cls.__unicode__()
        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestScenario(TestCase):
    """Tests for Scenario."""
    def setUp(self):
        self.aot = ApprovalObjectType.objects.create(
            type=ApprovalObjectType.TYPE_PROJECT)
        self.rule = ApprovalRule.objects.create(
            name="test_rule",
            description="test",
            position=0)
        self.aot.approvalrule.add(self.rule)

    def testMainProject(self):
        """Use set_project to set a scenario's main project, then use the
        main_project property to see that it is returned correctly."""

        scenario = ScenarioF.create()
        project = ProjectF.create()

        scenario.set_project(project)
        self.assertEquals(project.pk, scenario.main_project.pk)

    def testGetMainProject(self):
        """A scenario may have more than one project associated with
        it. If it has, scenario.main_project should be the first of
        them."""

        scenario = ScenarioF.create()
        project1 = ProjectF.create()
        project2 = ProjectF.create()

        scenario.set_project(project1)
        project2.add_scenario(scenario)
        scenario.save()

        main_project = scenario.main_project
        self.assertEquals(main_project.pk, project1.pk)

    def testSettingProjectTwiceRaisesValueError(self):
        scenario = ScenarioF.create()
        project1 = ProjectF.create()
        project2 = ProjectF.create()

        scenario.set_project(project1)
        self.assertRaises(
            ValueError, lambda: scenario.set_project(project2))

    def testAllProjects(self):
        scenario = ScenarioF.create()
        project1 = ProjectF.create()
        project2 = ProjectF.create()
        scenario.set_project(project1)
        project2.add_scenario(scenario)

        projects = scenario.all_projects()
        self.assertEqual(len(projects), 2)

        ids = set(project.id for project in projects)
        self.assertEqual(len(ids), 2)
        self.assertTrue(project1.id in ids)
        self.assertTrue(project2.id in ids)

    def test_in_project_list(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        scenarios = models.Scenario.in_project_list(
            models.Project.objects.all())
        self.assertEquals(scenarios.count(), 1)
        self.assertEquals(scenario.id, scenarios[0].id)

    def test_update_status_new_scenario(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        scenario.update_status()
        self.assertEquals(scenario.status_cache, models.Scenario.STATUS_NONE)

    def test_main_approval_object_always_same(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        # There was a bug because they weren't saved
        ao1 = scenario.main_approval_object()
        ao2 = scenario.main_approval_object()

        self.assertEquals(ao1, ao2)

    def test_update_status_scenario_one_task(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        tasktype = models.TaskType.objects.create(
            name='calculate sobek',
            id=models.TaskType.TYPE_SCENARIO_CREATE)

        models.Task.create_fake(
            scenario=scenario,
            task_type=tasktype.id,
            remarks="test",
            creatorlog="test")

        scenario.update_status()
        self.assertEquals(
            scenario.status_cache, models.Scenario.STATUS_WAITING)

    def test_update_scenario_disapprove(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        tasktype = models.TaskType.objects.create(
            name='calculate sobek',
            id=models.TaskType.TYPE_SCENARIO_CREATE)

        models.Task.create_fake(
            scenario=scenario,
            task_type=tasktype.id,
            remarks="test",
            creatorlog="test")

        approvalobject = scenario.main_approval_object()
        aos = ApprovalObjectState.objects.get(
            approvalobject=approvalobject,
            approvalrule=self.rule)
        aos.successful = False
        aos.save()

        scenario.update_status()

        self.assertEquals(
            scenario.status_cache, models.Scenario.STATUS_DISAPPROVED)

    def test_update_scenario_approve(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        tasktype = models.TaskType.objects.create(
            name='calculate sobek',
            id=models.TaskType.TYPE_SCENARIO_CREATE)

        models.Task.create_fake(
            scenario=scenario,
            task_type=tasktype.id,
            remarks="test",
            creatorlog="test")

        approvalobject = scenario.main_approval_object()
        aos = ApprovalObjectState.objects.get(
            approvalobject=approvalobject,
            approvalrule=self.rule)
        aos.successful = True
        aos.save()

        scenario.update_status()

        self.assertEquals(
            scenario.status_cache, models.Scenario.STATUS_APPROVED)

    def test_update_scenario_deleted(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        tasktype = models.TaskType.objects.create(
            name='calculate sobek',
            id=models.TaskType.TYPE_SCENARIO_DELETE)

        models.Task.create_fake(
            scenario=scenario,
            task_type=tasktype.id,
            remarks="test",
            creatorlog="test")

        # Approve or disapprove shouldn't matter, we test approved
        approvalobject = scenario.main_approval_object()
        aos = ApprovalObjectState.objects.get(
            approvalobject=approvalobject,
            approvalrule=self.rule)
        aos.successful = True
        aos.save()

        scenario.update_status()

        self.assertEquals(
            scenario.status_cache, models.Scenario.STATUS_DELETED)

    def test_set_value_raises_not_implemented(self):
        """The function supports only a few destination tables, should
        raise NotImplementedError if another table is asked for."""
        scenario = ScenarioF.build()
        inputfield = InputFieldF.build(
            destination_table="Project")

        self.assertRaises(
            NotImplementedError,
            lambda: scenario.set_value_for_inputfield(inputfield, None))

    def test_set_value_for_inputfield_on_scenario_sets_value(self):
        """See if a value is really set."""
        scenario = ScenarioF.create()

        inputfield = InputFieldF.build(
            destination_table='Scenario',
            destination_field='name',
            type=importmodels.InputField.TYPE_STRING)

        value_object = inputfield.build_value_object()
        value_object.set("new name")

        scenario.set_value_for_inputfield(inputfield, value_object)

        # Was it saved?
        scenario = models.Scenario.objects.get(pk=scenario.id)

        self.assertEquals(scenario.name, "new name")

    def test_set_value_for_inputfield_sets_scenariobreach_value(self):
        """See if an inputfield using ScenarioBreach is set."""
        scenario = ScenarioF.create()
        ScenarioBreachF.create(scenario=scenario)

        inputfield = InputFieldF.build(
            destination_table='ScenarioBreach',
            destination_field='widthbrinit',
            type=importmodels.InputField.TYPE_FLOAT)

        value_object = inputfield.build_value_object()
        value_object.set(0.5)

        scenario.set_value_for_inputfield(inputfield, value_object)

        # Was it saved?
        if hasattr(scenario, '_data_objects'):
            del scenario._data_objects

        scenariobreach = scenario.gather_data_objects()['scenariobreach']
        self.assertEquals(scenariobreach.widthbrinit, 0.5)

    def test_set_value_for_inputfield_sets_extrascenarioinfo(self):
        """See if an inputfield using ExtraScenarioInfo is set."""
        scenario = ScenarioF.create()
        ExtraInfoFieldF.create(name="test")
        inputfield = InputFieldF.build(
            destination_table='ExtraScenarioInfo',
            destination_field='test',
            type=importmodels.InputField.TYPE_FLOAT)

        value_object = inputfield.build_value_object()
        value_object.set(0.5)

        scenario.set_value_for_inputfield(inputfield, value_object)

        # Was it saved?
        esi = models.ExtraScenarioInfo.get(scenario, 'test')
        self.assertEquals(esi.value, u'0.5')

    def test_has_all_required_metadata(self):
        scenario = ScenarioF.create()
        scenariobreach = ScenarioBreachF.create(
            scenario=scenario,
            extwbaselevel=None)

        if1 = InputFieldF.build(
            destination_table='Scenario',
            destination_field='whee',
            required=True)
        if2 = InputFieldF.build(
            destination_table='ScenarioBreach',
            destination_field='extwbaselevel',
            required=True)

        self.assertFalse(scenario.has_values_for((if1,)))
        scenario.whee = "something"
        self.assertTrue(scenario.has_values_for((if1,)))
        self.assertFalse(scenario.has_values_for((if1, if2)))

        scenariobreach.extwbaselevel = 3.0
        scenariobreach.save()

        del scenario._data_objects  # Clear cache

        self.assertTrue(scenario.has_values_for((if1, if2)))

    def test_visible_in_project_other_permission(self):
        """Always returns true if permission isn't scenario_view."""
        scenario = ScenarioF.build()

        self.assertTrue(scenario.visible_in_project(
                None, None,
                permission=models.UserPermission.PERMISSION_SCENARIO_APPROVE))

    def test_visible_in_project_user_can_approve(self):
        """If the user has approval rights, he can see the scenario."""
        scenario = ScenarioF.create()
        project = ProjectF.create()
        group = Group.objects.create()
        user = User.objects.create()

        scenario.set_project(project)
        user.groups.add(group)
        user.userpermission_set.add(
            models.UserPermission(
                permission=models.UserPermission.PERMISSION_SCENARIO_APPROVE,
                user=user))
        group.projectgrouppermission_set.add(
            models.ProjectGroupPermission(
                group=group, project=project,
                permission=models.UserPermission.PERMISSION_SCENARIO_APPROVE))

        pm = permission_manager.get_permission_manager(user)

        self.assertTrue(scenario.visible_in_project(pm, project))

    def test_visible_in_project_false_if_not_approved(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        pm = permission_manager.AnonymousPermissionManager()

        self.assertFalse(scenario.visible_in_project(pm, project))

    def test_visible_in_project_true_if_approved(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        scenarioproject = scenario.scenarioproject(project)
        scenarioproject.approved = True
        scenarioproject.save()

        pm = permission_manager.AnonymousPermissionManager()

        self.assertTrue(scenario.visible_in_project(pm, project))

    def test_is_3di(self):
        # If the sobekmodel is 3di then the scenario is
        sobekversion = SobekVersionF.create(
            name="3di", fileloc_startfile="")
        sobekmodel = SobekModelF.create(
            sobekversion=sobekversion)
        scenario = ScenarioF.create(sobekmodel_inundation=sobekmodel)

        self.assertTrue(scenario.is_3di())


class TestScenarioProject(TestCase):
    def test_approved(self):
        sp = ScenarioProjectF.build()
        self.assertTrue(sp.approved is None)

        ao = mock.MagicMock()
        ao.approved = True

        sp.update_approved_status(ao)
        self.assertTrue(sp.approved)

    def test_disapproved(self):
        sp = ScenarioProjectF.build()
        self.assertTrue(sp.approved is None)

        ao = mock.MagicMock()
        ao.approved = False
        ao.disapproved = True

        sp.update_approved_status(ao)
        self.assertTrue(sp.approved is False)

    def test_neither(self):
        sp = ScenarioProjectF.build()
        self.assertTrue(sp.approved is None)

        ao = mock.MagicMock()
        ao.approved = False
        ao.disapproved = False

        sp.update_approved_status(ao)
        self.assertTrue(sp.approved is None)


class TestProject(TestCase):
    def setUp(self):
        ApprovalObjectType.objects.create(
            type=ApprovalObjectType.TYPE_PROJECT)

    def testAddScenarioValueErrorIfScenarioHasNoMainProject(self):
        """You can't add a scenario to another project if it doesn't have a
        main project yet."""
        scenario = ScenarioF.create()
        project = ProjectF.create()

        self.assertRaises(ValueError, lambda: project.add_scenario(scenario))

    def testAddScenarioValueErrorIfAddedToMainProject(self):
        """You can't add a scenario to a project if that project is already
        the scenario's main project."""

        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        self.assertRaises(ValueError, lambda: project.add_scenario(scenario))

    def testSetProject(self):
        """Set a scenario, see that count_scenarios returns 1."""
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        self.assertEquals(project.count_scenarios(), 1)

    def testAddScenario(self):
        """Add a scenario, see that count_scenarios returns 1."""
        scenario = ScenarioF.create()
        project1 = ProjectF.create()
        project2 = ProjectF.create()
        scenario.set_project(project1)
        project2.add_scenario(scenario)

        self.assertEquals(project2.count_scenarios(), 1)

    def test_in_scenario_list(self):
        scenario = ScenarioF.create()
        project = ProjectF.create()
        scenario.set_project(project)

        projects = models.Project.in_scenario_list(
            models.Scenario.objects.all())

        self.assertEquals(projects.count(), 1)
        self.assertEquals(project.id, projects[0].id)

    def test_all_scenarios(self):
        scenario1 = ScenarioF.create()
        scenario2 = ScenarioF.create()
        project = ProjectF.create()
        scenario1.set_project(project)
        scenario2.set_project(project)

        scenarios = project.all_scenarios()
        self.assertEquals(scenarios.count(), 2)

        # We don't test anything about order, that's not specified
        scenarioset = set(scenario.id for scenario in scenarios)
        self.assertTrue(scenario1.id in scenarioset)
        self.assertTrue(scenario2.id in scenarioset)

    def test_original_scenarios(self):
        # Three scenarios; two are originally in project1,
        # the other is originally in project2 and was added to project1.
        # Function should return the first two.
        scenario1 = ScenarioF.create()
        scenario2 = ScenarioF.create()
        scenario3 = ScenarioF.create()
        project1 = ProjectF.create()
        project2 = ProjectF.create()

        scenario1.set_project(project1)
        scenario2.set_project(project1)
        scenario3.set_project(project2)
        project1.add_scenario(scenario3)

        scenarios = project1.original_scenarios()

        self.assertEquals(scenarios.count(), 2)
        scenarioset = set(scenario.id for scenario in scenarios)
        self.assertTrue(scenario1.id in scenarioset)
        self.assertTrue(scenario2.id in scenarioset)

    def test_original_scenarios_deleted(self):
        """original_scenarios() shouldn't return deleted scenarios."""
        scenario = ScenarioF.create(
            status_cache=models.Scenario.STATUS_DELETED)
        project = ProjectF.create()
        scenario.set_project(project)

        scenarios = project.original_scenarios()

        self.assertEquals(scenarios.count(), 0)

    def test_has_unicode(self):
        """Test whether it returns unicode."""
        project = ProjectF.build()
        uni = project.__unicode__()
        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))

    def test_absolute_url_works(self):
        project = ProjectF.create()
        self.assertTrue(project.get_absolute_url())

    def test_excel_filename_contains_id(self):
        project = ProjectF.build()
        project.id = 66
        self.assertTrue('66' in project.excel_filename())

    def test_excel_file_strips_strange_characters(self):
        project = ProjectF.build(
            name="clearly/illegal/<filename>")
        project.id = 66
        excel_filename = project.excel_filename()
        self.assertEquals("66 clearlyillegalfilename.xls", excel_filename)


class TestScenarioBreach(UnicodeTester, TestCase):
    """Tests for ScenarioBreach."""
    def test_has_unicode(self):
        """Test whether it returns unicode."""
        scenariobreach = ScenarioBreachF.build()
        self.assert_has_unicode(scenariobreach)


class TestScenarioCutoffLocation(UnicodeTester, TestCase):
    """Tests for ScenarioCutoffLocation."""
    def test_has_unicode(self):
        """Test whether it has unicode."""
        scl = ScenarioCutoffLocationF.build()
        self.assert_has_unicode(scl)


class TestProgram(UnicodeTester, TestCase):
    """Tests for Program."""
    def test_has_unicode(self):
        """Test whether it has unicode."""
        program = ProgramF.build()
        self.assert_has_unicode(program)


class TestResultType(UnicodeTester, TestCase):
    """Tests for ResultType."""
    def test_has_unicode(self):
        """Test whether it has unicode."""
        resulttype = ResultTypeF.build()
        self.assert_has_unicode(resulttype)


class TestCutoffLocationSobekModelSetting(UnicodeTester, TestCase):
    """Tests for CutoffLocationSobekModelSetting."""
    def test_has_unicode(self):
        """Test whether it has unicode."""
        clsms = CutoffLocationSobekModelSettingF.build()
        self.assert_has_unicode(clsms)


class TestTaskType(UnicodeTester, TestCase):
    """Tests for TaskType."""
    def test_has_unicode(self):
        """Test whether it has unicode."""
        tasktype = TaskTypeF.build()
        self.assert_has_unicode(tasktype)


class TestTask(UnicodeTester, TestCase):
    """Tests for Task."""
    def test_has_unicode(self):
        """Test whether it has unicode."""
        task = TaskF.build()
        self.assert_has_unicode(task)


class TestUserPermission(TestCase):
    """Tests for UserPermission."""
    def test_has_unicode(self):
        userpermission = UserPermissionF.build()
        uni = userpermission.__unicode__()
        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestProjectGroupPermission(UnicodeTester, TestCase):
    """Tests for ProjectGroupPermission."""
    def test_has_unicode(self):
        """Check if __unicode__ is valid."""
        self.assert_has_unicode(ProjectGroupPermissionF.build())


class TestExtraInfoField(UnicodeTester, TestCase):
    """Tests for ExtraInfoField."""
    def test_has_unicode(self):
        """Check if __unicode__ is valid."""
        self.assert_has_unicode(ExtraInfoFieldF.build())


class TestExtraScenarioInfo(UnicodeTester, TestCase):
    """Tests for ExtraScenarioInfo."""
    def test_has_unicode(self):
        """Check if __unicode__ is valid."""
        self.assert_has_unicode(ExtraScenarioInfoF.build())


class TestFindImportedValue(TestCase):
    def test_get_integer_from_scenario(self):
        scenario = FakeObject(field=3)

        inputfield = InputFieldF.build(
            destination_table='Scenario',
            destination_field='field')

        retvalue = models.find_imported_value(
            inputfield, {'scenario': scenario})
        self.assertEquals(retvalue, 3)

    def test_simple_scenario_info(self):
        scenario = ScenarioF.create()
        fieldname = 'test'
        value = 3

        extrainfofield = ExtraInfoFieldF.create(name=fieldname)
        ExtraScenarioInfoF.create(
            scenario=scenario,
            extrainfofield=extrainfofield,
            value=value)

        inputfield = InputFieldF.build(
            destination_table='ExtraScenarioInfo',
            destination_field=fieldname)

        retvalue = models.find_imported_value(
            inputfield, {'scenario': scenario})
        self.assertEquals(retvalue, 3)

    def test_999(self):
        # It used to be that values like -999 were treated separately
        # (as if they were None), but that is disabled now so this is
        # just a pretty random test.
        scenario = ScenarioF.create()
        fieldname = 'test'
        value = '-999'

        extrainfofield = ExtraInfoFieldF.create(name=fieldname)
        ExtraScenarioInfoF.create(
            scenario=scenario,
            extrainfofield=extrainfofield,
            value=value)

        inputfield = InputFieldF.build(
            destination_table='ExtraScenarioInfo',
            destination_field=fieldname,
            type=importmodels.InputField.TYPE_STRING)

        retvalue = models.find_imported_value(
            inputfield, {'scenario': scenario})
        self.assertEquals(retvalue, u'-999')

    def test_xy(self):
        WGS_X = 10
        WGS_Y = 20
        RD_X = 110
        RD_Y = 120

        breach = FakeObject(
            geom=FakeObject(
                x=WGS_X, y=WGS_Y))

        inputfieldx = InputFieldF.build(
            name='X coordinaat',
            destination_table='Breach',
            destination_field='geom')
        inputfieldy = InputFieldF.build(
            name='Y coordinaat',
            destination_table='Breach',
            destination_field='geom')

        with mock.patch(
            'flooding_lib.coordinates.wgs84_to_rd',
            return_value=(RD_X, RD_Y)):
            retvaluex = models.find_imported_value(
                inputfieldx, {'breach': breach})
            retvaluey = models.find_imported_value(
                inputfieldy, {'breach': breach})
            self.assertEquals(retvaluex, RD_X)
            self.assertEquals(retvaluey, RD_Y)


class TestTaskExecutor(TestCase):
    def test_has_unicode(self):
        task_executor = TaskExecutorF.build()

        uni = task_executor.__unicode__()

        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestResultTypePresentationType(TestCase):
    def test_has_unicode(self):
        rtpt = ResultTypePresentationTypeF.build()
        uni = rtpt.__unicode__()

        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestStrategy(TestCase):
    def test_has_unicode(self):
        strategy = StrategyF.build()

        uni = strategy.__unicode__()

        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestMeasure(TestCase):
    def test_has_unicode(self):
        measure = MeasureF.build()

        uni = measure.__unicode__()

        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))


class TestEmbankmentUnit(TestCase):
    def test_has_unicode(self):
        embankment_unit = EmbankmentUnitF.build()

        uni = embankment_unit.__unicode__()

        self.assertTrue(uni)
        self.assertTrue(isinstance(uni, unicode))
