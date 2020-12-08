# gitlab-issues-parser

## Project

### Gitlab Issue Log Parser

## Author

### James Anderton

## Date

### 12/08/2020

## Purpose

This is a mediator script that will receive a webhook sent from a
GitLab Issue being created. It will parse the json payload, looking for
the object_attributes[description] field. In this field it will trigger on
KEYWORD:Value pairs and separate them for use in a POST request. Finally
It will print out the equivalent Curl request for debugging use.
