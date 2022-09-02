#!/usr/bin/env python3
"""
Migrates all Kong 0.14.1 APIs to Services and Routes
Author: Pavel Jelinek, https://github.com/pajel
"""

import os
import requests

old_kong_url = os.environ['OLD_KONG_URL']
new_kong_url = os.environ['NEW_KONG_URL']
try:
  kong_migrate = os.environ["KONG_MIGRATE"]
except KeyError:
  kong_migrate = 'False'

# Get first 1000 APIS and process them
resp_apis = requests.get("{}/apis/?size=1000".format(old_kong_url))
resp_apis_json = resp_apis.json()

if "data" in resp_apis_json:
  if kong_migrate == 'True':
    print("Running migrations: True")
    for api in resp_apis_json["data"]:
      data_service = {'name': api["name"], 'url': api["upstream_url"], 'retries': api["retries"], 'connect_timeout': api["upstream_connect_timeout"], 'write_timeout': api["upstream_send_timeout"], 'read_timeout': api["upstream_read_timeout"]}
      print("Migrating API with id: {}, name: {}".format(api["id"], api["name"]))
      print("  Creating service with data: {}".format(data_service))
      # 创建 service
      resp_service = requests.post("{}/services/".format(new_kong_url), data_service)
      resp_service_json = resp_service.json()

      data_route = {"paths": api["uris"], "preserve_host": api["preserve_host"], "service": {"id": resp_service_json["id"]}}
      if "methods" in api:
        data_route['methods'] = api["methods"]
      if "hosts" in api:
        data_route['hosts'] = api["hosts"]
      if "strip_uri" in api:
        data_route['strip_path'] = api["strip_uri"]
      if api["https_only"] is True:
        data_route['protocols'] = ["https"]

      print("  Creating route with data: {}".format(data_route))
      # 创建 route
      resp_route = requests.post("{}/routes/".format(new_kong_url), json=data_route)

      resp_plugins = requests.get("{}/plugins/?api_id={}".format(old_kong_url, api["id"]))
      resp_plugins_json = resp_plugins.json()
      if "data" in resp_plugins_json:
        for plugin in resp_plugins_json["data"]:
          data_plugin = {"name": plugin["name"], "id": plugin["id"], "created_at": plugin["created_at"], "enabled": plugin["enabled"], "service_id": resp_service_json["id"], "config": plugin["config"]}
          print("    Migrating plugin with name: {}".format(plugin["name"]))
          resp_plugin = requests.put("{}/plugins/".format(new_kong_url), json=data_plugin)

      print("  Deleting API: {}".format(api["name"]))
      # 旧的留着，不删除
      # requests.delete("{}/apis/{}".format(old_kong_url, api["name"]))
  else:
    print("Running migrations: False")
    for api in resp_apis_json["data"]:
      data_service = {'name': api["name"], 'url': api["upstream_url"], 'retries': api["retries"], 'connect_timeout': api["upstream_connect_timeout"], 'write_timeout': api["upstream_send_timeout"], 'read_timeout': api["upstream_read_timeout"]}
      data_route = {"paths": api["uris"], "preserve_host": api["preserve_host"]}
      if "methods" in api:
        data_route['methods'] = api["methods"]
      if "hosts" in api:
        data_route['hosts'] = api["hosts"]
      if "strip_uri" in api:
        data_route['strip_path'] = api["strip_uri"]
      if api["https_only"] is True:
        data_route['protocols'] = ["https"]
      print("Would migrate API with id: {}, name: {}".format(api["id"], api["name"]))
      print("  Would create service with data: {}".format(data_service))
      print("  Would create route with data: {}".format(data_route))
      resp_plugins = requests.get("{}/plugins/?api_id={}".format(old_kong_url, api["id"]))
      resp_plugins_json = resp_plugins.json()
      if "data" in resp_plugins_json:
        for plugin in resp_plugins_json["data"]:
          print("    Would migrate plugin with name: {}".format(plugin["name"]))
      print("  Would delete API: {}".format(api["name"]))
else:
  print("Nothing to migrate")