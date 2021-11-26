#!/usr/bin/env python3

# copied and modified from https://gist.github.com/tetrillard/4e1ed77cebb5fab42989da3bf944fd4e

import sys
import requests
import urllib3
import json
from types import SimpleNamespace as Namespace
from feedgen.feed import FeedGenerator

output = ''
if len(sys.argv) > 2:
    output = sys.argv[1]

fg = FeedGenerator()
fg.id("https://hackerone.com/hacktivity")
fg.link(href="https://hackerone.com/hacktivity")
fg.title("HackerOne Hacktivity")
fg.description("HackerOne Hacktivity")

url = "https://hackerone.com/graphql"
headers = {'Content-Type':'application/json'}
data = '{"operationName":"HacktivityPageQuery","variables":{"querystring":"","where":{"report":{"disclosed_at":{"_is_null":false}}},"orderBy":null,"secureOrderBy":{"latest_disclosable_activity_at":{"_direction":"DESC"}},"count":50},"query":"query HacktivityPageQuery($querystring: String, $orderBy: HacktivityItemOrderInput, $secureOrderBy: FiltersHacktivityItemFilterOrder, $where: FiltersHacktivityItemFilterInput, $count: Int, $cursor: String) {\n  hacktivity_items(first: $count, after: $cursor, query: $querystring, order_by: $orderBy, secure_order_by: $secureOrderBy, where: $where) {\n    ...HacktivityList\n  }\n}\n\nfragment HacktivityList on HacktivityItemConnection {\n    edges {\n    node {\n      ... on HacktivityItemInterface {\n        ...HacktivityItem\n      }\n    }\n  }\n}\n\nfragment HacktivityItem on HacktivityItemUnion {\n  ... on Undisclosed {\n    id\n    ...HacktivityItemUndisclosed\n  }\n  ... on Disclosed {\n    ...HacktivityItemDisclosed\n  }\n  ... on HackerPublished {\n    ...HacktivityItemHackerPublished\n  }\n}\n\nfragment HacktivityItemUndisclosed on Undisclosed {\n  reporter {\n    username\n    ...UserLinkWithMiniProfile\n  }\n  team {\n    handle\n    name\n     url\n    ...TeamLinkWithMiniProfile\n  }\n  latest_disclosable_action\n  latest_disclosable_activity_at\n  requires_view_privilege\n  total_awarded_amount\n  currency\n}\n\nfragment TeamLinkWithMiniProfile on Team {\n  handle\n  name\n }\n\nfragment UserLinkWithMiniProfile on User {\n  username\n}\n\nfragment HacktivityItemDisclosed on Disclosed {\n  reporter {\n    username\n    ...UserLinkWithMiniProfile\n  }\n  team {\n    handle\n    name\n    url\n    ...TeamLinkWithMiniProfile\n  }\n  report {\n    title\n    substate\n    url\n  }\n  latest_disclosable_activity_at\n  total_awarded_amount\n  severity_rating\n  currency\n}\n\nfragment HacktivityItemHackerPublished on HackerPublished {\n  reporter {\n    username\n    ...UserLinkWithMiniProfile\n  }\n  team {\n    handle\n    name\n    medium_profile_picture: profile_picture(size: medium)\n    url\n    ...TeamLinkWithMiniProfile\n  }\n  report {\n    url\n    title\n    substate\n  }\n  latest_disclosable_activity_at\n  severity_rating\n}\n"}'.replace('\n','\\n')

s = requests.session()
e = s.post(url, data, headers=headers)
j = json.loads(e.text, object_hook=lambda d: Namespace(**d))
for i in j.data.hacktivity_items.edges:
    report = i.node
    published_at = report.latest_disclosable_activity_at
    report_url = report.report.url
    reporter = report.reporter.username
    bounty = str(int(report.total_awarded_amount)) if report.total_awarded_amount else 'N/A'
    title = report.report.title
    team = report.team.name
    #print('%s | %s | %s | %s' % (team, reporter, bounty, title))
    fe = fg.add_entry()
    fe.id(report_url)
    fe.content( "")
    fe.published(published_at)
    fe.link(href=report_url)
    a = s.get(report_url + '.json')
    x = a.json()
    if 'vulnerability_information_html' in x:
        content = x['vulnerability_information_html']
    else:
        content = x['vulnerability_information']
    fe.content('<a href="%s">%s</a><br/>%s' % (report_url, report_url, content))
    fe.title('%s | %s | %s | %s' % (team, reporter, bounty, title))

fg.atom_file(output + 'hackerone_atom.xml')
fg.rss_file(output + 'hackerone_rss.xml')
