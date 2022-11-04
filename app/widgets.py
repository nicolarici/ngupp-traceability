from wtforms.fields import PasswordField, StringField, IntegerField


class CustomPasswordField(PasswordField):
    """ Validator for password"""

    def __init__(self, label='', validators=None, error_class=u"is-invalid", **kwargs):
        super(CustomPasswordField, self).__init__(label, validators, **kwargs)
        self.error_class = error_class

    def __call__(self, **kwargs):
        if self.errors:
            c = kwargs.pop("class", "") or kwargs.pop("class_", "")
            kwargs["class"] = u"%s %s" % (self.error_class, c)
            kwargs["style"] = u"%s" % ("margin-bottom: 0px;")

        return super(CustomPasswordField, self).__call__(**kwargs)


class CustomStringField(StringField):
    """ Validator for text"""

    def __init__(self, label='', validators=None, error_class=u"is-invalid", **kwargs):
        super(CustomStringField, self).__init__(label, validators, **kwargs)
        self.error_class = error_class

    def __call__(self, **kwargs):
        if self.errors:
            c = kwargs.pop("class", "") or kwargs.pop("class_", "")
            kwargs["class"] = u"%s %s" % (self.error_class, c)
            kwargs["style"] = u"%s" % ("margin-bottom: 0px;")

        return super(CustomStringField, self).__call__(**kwargs)


class CustomIntegerField(IntegerField):
    """ Validator for text"""

    def __init__(self, label='', validators=None, error_class=u"is-invalid", **kwargs):
        super(CustomIntegerField, self).__init__(label, validators, **kwargs)
        self.error_class = error_class

    def __call__(self, **kwargs):
        if self.errors:
            c = kwargs.pop("class", "") or kwargs.pop("class_", "")
            kwargs["class"] = u"%s %s" % (self.error_class, c)
            kwargs["style"] = u"%s" % ("margin-bottom: 0px;")

        return super(CustomIntegerField, self).__call__(**kwargs)

