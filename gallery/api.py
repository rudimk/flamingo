# encoding: utf-8
import base64
import re
import trafaret as t

from flamaster.core import http
from flamaster.core.decorators import api_resource
from flamaster.core.resources import ModelResource
from flamaster.core.utils import jsonify_status_code

from flask import abort, g, request, send_file
from flask.ext.security import login_required, current_user

from sqlalchemy import or_

from . import bp
from .models import Image, Album


def get_access_type(data_dict):
    album = Album.query.get(data_dict['album_id']) or abort(http.BAD_REQUEST)
    is_public = data_dict.get('is_public', True) and album.is_public
    data_dict['is_public'] = is_public
    return data_dict


@api_resource(bp, 'images', {'id': None})
class ImageResource(ModelResource):
    model = Image
    mime_re = re.compile('data\:(\w+\/\w+)')
    validation = t.Dict({
        'image': t.String,
        'name': t.String
    }).ignore_extra('*')

    method_decorators = {'post': [login_required],
                         'put': [login_required],
                         'delete': [login_required]}

    def post(self):
        status = http.CREATED
        try:
            if request.json:
                data = self.validation.check(request.json)
                response = self.__process_json(data)
            elif request.files:
                response = self.__process_form(request.form.to_dict())
        except t.DataError as e:
            status, response = http.BAD_REQUEST, e.as_dict()

        return jsonify_status_code(response, status)

    def __process_json(self, data):
        meta, image = data['image'].split(',')
        mime_type = self.mime_re.match(meta).group(1)
        image = base64.urlsafe_b64decode(image)
        imageModel = self.model.create(image, mime_type, name=data['name'],
                                       author=current_user,)
        return imageModel.as_dict()

    def __process_form(self, data):
        # TODO: have to complete
        data['image'] = request.files.get('image')
        data = self.validation.check(data)
        data['author_id'] = current_user.id

        return self.model.create(**data).as_dict()

    def get(self, id):
        # validation = self.validation.append(get_access_type)
        file_object = self.model.get(id) or abort(404)
        return send_file(file_object)

    def get_objects(self, **kwargs):
        """ Method for extraction object list query
        """
        query = super(ImageResource, self).get_objects(**kwargs)
        if current_user.is_anonymous():
            return query.filter_by(is_public=True)
        elif current_user.is_superuser:
            return query
        else:
            return query.filter(or_(self.model.author_id == current_user.id,
                                       self.model.is_public is True))


# TODO: Establish why GET params does not pass to request.args
@api_resource(bp, 'albums', {'id': int})
class AlbumResource(ImageResource):
    model = Album

    validation = t.Dict({
        'name': t.String,
        'description': t.String,
        'coverage': t.Dict({'id': t.Int}).ignore_extra('*')
    }).ignore_extra('*')

    def post(self, owner=None):
        #TODO: how to set an owner?
        author = g.user.is_anonymous() and abort(http.UNAUTHORIZED) or g.user
        request.json.update({'author': author})
#        if owner is not None:
#            request.json.update({'owner': owner})
        return super(ImageResource, self).post()
