from collections import OrderedDict

from django.utils.functional import cached_property
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from six import itervalues

from portia_orm.models import Project
from storage import get_storage_class
from .route import JsonApiRoute, ListModelMixin, RetrieveModelMixin
from ..jsonapi.exceptions import JsonApiFeatureNotAvailableError


class ProjectDownloadMixin(object):
    @detail_route(methods=['get'])
    def download(self, *args, **kwargs):
        # project_manager = self.project_manager
        project_id = self.kwargs.get('project_id')
        spider_id = self.kwargs.get('spider_id', None)
        spider_ids = [spider_id] if spider_id is not None else '*'
        fmt = self.query.get('format', 'spec')
        # return ProjectDownloadResponse(
        #     project_id, spider_ids, fmt, project_manager)
        return Response(b'', status=HTTP_200_OK)


class ProjectDataMixin(object):
    @cached_property
    def projects(self):
        storage_class = get_storage_class()
        project_list = storage_class.list_projects(self.request.user)
        return OrderedDict([(project['id'], project)
                            for project in project_list])


class ProjectRoute(ProjectDownloadMixin, JsonApiRoute, ProjectDataMixin,
                   ListModelMixin, RetrieveModelMixin):
    lookup_url_kwarg = 'project_id'
    default_model = Project

    class FakeStorage(object):
        def exists(self, *args, **kwargs):
            return False

        def listdir(self, *args, **kwargs):
            return [], []

    # def create(self):
    #     """Create a new project from the provided attributes"""
    #     manager = self.project_manager
    #     attributes = _check_project_attributes(manager, self.data)
    #     manager.create_project(attributes['name'])
    #     return self.serialize_instance({
    #         'id': attributes['name'],
    #         'name': attributes['name'],
    #     })

    # def update(self):
    #     """Update an exiting project with the provided attributes"""
    #     manager = self.project_spec
    #     project_id = self.args.get('project_id')
    #     attributes = _check_project_attributes(manager, self.data)
    #     if project_id != attributes['name']:
    #         manager.rename_project(project_id, attributes['name'])
    #     return self.serialize_instance({
    #         'id': project_id,
    #         'name': attributes['name'],
    #     })

    # def destroy(self):
    #     """Delete the request project"""
    #     manager = self.project_spec
    #     project_id = self.args.get('project_id')
    #     manager.remove_project(project_id)
    #     return self.get_empty()

    @detail_route(methods=['get'])
    def status(self, *args, **kwargs):
        response = self.retrieve()
        data = OrderedDict()
        data.update({
            'meta': {
                'changes': self.get_project_changes()
            }
        })
        data.update(response.data)
        return Response(data, status=HTTP_200_OK)

    @detail_route(methods=['put', 'patch', 'post'])
    def publish(self, *args, **kwargs):
        # manager = self.project_spec
        # if not hasattr(manager.pm, 'publish_project'):
        #     raise JsonApiFeatureNotAvailableError()
        # project_id = manager.project_name
        # if not self.get_project_changes():
        #     raise BadRequest('The project is up to date')
        # publish_status = json.loads(
        #     manager.pm.publish_project(project_id,
        #                                self.data.get('force', False)))
        # if publish_status['status'] == 'conflict':
        #     raise BaseError(409, 'A conflict has occurred in this project',
        #                     'You must resolve the conflict for the project to be'
        #                     ' successfully published')

        response = self.retrieve()
        data = OrderedDict()
        # data.update({
        #     'meta': manager.pm._schedule_data(project_id=project_id)
        # })
        data.update(response.data)
        return Response(data, status=HTTP_200_OK)

    @detail_route(methods=['put', 'patch', 'post'])
    def reset(self, *args, **kwargs):
        # manager = self.project_spec
        # if not hasattr(manager.pm, 'discard_changes'):
        #     raise JsonApiFeatureNotAvailableError()
        # project_id = manager.project_name
        # if not self.get_project_changes():
        #     raise BadRequest('There are no changes to discard')
        # manager.pm.discard_changes(project_id)
        return self.retrieve()

    def get_instance(self):
        return Project(
            self.storage, **self.projects[self.kwargs.get('project_id')])

    def get_collection(self):
        storage = self.FakeStorage()
        return Project.collection(Project(storage, **project)
                                  for project in itervalues(self.projects))

    def get_detail_kwargs(self):
        return {
            'include_data': [
                'spiders',
                'schemas',
            ],
            'fields_map': {
                'spiders': [
                    'project',
                ],
                'schemas': [
                    'name',
                    'project',
                ],
            },
            'exclude_map': {
                'projects': [
                    'extractors',
                ],
            }
        }

    def get_list_kwargs(self):
        return {
            'fields_map': {
                'projects': [
                    'name',
                ],
            }
        }

    def get_project_changes(self):
        storage = self.storage
        if not storage.version_control:
            raise JsonApiFeatureNotAvailableError()
        return [{'type': type_, 'path': path, 'old_path': old_path}
                for type_, path, old_path
                in storage.changed_files()]


# def _check_project_attributes(manager, attributes):
#     attributes = ProjectSchema().load(attributes).data
#     if 'name' not in attributes:
#         raise BadRequest('Bad Request',
#                          'Can\'t create a project without a name')
#     manager.validate_project_name(attributes['name'])
#     return attributes