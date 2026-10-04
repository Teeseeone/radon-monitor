"""Resource registration is idempotent and preserves other cards."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('radon_frontend', Path(__file__).parents[1] / 'custom_components/radon_monitor/frontend.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Resources:
    def __init__(self, items):
        self.items = items
        self.loaded = False
        self.changes = []
    async def async_get_info(self):
        self.loaded = True
    def async_items(self):
        assert self.loaded
        return self.items
    async def async_create_item(self, data):
        self.changes.append(('create', data))
        self.items.append({'id': 'new', 'url': data['url'], 'type': data['res_type']})
    async def async_update_item(self, item_id, data):
        self.changes.append(('update', item_id))
        next(item for item in self.items if item['id'] == item_id).update(url=data['url'], type=data['res_type'])

class RegistrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_new_card_registers_once(self):
        resources = Resources([])
        url = '/radon_monitor/radon-monitor-card.js?v=0.2.3'
        await module.async_register_card_resource(resources, url)
        await module.async_register_card_resource(resources, url)
        self.assertEqual(len(resources.changes), 1)
        self.assertEqual(resources.items[0]['type'], 'module')
    async def test_existing_card_updates_without_touching_others(self):
        resources = Resources([
            {'id': 'old', 'url': '/radon_monitor/radon-monitor-card.js?v=0.2.2', 'type': 'js'},
            {'id': 'other', 'url': '/hacsfiles/another/card.js', 'type': 'module'},
            {'id': 'remote', 'url': 'https://example.com/radon_monitor/radon-monitor-card.js', 'type': 'module'}])
        await module.async_register_card_resource(resources, '/radon_monitor/radon-monitor-card.js?v=0.2.3')
        self.assertEqual(resources.changes, [('update', 'old')])
        self.assertEqual(len(resources.items), 3)
        self.assertEqual(resources.items[1]['url'], '/hacsfiles/another/card.js')
        self.assertTrue(resources.items[2]['url'].startswith('https:'))
