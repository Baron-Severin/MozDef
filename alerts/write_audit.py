#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# This code alerts on every successfully opened session on any of the host from a given list

from lib.alerttask import AlertTask
from mozdef_util.query_models import SearchQuery, TermMatch, QueryStringMatch, PhraseMatch


class WriteAudit(AlertTask):
    def main(self):
        self.parse_config('write_audit.conf', ['skipprocess'])
        search_query = SearchQuery(minutes=15)

        search_query.add_must([
            TermMatch('category', 'write'),
            TermMatch('details.auditkey', 'audit'),
        ])

        for processname in self.config.skipprocess.split():
            search_query.add_must_not(PhraseMatch('details.processname', processname))

        self.filtersManual(search_query)
        self.searchEventsAggregated('details.originaluser', samplesLimit=10)
        self.walkAggregations(threshold=2)

    def onAggregation(self, aggreg):
        category = 'write'
        severity = 'WARNING'
        tags = ['audit']

        summary = ('{0} Filesystem write(s) to an auditd path by {1}'.format(aggreg['count'], aggreg['value'], ))
        hostnames = self.mostCommon(aggreg['allevents'],'_source.hostname')
        #did they modify more than one host?
        #or just modify an existing configuration more than once?
        if len(hostnames) > 1:
            for i in hostnames[:5]:
                summary += ' on {0} ({1} hosts)'.format(i[0], i[1])

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)
