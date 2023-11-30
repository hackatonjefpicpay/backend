from flask import Flask
import utils.service
from requests import get

app = Flask(__name__)


@app.route("/oracle/select")
def findAllStatusInfoOracle():
    statusJson = utils.service.selectRequestUrl(
        "https://ocistatus.oraclecloud.com/api/v2/status.json"
    )
    componentsJson = utils.service.selectRequestUrl(
        "https://ocistatus.oraclecloud.com/api/v2/components.json"
    )

    regions = {}
    componentsJson = componentsJson["regionHealthReports"]
    for component in componentsJson:
        if (
            component["regionName"] == "Brazil East (Sao Paulo)"
            or component["regionName"] == "Brazil Southeast (Vinhedo)"
        ):
            if component["regionName"] not in regions:
                regions[component["regionName"]] = []
                for info in component["serviceHealthReports"]:
                    regions[component["regionName"]].append(
                        {
                            "name": info["serviceName"],
                            "status": info["serviceStatus"],
                            "incident": info["incidents"],
                        }
                    )
    return {
        "page": {"updated_at": statusJson["page"]["updated_at"]},
        "status": {"description": statusJson["status"]["description"]},
        "components": regions,
    }


@app.route("/jira/select")
def returnSummaryJiraSoftware():
    jsonSumary = utils.service.selectRequestUrl(
        "https://jira-software.status.atlassian.com/api/v2/summary.json"
    )

    keySumaryPage = ["updated_at"]

    keySumaryStatus = ["description"]

    keySumaryComponents = ["name", "status", "updated_at"]

    filteredSumaryPage = {
        item: jsonSumary["page"].get(item)
        if item in jsonSumary["page"]
        else jsonSumary.get(item)
        for item in keySumaryPage
    }
    filteredSumaryStatus = {
        item: jsonSumary["status"].get(item)
        if item in jsonSumary["status"]
        else jsonSumary.get(item)
        for item in keySumaryStatus
    }
    filteredSumaryComponents = []

    for i in jsonSumary["components"]:
        filteredSumaryComponents.append(
            {
                item: jsonSumary["components"][0].get(item)
                if item in jsonSumary["components"][0]
                else jsonSumary.get(item)
                for item in keySumaryComponents
            }
        )

    objectSumary = {
        "page": filteredSumaryPage,
        "status": filteredSumaryStatus,
        "components": filteredSumaryComponents,
    }

    return objectSumary
