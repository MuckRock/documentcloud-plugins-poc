"""
This is a base class for DocumentCloud Add-Ons to inherit from.
It provides some common Add-On functionality, and for basic Add-On development,
does not need to be edited.  Advanced users may edit as needed
"""

import json
import os
import sys

import documentcloud
import requests


class AddOn:
    """Base functionality for DocumentCloud Add-Ons."""

    def __init__(self):
        token, base_uri = self._load_params()
        # set up the client
        kwargs = {"base_uri": base_uri} if base_uri is not None else {}
        self.client = documentcloud.DocumentCloud(**kwargs)
        self.client.session.headers.update({"Authorization": "Bearer {}".format(token)})
        self.client.session.headers["User-Agent"] += " (DC AddOn)"

    def _load_params(self):
        """Load the parameters passed in to the GitHub Action."""
        params = json.loads(sys.argv[1])
        # token is a JWT to use to authenticate against the DocumentCloud API
        token = params.pop("token")
        # base_uri is the URI to make API calls to - allows the plugin to function
        # in non-production environments
        base_uri = params.pop("base_uri", None)

        # a unique identifier for this run
        self.id = params.pop("id")
        # Documents is a list of document IDs which were selected to run with this
        # plugin activation
        self.documents = params.pop("documents", None)
        # Query is the search query selected to run with this plugin activation
        self.query = params.pop("query", None)
        # user and org IDs
        self.user_id = params.pop("user", None)
        self.org_id = params.pop("organization", None)
        # add on specific data
        self.data = params.pop("data", None)

        return token, base_uri

    def set_progress(self, progress):
        """Set the progress as a percentage between 0 and 100."""
        assert 0 <= progress <= 100
        self.client.patch(f"plugin_runs/{self.id}/", json={"progress": progress})

    def set_message(self, message):
        """Set the progress message."""
        self.client.patch(f"plugin_runs/{self.id}/", json={"message": message})

    def upload_file(self, file):
        """Uploads a file to the plugin run."""

        # go to the beginning of the file
        file.seek(0)
        file_name = os.path.basename(file.name)
        resp = self.client.get(
            f"plugin_runs/{self.id}/", params={"upload_file": file_name}
        )
        presigned_url = resp.json()["presigned_url"]
        # use buffer as it should always be binary, which requests wants
        requests.put(presigned_url, data=file.buffer)
        self.client.patch(f"plugin_runs/{self.id}/", json={"file_name": file_name})

