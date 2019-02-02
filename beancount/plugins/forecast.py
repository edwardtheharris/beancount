"""An example of adding a forecasting feature to Beancount via a plugin.

This entry filter plugin uses existing syntax to define and automatically
inserted transactions in the future based on a convention. It serves mostly as
an example of how you can experiment by creating and installing a local filter,
and not so much as a serious forecasting feature (though the experiment is a
good way to get something more general kickstarted eventually, I think the
concept would generalize nicely and should eventually be added as a comon
feature of Beancount).

A user can create a create a transaction like this:

  2014-03-08 # "Electricity bill [MONTHLY]""
    Expenses:Electricity 			50.10 USD
    Assets:Checking			       -50.10 USD

and new transactions will be created monthly for the following year.
Note the use of the '#' flag and the word 'MONTHLY' which defines the
periodicity.

The number of recurrences can optionally be specified either by providing an
end date or by specifying the number of times that the transaction will be
repeated. For example:

  2014-03-08 # "Electricity bill [MONTHLY UNTIL 2019-12-31]""
    Expenses:Electricity 			50.10 USD
    Assets:Checking			       -50.10 USD

  2014-03-08 # "Electricity bill [MONTHLY REPEAT 10 TIMES]""
    Expenses:Electricity 			50.10 USD
    Assets:Checking			       -50.10 USD

Transactions can be also be repeated at yearly intervals, e.g.:

  2014-03-08 # "Electricity bill [YEARLY REPEAT 10 TIMES]""
    Expenses:Electricity 			50.10 USD
    Assets:Checking			       -50.10 USD
"""

__copyright__ = "Copyright (C) 2014-2017  Martin Blais"
__license__ = "GNU GPLv2"

import datetime
import logging
import re

from dateutil import rrule

from beancount.core import data

__plugins__ = ('forecast_plugin',)

LOG = logging.getLogger('forecast')


def forecast_plugin(entries, options_map):
    """An example filter that piggybacks on top of the Beancount input syntax to
    insert forecast entries automatically. This functions accepts the return
    value of beancount.loader.load_file() and must return the same type of output.

    Args:
      entries: a list of entry instances
      options_map: a dict of options parsed from the file
    Returns:
      A tuple of entries and errors.
    """

    periodicities = {
        'YEARLY': rrule.YEARLY,
        'MONTHLY': rrule.MONTHLY,
        'BIWEEKLY': rrule.WEEKLY,
    }
    LOG.info(options_map)

    # Filter out forecast entries from the list of valid entries.
    forecast_entries = []
    filtered_entries = []
    for entry in entries:
        if (isinstance(entry, data.Transaction) and entry.flag == '#'):
            outlist = forecast_entries
        else:
            outlist = filtered_entries
        outlist.append(entry)

    # Generate forecast entries up to the end of the current year.
    new_entries = []
    for entry in forecast_entries:
        # Parse the periodicity.
        match = re.search(r'(^.*)\[(MONTHLY|YEARLY|BIWEEKLY)'
                          r'(\s+REPEAT\s+([1-9][0-9]*)\s+TIMES)'
                          r'?(\s+UNTIL\s+([0-9\-]+))?\]', entry.narration)
        if not match:
            new_entries.append(entry)
            continue
        forecast_narration = match.group(1).strip()
        forecast_interval = periodicities.get(match.group(2).strip())
        forecast_periodicity = {
            'dtstart': entry.date,
            'count': # e.g., [MONTHLY REPEAT 3 TIMES]:
                int(match.group(4)) if match.group(4) else None,
            'interval':
                2 if match.group(2).strip() == 'BIWEEKLY' else 1,
            'until': # e.g., [MONTHLY UNTIL 2020-01-01]:
                datetime.datetime.strptime(match.group(6), '%Y-%m-%d').date()
                if match.group(5)
                else datetime.date(datetime.date.today().year, 12, 31),
        }

        print(forecast_periodicity)
        # Generate a new entry for each forecast date.
        forecast_dates = [dt.date() for dt in rrule.rrule(forecast_interval,
                                                          **forecast_periodicity)]
        for forecast_date in forecast_dates:
            forecast_entry = entry._replace(date=forecast_date,
                                            narration=forecast_narration)
            new_entries.append(forecast_entry)

    # Make sure the new entries inserted are sorted.
    new_entries.sort(key=data.entry_sortkey)

    return (filtered_entries + new_entries, [])
