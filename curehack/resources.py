import deform

from curehack import choice
from curehack import docclass
from curehack import schemas


class BaseResource(object):
    def __init__(self, request):
        self.request = request


class PrecureNamesMixin(object):
    @property
    def precure_names(self):
        return [d['name']
                for d in self.request.db.precures.find({}, {'name': 1})]


class PrecureNamesResource(BaseResource, PrecureNamesMixin):
    pass


class PrecuresResource(BaseResource):
    @property
    def precures(self):
        return self.request.db.precures.find()


class PrecureRegisterResource(BaseResource):
    @property
    def appstruct(self):
        controls = self.request.POST.items()
        schema = schemas.PrecureRegisterSchema()
        form = deform.Form(schema)
        appstruct = form.validate(controls)
        return appstruct

    @property
    def name(self):
        return self.appstruct['name']

    @property
    def description(self):
        return self.appstruct['description']


class PrecureTrainResource(BaseResource, PrecureNamesMixin):
    @property
    def appstruct(self):
        controls = self.request.POST.items()
        schema = schemas.PrecureTrainSchemaNode(self.precure_names)
        form = deform.Form(schema)
        appstruct = form.validate(controls)
        return appstruct

    @property
    def user(self):
        return self.appstruct['user']

    @property
    def category_names(self):
        appstruct = self.appstruct
        appstruct.pop('user')
        return [(vote, name)
                for name, vote in appstruct.items() if vote != 'soso']

    @property
    def category_descriptions(self):
        """Pairs of categories and distription text of precures"""
        category_descriptions = []
        for category, name in self.category_names:
            description = self.request.db.precures.find_one(
                {'name': name}
            ).get('description', '')

            category_descriptions.append((category, description))

        return category_descriptions

    @property
    def classifier(self):
        backend = docclass.MongoDBBackend(self.request.db, self.user)
        return docclass.DefaultClassifier(backend)


class PrecureClassifyResource(BaseResource):
    @property
    def appstruct(self):
        controls = self.request.GET.items()
        schema = schemas.PrecureClassifySchema()
        form = deform.Form(schema)
        appstruct = form.validate(controls)
        return appstruct

    @property
    def item(self):
        return self.appstruct['item']

    @property
    def user(self):
        return self.request.matchdict['user']

    @property
    def classifier(self):
        backend = docclass.MongoDBBackend(self.request.db, self.user)
        return docclass.DefaultClassifier(backend)


class ResultResource(BaseResource):
    @property
    def user(self):
        return self.request.matchdict['user']

    @property
    def ranking(self):
        ds = self.request.db.features.find(
            {'user': self.user}
        ).sort('count')

        ret = {}
        for d in ds:
            liking = d['count'] * int(choice.LikingChoice(d['category']))
            if d['feature'] in ret:
                ret[d['feature']] += liking
            else:
                ret[d['feature']] = liking

        return sorted(ret.items(), key=lambda x: x[1])
