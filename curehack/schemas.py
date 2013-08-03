import colander
import deform


from curehack.choice import LikingChoice


CHOICES = LikingChoice.choices


def user_node_factory():
    return colander.SchemaNode(colander.String(), title='user')


class PrecureRegisterSchema(colander.MappingSchema):
    name = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(colander.String(),
                                      widget=deform.widget.TextAreaWidget())


class PrecureClassifySchema(colander.MappingSchema):
    item = colander.SchemaNode(colander.String())


class Choice(colander.String):
    def __init__(self, choice_class, encoding=None):
        self.choice_class = choice_class
        self.encoding = encoding

    def deserialize(self, node, cstruct):
        value = super(Choice, self).deserialize(node, cstruct)
        try:
            choice = self.choice_class(value)
        except self.choice_class.IsInvalidChoice:
            choices = ', '.join(['%s' % x for x in self.choice_class.choices])
            err = colander._('"${val}" is not one of ${choices}',
                    mapping={'val':value, 'choices':choices})
            raise colander.Invalid(node, err)
        return choice


class PrecureTrainSchemaNode(colander.SchemaNode):
    def __init__(self, precures):
        colander.SchemaNode.__init__(self, colander.Mapping())

        user_node = user_node_factory()
        user_node.name = 'user'
        self.add(user_node)

        for precure in precures:
            precure_node = colander.SchemaNode(
                Choice(LikingChoice),
                widget=deform.widget.RadioChoiceWidget(values=CHOICES),
                title=precure,
            )
            precure_node.name = precure
            self.add(precure_node)
