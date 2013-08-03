from pyramid.view import view_config
from pyramid import httpexceptions as httpexc

import deform

from curehack import schemas


@view_config(route_name='home',
             request_method='GET',
             renderer='curehack:templates/home.mako')
def home(request):
    precure_names = request.context.precure_names
    schema = schemas.PrecureTrainSchemaNode(precure_names)
    form = deform.Form(schema, buttons=('submit',),
                       action=request.route_url('train'))
    return dict(form=form.render(),
                desc_link=request.route_url('precures'))


@view_config(route_name='train',
             request_method='POST')
def train(request):
    classifier = request.context.classifier
    for cat, desc in request.context.category_descriptions:
        classifier.train(desc, cat)

    return httpexc.HTTPFound(
        location=request.route_url('result', user=request.context.user)
    )


@view_config(route_name='result',
             request_method='GET',
             renderer='curehack:templates/ranking.mako')
def result(request):
    schema = schemas.PrecureClassifySchema()
    form = deform.Form(schema,
                       buttons=('submit',),
                       method='GET',
                       action=request.route_url('classify',
                                                user=request.context.user))
    return dict(ranking=request.context.ranking,
                form=form.render())


@view_config(route_name='precures',
             request_method='GET',
             renderer='curehack:templates/precures.mako')
def precures(request):
    precures = request.context.precures
    schema = schemas.PrecureRegisterSchema()
    form = deform.Form(schema, buttons=('submit',),
                       action=request.route_url('register'))
    return dict(precures=precures,
                form=form.render())


@view_config(route_name='register',
             request_method='POST')
def register_precure(request):
    # TODO: Move this logic to specified module.
    request.db.precures.insert({'name': request.context.name,
                                'description': request.context.description})
    return httpexc.HTTPFound(request.route_url('precures'))


@view_config(route_name='classify',
             request_method='GET',
             renderer='curehack:templates/classify.mako')
def classify(request):
    classifier = request.context.classifier
    category = classifier.classify(request.context.item)
    return dict(category=category)
