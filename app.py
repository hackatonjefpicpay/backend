from flask import Flask
import utils.service
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)


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
    jsonSummary = utils.service.selectRequestUrl(
        "https://jira-software.status.atlassian.com/api/v2/summary.json"
    )

    keySummaryPage = ["updated_at"]
    keySummaryStatus = ["description"]
    keySummaryComponents = ["name", "status", "updated_at"]

    filteredSummaryPage = {
        item: jsonSummary["page"].get(item)
        if item in jsonSummary["page"]
        else jsonSummary.get(item)
        for item in keySummaryPage
    }

    filteredSummaryStatus = {
        item: jsonSummary["status"].get(item)
        if item in jsonSummary["status"]
        else jsonSummary.get(item)
        for item in keySummaryStatus
    }

    filteredSummaryComponents = []
    for i in jsonSummary["components"]:
        filteredSummaryComponents.append(
            {
                item: i.get(item) if item in i else jsonSummary.get(item)
                for item in keySummaryComponents
            }
        )

    objectSummary = {
        "page": filteredSummaryPage,
        "status": filteredSummaryStatus,
        "components": filteredSummaryComponents,
        "incidents": jsonSummary["incidents"],
    }

    return objectSummary


@app.route("/oracle/countStatus")
def countOracleServiceStatus():
    regions = {}
    dataResponse = findAllStatusInfoOracle()
    for i in dataResponse["components"]:
        status = {
            "normal": 0,
            "warn": 0,
            "down": 0,
            "total": 0,
            "percentualNormal": "0",
            "percentualWarn": "0",
            "percentualDown": "0",
        }
        for j in dataResponse["components"][i]:
            status["total"] += 1
            if j["status"] == "NormalPerformance":
                status["normal"] += 1
            elif j["status"] == "Service Down":
                status["down"] += 1
            else:
                status["warn"] += 1
            regions[i] = status

            status[
                "percentualNormal"
            ] = f'{round((status["normal"] * 100) / (status["total"]),2)}%'
            status[
                "percentualDown"
            ] = f'{round((status["down"] * 100) / (status["total"]), 2)}%'
            status[
                "percentualWarn"
            ] = f'{round((status["warn"] * 100) / (status["total"]),2)}%'

    return regions


@app.route("/jira/countStatus")
def countComponentsJiraSoftware():
    responseSummary = returnSummaryJiraSoftware()

    countComponentsJiraSoftware = len(responseSummary["components"])

    operational = sum(
        1 for i in responseSummary["components"] if i["status"] == "operational"
    )
    degraded_performance = sum(
        1
        for i in responseSummary["components"]
        if i["status"] == "degraded_performance"
    )
    partial_outage = sum(
        1 for i in responseSummary["components"] if i["status"] == "partial_outage"
    )
    major_outage = sum(
        1 for i in responseSummary["components"] if i["status"] == "major_outage"
    )

    countObject = {
        "donw": major_outage,
        "normal": operational,
        "percentualDown": f"{major_outage/ countComponentsJiraSoftware * 100:.1f}%"
        if countComponentsJiraSoftware
        else "0.00%",
        "percentualNormal": f"{operational / countComponentsJiraSoftware * 100:.1f}%"
        if countComponentsJiraSoftware
        else "0.00%",
        "percentualWarn": f"{(partial_outage + degraded_performance) / countComponentsJiraSoftware * 100:.1f}%"
        if countComponentsJiraSoftware
        else "0.00%",
        "total": countComponentsJiraSoftware,
        "warn": degraded_performance + partial_outage,
    }

    return countObject


@app.route("/jira/historicalAcidents")
def returnIncidentsHistoricJiraSoftware():
    jsonIncidents = utils.service.selectRequestUrl(
        "https://jira-software.status.atlassian.com/api/v2/incidents.json"
    )

    arrayIncidents = jsonIncidents["incidents"]

    filteredIncidentsHistoric = []

    for i in arrayIncidents:
        filteredIncidentsHistoric.append(
            {
                "name": i["name"],
                "status": i["status"],
                "created_at": i["created_at"],
                "impact": i["impact"],
            }
        )

    return filteredIncidentsHistoric


@app.route("/aws/select")
def index():
    try:
        return utils.service.get_AWS_status("Sao Paulo")
    except Exception as error:
        return json.dumps({"status": 500, "error": error})
