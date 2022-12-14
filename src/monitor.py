from datetime import datetime, timedelta
from os import environ
from subprocess import PIPE, run

from elasticsearch import Elasticsearch

res = run("kubectl get jobs --all-namespaces --field-selector status.successful=0".split(),  capture_output=True, text=True).stdout

es = Elasticsearch([environ.get("ELASTICSEARCH_URL", "http://localhost:9200")])

def convert(k8sresult):
    k8sresult = k8sresult.split("\n")[1:-1]
    results = []
    for res in k8sresult:
        results.append(res.split())
    return results

def convertAge(agestr):
    if "s" in agestr and len(agestr) <= 3:
        return datetime.utcnow() - timedelta(seconds=int(agestr[:-1]))
    if "m" in agestr:
        return datetime.utcnow() - timedelta(minutes=int(agestr.split("m")[0]))
    elif "h" in agestr:
        return datetime.utcnow() - timedelta(hours=int(agestr.split("h")[0]))
    else:
        raise ValueError("age string not in correct format: ", agestr)
    
def getLogs(namespace, name):
    logs = run(f"kubectl logs -n {namespace} job/{name}".split(), capture_output=True, text=True)
    if len(logs.stdout) == 0:
        raise ValueError(logs.stderr)
    return logs.stdout

if len(res) == 0:
    print("all jobs successful, exit now")
else:
    results = convert(res)
    for namespace, name, completions, duration, age in results:
        timestamp = convertAge(age)
        logs = getLogs(namespace, name)
        print(name, logs)
        errorObj = {
            "@timestamp": timestamp.isoformat(),
            "namespace": namespace,
            "jobname": name.rsplit("-", 1)[0],
            "containername": name,
            "failed" : True,
            "logs" : logs
        }
        es.index(index="k8s-job-logs-%s" % datetime.utcnow().strftime("%Y-%m"), 
                id = name,
                document=errorObj)
