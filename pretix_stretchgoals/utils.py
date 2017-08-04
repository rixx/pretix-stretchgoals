import json

from i18nfield.strings import LazyI18nString
from i18nfield.utils import I18nJSONEncoder


def get_goals(event):
    goals = json.loads(event.settings.get('stretchgoals_goals') or '[]')
    for goal in goals:
        goal['name'] = LazyI18nString(goal['name'])
        goal['description'] = LazyI18nString(goal['description'])
    return goals


def set_goals(event, goals):
    event.settings.set('stretchgoals_goals', json.dumps(goals, cls=I18nJSONEncoder))


def get_cache_key(event):
    return 'stretchgoals_data_{}'.format(event.slug)


def invalidate_cache(event):
    event.get_cache().delete(get_cache_key(event))
