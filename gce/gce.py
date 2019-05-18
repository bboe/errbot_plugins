import json
from pprint import pformat

from errbot import BotPlugin, botcmd, arg_botcmd, webhook
from google.oauth2 import service_account
from googleapiclient import discovery, errors


class GCE(BotPlugin):
    """Google Compute Engine"""

    def activate(self):
        """Triggers on plugin activation"""
        with open("gcloud_errbot.json") as fp:
            credential_data = json.load(fp)
        credentials = service_account.Credentials.from_service_account_info(
            credential_data
        )
        self.google_cloud_client = discovery.build(
            "compute", "v1", cache_discovery=False, credentials=credentials
        )
        super(GCE, self).activate()

    @arg_botcmd("name", type=str)
    @arg_botcmd("--project", default="invoice-processing-ocr", type=str)
    @arg_botcmd("--raw", action="store_true", help="Return the RAW output.")
    @arg_botcmd("--zone", default="us-west2-a", type=str)
    def gce_start(self, message, name, raw, project, zone):
        """Start a Google Cloud Compute Engine instance."""
        try:
            instance = start_instance(
                self.google_cloud_client, name, project=project, zone=zone
            )
        except errors.HttpError as exception:
            return json.loads(exception.content)["error"]["message"]
        if raw:
            return f"```{pformat(instance)}```"
        return f"({name}) START (progress: {instance['progress']}) (instance status: {instance['status']})"

    @arg_botcmd("name", type=str)
    @arg_botcmd("--project", default="invoice-processing-ocr", type=str)
    @arg_botcmd("--raw", action="store_true", help="Return the RAW output.")
    @arg_botcmd("--zone", default="us-west2-a", type=str)
    def gce_status(self, message, name, project, raw, zone):
        """Return the running status of a Google Cloud Compute Engine instance."""
        try:
            instance = get_instance(
                self.google_cloud_client, name, project=project, zone=zone
            )
        except errors.HttpError as exception:
            return json.loads(exception.content)["error"]["message"]
        if raw:
            return f"```\n{pformat(instance)}```"
        return format_status(instance)

    @arg_botcmd("name", type=str)
    @arg_botcmd("--project", default="invoice-processing-ocr", type=str)
    @arg_botcmd("--raw", action="store_true", help="Return the RAW output.")
    @arg_botcmd("--zone", default="us-west2-a", type=str)
    def gce_stop(self, message, name, project, raw, zone):
        """Stop a Google Cloud Compute Engine instance."""
        try:
            instance = stop_instance(
                self.google_cloud_client, name, project=project, zone=zone
            )
        except errors.HttpError as exception:
            return json.loads(exception.content)["error"]["message"]
        if raw:
            return f"```{pformat(instance)}```"
        return f"({name}) STOP (progress: {instance['progress']}) (instance status: {instance['status']})"


def format_status(instance):
    if instance["status"] == "RUNNING":
        ip = instance["networkInterfaces"][0]["accessConfigs"][0]["natIP"]
        return f'({instance["name"]}) RUNNING {ip}'
    return f'({instance["name"]}) {instance["status"]}'


def get_instance(service, name, project, zone):
    request = service.instances().get(instance=name, project=project, zone=zone)
    return request.execute()


def list_instances(service, project, zone):
    request = service.instances().list(project=project, zone=zone)
    while request is not None:
        response = request.execute()
        for instance in response["items"]:
            yield instance
        request = service.instances().list_next(
            previous_request=request, previous_response=response
        )


def start_instance(service, name, project, zone):
    request = service.instances().start(instance=name, project=project, zone=zone)
    return request.execute()


def stop_instance(service, name, project, zone):
    request = service.instances().stop(instance=name, project=project, zone=zone)
    return request.execute()
