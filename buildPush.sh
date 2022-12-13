#!/bin/bash
docker build -t guestros/kubernetes-job-monitor-simple:latest . 
docker push guestros/kubernetes-job-monitor-simple:latest