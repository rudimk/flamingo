# -*- encoding: utf-8 -*-
from datetime import datetime

from sqlalchemy.ext.hybrid import hybrid_property
from flask.ext.security import (UserMixin, RoleMixin, Security,
                                SQLAlchemyUserDatastore)
from flask.ext.security.registerable import register_user
from flask.ext.social import Social, SQLAlchemyConnectionDatastore

from flamaster.core.models import CRUDMixin

from . import app, db


user_roles = db.Table('user_roles', db.metadata,
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'),
              primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'),
              primary_key=True),
)


class Role(db.Model, CRUDMixin, RoleMixin):
    """ User's role representation as datastore persists it.
        By default model inherits id and created_at fields from the CRUDMixin
    """
    name = db.Column(db.String(255), unique=True, index=True, nullable=False)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Role: %r>" % self.name

    @classmethod
    def get_or_create(cls, name=app.config['USER_ROLE']):
        return cls.query.filter_by(name=name).first() or cls.create(name=name)


class User(db.Model, CRUDMixin, UserMixin):
    """ User representation from the datastore view.
        By default model inherits id and created_at fields from the CRUDMixin
    """

    __mapper_args__ = {
        'order_by': ['email']
    }

    email = db.Column(db.String(80), unique=True, index=True)
    password = db.Column(db.String(512))
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    remember_token = db.Column(db.String(255), unique=True, index=True)
    authentication_token = db.Column(db.String(255), unique=True, index=True)
    confirmed_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    current_login_ip = db.Column(db.String(128))
    login_count = db.Column(db.Integer)

    roles = db.relationship('Role', secondary=user_roles,
                                backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return "<User: %r>" % self.email

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    @classmethod
    def create(cls, **kwargs):
        """ User creation process, set up role for user
            :params kwargs: should contains `email`, `password` and `active`
                            flag to set up base user data
        """
        customer_args = {
            'first_name': kwargs.pop('first_name', ''),
            'last_name': kwargs.pop('last_name', ''),
            'phone': kwargs.pop('phone', ''),
            'email': kwargs.get('email')
        }

        admin_role, user_role = (app.config['ADMIN_ROLE'],
                                 app.config['USER_ROLE'])
        email, admins = kwargs['email'], app.config['ADMINS']

        role = email in admins and admin_role or user_role
        # ensure on role existence
        kwargs['roles'] = [Role.get_or_create(name=role)]
        instance = register_user(**kwargs)
        instance.customer.update(**customer_args)
        return instance

    @classmethod
    def is_unique(cls, email):
        """ uniqueness check on email property
            :params email: email to check against existing users
        """
        return cls.query.filter_by(email=email).count() == 0

    @hybrid_property
    def first_name(self):
        return self.customer.first_name

    @first_name.setter
    def first_name(self, value):
        self.customer.first_name = value

    @hybrid_property
    def last_name(self):
        return self.customer.last_name

    @last_name.setter
    def last_name(self, value):
        self.customer.last_name = value

    @hybrid_property
    def phone(self):
        return self.customer.phone

    @phone.setter
    def phone(self, value):
        self.customer.phone = value

    @hybrid_property
    def addresses(self):
        return self.customer.addresses

    @addresses.setter
    def addresses(self, value):
        if not isinstance(value, list):
            value = [value]

        map(self.customer.addresses.append, value)

    @property
    def is_superuser(self):
        """ Flag signalized that user is superuse """
        return self.has_role(app.config['ADMIN_ROLE'])

    @property
    def full_name(self):
        """ User full name helper """
        full_name = " ".join([self.first_name or '', self.last_name or ''])
        return full_name.strip() or self.email


class BankAccount(db.Model, CRUDMixin):
    bank_name = db.Column(db.String(512))
    iban = db.Column(db.String(256))
    swift = db.Column(db.String(256))
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('accounts',
                           lazy='dynamic'))

    def check_owner(self, user_id):
        return user_id == self.user_id


class SocialConnection(db.Model, CRUDMixin):
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('connections',
                           lazy='dynamic'), cascade='all')
    provider_id = db.Column(db.String(255))
    provider_user_id = db.Column(db.String(255))
    access_token = db.Column(db.String(255))
    secret = db.Column(db.String(255))
    display_name = db.Column(db.Unicode(255))
    profile_url = db.Column(db.String(512))
    image_url = db.Column(db.String(512))
    rank = db.Column(db.Integer)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
Security(app, user_datastore)
Social(app, SQLAlchemyConnectionDatastore(db, SocialConnection))