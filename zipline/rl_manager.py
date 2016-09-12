import abc
from six import with_metaclass
from collections import namedtuple
from intervaltree import IntervalTree
from itertools import groupby


Restriction = namedtuple(
    'Restriction', ['sid',
                    'effective_date',
                    'expiry_date',
                    'restriction_type']
)


class RestrictionHistoryOverlapError(Exception):
    pass


class RestrictionsController(object):

    def __init__(self):
        self.rl_managers = []

    def add_restrictions(self, rl_manager):
        self.rl_managers.append(rl_manager)

    def restriction(self, sid, dt):
        restrictions = [rlm.restriction(sid, dt) for rlm in self.rl_managers]
        if 'liquidate' in restrictions:
            return 'liquidate'
        elif 'freeze' in restrictions:
            return 'freeze'
        elif 'long_only' in restrictions and 'reduce_only' in restrictions:
            return 'freeze'
        elif 'long_only' in restrictions:
            return 'long_only'
        elif 'reduce_only' in restrictions:
            return 'reduce_only'
        else:
            return 'allowed'

    def is_restricted(self, sid, dt):
        return any([rlm.is_restricted(sid, dt) for rlm in self.rl_managers])


class RLManager(with_metaclass(abc.ABCMeta)):

    def __init__(self, **kwargs):
        pass

    @abc.abstractmethod
    def restriction(self, sid, dt):
        raise NotImplementedError

    @abc.abstractmethod
    def is_restricted(self, sid, dt):
        raise NotImplementedError


class InMemoryRLManager(RLManager):

    def __init__(self, restrictions):
        super(InMemoryRLManager, self).__init__()

        self.restriction_history = {}
        for sid, restrictions_for_sid in \
                groupby(restrictions, lambda x: x.sid):
            interval_tree = IntervalTree()
            for rstn in restrictions_for_sid:
                overlap = \
                    interval_tree.search(rstn.effective_date, rstn.expiry_date)
                if overlap:
                    overlap = list(overlap)[0]
                    overlap_restriction = Restriction(sid,
                                                      overlap.begin,
                                                      overlap.end,
                                                      overlap.data)
                    raise RestrictionHistoryOverlapError(
                        '%s overlaps with %s' % (rstn, overlap_restriction))
                else:
                    interval_tree[rstn.effective_date: rstn.expiry_date] = \
                        rstn.restriction_type

            self.restriction_history[sid] = interval_tree

    def restriction(self, sid, dt):
        try:
            restrictions_for_sid = self.restriction_history[sid]
            return list(restrictions_for_sid[dt])[0].data
        except (KeyError, IndexError):
            return 'allowed'

    def is_restricted(self, sid, dt):
        return self.restriction(sid, dt) != 'allowed'
