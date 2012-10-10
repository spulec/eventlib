# eventlib - Copyright (c) 2012  Yipit, Inc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import os
from mock import Mock, patch
from datetime import datetime

import eventlib
from eventlib import exceptions, conf, core, tasks, serializers


def test_parse_event_name():
    core.parse_event_name('app.Event').should.be.equal(
        ('app.events', 'Event'))

    core.parse_event_name.when.called_with('stuff').should.throw(
        exceptions.InvalidEventNameError,
        'The name "stuff" is invalid. Make sure you are using the '
        '"app.KlassName" format')

    core.parse_event_name.when.called_with('other.stuff.blah').should.throw(
        exceptions.InvalidEventNameError,
        'The name "other.stuff.blah" is invalid. Make sure you are using the '
        '"app.KlassName" format')


@patch('eventlib.core.import_module')
def test_find_event(import_module):
    fake_module = Mock()
    fake_module.Event = 'my-lol-module'

    import_module.return_value = fake_module
    core.find_event('app.Event').should.be.equals('my-lol-module')

    import_module.reset_mock()
    import_module.side_effect = ImportError
    core.find_event.when.called_with('app.Event2').should.throw(
        exceptions.EventNotFoundError,
        'Event "app.Event2" not found. Make sure you have a class '
        'called "Event2" inside the "app.events" module.')


def test_event_validate():
    class MyEvent(eventlib.BaseEvent):
        pass

    data = {'name': 'Lincoln', 'age': 25, 'answer': 42}
    event = MyEvent('stuff', data)

    assert event.validate_keys('name', 'age')

    event.validate_keys.when.called_with('unknown', 'blah').should.throw(
        exceptions.ValidationError,
        'One of the following keys are missing from the event\'s data: '
        'unknown, blah')


def test_filter_data_values():
    core.filter_data_values({'a': 'b', 'c': 'd'}).should.be.equals(
        {'a': 'b', 'c': 'd'}
    )
    core.filter_data_values({'a': 'b', 'request': None}).should.be.equals(
        {'a': 'b'}
    )


@patch('eventlib.core.datetime')
@patch('eventlib.core.get_ip')
def test_get_default_values_with_request(get_ip, datetime):
    get_ip.return_value = '150.164.211.1'
    datetime.now.return_value = 'tea time!'
    data = {'foo': 'bar', 'request': Mock()}
    core.get_default_values(data).should.be.equals({
        '__datetime__': 'tea time!',
        '__ip_address__': '150.164.211.1',
    })


@patch('eventlib.tasks.process')
def test_celery_process_wrapper(process):
    tasks.process_task('name', 'data')
    process.assert_called_once_with('name', 'data')


@patch('django.conf.importlib')
def test_django_integration(importlib):
    # Given I mock django conf
    settings = importlib.import_module.return_value
    settings.LOCAL_GEOLOCATION_IP = 'CHUCK NORRIS'

    # When I reload the eventlib conf with the django environment
    # variable
    os.environ['DJANGO_SETTINGS_MODULE'] = 'LOL'
    reload(conf)

    # Then it should contain the mocked values
    conf.LOCAL_GEOLOCATION_IP.should.equal('CHUCK NORRIS')

    # Cleaning up
    del os.environ['DJANGO_SETTINGS_MODULE']


def test_date_serializer_and_unserializer():
    my_date = datetime(2012, 9, 26, 14, 31)
    serializers.serialize_datetime(my_date).should.equal(
        '2012-09-26T14:31:00')
    serializers.deserialize_datetime('2012-09-26T14:31:00').should.equal(
        my_date)
